import asyncio as _asyncio
from threading import Lock as _Lock
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

from discord import TextChannel as _TextChannel
from discord import Member as _Member
from discord.ext.commands import Context as _Context

from . import database as _database




class ReactionRole(_database.DatabaseRowBase):
    TABLE_NAME: str = 'reaction_role'
    ID_COLUMN_NAME: str = 'reaction_role_id'

    def __init__(self, reaction_role_id: int, guild_id: int, channel_id: int, message_id: int, name: str, reaction: str, is_active: bool) -> None:
        super().__init__(reaction_role_id)
        self.__guild_id: int = guild_id
        self.__channel_id: int = channel_id
        self.__message_id: int = message_id
        self.__name: str = name
        self.__reaction: str = reaction
        self.__is_active: bool = is_active
        self.__role_changes: _List['ReactionRoleChange'] = []
        self.__role_requirements: _List['ReactionRoleRequirement'] = []
        self.__edit_changes_lock: _Lock = _Lock()
        self.__edit_requirements_lock: _Lock = _Lock()


    def __repr__(self) -> str:
        deleted_text = ' - deleted' if self.deleted else ''
        return f'Reaction Role \'{self.__name}\' (ID: {super().id}){deleted_text}'


    def __str__(self) -> str:
        return f'\'{self.__name}\' (ID: {super().id})'


    @property
    def channel_id(self) -> int:
        super()._assert_not_deleted()
        return self.__channel_id

    @property
    def guild_id(self) -> int:
        super()._assert_not_deleted()
        return self.__guild_id

    @property
    def is_active(self) -> bool:
        super()._assert_not_deleted()
        return self.__is_active

    @property
    def message_id(self) -> int:
        super()._assert_not_deleted()
        return self.__message_id

    @property
    def name(self) -> str:
        super()._assert_not_deleted()
        return self.__name

    @property
    def reaction(self) -> str:
        super()._assert_not_deleted()
        return self.__reaction

    @property
    def role_changes(self) -> _List['ReactionRoleChange']:
        super()._assert_not_deleted()
        return list(self.__role_changes)

    @property
    def role_requirements(self) -> _List['ReactionRoleRequirement']:
        super()._assert_not_deleted()
        return list(self.__role_requirements)


    async def add_change(self, role_id: int, add: bool, allow_toggle: bool, message_content: str = None, message_channel_id: int = None) -> 'ReactionRoleChange':
        super()._assert_not_deleted()
        with self.__edit_changes_lock:
            for change in self.role_requirements:
                if change.id == role_id:
                    return change

            result = await _db_create_reaction_role_change(self.id, role_id, add, allow_toggle, message_content, message_channel_id)
            self.__role_changes.append(result)
            return result


    async def add_requirement(self, required_role_id: int) -> 'ReactionRoleRequirement':
        super()._assert_not_deleted()
        with self.__edit_requirements_lock:
            for requirement in self.role_requirements:
                if requirement.id == required_role_id:
                    return requirement

            result = await _db_create_reaction_role_requirement(self.id, required_role_id)
            self.__role_requirements.append(result)
            return result


    async def apply_add(self, member: _Member) -> None:
        roles_to_add = []
        roles_to_remove = []
        messages_to_post: _List[_Tuple[_TextChannel, str]] = []
        for change in self.role_changes:
            role = member.guild.get_role(change.role_id)
            if role:
                role_change = False
                if change.add and role not in member.roles:
                    roles_to_add.append(role)
                    role_change = True
                elif not change.add and role in member.roles:
                    roles_to_remove.append(role)
                    role_change = True
                if role_change and change.message_channel_id and change.message_content:
                    channel = member.guild.get_channel(change.message_channel_id)
                    messages_to_post.append((channel, change.message_content))
        await member.add_roles(*roles_to_add)
        await member.remove_roles(*roles_to_remove)
        for channel, msg in messages_to_post:
            msg = msg.replace('{user}', member.mention)
            await channel.send(msg)


    async def apply_remove(self, member: _Member) -> None:
        roles_to_add = []
        roles_to_remove = []
        for change in self.role_changes:
            if change.allow_toggle:
                role = member.guild.get_role(change.role_id)
                if role:
                    if change.add:
                        roles_to_remove.append(role)
                    else:
                        roles_to_add.append(role)
        await member.add_roles(*roles_to_add)
        await member.remove_roles(*roles_to_remove)


    async def delete(self) -> bool:
        super()._assert_not_deleted()
        result = await _db_delete_reaction_role(self.id)
        if result:
            for requirement in self.role_requirements:
                await requirement._delete()
            self.__role_requirements.clear()
            for change in self.role_changes:
                await change._delete()
            self.__role_changes.clear()
            super()._set_deleted()
        return result


    async def remove_change(self, reaction_role_change_id: int) -> bool:
        super()._assert_not_deleted()
        with self.__edit_changes_lock:
            change = None
            found_change = False
            for change in self.role_changes:
                if change.id == reaction_role_change_id:
                    found_change = True
                    break

            if not found_change:
                return True

            self.__role_changes.remove(change)
            success = await change._delete()
            return success


    async def remove_requirement(self, reaction_role_requirement_id: int) -> bool:
        super()._assert_not_deleted()
        with self.__edit_requirements_lock:
            requirement = None
            found_requirement = False
            for requirement in self.role_requirements:
                if requirement.id == reaction_role_requirement_id:
                    found_requirement = True
                    break

            if not found_requirement:
                return True

            self.__role_requirements.remove(requirement)
            success = await requirement._delete()
            return success


    async def try_activate(self, ctx: _Context) -> bool:
        try:
            reaction_message = await ctx.guild.get_channel(self.channel_id).fetch_message(self.message_id)
            await reaction_message.add_reaction(self.reaction)
            result = True
        except:
            result = False
        if result:
            result = await self.update(is_active=True)
        return result


    async def try_deactivate(self, ctx: _Context) -> bool:
        result = await self.update(is_active=False)
        try:
            reaction_message = await ctx.guild.get_channel(self.channel_id).fetch_message(self.message_id)
            await reaction_message.remove_reaction(self.reaction, ctx.guild.me)
        except:
            pass
        return result


    async def update(self, channel_id: int = None, message_id: int = None, name: str = None, reaction: str = None, is_active: bool = None) -> bool:
        super()._assert_not_deleted()
        if channel_id is None and message_id is None and name is None and reaction is None and is_active is None:
            return True
        channel_id = channel_id or self.channel_id
        message_id = message_id or self.message_id
        name = name or self.name
        reaction = reaction or self.reaction
        is_active = self.is_active if is_active is None else is_active
        updated = await _db_update_reaction_role(self.id, channel_id, message_id, name, reaction, is_active)
        if updated:
            self.__message_id = message_id
            self.__name = name
            self.__reaction = reaction
            self.__is_active = is_active
        return updated


    def update_changes(self, reaction_role_changes: _List['ReactionRoleChange']) -> None:
        if not reaction_role_changes:
            return

        with self.__edit_changes_lock:
            existing_changes_ids = [change.id for change in self.role_changes]
            for reaction_role_change in reaction_role_changes:
                if reaction_role_change.id in existing_changes_ids:
                    self.__role_changes = [change for change in self.__role_changes if change.id == reaction_role_change.id]
                    self.__role_changes.append(reaction_role_change)
                else:
                    self.__role_changes.append(reaction_role_change)
                reaction_role_change.set_reaction_role(self)
            self.__role_changes.sort(key=lambda change: change.id)


    def update_requirements(self, reaction_role_requirements: _List['ReactionRoleRequirement']) -> None:
        if not reaction_role_requirements:
            return

        with self.__edit_requirements_lock:
            existing_requirements_ids = [requirement.id for requirement in self.role_requirements]
            for reaction_role_requirement in reaction_role_requirements:
                if reaction_role_requirement.id in existing_requirements_ids:
                    self.__role_requirements = [requirement for requirement in self.__role_requirements if requirement.id == reaction_role_requirement.id]
                    self.__role_requirements.append(reaction_role_requirement)
                else:
                    self.__role_requirements.append(reaction_role_requirement)
                reaction_role_requirement.set_reaction_role(self)
            self.__role_requirements.sort(key=lambda requirement: requirement.id)


    @staticmethod
    async def create(guild_id: int, reaction_channel_id: int, message_id: int, name: str, reaction: str, is_active: bool = False) -> _Optional['ReactionRole']:
        record = await _database.insert_row(
            ReactionRole.TABLE_NAME,
            ReactionRole.ID_COLUMN_NAME,
            guild_id=guild_id,
            channel_id=reaction_channel_id,
            message_id=message_id,
            name=name,
            reaction=reaction,
            is_active=is_active,
        )
        if record:
            return ReactionRole(record[0], guild_id, reaction_channel_id, message_id, name, reaction, is_active)
        return None





