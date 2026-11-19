import pssapi


class PusherWithRemove(pssapi.pusher.Pusher):
    @classmethod
    def remove(cls, channel: pssapi.pusher.Channel) -> None:
        if channel.name in cls._channels:
            del cls._channels[channel.name]


__all__ = [
    "PusherWithRemove",
]
