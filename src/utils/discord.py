from asyncio import TimeoutError as _TimeoutError
from datetime import timedelta as _timedelta
from json import dumps as _json_dumps
from json import loads as _json_loads
from json import JSONEncoder as _JSONEncoder
from json import JSONDecodeError as _JSONDecodeError
from json import JSONDecoder as _JSONDecoder
import re as _re
from typing import Any as _Any
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional
from typing import Protocol as _Protocol
from typing import Tuple as _Tuple
from typing import Union as _Union

from discord import Asset as _Asset
from discord import Colour as _Colour
from discord import Embed as _Embed
from discord import Guild as _Guild
from discord import Member as _Member
from discord import Message as _Message
from discord import Role as _Role
from discord import TextChannel as _TextChannel
from discord import User as _User
from discord.errors import Forbidden as _Forbidden
from discord.errors import NotFound as _NotFound
from discord.abc import Messageable as _Messageable
from discord.ext.commands import Context as _Context
import emoji as _emoji

from . import settings as _settings
from . import web as _web
from .datetime import get_utc_now as _get_utc_now
from .datetime import utc_from_timestamp as _utc_from_timestamp
from .datetime import utc_to_timestamp as _utc_to_timestamp



# ---------- Typehints ----------

class WaitForCheck(_Protocol):
    def __call__(self, message_content: str, allow_abort: bool, allow_skip: bool, *args, **kwargs) -> bool:
        pass





# ---------- Constants ----------

__DEFAULT_FALSE_VALUES: _List[str] = ['no', 'n', 'false', '0', '👎']
__DEFAULT_TRUE_VALUES: _List[str] = ['yes', 'y', 'true', '1', '👍']
DEFAULT_INQUIRE_TIMEOUT: float = 120.0

__RX_CHANNEL_MENTION: _re.Pattern = _re.compile('<#(\d+)>')
__RX_EMOJI: _re.Pattern = _re.compile('<a?:\w+:(\d+)>')
__RX_MESSAGE_LINK: _re.Pattern = _re.compile('https://discord.com/channels/(\d+)/(\d+)/(\d+)/?')
__RX_ROLE_MENTION: _re.Pattern = _re.compile('<@&(\d+)>')
__RX_USER_MENTION: _re.Pattern = _re.compile('<@\!?(\d+)>')

PLACEHOLDERS: str = """
`\{` - `{`
`\}` - `}`

`{server}` - Guild name
`{server.iconUrl}` - Guild's icon url
`{server.id}` - Guild ID
`{server.memberCount}` - Guild's member count
`{server.name}` - Guild name

`{channel}` - Channel mention
`{channel.category}` - Channel category name (empty if not in a category)
`{channel.category.id}` - Channel category id (empty if not in a category)
`{channel.category.name}` - Channel category name (empty if not in a category)
`{channel.mention}` - Channel mention
`{channel.name}` - Channel name

`{role}` - Role mention (will not notify its members if used in embeds)
`{role.id}` - Role id
`{role.memberCount}` - Role member count
`{role.mention}` - Role mention (will not notify its members if used in embeds)
`{role.name}` - Role name

`{user}` - User mention (will not notify the user if used in embeds)
`{user.avatarUrl}` - User's avatar url
`{user.discriminator}` - User discriminator
`{user.id}` - User id
`{user.displayName}` - User nick if set, else user name and discriminator
`{user.mention}` - User mention (will not notify the user if used in embeds)
`{user.name}` - User name and discriminator
`{user.nick}` - User nick if set, else empty
`{user.username}` - User name
""".strip()





# ---------- JSON De- & Encoding ----------

class EmbedLeovoelEncoder(_JSONEncoder):
    """
    Tool at: https://leovoel.github.io/embed-visualizer/
    """
    def default(self, obj):
        if isinstance(obj, _Embed):
            embed: _Embed = obj
            result = {}
            if embed.title:
                result['title'] = embed.title
            if embed.description:
                result['description'] = embed.description
            if embed.url:
                result['url'] = embed.url
            if embed.color:
                r, g, b = embed.color.to_rgb()
                result['color'] = (r << 16) + (g << 8) + b
            if embed.timestamp:
                result['timestamp'] = _utc_to_timestamp(embed.timestamp)
            if embed.footer:
                if embed.footer.icon_url:
                    result.setdefault('footer', {})['icon_url'] = embed.footer.icon_url
                if embed.footer.text:
                    result.setdefault('footer', {})['text'] = embed.footer.text
            if embed.thumbnail and embed.thumbnail.url:
                result.setdefault('thumbnail', {})['url'] = embed.thumbnail.url
            if embed.image and embed.image.url:
                result.setdefault('image', {})['url'] = embed.image.url
            if embed.author:
                if embed.author.icon_url:
                    result.setdefault('author', {})['icon_url'] = embed.footer.icon_url
                if embed.author.name:
                    result.setdefault('author', {})['name'] = embed.footer.name
                if embed.author.url:
                    result.setdefault('author', {})['url'] = embed.footer.url
            if embed.fields:
                for field in embed.fields:
                    result.setdefault('fields', []).append({
                        'inline': field.inline,
                        'name': field.name,
                        'value': field.value
                    })
            return result
        else:
            # call base class implementation which takes care of
            # raising exceptions for unsupported types
            return _JSONEncoder.default(self, obj)