class ReactionRoleChange(_database.DatabaseRowBase):
    TABLE_NAME: str = 'reaction_role_change'
    ID_COLUMN_NAME: str = 'reaction_role_change_id'

    def __init__(self, reaction_role_change_id: int, reaction_role_id: int, role_id: int, add: bool, allow_toggle: bool, message_content: str, message_channel_id: int) -> None:
        super().__init__(reaction_role_change_id)
        self.__reaction_role: ReactionRole = None
        self.__reaction_role_id: int = reaction_role_id
        self.__role_id: int = role_id
        self.__add: bool = add
        self.__allow_toggle: bool = allow_toggle
        self.__message_channel_id: int = message_channel_id
        self.__message_content: int = message_content


    @property
    def add(self) -> bool:
        super()._assert_not_deleted()
        return self.__add

    @property
    def allow_toggle(self) -> bool:
        super()._assert_not_deleted()
        return self.__allow_toggle

    @property
    def message_channel_id(self) -> int:
        super()._assert_not_deleted()
        return self.__message_channel_id

    @property
    def message_content(self) -> str:
        super()._assert_not_deleted()
        return self.__message_content

    @property
    def reaction_role(self) -> _Optional[ReactionRole]:
        super()._assert_not_deleted()
        return self.__reaction_role

    @property
    def reaction_role_id(self) -> int:
        super()._assert_not_deleted()
        return self.__reaction_role.id if self.__reaction_role else self.__reaction_role_id

    @property
    def role_id(self) -> int:
        super()._assert_not_deleted()
        return self.__role_id


    async def _delete(self) -> bool:
        super()._assert_not_deleted()
        result = await _db_delete_reaction_role_change(self.id)
        if result:
            super()._set_deleted()
        return result


    async def update(self, role_id: int = None, add: bool = None, allow_toggle: bool = None, message_content: str = None, message_channel_id: int = None) -> bool:
        super()._assert_not_deleted()
        if role_id is None and add is None and allow_toggle is None and message_channel_id is None and message_content is None:
            return True
        role_id = role_id or self.role_id
        add = self.add if add is None else add
        allow_toggle = self.allow_toggle if allow_toggle is None else allow_toggle
        message_channel_id = message_channel_id or self.message_channel_id
        message_content = message_content or self.message_content
        updated = await _db_update_reaction_role_change(self.id, role_id, add, allow_toggle, message_content, message_channel_id)
        if updated:
            self._role_id = role_id
            self.__add = add
            self.__allow_toggle = allow_toggle
            self.__message_channel_id = message_channel_id
            self.__message_content = message_content
        return updated


    def set_reaction_role(self, reaction_role: ReactionRole) -> None:
        super()._assert_not_deleted()
        self.__reaction_role = reaction_role





