from discord import Role as _Role
from discord.ext.commands import Bot as _Bot
from discord.ext.commands import Cog as _Cog
from discord.ext.commands import Context as _Context
from discord.ext.commands import group as _command_group
from discord.ext.commands import bot_has_guild_permissions as _bot_has_guild_permissions
from discord.ext.commands import has_guild_permissions as _has_guild_permissions

from confirmator import Confirmator as _Confirmator





class RolesCog(_Cog):
    def __init__(self, bot: _Bot) -> None:
        self.__bot = bot


    @_command_group(name='role', brief='Role management', invoke_without_command=True)
    async def base(ctx: _Context) -> None:
        await ctx.send_help('role')


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='add', brief='Add a role to specified members')
    async def add(self, ctx: _Context, role: _Role, *, user_ids: str) -> None:
        """
        Add one role to multiple members.
        """
        user_ids = set(user_ids.split(' '))
        confirmator = _Confirmator(ctx, f'This command will add the role `{role}` to {len(user_ids)} members!')
        if (await confirmator.wait_for_option_selection()):
            users_added = []
            for user_id in user_ids:
                member = await ctx.guild.fetch_member(int(user_id))
                await member.add_roles(role)
                users_added.append(f'{member.display_name} ({user_id})')

            user_list = '\n'.join(sorted(users_added))

            await ctx.reply(f'Added role {role} to members:\n{user_list}', mention_author=False)


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='clear', brief='Remove a role from all members')
    async def clear(self, ctx: _Context, role: _Role) -> None:
        """
        Remove a specific role from all members.
        """
        members = list(role.members)
        if len(members) > 0:
            confirmator = _Confirmator(ctx, f'This command will remove the role `{role}` from {len(members)} members!')
            if (await confirmator.wait_for_option_selection()):
                users_removed = []
                for member in members:
                    await member.remove_roles(role)
                    users_removed.append(f'{member.display_name} ({member.id})')

                user_list = '\n'.join(sorted(users_removed))

                await ctx.reply(f'Removed role {role} from members:\n{user_list}', mention_author=False)
        else:
            await ctx.reply(f'There are no members with the role {role}.', mention_author=False)


    @_bot_has_guild_permissions(manage_roles=True)
    @_has_guild_permissions(manage_roles=True)
    @base.command(name='remove', brief='Remove a role from specified members')
    async def remove(self, ctx: _Context, role: _Role, *, user_ids: str) -> None:
        """
        Remove one role from multiple members.
        """
        user_ids = set(user_ids.split(' '))
        confirmator = _Confirmator(ctx, f'This command removes the role `{role}` from {len(user_ids)} members.')
        if (await confirmator.wait_for_option_selection()):
            users_removed = []
            for user_id in user_ids:
                member = await ctx.guild.fetch_member(int(user_id))
                await member.remove_roles(role)
                users_removed.append(f'{member.display_name} ({user_id})')

            user_list = '\n'.join(sorted(users_removed))

            await ctx.reply(f'Removed role {role} from members:\n{user_list}', mention_author=False)
