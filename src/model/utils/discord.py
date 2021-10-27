from asyncio import TimeoutError as _TimeoutError
from datetime import timedelta as _timedelta
import re as _re
from typing import Any as _Any
from typing import List as _List
from typing import Optional as _Optional
from typing import Protocol as _Protocol
from typing import Tuple as _Tuple

from discord import Message as _Message
from discord import Role as _Role
from discord import TextChannel as _TextChannel
from discord.errors import Forbidden as _Forbidden
from discord.errors import NotFound as _NotFound
from discord.abc import Messageable as _Messageable
from discord.ext.commands import Context as _Context
import emoji as _emoji

from .datetime import get_utc_now as _get_utc_now



# ---------- Typehints ----------

class WaitForCheck(_Protocol):
    def __call__(self, message_content: str, allow_abort: bool, allow_skip: bool, *args, **kwargs) -> bool:
        pass





# ---------- Constants ----------

__DEFAULT_FALSE_VALUES: _List[str] = ['no', 'n', 'false', '0', '👎']
__DEFAULT_TRUE_VALUES: _List[str] = ['yes', 'y', 'true', '1', '👍']
DEFAULT_INQUIRE_TIMEOUT: float = 120.0

__RX_CHANNEL_MENTION: _re.Pattern = _re.compile('<#(\d+)>')
__RX_EMOJI: _re.Pattern = _re.compile('<:\w+:(\d+)>')
__RX_ROLE_MENTION: _re.Pattern = _re.compile('<@&(\d+)>')
__RX_USER_MENTION: _re.Pattern = _re.compile('<@\!?(\d+)>')





# ---------- Public Functions ----------

def check_for_add_remove(message_content: str,
                            allow_abort: bool = True,
                            allow_skip: bool = False
                        ) -> bool:
    return check_for_boolean_string(message_content, allow_abort, allow_skip, ['add'], ['remove'])


def check_for_boolean_string(message_content: str,
                                allow_abort: bool,
                                allow_skip: bool,
                                true_values: _List[str],
                                false_values: _List[str]
                            ) -> bool:
    if not true_values:
        raise ValueError(f'Parameter \'true_values\' must not be None or empty!')
    if not false_values:
        raise ValueError(f'Parameter \'false_values\' must not be None or empty!')

    content_lower = message_content.lower()
    return message_content in true_values \
        or message_content in false_values \
        or (allow_abort and content_lower == 'abort') \
        or (allow_skip and content_lower == 'skip')


def check_for_channel_id_or_mention(message_content: str,
                                    allow_abort: bool,
                                    allow_skip: bool
                                ) -> bool:
    try:
        int(message_content)
        return True
    except:
        pass
    if __RX_CHANNEL_MENTION.match(message_content):
        return True
    content_lower = message_content.lower()
    return (allow_abort and content_lower == 'abort') \
        or (allow_skip and content_lower == 'skip')


def check_for_integer(message_content: str,
                        allow_abort: bool,
                        allow_skip: bool
                    ) -> bool:
    try:
        int(message_content)
        return True
    except:
        pass
    content_lower = message_content.lower()
    return (allow_abort and content_lower == 'abort') \
        or (allow_skip and content_lower == 'skip')


def check_for_member_id_name_or_mention(message_content: str,
                                            allow_abort: bool,
                                            allow_skip: bool
                                        ) -> bool:
    try:
        int(message_content)
        return True
    except:
        pass
    if __RX_USER_MENTION.match(message_content):
        return True
    content_lower = message_content.lower()
    return (allow_abort and content_lower == 'abort') \
        or (allow_skip and content_lower == 'skip')


def check_for_message_id(message_content: str,
                            allow_abort: bool = True,
                            allow_skip: bool = False
                        ) -> bool:
    try:
        int(message_content)
        return True
    except:
        pass
    content_lower = message_content.lower()
    return (allow_abort and content_lower == 'abort') \
        or (allow_skip and content_lower == 'skip')


