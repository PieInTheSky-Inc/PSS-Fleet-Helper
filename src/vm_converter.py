from typing import List as _List

import discord as _discord

from model import ReactionRole as _ReactionRole



class ConverterBase():
    def __init__(self) -> None:
        pass


    def to_text(self) -> str:
        pass


class ReactionRoleConverter():
    def __init__(self, reaction_role: _ReactionRole) -> None:
        super().__init__()
        self.__reaction_role: _ReactionRole = reaction_role
        self.__text: _List[str] = None


    async def to_text(self, guild: _discord.Guild, include_messages: bool) -> _List[str]:
        if self.__text is not None:
            return self.__text

        details = [f'ID = {self.__reaction_role.id}',
            f'Name = {self.__reaction_role.name}',
            f'Message ID = {self.__reaction_role.message_id}',
            f'Emoji = {self.__reaction_role.reaction}',
            f'Is active = {self.__reaction_role.is_active}',
        ]
        if self.__reaction_role.role_requirements:
            required_roles = ', '.join([guild.get_role(role_requirement.role_id).name for role_requirement in self.__reaction_role.role_requirements])
            details.append(f'Required role(s) = {required_roles}')
        details.append(f'_Role Changes_')
        review_messages = []
        for i, role_change in enumerate(self.__reaction_role.role_changes, 1):
            role = guild.get_role(role_change.role_id)
            add_text = 'add' if role_change.add else 'remove'
            send_message_str = ''
            if  role_change.message_channel_id:
                message_channel = guild.get_channel(role_change.message_channel_id)
                review_text = ' (view message text below)' if include_messages else ''
                send_message_str = f' and send a message to {message_channel.mention}{review_text}'
                if include_messages:
                    review_messages.append((i, role_change.message_content))
            allow_toggle_text = 'toggable' if role_change.allow_toggle else 'non-toggable'
            details.append(f'{i} = {add_text} {allow_toggle_text} role `{role.name}`{send_message_str}')
        result = ['\n'.join(details)]
        for role_change_number, msg in review_messages:
            result.append(f'__Message for Role Change **\#{role_change_number}** of Reaction Role **{self.__reaction_role.name}**:__\n{msg}')
        self.__text = result

        return result