import asyncio as _asyncio
from typing import Iterable as _Iterable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

from discord import Member as _Member
from discord import TextChannel as _TextChannel
from discord.ext.commands import Context as _Context
import sqlalchemy as _db

from . import orm as _orm
from .. import utils as _utils




class ReactionRole(_orm.ModelBase):
    ID_COLUMN_NAME: str = 'reaction_role_id'
    TABLE_NAME: str = 'reaction_role'
    __tablename__ = TABLE_NAME

    id = _db.Column(ID_COLUMN_NAME, _db.Integer, primary_key=True, autoincrement=True, nullable=False)
    channel_id = _db.Column('channel_id', _db.Integer, nullable=False)
    guild_id = _db.Column('guild_id', _db.Integer, nullable=False)
    is_active = _db.Column('is_active', _db.Boolean, nullable=False, default=False)
    message_id = _db.Column('message_id', _db.Integer, nullable=False)
    name = _db.Column('name', _db.Text, nullable=False)
    reaction = _db.Column('reaction', _db.Text, nullable=False)
    role_changes: _Iterable['ReactionRoleChange'] = _db.orm.relationship('ReactionRoleChange', back_populates='reaction_role', cascade='all, delete')
    role_requirements: _Iterable['ReactionRoleRequirement'] = _db.orm.relationship('ReactionRoleRequirement', back_populates='reaction_role', cascade='all, delete')


    def __repr__(self) -> str:
        return f'<Reaction Role id={self.id} name={self.name}>'


    def __str__(self) -> str:
        return f'\'{self.name}\' (ID: {self.id})'


    def add_change(self,
                   role_id: int,
                   add: bool,
                   allow_toggle: bool,
                   message_content: _Optional[str] = None,
                   message_channel_id: _Optional[int] = None,
                   message_embed: _Optional[str] = None
    ) -> 'ReactionRoleChange':
        change = ReactionRoleChange(
            add=add,
            allow_toggle=allow_toggle,
            message_content=message_content,
            message_channel_id=message_channel_id,
            message_embed=message_embed,
            role_id=role_id
        )
        change.reaction_role = self
        change.create()
        return change


    def add_requirement(self,
                        required_role_id: int
    ) -> 'ReactionRoleRequirement':
        requirement = ReactionRoleRequirement(
            role_id=required_role_id
        )
        requirement.reaction_role = self
        requirement.create()
        return requirement


    async def apply_add(self,
                        member: _Member
    ) -> None:
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
                if role_change and change.message_channel_id and (change.message_content or change.message_embed):
                    channel = member.guild.get_channel(change.message_channel_id)
                    messages_to_post.append((channel, change.message_content, change.message_embed, role))
        await member.add_roles(*roles_to_add)
        await member.remove_roles(*roles_to_remove)
        for channel, text, embed_definition, role in messages_to_post:
            substitutions = _utils.discord.create_substitutions(guild=member.guild, role=role, member=member)
            if text:
                for key, value in substitutions.items():
                    text = text.replace(key, value)
            if embed_definition:
                embed_definition = _utils.discord.update_embed_definition(embed_definition, substitutions)
                embed = await _utils.discord.get_embed_from_definition_or_url(embed_definition)
            else:
                embed = None
            await channel.send(text, embed=embed)


    async def apply_remove(self,
                           member: _Member
    ) -> None:
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


    def remove_change(self,
                      role_change_id: int
    ) -> None:
        for change in self.role_changes:
            if change.id == role_change_id:
                change.delete()
                return
        raise Exception(f'There is no role change with ID \'{role_change_id}\' related to the Reaction Role {self}.')


    def remove_requirement(self,
                           role_requirement_id: int
    ) -> None:
        for requirement in self.role_requirements:
            if requirement.id == role_requirement_id:
                requirement.delete()
                return
        raise Exception(f'There is no role requirement with ID \'{role_requirement_id}\' related to the Reaction Role {self}.')


    async def try_activate(self,
                           ctx: _Context
    ) -> bool:
        try:
            reaction_message = await ctx.guild.get_channel(self.channel_id).fetch_message(self.message_id)
            await reaction_message.add_reaction(self.reaction)
            success = True
        except:
            success = False
        self.is_active = success
        return success


    async def try_deactivate(self,
                             ctx: _Context
    ) -> bool:
        try:
            reaction_message = await ctx.guild.get_channel(self.channel_id).fetch_message(self.message_id)
            await reaction_message.remove_reaction(self.reaction, ctx.guild.me)
            success = True
        except:
            success = False
        self.is_active = not success
        return success


    def update(self,
               channel_id: _Optional[int] = None,
               message_id: _Optional[int] = None,
               is_active: _Optional[bool] = None
    ) -> None:
        if channel_id is not None:
            self.channel_id = channel_id
        if message_id is not None:
            self.message_id = message_id
        if is_active is not None:
            self.is_active = is_active
        self.save()


    @classmethod
    def make(cls,
             guild_id: int,
             message_channel_id: int,
             message_id: int,
             name: str,
             reaction: str
    ) -> 'ReactionRole':
        result = ReactionRole(
            guild_id=guild_id,
            channel_id=message_channel_id,
            message_id=message_id,
            name=name,
            reaction=reaction,
            )
        return result





