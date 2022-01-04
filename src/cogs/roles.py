from discord import Role as _Role
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group
from discord.ext.commands import bot_has_guild_permissions as _bot_has_guild_permissions
from discord.ext.commands import has_guild_permissions as _has_guild_permissions

from .. import utils as _utils





class RolesCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        if not bot:
            raise ValueError('Parameter \'bot\' must not be None.')
        self.__bot = bot


    @property
    def bot(self) -> _Bot:
        return self.__bot


    @_command_group(name='role', brief='Role management', invoke_without_command=True)
    async def base(self, ctx: _Context) -> None:
        await ctx.send_help('role')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='add', brief='Add a role to specified members')
    async def add(self, ctx: _Context, role: _Role, *, user_ids: str) -> None:
        """
        Add one role to multiple members.
        """
        user_ids = set(user_ids.split(' '))
        confirmator = _utils.Confirmator(ctx, f'This command will add the role `{role}` to {len(user_ids)} members!')
        if (await confirmator.wait_for_option_selection()):
            users_added = []
            for user_id in user_ids:
                member = await ctx.guild.fetch_member(int(user_id))
                await member.add_roles(role)
                users_added.append(f'{member.display_name} ({user_id})')

            lines = [
                f'Added role {role} to members:',
                *sorted(users_added)
            ]
            await _utils.discord.reply_lines(ctx, lines)


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='clear', brief='Remove a role from all members')
    async def clear(self, ctx: _Context, role: _Role) -> None:
        """
        Remove a specific role from all members.
        """
        members = list(role.members)
        if len(members) > 0:
            confirmator = _utils.Confirmator(ctx, f'This command will remove the role `{role}` from {len(members)} members!')
            if (await confirmator.wait_for_option_selection()):
                users_removed = []
                for member in members:
                    await member.remove_roles(role)
                    users_removed.append(f'{member.display_name} ({member.id})')

                lines = [
                    f'Removed role {role} from members:',
                    *sorted(users_removed)
                ]
                await _utils.discord.reply_lines(ctx, lines)
        else:
            await _utils.discord.reply(ctx, f'There are no members with the role {role}.')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='remove', brief='Remove a role from specified members')
    async def remove(self, ctx: _Context, role: _Role, *, user_ids: str) -> None:
        """
        Remove one role from multiple members.
        """
        user_ids = set(user_ids.split(' '))
        confirmator = _utils.Confirmator(ctx, f'This command removes the role `{role}` from {len(user_ids)} members.')
        if (await confirmator.wait_for_option_selection()):
            users_removed = []
            for user_id in user_ids:
                member = await ctx.guild.fetch_member(int(user_id))
                await member.remove_roles(role)
                users_removed.append(f'{member.display_name} ({user_id})')

            lines = [
                f'Removed role {role} from members:',
                *sorted(users_removed)
            ]
            await _utils.discord.reply_lines(ctx, lines)


def setup(bot: _Bot):
    bot.add_cog(RolesCog(bot))