class EmbedLeovoelDecoder(_JSONDecoder):
    """
    Tool at: https://leovoel.github.io/embed-visualizer/
    """
    __EMBED_PROP_NAMES = ['author', 'color', 'description', 'footer', 'image', 'timestamp', 'title', 'url', 'thumbnail', 'fields']

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct: _Dict) -> _Union[_Dict, _Embed]:
        if any(prop in dct.keys() for prop in EmbedLeovoelDecoder.__EMBED_PROP_NAMES):
            title = dct.get('title', _Embed.Empty)
            color = dct.get('color', dct.get('colour', _Embed.Empty))
            url = dct.get('url', _Embed.Empty)
            description = dct.get('description', _Embed.Empty)
            timestamp = dct.get('timestamp', _Embed.Empty)
            if color is not _Embed.Empty:
                color = _Colour(color)
            if timestamp is not _Embed.Empty:
                timestamp = _utc_from_timestamp(timestamp)
            result = _Embed(title=title, color=color, url=url, description=description, timestamp=timestamp)
            author_info = dct.get('author')
            if author_info:
                result.set_author(author_info.get('name'), url=author_info.get('url', _Embed.Empty), icon_url=author_info.get('icon_url', _Embed.Empty))
            footer_info = dct.get('footer')
            if footer_info:
                result.set_footer(text=footer_info.get('text', _Embed.Empty), icon_url=footer_info.get('icon_url', _Embed.Empty))
            image_info = dct.get('image')
            if image_info:
                result.set_image(image_info.get('url'))
            thumbnail_info = dct.get('thumbnail')
            if thumbnail_info:
                result.set_thumbnail(thumbnail_info.get('url'))
            for field in dct.get('fields', []):
                result.add_field(name=field.get('name'), value=field.get('value'), inline=field.get('inline', True))
            return result
        else:
            return dct







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


def check_for_message_link(message_content: str,
                            allow_abort: bool = True,
                            allow_skip: bool = False
                        ) -> bool:
    if __RX_MESSAGE_LINK.match(message_content):
        return True
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


def create_posts_from_lines(lines: _List[str], char_limit: int) -> _List[str]:
    result = []
    current_post = ''

    for line in lines:
        line_length = len(line)
        new_post_length = 1 + len(current_post) + line_length
        if new_post_length > char_limit:
            result.append(current_post)
            current_post = ''
        if len(current_post) > 0:
            current_post += '\n'

        current_post += line

    if current_post:
        result.append(current_post)

    if not result:
        result = ['']

    return result


def create_prompt_text(prompt_text: str,
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
    result = '\n'.join((
        prompt_text,
        f'(Send {options_hint}.)'
    ))
    return f'```{result}```'


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


async def get_embed_from_definition_or_url(definition_or_url: str) -> _Embed:
    try:
        return _json_loads(definition_or_url, cls=EmbedLeovoelDecoder)
    except _JSONDecodeError:
        if 'pastebin.com' in definition_or_url:
            url = _web.get_raw_pastebin(definition_or_url)
        else:
            url = definition_or_url
        url_definition = await _web.get_data_from_url(url)

    try:
        return _json_loads(url_definition, cls=EmbedLeovoelDecoder)
    except _JSONDecodeError:
        raise Exception('This is not a valid embed definition or this url points to a file not containing a valid embed definition.')


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


async def get_channel_and_message_from_message_link(ctx: _Context,
                                                        message_link: str
                                                    ) -> _Tuple[_Optional[_TextChannel], _Optional[_Message]]:
    channel = None
    message = None
    match = __RX_MESSAGE_LINK.match(message_link)
    if match:
        channel_id = int(match.groups()[1])
        message_id = int(match.groups()[2])
        channel = get_channel(ctx, channel_id)
        if channel:
            message = await fetch_message(channel, message_id)
    return channel, message


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
    `true_values` defaults to `.model.utils.discord.__DEFAULT_TRUE_VALUES` if `None` or empty.
    `false_values` defaults to `.model.utils.discord.__DEFAULT_FALSE_VALUES` if `None` or empty.

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

    full_prompt_text = create_prompt_text(prompt_text, f'\'{true_values_text}\' or \'{false_values_text}\'', allow_abort, allow_skip)
    if respond_to_message:
        prompt_message = await respond_to_message.reply(full_prompt_text, mention_author=False)
    else:
        prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, true_values, false_values, check=check_for_boolean_string, timeout=timeout)
    if user_reply:
        content_lower = user_reply.content.strip().lower()
        aborted, skipped = await __check_for_abort_or_skip(content_lower, allow_abort, allow_skip)
        if not (aborted or skipped):
            result = content_lower in true_values_lower or not (content_lower in false_values_lower)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return result, aborted, skipped


