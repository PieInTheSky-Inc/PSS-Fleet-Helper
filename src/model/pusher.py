from inspect import isawaitable
from json import dumps, loads
from platform import system
from typing import Any, Optional

import pssapi
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pssapi.constants import PUSHER_APP_CLUSTER, PUSHER_APP_ID
from pssapi.exc import PusherConnectionClosed
from pssapi.pusher.channel import Channel
from websockets.client import connect


# TODO: Add error handling, add ping/pong timeout
class Pusher:
    def __init__(self, *, client_name: str | None = None, protocol_version: int | None = 7, connection_timeout: int | None = 305, ping_interval: int | None = 120, socket_id: str | None = ""):
        # Should be of the form `platform-library`
        self.client: str = client_name or f"{system()}-pssapi"

        # Pusher protocol (as of 6/1/23, protocol 7)
        self.protocol: int = 7 if protocol_version is None else protocol_version

        # Time values
        self.connection_timeout: int = 305 if connection_timeout is None or connection_timeout <= 0 else connection_timeout
        self.ping_interval: int = 120 if ping_interval is None or ping_interval <= 0 else ping_interval

        self._socket_id = "" if socket_id is None else socket_id

        self._connection = None
        self._scheduler = AsyncIOScheduler()

        self._channels: dict[str, Channel] = {}

    async def _connect_to_pusher(self) -> None:
        host = f"ws://ws-{PUSHER_APP_CLUSTER}.pusher.com"
        url = f"{host}/app/{PUSHER_APP_ID}?client={self.client}&version={pssapi.__version__}&protocol={self.protocol}"

        self._connection = await connect(url)
        await self._send_ping()

    async def _send_event(self, event_name: str, data: Any, channel: Optional[str] = None) -> None:
        event = {"event": event_name, "data": data}
        if channel:
            event["channel"] = channel

        event = dumps(event)
        await self._connection.send(event)

    # Ping pong
    async def _send_ping(self) -> None:
        await self._send_event("pusher:ping", "")

    async def _send_pong(self) -> None:
        await self._send_event("pusher:pong", "")

    def _reset_connection_timeout(self, job_id: Any) -> None:
        self._scheduler.reschedule_job(job_id, trigger=IntervalTrigger(seconds=self.connection_timeout))

    async def _connection_closed(self, code: Optional[int] = None, error_message: Optional[str] = "") -> None:
        await self._connection.close()

        if code or error_message:
            raise PusherConnectionClosed(
                f"""Connection closed.
Code: {code}
Message: {error_message}""",
                code,
                error_message,
            )

        raise PusherConnectionClosed("Connection timed out / closed with unknown cause.")

    # Scheduled tasks
    def _start_timers(self) -> None:
        job_id = self._scheduler.add_job(self._connection_closed, IntervalTrigger(seconds=self.connection_timeout)).id
        self._scheduler.add_job(self._send_ping, IntervalTrigger(seconds=self.ping_interval))

        return job_id

    async def _subscribe(self, channel: Channel, token: Optional[str] = "") -> None:
        if channel.private and not token:
            raise ValueError("Token required if channel is private.")

        data = {"channel": channel.name, "auth": await channel._auth(token, self._socket_id) if channel.private else "", "channel_data": "{}"}
        await self._send_event("pusher:subscribe", data)

    def add(self, channel: Channel) -> None:
        """
        Add a new channel to subscribe to
        Args:
            - `channel` - The channel to subscribe to
        """
        self._channels[channel.name] = channel

    async def _handle_message(self, event: str, data: dict, channel: Optional[str] = "", token: Optional[str] = "") -> None:
        if event == "pusher:connection_established":
            self._socket_id = data["socket_id"]

            for channel_name in self._channels.keys():
                channel = self._channels[channel_name]

                await self._subscribe(channel, token)

        if event == "pusher:error":
            return await self._connection_closed(data["code"], data["message"])

        if channel and event == "message":
            channel_class = self._channels.get(channel)
            if not channel_class:
                return

            callback = channel_class.callback
            if isawaitable(callback):
                return await callback(data)

            return callback(data)

    def _keep_persistent_connection(self, token: str, user_id: int) -> None:
        if not token and not user_id:
            return

        if token and not user_id:
            raise RuntimeError("Token specified but not user_id")

        if user_id and not token:
            raise RuntimeError("user_id specified but no token")

        channel = Channel(f"private-user-{user_id}", private=True)
        self.add(channel)

    async def run(self, token: Optional[str] = "", user_id: Optional[int] = 0) -> None:
        """
        Start the Pusher client
        Args:
            - `token`: Account-binded token (required to auth/keep persistent connection)
            - `user_id`: User ID of the account (acquired through `SearchUsers`)
        """
        job_id = self._start_timers()
        self._scheduler.start()

        await self._connect_to_pusher()
        self._keep_persistent_connection(token, user_id)

        while True:
            message = await self._connection.recv()
            message = loads(message)
            self._reset_connection_timeout(job_id)

            event = message["event"]
            data = loads(message["data"]) if isinstance(message["data"], str) else message["data"]
            channel = message["channel"] if message.get("channel") else ""

            await self._handle_message(event, data, channel, token)

    def remove(self, channel: pssapi.pusher.Channel) -> None:
        if channel.name in self._channels:
            del self._channels[channel.name]


__all__ = [
    "Pusher",
]
