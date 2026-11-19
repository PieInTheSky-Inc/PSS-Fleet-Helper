import asyncio
import threading
from abc import ABC, abstractmethod

import pssapi

from .pusher import PssPusherChannel, PssPusherClientAsync


class PssChatListener(ABC):
    @abstractmethod
    def __init__(self, name: str, *args, **kwargs):
        self.name = name

    @abstractmethod
    def on_message(self, message: pssapi.entities.Message) -> None:
        raise NotImplementedError("Subclasses must implement the on_message method.")


class PssChatListenerAsync(ABC):
    @abstractmethod
    def __init__(self, name: str, *args, **kwargs):
        self.name = name

    @abstractmethod
    async def on_message(self, message: pssapi.entities.Message) -> None:
        raise NotImplementedError("Subclasses must implement the on_message method.")


class NullPssChatListener(PssChatListener):
    def __init__(self, name: str = "NullListener"):
        super().__init__(name)

    def on_message(self, message: pssapi.entities.Message) -> None:
        pass


class PssChatChannel:
    def __init__(self, channel_key: str):
        self.channel_key: str = channel_key
        self._listeners: dict[str, PssChatListener | PssChatListenerAsync] = {}
        self.pusher_channel: PssPusherChannel = PssPusherChannel(channel_key)
        self.pusher_channel.on_message(self._on_message)

    @property
    def listeners_count(self) -> int:
        return len(self._listeners)

    def subscribe(self, listener: PssChatListener):
        if listener.name in self._listeners:
            raise ValueError(f"A listener with the name '{listener.name}' is already subscribed to this channel.")

        self._listeners[listener.name] = listener

    def unsubscribe(self, listener_name: str):
        if listener_name in self._listeners:
            del self._listeners[listener_name]

    async def _on_message(self, data: dict):
        message = pssapi.entities.Message(data)
        for listener in self._listeners.values():
            if isinstance(listener, PssChatListener):
                listener.on_message(message)
            elif isinstance(listener, PssChatListenerAsync):
                await listener.on_message(message)


class PssChatLoggerManager:
    def __init__(self):
        self._channels: dict[str, PssChatChannel] = {}
        self._pusher: PssPusherClientAsync = PssPusherClientAsync()
        self._pusher_thread: threading.Thread | None = None

    def subscribe_to_channel(self, channel_key: str, listener: PssChatListener):
        pss_channel = self.get_pss_channel(channel_key)
        pss_channel.subscribe(listener)

    def unsubscribe_from_channel(self, channel_key: str, listener_name: str):
        pss_channel = self.get_pss_channel(channel_key)
        pss_channel.unsubscribe(listener_name)
        if pss_channel.listeners_count == 0:
            self.remove_pss_channel(channel_key)

    def get_pss_channel(self, channel_key: str) -> PssChatChannel:
        if channel_key not in self._channels:
            pss_channel = PssChatChannel(channel_key)
            self._channels[channel_key] = pss_channel
            self._pusher.add(pss_channel.pusher_channel)
        return self._channels[channel_key]

    def remove_pss_channel(self, channel_key: str) -> None:
        pss_channel = self.get_pss_channel(channel_key)
        self._pusher.remove(pss_channel.pusher_channel)
        del self._channels[channel_key]

    def start(self, access_token: str, user_id: str | int):
        channel_count = len(self._channels)
        listener_count = sum(channel.listeners_count for channel in self._channels.values())
        print(f"[PssChatLoggerManager.start] Starting PSS Chat Logger Manager with {channel_count} channels with {listener_count} listeners.")

        if self._pusher_thread and self._pusher_thread.is_alive():
            return

        self._thread = threading.Thread(
            target=lambda: asyncio.run(self._pusher.run(access_token, user_id)),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._pusher.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._thread = None

    def dispose(self):
        if self._pusher_thread and self._pusher_thread.is_alive():
            raise RuntimeError(f"Cannot dispose of the {PssChatLoggerManager.__name__} while running a Pusher listener.")

        for channel_key in list(self._channels.keys()):
            self.remove_pss_channel(channel_key)