async def inquire_for_embed_definition(ctx: _Context,
                                        prompt_text: str,
                                        timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                        abort_text: _Optional[str] = None,
                                        skip_text: _Optional[str] = None
                                    ) -> _Tuple[_Optional[str], bool, bool]:
    """
    Returns (embed_definition: `Optional[str]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    result = None
    aborted = False
    skipped = False

    full_prompt_text = create_prompt_text(prompt_text, 'an embed definition as JSON as plain text, a hyperlink to a web resource containing a definition or a file uploaded containing a definition', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            if not content and user_reply.attachments:
                content = (await user_reply.attachments[0].read()).decode('utf-8')
            embed = await get_embed_from_definition_or_url(content)
            result = _json_dumps(embed, cls=EmbedLeovoelEncoder, separators=(',', ':')) if embed and content else None
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

    full_prompt_text = create_prompt_text(prompt_text, 'an emoji', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
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

    full_prompt_text = create_prompt_text(prompt_text, 'an integer', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, check=check_for_integer, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
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

    full_prompt_text = create_prompt_text(prompt_text, 'a member mention, name or ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, check=check_for_member_id_name_or_mention, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
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

    full_prompt_text = create_prompt_text(prompt_text, 'a message ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, check=check_for_message_id, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            message = await fetch_message(channel, content)
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return message, aborted, skipped


async def inquire_for_message_link(ctx: _Context,
                                    prompt_text: str,
                                    timeout: float = DEFAULT_INQUIRE_TIMEOUT,
                                    abort_text: _Optional[str] = None,
                                    skip_text: _Optional[str] = None
                                ) -> _Tuple[_Optional[str], bool, bool]:
    """
    Returns (message_link: `Optional[str]`, user_has_aborted: `bool`, user_has_skipped: `bool`)
    """
    allow_abort = bool(abort_text)
    allow_skip = bool(skip_text)
    result = None
    aborted = False
    skipped = False

    full_prompt_text = create_prompt_text(prompt_text, 'an full link to a Discord message', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, check=check_for_message_link, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            result = content
    else:
        aborted = True
    await __send_aborted_or_skipped(ctx.message, prompt_message, aborted, skipped, abort_text, skip_text)
    return result, aborted, skipped


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

    full_prompt_text = create_prompt_text(prompt_text, 'a role mention or ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, check=check_for_role_id_or_mention, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
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

    full_prompt_text = create_prompt_text(prompt_text, None, allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
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

    full_prompt_text = create_prompt_text(prompt_text, 'a channel mention or ID', allow_abort, allow_skip)
    prompt_message = await ctx.reply(full_prompt_text, mention_author=False)
    user_reply = await wait_for_message(ctx, allow_abort, allow_skip, check=check_for_channel_id_or_mention, timeout=timeout)
    if user_reply:
        content = user_reply.content.strip()
        aborted, skipped = await __check_for_abort_or_skip(content.lower(), allow_abort, allow_skip)
        if not (aborted or skipped):
            channel = get_channel(ctx, content)
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


def create_substitutions(guild: _Guild = None, channel: _TextChannel = None, role: _Role = None, member: _Member = None) -> _Dict[str, str]:
    """
    Creates a dictionary of placeholders and their substitutions based on the provided Assets.

    The following substitutions will be created:

    {PLACEHOLDERS}
    """
    replacements = {}
    if guild:
        replacements['{server}'] = guild.name
        replacements['{server.iconUrl}'] = f'{_Asset.BASE}{guild.icon_url._url}' if guild.icon_url._url else ''
        replacements['{server.id}'] = str(guild.id)
        replacements['{server.memberCount}'] = str(guild.member_count)
        replacements['{server.name}'] = guild.name
    if channel:
        replacements['{channel}'] = channel.mention
        replacements['{channel.category}'] = channel.category.name if channel.category else ''
        replacements['{channel.category.id}'] = str(channel.category.id) if channel.category else ''
        replacements['{channel.category.name}'] = channel.category.name if channel.category else ''
        replacements['{channel.id}'] = str(channel.id)
        replacements['{channel.mention}'] = channel.mention
        replacements['{channel.name}'] = channel.name
    if role:
        replacements['{role}'] = role.mention
        replacements['{role.id}'] = str(role.id)
        replacements['{role.memberCount}'] = str(len(role.members))
        replacements['{role.mention}'] = role.mention
        replacements['{role.name}'] = role.name
    if member:
        user: _User = member._user
        replacements['{user}'] = member.mention
        replacements['{user.avatarUrl}'] = f'{_Asset.BASE}{user.avatar_url._url}' if user.avatar_url._url else ''
        replacements['{user.discriminator}'] = user.discriminator
        replacements['{user.id}'] = str(user.id)
        replacements['{user.displayName}'] = member.display_name
        replacements['{user.name}'] = f'{user.name}#{user.discriminator}'
        replacements['{user.nick}'] = member.nick or ''
        replacements['{user.username}'] = user.name
    replacements['\{'] = '{'
    replacements['\}'] = '}'
    return replacements


create_substitutions.__doc__ = f"""
Creates a dictionary of placeholders and their substitutions based on the provided Assets.

