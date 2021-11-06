import asyncio as _asyncio
from typing import Iterable as _Iterable
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple

from discord import Member as _Member
from discord import TextChannel as _TextChannel
from discord.ext.commands import Context as _Context
import sqlalchemy as _db

from . import database as _database
from .. import utils as _utils




class ReactionRole(_database.DatabaseRowBase):
    FOREIGN_KEY_COLUMN_NAME: str = 'reaction_role_id'
    TABLE_NAME: str = 'reaction_role'
    __tablename__ = TABLE_NAME

    channel_id = _db.Column('channel_id', _db.Integer, nullable=False)
    guild_id = _db.Column('guild_id', _db.Integer, nullable=False)
    is_active = _db.Column('is_active', _db.Boolean, nullable=False)
    message_id = _db.Column('message_id', _db.Integer, nullable=False)
    name = _db.Column('name', _db.Text, nullable=False)
    reaction = _db.Column('reaction', _db.Text, nullable=False)
    role_changes: _Iterable['ReactionRoleChange'] = _db.orm.relationship('ReactionRoleChange', back_populates='reaction_role', cascade='all, delete')
    role_requirements: _Iterable['ReactionRoleRequirement'] = _db.orm.relationship('ReactionRoleRequirement', back_populates='reaction_role', cascade='all, delete')


    def __repr__(self) -> str:
        return f'<Reaction Role id={self.id} name={self.name}>'


    def __str__(self) -> str:
        return f'\'{self.name}\' (ID: {self.id})'


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


    @staticmethod
    async def create(guild_id: int, reaction_channel_id: int, message_id: int, name: str, reaction: str, is_active: bool = False) -> _Optional['ReactionRole']:
        record = await _database.insert_row(
            ReactionRole.TABLE_NAME,
            ReactionRole.FOREIGN_KEY_COLUMN_NAME,
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
    FOREIGN_KEY_COLUMN_NAME: str = 'reaction_role_change_id'
    TABLE_NAME: str = 'reaction_role_change'
    __tablename__ = TABLE_NAME

    reaction_role_id = _db.Column(ReactionRole.FOREIGN_KEY_COLUMN_NAME, _db.Integer, _db.ForeignKey(f'{ReactionRole.TABLE_NAME}.{_database.DatabaseRowBase.ID_COLUMN_NAME}'), nullable=False)
    reaction_role = _db.orm.relationship('ReactionRole', back_populates='role_changes')

    add = _db.Column('add', _db.Boolean, nullable=False)
    allow_toggle = _db.Column('allow_toggle', _db.Boolean, nullable=False)
    message_channel_id = _db.Column('message_channel_id', _db.Integer, nullable=True)
    message_content = _db.Column('message_content', _db.Text, nullable=True)
    message_embed = _db.Column('message_embed', _db.Text, nullable=True)
    role_id = _db.Column('role_id', _db.Integer, nullable=False)


    def __repr__(self) -> str:
        return f'<ReactionRoleChange id={self.id} reaction_role_id={self.reaction_role_id}>'





class ReactionRoleRequirement(_database.DatabaseRowBase):
    FOREIGN_KEY_COLUMN_NAME: str = 'reaction_role_requirement_id'
    TABLE_NAME: str = 'reaction_role_requirement'
    __tablename__ = TABLE_NAME

    reaction_role_id = _db.Column(ReactionRole.FOREIGN_KEY_COLUMN_NAME, _db.Integer, _db.ForeignKey(f'{ReactionRole.TABLE_NAME}.{_database.DatabaseRowBase.ID_COLUMN_NAME}'), nullable=False)
    reaction_role = _db.orm.relationship('ReactionRole', back_populates='role_requirements')
    role_id = _db.Column('role_id', _db.Integer, nullable=False)


    def __repr__(self) -> str:
        return f'<ReactionRoleRequirement id={self.id} reaction_role_id={self.reaction_role_id}>'





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