class ReactionRoleRequirement(_database.DatabaseRowBase):
    TABLE_NAME: str = 'reaction_role_requirement'
    ID_COLUMN_NAME: str = 'reaction_role_requirement_id'

    def __init__(self, reaction_role_requirement_id: int, reaction_role_id: int, role_id: int) -> None:
        super().__init__(reaction_role_requirement_id)
        self.__reaction_role: ReactionRole = None
        self.__reaction_role_id: int = reaction_role_id
        self.__role_id: int = role_id


    @property
    def reaction_role(self) -> _Optional[ReactionRole]:
        super()._assert_not_deleted()
        return self.__reaction_role

    @property
    def reaction_role_id(self) -> int:
        super()._assert_not_deleted()
        return self.__reaction_role.id if self.__reaction_role else self.__reaction_role_id

    @property
    def role_id(self) -> int:
        super()._assert_not_deleted()
        return self.__role_id


    async def _delete(self) -> bool:
        super()._assert_not_deleted()
        result = await _db_delete_reaction_role_requirement(self.id)
        if result:
            super()._set_deleted()
        return result


    async def update(self, role_id: str = None) -> bool:
        super()._assert_not_deleted()
        if role_id is None:
            return True
        role_id = role_id or self.role_id
        updated = await _db_update_reaction_role_requirement(self.id, role_id)
        if updated:
            self.__role_id = role_id
        return updated


    def set_reaction_role(self, reaction_role: ReactionRole) -> None:
        super()._assert_not_deleted()
        self.__reaction_role = reaction_role




# ---------- Static functions ----------

async def _db_delete_reaction_role(reaction_role_id: int) -> bool:
    result = await _database.delete_rows(
        ReactionRole.TABLE_NAME,
        ReactionRole.ID_COLUMN_NAME,
        [reaction_role_id],
    )
    return bool(result)


