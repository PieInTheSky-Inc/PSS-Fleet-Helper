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
            selector = _utils.Selector(ctx, fleet_name, alliances, _model.Fleet.get_fleet_search_description, 'Select a fleet')
            selected, alliance = await selector.wait_for_option_selection()
            if not selected:
                raise Exception('No fleet has been selected by the user.')
        
        confirmator = _utils.Confirmator(ctx, f'Do you want to add the fleet {_model.Fleet.get_fleet_search_description(alliance)}?')
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
            await _utils.discord.send(ctx, f'The fleet {alliance.alliance_name} (ID: {alliance.id}) has been added.')
        else:
            raise Exception('Process aborted by user.')


def setup(bot: _model.PssApiDiscordBot):
    bot.add_cog(Fleets(bot))