def check_for_role_id_or_mention(message_content: str,
                                    allow_abort: bool,
                                    allow_skip: bool
                                ) -> bool:
    try:
        int(message_content)
        return True
    except:
        pass
    if __RX_ROLE_MENTION.match(message_content):
        return True
    content_lower = message_content.lower()
    return (allow_abort and content_lower == 'abort') \
        or (allow_skip and content_lower == 'skip')


def check_for_true_false(message: _Message) -> bool:
    return check_for_boolean_string(message, __DEFAULT_TRUE_VALUES, __DEFAULT_FALSE_VALUES)


def create_discord_link(guild_id: int, channel_id: _Optional[int] = None, message_id: _Optional[int] = None) -> str:
    result = f'https://discord.com/channels/{guild_id}'
    if channel_id:
        result += f'/{channel_id}'
        if message_id:
            result += f'/{message_id}'
    return result


async def fetch_message(channel: _TextChannel,
                        message_id: str
                        ) -> _Optional[_Message]:
    """
    Attempts to obtain a message in the specified `channel`.
    """
    try:
        message_id = int(message_id)
    except:
        message_id = None
    if message_id:
        try:
            return (await channel.fetch_message(message_id))
        except (_Forbidden, _NotFound):
            pass
    return None


def get_channel(ctx: _Context,
                channel_id_or_mention: str
                ) -> _Optional[_Messageable]:
    """
    Attempts to obtain a channel on the guild, `ctx` originates from.
    """
    try:
        channel_id = int(channel_id_or_mention)
    except:
        channel_id = None
    if channel_id is None:
        match = __RX_CHANNEL_MENTION.match(channel_id_or_mention)
        if match:
            channel_id = int(match.groups()[0])
    if channel_id:
        return ctx.guild.get_channel(channel_id)
    return None


def get_emoji(ctx: _Context,
                emoji: str
            ) -> _Optional[str]:
    """
    Attempts to obtain an emoji on the guild, `ctx` originates from.
    Returns either a unicode emoji or a Discord emoji `str` in format: `<:name:id>` or `None` if a Discord emoji does not exist or cannot be accessed.
    """
    emoji_list = _emoji.emoji_lis(emoji)
    if emoji_list:
        return emoji_list[0]['emoji']
    else:
        match = __RX_EMOJI.match(emoji)
        if match:
            emoji_id = int(match.groups()[0])
            result = ctx.bot.get_emoji(emoji_id)
            if result and ctx.guild == result.guild:
                return f'<:{result.name}:{result.id}>'
    return None


def get_role(ctx: _Context,
                role_id_or_mention: str
            ) -> _Optional[_Role]:
    """
    Attempts to obtain a role on the guild, `ctx` originates from.
    """
    try:
        role_id = int(role_id_or_mention)
    except:
        role_id = None
    if not role_id:
        match = __RX_ROLE_MENTION.match(role_id_or_mention)
        if match:
            role_id = int(match.groups()[0])
    if role_id:
        return ctx.guild.get_role(role_id)
    return None


def get_text_channel(ctx: _Context,
                        channel_id_or_mention: str
                    ) -> _Optional[_TextChannel]:
    """
    Attempts to obtain a text channel on the guild, `ctx` originates from.
    Only returns the channel, if the bot has permissions to see it.
    """
    result: _TextChannel = get_channel(ctx, channel_id_or_mention)
    if isinstance(result, _TextChannel) and result.permissions_for(ctx.guild.me).view_channel:
        return result
    return None


def get_member(ctx: _Context,
                member_id_mention_or_name: str
            ) -> _Optional[_Role]:
    """
    Attempts to obtain a member on the guild, `ctx` originates from.
    """
    result = None
    try:
        member_id = int(member_id_mention_or_name)
    except:
        member_id = None
    if not member_id:
        match = __RX_USER_MENTION.match(member_id_mention_or_name)
        if match:
            member_id = int(match.groups()[0])
    if member_id:
        result = ctx.guild.get_member(member_id)
    if not result:
        result = ctx.guild.get_member_named(member_id_mention_or_name)
    return result


