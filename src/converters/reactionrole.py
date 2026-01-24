from typing import List as _List

from discord import Guild as _Guild
from discord.ext.commands import Context as _Context

from .. import utils as _utils
from ..model import ReactionRole as _ReactionRole
from ..model import ReactionRoleChange as _ReactionRoleChange
from ..model import ReactionRoleRequirement as _ReactionRoleRequirement


class ReactionRoleConverter:
    def __init__(self, reaction_role: _ReactionRole) -> None:
        self.__reaction_role: _ReactionRole = reaction_role
        self.__text: _List[str] = None

    async def to_text(self, guild: _Guild, include_messages: bool) -> _List[str]:
        if self.__text is not None:
            return self.__text

        details = [
            f"**Reaction Role {self.__reaction_role}**",
            f"Message ID = {self.__reaction_role.message_id} {_utils.discord.create_discord_link(guild.id, self.__reaction_role.channel_id, self.__reaction_role.message_id)}",
            f"Emoji = {self.__reaction_role.reaction}",
            f"Is active = {self.__reaction_role.is_active}",
        ]
        if self.__reaction_role.role_requirements:
            required_roles_list = []
            for role_requirement in self.__reaction_role.role_requirements:
                required_role = guild.get_role(role_requirement.role_id)
                if required_role:
                    required_roles_list.append(required_role.name)
                else:
                    required_roles_list.append("<deleted role>")
            required_roles = ", ".join(required_roles_list)
            details.append(f"Required role(s) = {required_roles}")
        details.append(f"_Role Changes_")
        review_messages = []
        for i, role_change in enumerate(self.__reaction_role.role_changes, 1):
            changed_role = guild.get_role(role_change.role_id)
            add_text = "add" if role_change.add else "remove"
            send_message_str = ""
            if role_change.message_channel_id:
                message_channel = guild.get_channel(role_change.message_channel_id)
                review_text = " (view message text below)" if include_messages else ""
                send_message_str = (
                    f" and send a message to {message_channel.mention}{review_text}"
                )
                if include_messages:
                    review_messages.append((i, role_change.message_content))
            allow_toggle_text = (
                "toggleable" if role_change.allow_toggle else "non-toggleable"
            )
            if changed_role:
                changed_role_name = changed_role.name
            else:
                changed_role_name = "<deleted role>"
            details.append(
                f"{i} = {add_text} {allow_toggle_text} role `{changed_role_name}`{send_message_str}"
            )
        result = ["\n".join(details)]
        for role_change_number, msg in review_messages:
            result.append(
                f"__Message for Role Change **\#{role_change_number}** of Reaction Role **{self.__reaction_role.name}**:__\n{msg}"
            )
        self.__text = result

        return result


class ReactionRoleChangeConverter:
    @classmethod
    def to_text(cls, ctx: _Context, reaction_role_change: _ReactionRoleChange) -> str:
        role = ctx.guild.get_role(reaction_role_change.role_id)
        add_text = "add" if reaction_role_change.add else "remove"
        send_message_str = ""
        if reaction_role_change.message_channel_id:
            message_channel = ctx.guild.get_channel(
                reaction_role_change.message_channel_id
            )
            send_message_str = f" and send a message to #{message_channel.name}"
        allow_toggle_text = (
            "toggleable" if reaction_role_change.allow_toggle else "non-toggleable"
        )
        result = f"{add_text} {allow_toggle_text} role '{role.name}' (ID: {role.id}){send_message_str}"
        return result


class ReactionRoleRequirementConverter:
    @classmethod
    def to_text(
        cls, ctx: _Context, reaction_role_requirement: _ReactionRoleRequirement
    ) -> str:
        role = ctx.guild.get_role(reaction_role_requirement.role_id)
        result = role.name
        return result