class ReactionRoleChange(_orm.ModelBase):
    ID_COLUMN_NAME: str = 'reaction_role_change_id'
    TABLE_NAME: str = 'reaction_role_change'
    __tablename__ = TABLE_NAME

    id = _db.Column(ID_COLUMN_NAME, _db.Integer, primary_key=True, autoincrement=True, nullable=False)
    reaction_role_id = _db.Column(ReactionRole.ID_COLUMN_NAME, _db.Integer, _db.ForeignKey(f'{ReactionRole.TABLE_NAME}.{ReactionRole.ID_COLUMN_NAME}'), nullable=False)
    reaction_role = _db.orm.relationship('ReactionRole', back_populates='role_changes')

    add = _db.Column('add', _db.Boolean, nullable=False)
    allow_toggle = _db.Column('allow_toggle', _db.Boolean, nullable=False)
    message_channel_id = _db.Column('message_channel_id', _db.Integer, nullable=True)
    message_content = _db.Column('message_content', _db.Text, nullable=True)
    message_embed = _db.Column('message_embed', _db.Text, nullable=True)
    role_id = _db.Column('role_id', _db.Integer, nullable=False)


    def __repr__(self) -> str:
        return f'<ReactionRoleChange id={self.id} reaction_role_id={self.reaction_role_id}>'


    @classmethod
    def make(cls,
             add: bool,
             allow_toggle: bool,
             role_id: int,
             message_channel_id: _Optional[int] = None,
             message_content: _Optional[str] = None,
             message_embed: _Optional[str] = None,
    ) -> 'ReactionRoleChange':
        result = ReactionRoleChange(
            add=add,
            allow_toggle=allow_toggle,
            role_id=role_id,
            message_channel_id=message_channel_id,
            message_content=message_content,
            message_embed=message_embed
            )
        return result





class ReactionRoleRequirement(_orm.ModelBase):
    ID_COLUMN_NAME: str = 'reaction_role_requirement_id'
    TABLE_NAME: str = 'reaction_role_requirement'
    __tablename__ = TABLE_NAME

    id = _db.Column(ID_COLUMN_NAME, _db.Integer, primary_key=True, autoincrement=True, nullable=False)
    reaction_role_id = _db.Column(ReactionRole.ID_COLUMN_NAME, _db.Integer, _db.ForeignKey(f'{ReactionRole.TABLE_NAME}.{ReactionRole.ID_COLUMN_NAME}'), nullable=False)
    reaction_role = _db.orm.relationship('ReactionRole', back_populates='role_requirements')
    role_id = _db.Column('role_id', _db.Integer, nullable=False)


    def __repr__(self) -> str:
        return f'<ReactionRoleRequirement id={self.id} reaction_role_id={self.reaction_role_id}>'


    @classmethod
    def make(cls,
             role_id: int
    ) -> 'ReactionRoleRequirement':
        result = ReactionRoleRequirement(
            role_id=role_id
        )
        return result