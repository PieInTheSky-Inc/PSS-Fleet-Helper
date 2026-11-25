import asyncio
import inspect
import json
import platform
from typing import Any, Callable

import pssapi
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pssapi.constants import PUSHER_APP_CLUSTER, PUSHER_APP_ID, PUSHER_AUTH_URL
from pssapi.exc import PusherConnectionClosed
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed as ConnectionClosedError


LOGGER = logging.getLogger("pss_fleet_helper.pusher")
SCHEDULER_JOB_DEFAULTS = {
    "misfire_grace_time": 5,
}


class PusherChannel:
    def __init__(self, name: str, private: bool, endpoint: str, callback: Callable | None = None) -> None:
        """
        Create a new `Channel` instance
        Args:
            `name` - Name of the channel
            `endpoint` - Authentication endpoint
            `private` - Whether the channel is private (requires `token` to be specified)
        """
        self.name: str = name
        self.endpoint: str = endpoint
        self.private: bool = bool(private or False)
        self.callback = lambda _: None

    def on_message(self, callback: Callable | None) -> None:
        """
        Set a callback to be called when a message is received
        Args:
            `callback` - The function to be called, `lambda _: None` if not specified
        """
        if callback:
            self.callback = callback

        else:
            self.callback = lambda _: None

    async def _auth(self, token: str, socket_id: str) -> str:
        data = {
            "channel_name": self.name,
            "socket_id": socket_id,
        }
        endpoint = f"{self.endpoint}?accessToken={token}"

        async with ClientSession() as session:
            async with session.post(endpoint, data=data) as response:
                if not response.ok:
                    msg = "Couldn't authenticate connection"
                    LOGGER.critical(msg)
                    raise RuntimeError(msg)

                return json.loads(await response.text())["auth"]


class PssPusherChannel(PusherChannel):
    def __init__(self, name: str, private: bool = False, callback: Callable | None = None):
        super().__init__(name, private, PUSHER_AUTH_URL, callback=callback)