async def _db_update_reaction_role(reaction_role_id: int, channel_id: int, message_id: int, name: str, reaction: str, is_active: bool) -> bool:
    result = await _database.update_row(
        ReactionRole.TABLE_NAME,
        ReactionRole.ID_COLUMN_NAME,
        reaction_role_id,
        channel_id=channel_id,
        message_id=message_id,
        name=name,
        reaction=reaction,
        is_active=is_active,
    )
    return bool(result)


async def _db_create_reaction_role_change(reaction_role_id: int, role_id: int, add: bool, allow_toggle: bool, message_content: str, message_channel_id: int) -> 'ReactionRoleChange':
    record = await _database.insert_row(
        ReactionRoleChange.TABLE_NAME,
        ReactionRoleChange.ID_COLUMN_NAME,
        reaction_role_id=reaction_role_id,
        role_id=role_id,
        add=add,
        allow_toggle=allow_toggle,
        message_content=message_content,
        message_channel_id=message_channel_id,
    )
    if record:
        return ReactionRoleChange(record[0], reaction_role_id, role_id, add, allow_toggle, message_content, message_channel_id)
    return None


async def _db_delete_reaction_role_change(reaction_role_change_id: int) -> bool:
    result = await _database.delete_rows(
        ReactionRoleChange.TABLE_NAME,
        ReactionRoleChange.ID_COLUMN_NAME,
        [reaction_role_change_id],
    )
    return bool(result)


async def _db_update_reaction_role_change(reaction_role_change_id: int, role_id: int, add: bool, allow_toggle: bool, message_content: str, message_channel_id: int) -> bool:
    result = await _database.update_row(
        ReactionRoleChange.TABLE_NAME,
        ReactionRoleChange.ID_COLUMN_NAME,
        reaction_role_change_id,
        role_id=role_id,
        add=add,
        allow_toggle=allow_toggle,
        message_content=message_content,
        message_channel_id=message_channel_id,
    )
    return bool(result)


async def _db_create_reaction_role_requirement(reaction_role_id: int, role_id: int) -> 'ReactionRoleRequirement':
    record = await _database.insert_row(
        ReactionRoleRequirement.TABLE_NAME,
        ReactionRoleRequirement.ID_COLUMN_NAME,
        reaction_role_id=reaction_role_id,
        role_id=role_id,
    )
    if record:
        return ReactionRoleRequirement(record[0], reaction_role_id, role_id)
    return None


async def _db_delete_reaction_role_requirement(reaction_role_requirement_id: int) -> bool:
    result = await _database.delete_rows(
        ReactionRoleRequirement.TABLE_NAME,
        ReactionRoleRequirement.ID_COLUMN_NAME,
        [reaction_role_requirement_id],
    )
    return bool(result)


async def _db_update_reaction_role_requirement(reaction_role_requirement_id: int, role_id: int) -> bool:
    result = await _database.update_row(
        ReactionRoleRequirement.TABLE_NAME,
        ReactionRoleRequirement.ID_COLUMN_NAME,
        reaction_role_requirement_id,
        role_id=role_id,
    )
    return bool(result)





# ---------- Testing ----------

async def test() -> bool:
    await _database.init()
    try:
        rr = await ReactionRole.create(896010670909304863, 896010670909304863, 896010670909304863, 'RR1234', '🙂')
    except Exception as e:
        return False

    try:
        await rr.update(message_id=896806211058532452, name='RR1345', reaction='🙃', is_active=False)
    except Exception as e:
        await rr.delete()
        return False

    try:
        ch_1 = await rr.add_change(680621105853242345, True, False)
    except Exception as e:
        await rr.delete()
        rr = None
        return False

    try:
        await ch_1.update(role_id=680621105853242456, add=False, allow_toggle=True, message_channel_id=3456, message_content='Test')
    except Exception as e:
        await ch_1._delete()
        await rr.delete()
        return False

    try:
        await rr.remove_change(ch_1.id)
        ch_1 = None
    except Exception as e:
        await ch_1._delete()
        await rr.delete()
        return False

    try:
        req_1 = await rr.add_requirement(76211058532452)
    except Exception as e:
        await rr.delete()
        rr = None
        return False

    try:
        await req_1.update(role_id=76211050000000)
    except Exception as e:
        await req_1._delete()
        await rr.delete()
        return False

    try:
        await rr.remove_requirement(req_1.id)
        req_1 = None
    except Exception as e:
        await req_1._delete()
        await rr.delete()
        return False

    ch_2 = await rr.add_change(2345, True, False)
    req_2 = await rr.add_requirement(6789)

    await rr.delete()
    print('All tests ran sucessfully!')


if __name__ == '__main__':
    _asyncio.get_event_loop().run_until_complete(test())