async def inquire_for_add_remove(ctx: _Context,
                                    prompt_message: str,
                                    timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                    abort_text: _Optional[str] = None
                                ) -> _Tuple[_Optional[bool], bool, bool]:
    """
    Returns (`Optional[discord.Role]`, user_has_aborted, `False`)
    """
    return (await inquire_for_boolean(ctx, prompt_message, ['add'], ['remove'], timeout=timeout, abort_text=abort_text))


async def inquire_for_boolean(ctx: _Context,
                                prompt_text: str,
                                true_values: _Optional[_List[str]] = None,
                                false_values: _Optional[_List[str]] = None,
                                timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                abort_text: _Optional[str] = None,
                                skip_text: _Optional[str] = None,
                                respond_to_message: _Optional[_Message] = None
                            ) -> _Tuple[_Optional[bool], bool, bool]:
    f"""
    `true_values` defaults to {', '.join(__DEFAULT_TRUE_VALUES)} if `None` or empty.
    `false_values` defaults to {', '.join(__DEFAULT_FALSE_VALUES)} if `None` or empty.

    Returns (result: `Optional[discord.Role]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    result = None
    aborted = False
    skipped = False

    true_values = true_values or __DEFAULT_TRUE_VALUES
    false_values = false_values or __DEFAULT_FALSE_VALUES
    true_values_text = ', '.join(true_values)
    false_values_text = ', '.join(false_values)
    true_values_lower = [value.lower() for value in true_values]
    false_values_lower = [value.lower() for value in false_values]

    full_prompt_text = get_prompt_text(prompt_text, f'\'{true_values_text}\' or \'{false_values_text}\'', allow_abort, allow_skip)
    if respond_to_message:
        prompt_message = await respond_to_message.reply(full_prompt_text, mention_author=False)
    else:
        prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, true_values, false_values, check=check_for_boolean_string, timeout=timeout)
    if user_reply:
        content_lower = user_reply.content.strip().lower()
        aborted, skipped = __check_for_abort_or_skip(content_lower, allow_abort, allow_skip)
        if not (aborted or skipped):
            result = content_lower in true_values_lower or not (content_lower in false_values_lower)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return result, aborted, skipped


async def inquire_for_emoji(ctx: _Context,
                                prompt_text: str,
                                timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                abort_text: _Optional[str] = None,
                                skip_text: _Optional[str] = None
                            ) -> _Tuple[_Optional[str], bool, bool]:
    """
    Returns (emoji: `Optional[str]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    result = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, 'an emoji', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            result = get_emoji(ctx, content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return result, aborted, skipped



async def inquire_for_integer(ctx: _Context,
                            prompt_text: str,
                            timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                            abort_text: _Optional[str] = None,
                            skip_text: _Optional[str] = None
                        ) -> _Tuple[_Optional[int], bool, bool]:
    """
    Returns (integer: `Optional[int]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    result = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, 'an integer', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, check=check_for_integer, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            result = int(content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return result, aborted, skipped


async def inquire_for_member(ctx: _Context,
                                prompt_text: str,
                                timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                abort_text: _Optional[str] = None,
                                skip_text: _Optional[str] = None
                            ) -> _Tuple[_Optional[_Role], bool, bool]:
    """
    Returns (channel: `Optional[discord.TextChannel]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    member = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, 'a member mention, name or ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, check=check_for_member_id_name_or_mention, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            member = get_member(content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return member, aborted, skipped


async def inquire_for_message_confirmation(ctx: _Context,
                                            respond_to_message: _Message,
                                            prompt_text: str,
                                            timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                            abort_text: _Optional[str] = None,
                                            skip_text: _Optional[str] = None
                                        ) -> _Tuple[_Optional[bool], bool, bool]:
    """
    Returns (result: `bool`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    return (await inquire_for_boolean(ctx, prompt_text, timeout=timeout, abort_text=abort_text, skip_text=skip_text, respond_to_message=respond_to_message))


async def inquire_for_message_id(ctx: _Context,
                            channel: _TextChannel,
                            prompt_text: str,
                            timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                            abort_text: _Optional[str] = None,
                            skip_text: _Optional[str] = None
                        ) -> _Tuple[_Optional[_Role], bool, bool]:
    """
    Returns (role: `Optional[discord.Role]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    message = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, 'a message ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, check=check_for_message_id, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            message = await fetch_message(channel, content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return message, aborted, skipped


async def inquire_for_role(ctx: _Context,
                            prompt_text: str,
                            timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                            abort_text: _Optional[str] = None,
                            skip_text: _Optional[str] = None
                        ) -> _Tuple[_Optional[_Role], bool, bool]:
    """
    Returns (role: `Optional[discord.Role]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    role = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, 'a role mention or ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, check=check_for_role_id_or_mention, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            role = get_role(ctx, content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return role, aborted, skipped


async def inquire_for_text(ctx: _Context,
                                prompt_text: str,
                                timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                abort_text: _Optional[str] = None,
                                skip_text: _Optional[str] = None,
                            ) -> _Tuple[_Optional[str], bool, bool]:
    """
    Returns (input: `Optional[str]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    result = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, None, allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, check=check_for_integer, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            result = content
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return result, aborted, skipped


async def inquire_for_text_channel(ctx: _Context,
                                prompt_text: str,
                                timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                abort_text: _Optional[str] = None,
                                skip_text: _Optional[str] = None
                            ) -> _Tuple[_Optional[_Role], bool, bool]:
    """
    Returns (channel: `Optional[discord.TextChannel]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    channel = None
    aborted = False
    skipped = False

    full_prompt_text = get_prompt_text(prompt_text, 'a channel mention or ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, False, check=check_for_channel_id_or_mention, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            channel = get_channel(content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return channel, aborted, skipped


async def inquire_for_true_false(ctx: _Context,
                                    prompt_text: str,
                                    timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                    abort_text: _Optional[str] = None,
                                    skip_text: _Optional[str] = None
                                ) -> _Tuple[_Optional[bool], bool, bool]:
    """
    Returns (result: `bool`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    return (await inquire_for_boolean(ctx, prompt_text, timeout=timeout, abort_text=abort_text, skip_text=skip_text))


async def try_delete_message(message: _Message) -> bool:
    if not message:
        return True

    try:
        await message.delete()
        return True
    except:
        return False


async def wait_for_message(ctx: _Context,
                            allow_abort: bool,
                            allow_skip: bool,
                            *check_args: _Any,
                            check: _Optional[WaitForCheck] = None,
                            timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                            **check_kwargs: _Any
                        ) -> _Optional[_Message]:
    timeout_delta = _timedelta(seconds=timeout)
    end_inquiry = _get_utc_now() + timeout_delta
    try:
        while True:
            user_reply = await ctx.bot.wait_for('message', timeout=timeout)
            content = user_reply.content.strip()
            if check(content, allow_abort, allow_skip, *check_args, **check_kwargs):
                return user_reply
            timeout = (end_inquiry - _get_utc_now()).total_seconds()
    except _TimeoutError:
        return None





# ---------- Private Functions ----------

async def __check_for_abort_or_skip(message_content: str,
                                    allow_abort: bool,
                                    allow_skip: bool
                                ) -> _Tuple[bool, bool]:
    aborted = False
    skipped = False
    if allow_abort and message_content == 'abort':
        aborted = True
    elif allow_skip and message_content == 'skip':
        skipped = True
    return aborted, skipped


def get_prompt_text(prompt_text: str,
                        options_text: str,
                        allow_abort: bool,
                        allow_skip: bool
                    ) -> str:
    options = []
    if options_text:
        options.append(options_text)
    if allow_abort:
        options.append('send \'abort\' to abort')
    if allow_skip:
        options.append('send \'skip\' to skip')
    options_hint = '; '.join(options)
    result = '\n'.join(
        prompt_text,
        f'(Send {options_hint}.)'
    )
    return f'```{result}```'


async def __send_aborted_or_skipped(abort_reply_to: _Message,
                            skip_reply_to: _Message,
                            aborted: bool,
                            skipped: bool,
                            abort_text: _Optional[str],
                            skip_text: _Optional[str]
                        ) -> None:
    if aborted and bool(abort_text):
        await abort_reply_to.reply(abort_text, mention_author=False)
    if skipped and bool(skip_text):
        await skip_reply_to.reply(skip_text, mention_author=False)