# TODO: Add error handling, add ping/pong timeout
class PusherClientAsync:
    def __init__(
        self,
        pusher_app_cluster: str,
        pusher_app_id: str,
        pusher_auth_url: str,
        *,
        client_name: str | None = None,
        protocol_version: int | None = 7,
        connection_timeout: int | None = 305,
        ping_interval: int | None = 120,
        socket_id: str | None = "",
        scheduler_job_defaults: dict[str, Any] | None = None,
    ):
        self.pusher_app_cluster: str = pusher_app_cluster
        self.pusher_app_id: str = pusher_app_id
        self.pusher_auth_url: str = pusher_auth_url

        # Should be of the form `platform-library`
        self.client_name: str = client_name or f"{platform.system()}-pssapi"

        # Pusher protocol (as of 6/1/23, protocol 7)
        self.protocol_version: int = 7 if protocol_version is None else protocol_version

        # Time values
        self.connection_timeout: int = 305 if connection_timeout is None or connection_timeout <= 0 else connection_timeout
        self.ping_interval: int = 120 if ping_interval is None or ping_interval <= 0 else ping_interval

        self.socket_id: str = "" if socket_id is None else socket_id

        self._connection: ClientConnection | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._scheduler: AsyncIOScheduler | None = None

        self._channels: dict[str, PusherChannel] = {}
        self._stop_requested: bool = False
        self._scheduler_job_defaults: dict[str, Any] = dict(scheduler_job_defaults if scheduler_job_defaults else SCHEDULER_JOB_DEFAULTS)

    async def _connect_to_pusher(self) -> None:
        host = f"ws://ws-{PUSHER_APP_CLUSTER}.pusher.com"
        url = f"{host}/app/{PUSHER_APP_ID}?client={self.client_name}&version={pssapi.__version__}&protocol={self.protocol_version}"

        self._connection = await connect(url)
        await self._send_ping()

    async def _send_event(self, event_name: str, data: Any, channel: str | None = None) -> None:
        event = {"event": event_name, "data": data}
        if channel:
            event["channel"] = channel

        event = json.dumps(event)
        await self._connection.send(event)

    # Ping pong
    async def _send_ping(self) -> None:
        await self._send_event("pusher:ping", "")

    async def _send_pong(self) -> None:
        await self._send_event("pusher:pong", "")

    def _reset_connection_timeout(self, job_id: Any) -> None:
        self._scheduler.reschedule_job(job_id, trigger=IntervalTrigger(seconds=self.connection_timeout))

    async def _connection_closed(self, code: int | None = None, error_message: str | None = "") -> None:
        await self._connection.close()

        if code or error_message:
            msg = f"Connection closed.\nCode: {code}\nMessage: {error_message}"
        else:
            msg = "Connection timed out / closed with unknown cause."
            
        LOGGER.error(msg)
        raise PusherConnectionClosed("Connection timed out / closed with unknown cause.")

    # Scheduled tasks
    def _start_timers(self) -> str:
        job_id = self._scheduler.add_job(self._connection_closed, IntervalTrigger(seconds=self.connection_timeout)).id
        self._scheduler.add_job(self._send_ping, IntervalTrigger(seconds=self.ping_interval))

        return job_id

    async def _subscribe(self, channel: PusherChannel, token: str | None = "") -> None:
        if channel.private and not token:
            raise ValueError("Token required if channel is private.")

        data = {"channel": channel.name, "auth": await channel._auth(token, self.socket_id) if channel.private else "", "channel_data": "{}"}
        await self._send_event("pusher:subscribe", data)

    async def _handle_message(self, event: str, data: dict, channel_name: str | None = "", token: str | None = "") -> None:
        if event == "pusher:connection_established":
            self.socket_id = data["socket_id"]

            for channel_name in self._channels.keys():
                channel = self._channels[channel_name]

                await self._subscribe(channel, token)

        if event == "pusher:error":
            return await self._connection_closed(data["code"], data["message"])

        if channel_name and event == "message":
            channel = self._channels.get(channel_name)
            if not channel:
                return

            callback = channel.callback
            if inspect.iscoroutinefunction(callback):
                return await callback(data)

            return callback(data)

    def _keep_persistent_connection(self, token: str, user_id: int) -> None:
        if not token and not user_id:
            return

        if token and not user_id:
            raise RuntimeError("Token specified but not user_id")

        if user_id and not token:
            raise RuntimeError("user_id specified but no token")

        channel = PusherChannel(f"private-user-{user_id}", True, self.pusher_auth_url)
        self.add(channel)

    async def _unsubscribe(self, channel: PusherChannel) -> None:
        await self._send_event("pusher:unsubscribe", {"channel": channel.name})

    def add(self, channel: PusherChannel, access_token: str | None = None) -> None:
        """
        Add a new channel to subscribe to
        Args:
            - `channel` - The channel to subscribe to
        """
        self._channels[channel.name] = channel

        if self.socket_id and self._connection and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._subscribe(channel, access_token),
                self._loop,
            )

    def remove(self, channel: PusherChannel) -> None:
        if channel.name in self._channels:
            del self._channels[channel.name]

            if self.socket_id and self._connection and self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._unsubscribe(channel),
                    self._loop,
                )

    async def run(self, token: str | None = "", user_id: int | None = 0) -> None:
        """
        Start the Pusher client
        Args:
            - `token`: Account-binded token (required to auth/keep persistent connection)
            - `user_id`: User ID of the account (acquired through `SearchUsers`)
        """
        self._loop = asyncio.get_running_loop()
        self._stop_requested = False

        self._scheduler = AsyncIOScheduler(job_defaults=self._scheduler_job_defaults)
        job_id = self._start_timers()
        self._scheduler.start()

        try:
            self._keep_persistent_connection(token, user_id)
            await self._connect_to_pusher()

            while not self._stop_requested:
                message = await self._connection.recv()

                message = json.loads(message)
                self._reset_connection_timeout(job_id)

                event = message["event"]
                data = json.loads(message["data"]) if isinstance(message["data"], str) else message["data"]
                channel = message["channel"] if message.get("channel") else ""

                await self._handle_message(event, data, channel, token)
        except ConnectionClosedError:
            pass
        finally:
            if self._scheduler and self._scheduler.running:
                self._scheduler.shutdown(wait=False)
                self._scheduler = None
            if self._connection:
                await self._connection.close()
                self._connection = None

    def stop(self) -> None:
        self._stop_requested = True

        if self._loop and self._loop.is_running():
            if self._connection:
                asyncio.run_coroutine_threadsafe(self._connection.close(), self._loop)

            if self._scheduler and self._scheduler.running:
                self._loop.call_soon_threadsafe(self._scheduler.shutdown, False)


class PssPusherClientAsync(PusherClientAsync):
    def __init__(self):
        super().__init__(PUSHER_APP_CLUSTER, PUSHER_APP_ID, PUSHER_AUTH_URL)


__all__ = [
    "PssPusherClientAsync",
]
