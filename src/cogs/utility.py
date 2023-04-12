import json as _json
from typing import List as _List

from discord import Embed as _Embed
from discord import File as _File
from discord import Message as _Message
from discord import Role as _Role
from discord import TextChannel as _TextChannel
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Context as _Context
from discord.ext.commands import is_owner as _is_owner
from discord.ext.commands import group as _command_group

from .cog_base import CogBase as _CogBase
from ..model import database as _db
from .. import bot_settings as _bot_settings
from .. import utils as _utils



class Utility(_CogBase):
    QUERY_UPDATE_SEQUENCES = '''
DO
$do$
BEGIN
   IF EXISTS (SELECT FROM pss_chat_log) THEN
      PERFORM setval('pss_chat_log_pss_chat_log_id_seq', (SELECT max(pss_chat_log_id) FROM pss_chat_log));
   END IF;
   IF EXISTS (SELECT FROM reaction_role_change) THEN
      PERFORM setval('reaction_role_change_reaction_role_change_id_seq', (SELECT max(reaction_role_change_id) FROM reaction_role_change));
   END IF;
   IF EXISTS (SELECT FROM reaction_role) THEN
      PERFORM setval('reaction_role_reaction_role_id_seq', (SELECT max(reaction_role_id) FROM reaction_role));
   END IF;
   IF EXISTS (SELECT FROM reaction_role_requirement) THEN
      PERFORM setval('reaction_role_requirement_reaction_role_requirement_id_seq', (SELECT max(reaction_role_requirement_id) FROM reaction_role_requirement));
   END IF;
END
$do$'''


    @_is_owner()
    @_command_group(name='check', hidden=True, invoke_without_command=True)
    async def check(self, ctx: _Context) -> None:
        """
        Provides commands for checking user input. Check out the subcommands.

        Usage:
          vivi check [subcommand]
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help('check')


    @_is_owner()
    @check.command(name='channel')
    async def check_channel(self, ctx: _Context, channel_id_or_mention: str) -> None:
        """
        Checks, if a channel with the provided ID or mention exists on this guild and can be accessed by the bot.

        Usage:
          vivi check channel [channel_id_or_mention]

        Parameters:
          channel_id_or_mention: Mandatory. A mention or an ID of a channel to be checked.

        Examples:
          vivi check channel 1
          vivi check channel #foobar
        """
        result = _utils.discord.get_text_channel(ctx, channel_id_or_mention)
        if result:
            await _utils.discord.reply(ctx, result.mention)
        else:
            lines = [
                f'This is not a valid channel or I cannot access it:',
                channel_id_or_mention
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @check.command(name='emoji')
    async def check_emoji(self, ctx: _Context, emoji: str) -> None:
        """
        Checks, if a given emoji exists on this guild or is a standard emoji and can be accessed by the bot.

        Usage:
          vivi check emoji [emoji]

        Parameters:
          emoji: Mandatory. A standard emoji or a custom emoji of the current guild.

        Examples:
          vivi check emoji 😁
          vivi check <:ayy:1>
        """
        result = _utils.discord.get_emoji(ctx, emoji)
        if result:
            await _utils.discord.reply(ctx, result)
        else:
            lines = [
                f'This is not a valid emoji or I cannot access it:',
                emoji
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @check.command(name='member')
    async def check_member(self, ctx: _Context, *, member_id_mention_or_name: str) -> None:
        """
        Checks, if a given member exists on this guild.

        Usage:
          vivi check member [member_id_mention_or_name]

        Parameters:
          member_id_mention_or_name: Mandatory. The ID, a mention or the (nick) name of a member of this guild.

        Examples:
          vivi check member 1
          vivi check member @The worst.
          vivi check member The worst.
          vivi check member The worst.#1337
        """
        result = _utils.discord.get_member(ctx, member_id_mention_or_name)
        if result:
            await _utils.discord.reply(ctx, result.mention)
        else:
            lines = [
                f'This is not a valid member of this server:',
                member_id_mention_or_name
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @check.command(name='message')
    async def check_message(self, ctx: _Context, channel: _TextChannel, message_id: str) -> None:
        """
        Checks, if a message with the given ID exists in the given channel and can be accessed by the bot.

        Usage:
          vivi check message [channel] [message_id]

        Parameters:
          channel:    Mandatory. A channel name or mention of a channel on this guild.
          message_id: Mandatory. The ID of a message in the given channel.

        Examples:
          vivi check message #foobar 1
        """
        result = await _utils.discord.fetch_message(channel, message_id)
        if result:
            await _utils.discord.reply(ctx, f'{result.content}\nBy {result.author.mention}')
        else:
            lines = [
                f'This is not a valid message id or I cannot access the channel:',
                channel.mention,
                message_id
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @check.command(name='role')
    async def check_role(self, ctx: _Context, role_id_or_mention: str) -> None:
        """
        Checks, if a role with the given ID or mention exists on this guild and prints information about it.

        Usage:
          vivi check role [role_id_or_mention]

        Parameters:
          role_id_or_mention: Mandatory. The ID or a mention of a role on this guild.

        Exmaples:
          vivi check role 1
          vivi check role @foobar
        """
        result: _Role = _utils.discord.get_role(ctx, role_id_or_mention)
        if result:
            lines = [
                result.mention,
                f'Position: {result.position}',
                f'Is managed by a bot: {result.is_bot_managed()}',
                f'Is managed by an integration: {result.is_integration()}',
                f'Is everyone: {result.is_default()}',
                f'Is Nitro Booster: {result.is_premium_subscriber()}',
            ]
            await _utils.discord.reply_lines(ctx, lines)
        else:
            lines = [
                f'This is not a valid role:',
                role_id_or_mention,
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_is_owner()
    @_command_group(name='db')
    async def db(self, ctx: _Context) -> None:
        pass


    @_is_owner()
    @db.command(name='export')
    async def db_export(self, ctx: _Context) -> None:
        utc_now = _utils.datetime.get_utc_now()
        export = await _db.export_to_json()

        file_name = f'pss-fleet-helper-db-export_{utc_now.strftime("%Y%m%d-%H%M%S")}.json'
        with open(file_name, 'w') as fp:
            fp.write(export)
        await ctx.reply('Database export:', file=_File(file_name))


    @_is_owner()
    @db.command(name='import')
    async def db_import(self, ctx: _Context) -> None:
        """
        Attempts to import the data from the provided JSON file.
        """
        if not ctx.message.attachments:
            raise Exception('You need to upload a JSON file to be imported with the command!')

        attachment = ctx.message.attachments[0]
        file_contents = (await attachment.read()).decode('utf-8')
        if not file_contents:
            raise Exception('The file provided must not be empty.')

        await _db.import_from_json(file_contents)
        updated_sequences = await _db.try_execute(Utility.QUERY_UPDATE_SEQUENCES)
        if updated_sequences:
            await ctx.reply('Database imported successfully!')
        else:
            await ctx.reply(f'Data has been imported, but the sequences could not be updated! You need to perform the following sql query:\n{Utility.QUERY_UPDATE_SEQUENCES}')


    @_command_group(name='embed', invoke_without_command=True)
    async def embed(self, ctx: _Context, *, definition_or_url: str = None) -> None:
        """
        Test the look of an embed.
        Create and edit embed definitions: https://leovoel.github.io/embed-visualizer/

        How to use:
        - Go to https://leovoel.github.io/embed-visualizer/
        - Create an embed as you like it
        - Copy the code on the left starting with the curled opening brackets right next to 'embed:' ending with the second to last curled closing bracket.
        - Paste the code as parameter 'definition_or_url'

        You can also copy the code into a file and attach that file instead, if the definition would be too long to send otherwise.
        You can also copy the code onto pastebin.com and type the url to that file instead.
        You can also type the link to any file on the web containing an embed definition.
        """
        embeds: _List[_Embed] = []
        if definition_or_url:
            embeds.append((await _utils.discord.get_embed_from_definition_or_url(definition_or_url)))
        elif ctx.message.attachments:
            for attachment in ctx.message.attachments:
                attachment_content = (await attachment.read()).decode('utf-8')
                if attachment_content:
                    embeds.append(_json.loads(attachment_content, cls=_utils.discord.EmbedLeovoelDecoder))
        else:
            raise Exception('You need to specify a definition or upload a file containing a definition!')
        for embed in embeds:
            await _utils.discord.reply(ctx, None, embed=embed)
    

    @embed.command(name='getdef', brief='Get the embed definition from a post')
    async def embed_getdef(self, ctx: _Context, url: str)-> None:
        """
        Retrieves the definition of an embed from a message.
        """
        if not _utils.discord.check_for_message_link(url, allow_abort=False, allow_skip=False):
            raise Exception('Parameter `url` received an invalid value: value is not a valid message url!')

        channel, message = await _utils.discord.get_channel_and_message_from_message_link(ctx, url)
        if not message.embeds:
            raise Exception('The referenced message does not include any embeds.')

        definitions_lines = []
        for embed in message.embeds:
            definitions_lines.extend(_json.dumps(embed, cls=_utils.discord.EmbedLeovoelEncoder).split('\n'))
        
        if definitions_lines:
            definitions_lines.insert(0, '```json')
            definitions_lines.append('```')
            await _utils.discord.reply_lines(ctx, definitions_lines)
        else:
            raise Exception('An unknown error occured. Please contact the bot\'s author.')


    @embed.command(name='link')
    async def embed_link(self, ctx: _Context, url: str, *, display_text: str = None) -> None:
        """
        Creates an embed containing a hyperlink.
        """
        if display_text:
            link = f'[{display_text}]({url})'
        else:
            link = url
        embed = _Embed(description=link)
        await _utils.discord.send(ctx, None, embed=embed)


    @embed.command(name='replace')
    async def embed_replace(self, ctx: _Context, message_link: str, *, definition_or_url: str = None) -> None:
        """
        Replaces the embeds in an existing message sent by the bot.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        channel, message = await _utils.discord.get_channel_and_message_from_message_link(ctx, message_link)
        if not channel:
            raise Exception('I cannot access the channel referenced in the link.')
        if not message:
            raise Exception('I cannot access the message referenced in the link or it does not exist.')
        if message.author != self.bot.user:
            raise Exception('I cannot edit the message referenced in the link, because I did not send it.')

        embeds: _List[_Embed] = []
        if definition_or_url:
            embeds.append((await _utils.discord.get_embed_from_definition_or_url(definition_or_url)))
        elif ctx.message.attachments:
            for attachment in ctx.message.attachments:
                attachment_content = (await attachment.read()).decode('utf-8')
                if attachment_content:
                    embeds.append(_json.loads(attachment_content, cls=_utils.discord.EmbedLeovoelDecoder))
        else:
            raise Exception('You need to specify a definition or upload a file containing a definition!')

        if len(embeds) > 10:
            raise Exception('Too many embeds! Max number of embeds per message is 10.')
        await message.edit(embeds=embeds)


    @_command_group(name='message', invoke_without_command=False)
    async def message(self, ctx: _Context) -> None:
        """

        """
        pass


    @message.command(name='replace')
    async def message_replace(self, ctx: _Context, message_link: str, *, content: str) -> None:
        """
        Replaces the contents of a message sent by the bot.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)

        channel, message = await _utils.discord.get_channel_and_message_from_message_link(ctx, message_link)
        if not channel:
            raise Exception('I cannot access the channel referenced in the link.')
        if not message:
            raise Exception('I cannot access the message referenced in the link or it does not exist.')
        if message.author != self.bot.user:
            raise Exception('I cannot edit the message referenced in the link, because I did not send it.')

        await message.edit(content=content)
        await _utils.discord.reply(ctx, 'Message edited successfully.')


def setup(bot: _Bot):
    bot.add_cog(Utility(bot))