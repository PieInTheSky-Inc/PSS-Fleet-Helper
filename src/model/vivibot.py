from typing import Dict as _Dict
from typing import List as _List

from discord.ext.commands import Bot as _Bot

from . import database as _database
from .reaction_role import ReactionRole as _ReactionRole
from .reaction_role import ReactionRoleChange as _ReactionRoleChange
from .reaction_role import ReactionRoleRequirement as _ReactionRoleRequirement


class ViViBot():
    def __init__(self, bot: _Bot) -> None:
        self.__bot: _Bot = bot
        self.__reaction_roles: _List[_ReactionRole] = []


    @property
    def bot(self) -> _Bot:
        return self.__bot

    @property
    def reaction_roles(self) -> _Dict[int, _List[_ReactionRole]]:
        return self.__reaction_roles


    async def initialize(self) -> None:
        self.__reaction_roles = await ViViBot._read_reaction_roles_from_db()


    def set_bot(self, bot: _Bot) -> None:
        self.__bot = bot


    @staticmethod
    async def _read_reaction_roles_from_db() -> _Dict[int, _ReactionRole]:
        reaction_roles: _List[_ReactionRole] = []
        changes: _Dict[int, _ReactionRoleChange] = {}
        requirements: _Dict[int, _ReactionRoleRequirement] = {}

        query = f'SELECT * FROM {_ReactionRole.TABLE_NAME}'
        rows = await _database.fetchall(query)
        reaction_roles = [_ReactionRole(row[0], *row[3:]) for row in rows]

        query = f'SELECT * FROM {_ReactionRoleChange.TABLE_NAME}'
        rows = await _database.fetchall(query)
        for row in rows:
            changes.setdefault(row[3], []).append(_ReactionRoleChange(row[0], *row[3:]))

        query = f'SELECT * FROM {_ReactionRoleRequirement.TABLE_NAME}'
        rows = await _database.fetchall(query)
        for row in rows:
            requirements.setdefault(row[3], []).append(_ReactionRoleRequirement(row[0], *row[3:]))

        reaction_roles.sort(key=lambda rr: rr.id)
        result = {}
        for reaction_role in reaction_roles:
            if reaction_role.id in changes:
                reaction_role.update_changes(changes[reaction_role.id])
            if reaction_role.id in requirements:
                reaction_role.update_requirements(requirements[reaction_role.id])
            result.setdefault(reaction_role.guild_id, []).append(reaction_role)

        return result