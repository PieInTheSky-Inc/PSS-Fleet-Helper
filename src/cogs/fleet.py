import json as _json
from typing import Callable as _Callable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

import discord as _discord
import discord.ext.commands as _commands
import pssapi as _pssapi

from .cog_base import CogBase as _CogBase
from .. import bot_settings as _bot_settings
from .. import utils as _utils
from .. import converters as _converters
from .. import model as _model


# ---------- Cog ----------

class Fleets(_CogBase):
    """
    Commands for configuring Reaction Roles on this server.
    """

    @_commands.group(name='fleet', aliases=['f'], brief='Set up fleets', invoke_without_command=True)
    async def base(self, ctx: _commands.Context) -> None:
        """
        Configure fleets to be used in other commands.
        """
        if ctx.invoked_subcommand is None:
            _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
            await ctx.send_help('fleet')
    

    @_commands.guild_only()
    @base.command(name='add', brief='Add a fleet')
    async def add(self, ctx: _commands.Context, *, fleet_name: str) -> None:
        """
        Add a fleet to be used in other commands.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        
        access_token = await self.bot.pssapi_login()
        alliances = await self.bot.pssapi_client.alliance_service.search_alliances(access_token, fleet_name, 0, 100)
        
        with _model.orm.create_session() as session:
            existing_fleets = _model.orm.get_all_filtered_by(
                _model.Fleet,
                session,
                guild_id=ctx.guild.id,
            )
        existing_fleets_ids = [fleet.id for fleet in existing_fleets]
        
        alliances = [alliance for alliance in alliances if alliance.id not in existing_fleets_ids]

        if not alliances:
            raise Exception(f'A fleet with the name `{fleet_name}` could not be found or has been already added.')

        alliance: _pssapi.entities.Alliance = None
        if len(alliances) == 1:
            alliance = alliances[0]
        else:
            selector = _utils.Selector(ctx, fleet_name, alliances, _model.Fleet.get_alliance_search_description, 'Select a fleet to add')
            selected, alliance = await selector.wait_for_option_selection()
            if not selected:
                raise Exception('No fleet has been selected by the user.')
        
        confirmator = _utils.Confirmator(ctx, f'Do you want to add the fleet {_model.Fleet.get_alliance_search_description(alliance)}?')
        confirm = await confirmator.wait_for_option_selection()
        if confirm:
            short_name = None
            short_name, aborted, skipped = await _utils.discord.inquire_for_text(ctx, 'Specify a short name for the fleet.', skip_text=f'No short name has been specified for the fleet {alliance.alliance_name}')
            with _model.orm.create_session() as session:
                fleet = _model.Fleet.make(
                    alliance.id,
                    ctx.guild.id,
                    short_name,
                )
                fleet.create(session)
                fleet.save(session)
            if short_name:
                await _utils.discord.send(ctx, f'The fleet **{alliance.alliance_name}** [{short_name}] (ID: {alliance.id}) has been added.')
            else:
                await _utils.discord.send(ctx, f'The fleet **{alliance.alliance_name}** (ID: {alliance.id}) has been added.')
        else:
            raise Exception('Process aborted by user.')
    

    @_commands.guild_only()
    @base.command(name='list', brief='List all fleets')
    async def list(self, ctx: _commands.Context, *, fleet_name: str = None) -> None:
        """
        List all fleets configured for this server matching the provided fleet name.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        
        with _model.orm.create_session() as session:
            existing_fleets = _model.orm.get_all_filtered_by(
                _model.Fleet,
                session,
                guild_id=ctx.guild.id,
            )
        
        if not existing_fleets:
            raise Exception('There are no fleets configured for this server.')
        
        access_token = await self.bot.pssapi_login()
        for fleet in existing_fleets:
            await fleet.get_fleet(self.bot.pssapi_client, access_token)

        if fleet_name:
            fleet_name_lower = fleet_name.lower()
            existing_fleets = [fleet for fleet in existing_fleets if fleet_name_lower in fleet.alliance.alliance_name.lower()]
            if not existing_fleets:
                raise Exception('No fleet configured for this server matches the given fleet name.')
        
        existing_fleets = sorted(existing_fleets, key=lambda fleet: fleet.alliance.alliance_name)
        lines = ['# Fleets configured for this server']
        for fleet in existing_fleets:
            unix_timestamp = _utils.datetime.get_unix_timestamp(fleet.created_at)
            if fleet.short_name:
                lines.append(f'**{fleet.alliance.alliance_name}** [{fleet.short_name}] (ID: {fleet.alliance.id}), added: <t:{unix_timestamp}:D> <t:{unix_timestamp}:T>')
            else:
                lines.append(f'**{fleet.alliance.alliance_name}** (ID: {fleet.alliance.id}), added: <t:{unix_timestamp}:D> <t:{unix_timestamp}:T>')
        await _utils.discord.send_lines(ctx, lines)


    @_commands.guild_only()
    @base.command(name='remove', aliases=['delete', 'rem', 'del'], brief='Remove a fleet')
    async def remove(self, ctx: _commands.Context, *, fleet_name: str = None) -> None:
        """
        Add a fleet to be used in other commands.
        """
        _utils.assert_.authorized_channel_or_server_manager(ctx, _bot_settings.AUTHORIZED_CHANNEL_IDS)
        
        with _model.orm.create_session() as session:
            existing_fleets = _model.orm.get_all_filtered_by(
                _model.Fleet,
                session,
                guild_id=ctx.guild.id,
            )
        
        if not existing_fleets:
            raise Exception('There are no fleets configured for this server.')
        
        access_token = await self.bot.pssapi_login()
        for existing_fleet in existing_fleets:
            await existing_fleet.get_fleet(self.bot.pssapi_client, access_token)

        if fleet_name:
            fleet_name_lower = fleet_name.lower()
            existing_fleets = [fleet for fleet in existing_fleets if fleet_name_lower in fleet.alliance.alliance_name.lower()]
            if not existing_fleets:
                raise Exception('No fleet configured for this server matches the given fleet name.')
        
        if len(existing_fleets) == 1:
            fleet = existing_fleets[0]
        else:
            selector = _utils.Selector(ctx, fleet_name, existing_fleets, _model.Fleet.get_fleet_search_description, 'Select a fleet to remove')
            selected, fleet = await selector.wait_for_option_selection()
            if not selected:
                raise Exception('No fleet has been selected by the user.')

        alliance_name = fleet.alliance.alliance_name
        alliance_id = fleet.alliance.id
        confirmator = _utils.Confirmator(ctx, f'Do you want to remove the fleet {_model.Fleet.get_fleet_search_description(fleet)}?')
        confirm = await confirmator.wait_for_option_selection()
        if confirm:
            with _model.orm.create_session() as session:
                fleet.delete(session)
                fleet.save(session)
            await _utils.discord.send(ctx, f'The fleet **{alliance_name}** (ID: {alliance_id}) has been deleted.')
        else:
            raise Exception('Process aborted by user.')


def setup(bot: _model.PssApiDiscordBot):
    bot.add_cog(Fleets(bot))