The following substitutions will be created:

{PLACEHOLDERS}
""".strip()


async def reply(ctx: _Context, content: str, mention_author: bool = False, **kwargs) -> _Message:
    if content:
        await ctx.reply(content=content, mention_author=mention_author, **kwargs)


async def reply_lines(ctx: _Context, content_lines: _List[str], mention_author: bool = False, **kwargs) -> _Message:
    posts = create_posts_from_lines(content_lines, _settings.MESSAGE_MAXIMUM_CHARACTER_COUNT)
    for post in posts:
        if post:
            await ctx.reply(content=post, mention_author=mention_author, **kwargs)


async def send(ctx: _Context, content: str, **kwargs) -> _Message:
    if content:
        await ctx.send(content=content, **kwargs)


async def send_lines(ctx: _Context, content_lines: _List[str], **kwargs) -> _Message:
    posts = create_posts_from_lines(content_lines, _settings.MESSAGE_MAXIMUM_CHARACTER_COUNT)
    for post in posts:
        if post:
            await ctx.send(content=post, **kwargs)


async def send_to_channel(channel: _TextChannel, content: str, **kwargs) -> _Message:
    if content:
        await channel.send(content=content, **kwargs)


async def send_lines_to_channel(channel: _TextChannel, content_lines: _List[str], **kwargs) -> _Message:
    posts = create_posts_from_lines(content_lines, _settings.MESSAGE_MAXIMUM_CHARACTER_COUNT)
    for post in posts:
        if post:
            await channel.send(content=post, **kwargs)


async def try_delete_message(message: _Message) -> bool:
    if not message:
        return True

    try:
        await message.delete()
        return True
    except:
        return False


def update_embed_definition(embed_definition: str, substitutions: _Optional[_Dict[str, _Any]]) -> str:
    embed_dct = _json_loads(embed_definition)

    for key, value in substitutions.items():
        embed_dct['title'] = embed_dct.get('title', '').replace(key, value)
        embed_dct['description'] = embed_dct.get('description', '').replace(key, value)
        for field in embed_dct.get('fields', []):
            field['name'] = field.get('name', '').replace(key, value)
            field['value'] = field.get('value', '').replace(key, value)
        if 'author' in embed_dct:
            embed_dct['author']['icon_url'] = embed_dct['author'].get('icon_url').replace(key, value)
            embed_dct['author']['name'] = embed_dct['author'].get('name').replace(key, value)
        if 'footer' in embed_dct:
            embed_dct['footer']['icon_url'] = embed_dct['footer'].get('icon_url').replace(key, value)
        if 'image' in embed_dct:
            embed_dct['image']['url'] = embed_dct['image'].get('url').replace(key, value)
        if 'thumbnail' in embed_dct:
            embed_dct['thumbnail']['url'] = embed_dct['thumbnail'].get('url').replace(key, value)

    return _json_dumps(embed_dct, separators=(',', ':'))


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
            if not check or check(content, allow_abort, allow_skip, *check_args, **check_kwargs):
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