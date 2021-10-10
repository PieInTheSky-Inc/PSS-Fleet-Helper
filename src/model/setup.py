import asyncio as _asyncio
from typing import Callable as _Callable

from . import database as _database
from .reaction_role import ReactionRole as _ReactionRole
from .reaction_role import ReactionRoleChange as _ReactionRoleChange
from .reaction_role import ReactionRoleRequirement as _ReactionRoleRequirement
from . import utils as _utils


# ---------- Initialization ----------

async def setup() -> None:
    await _database.init()
    await __setup_db_schema()





# ---------- DB Schema ----------

async def __setup_db_schema() -> None:
    init_functions = [
        ('0.1.0', __create_db_schema),
        ('0.2.0', __update_db_schema_0_2_0),
    ]
    for version, callable in init_functions:
        if not (await __update_schema(version, callable)):
            raise Exception('DB initialization failed')

    print('DB initialization succeeded')


async def __update_db_schema_0_2_0() -> bool:
    column_definitions_reaction_role = [
        (_ReactionRole.ID_COLUMN_NAME, 'SERIAL', True, True, None),
        ('created_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        ('modified_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        ('guild_id', 'BIGINT', False, True, None),
        ('channel_id', 'BIGINT', False, True, None),
        ('message_id', 'BIGINT', False, True, None),
        ('name', 'TEXT', False, True, None),
        ('reaction', 'TEXT', False, True, None),
        ('is_active', 'BOOLEAN', False, True, False),
    ]
    column_definitions_reaction_role_change = [
        (_ReactionRoleChange.ID_COLUMN_NAME, 'SERIAL', True, True, None),
        ('created_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        ('modified_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        (_ReactionRole.ID_COLUMN_NAME, 'INT', False, True, None),
        ('role_id', 'BIGINT', False, True, None),
        ('add', 'BOOLEAN', False, True, True), # True to add, False to remove
        ('allow_toggle', 'BOOLEAN', False, True, False),
        ('message_content', 'TEXT', False, False, None),
        ('message_channel_id', 'BIGINT', False, False, None),
    ]
    column_definitions_reaction_role_requirement = [
        (_ReactionRoleRequirement.ID_COLUMN_NAME, 'SERIAL', True, True, None),
        ('created_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        ('modified_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        (_ReactionRole.ID_COLUMN_NAME, 'INT', False, True, None),
        ('role_id', 'BIGINT', False, True, None),
    ]

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_2_0 = _utils.compare_versions(schema_version, '0.2.0')
        if compare_0_2_0 < 1:
            return True

    print(f'[update_schema_0_2_0] Updating to database schema v0.2.0')

    success_reaction_role = await _database.try_create_table(_ReactionRole.TABLE_NAME, column_definitions_reaction_role)
    if not success_reaction_role:
        print(f'[update_schema_0_2_0] Could not create table \'{_ReactionRole.TABLE_NAME}\'')
        return False

    success_reaction_role_change = await _database.try_create_table(_ReactionRoleChange.TABLE_NAME, column_definitions_reaction_role_change)
    if not success_reaction_role_change:
        print(f'[update_schema_0_2_0] Could not create table \'{_ReactionRoleChange.TABLE_NAME}\'. Rolling back changes made.')
        await _database.drop_table(_ReactionRole.TABLE_NAME)
        return False

    success_reaction_role_requirement = await _database.try_create_table(_ReactionRoleRequirement.TABLE_NAME, column_definitions_reaction_role_requirement)
    if not success_reaction_role_requirement:
        print(f'[update_schema_0_2_0] Could not create table \'{_ReactionRoleRequirement.TABLE_NAME}\'. Rolling back changes made.')
        await _database.drop_table(_ReactionRole.TABLE_NAME)
        await _database.drop_table(_ReactionRoleChange.TABLE_NAME)
        return False

    success = await _database.try_set_schema_version('0.2.0')
    return success


async def __create_db_schema() -> bool:
    column_definition_bot_settings = [
        ('setting_name', 'TEXT' , True, True, None),
        ('created_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        ('modified_at', 'TIMESTAMPTZ', False, True, 'CURRENT_TIMESTAMP'),
        ('setting_boolean', 'BOOLEAN', False, False, None),
        ('setting_float', 'FLOAT', False, False, None),
        ('setting_int', 'INT', False, False, None),
        ('setting_text', 'TEXT', False, False, None),
        ('setting_timestamp', 'TIMESTAMPTZ', False, False, None),
    ]

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_1_0 = _utils.compare_versions(schema_version, '0.1.0')
        if compare_0_1_0 < 1:
            return True

    print(f'[create_schema] Creating database schema v0.1.0')

    success_bot_settings = await _database.try_create_table(_database.TABLE_NAME_BOT_SETTINGS, column_definition_bot_settings)
    if not success_bot_settings:
        print(f'[create_schema] Could not create table \'{_database.TABLE_NAME_BOT_SETTINGS}\'')
        return False

    success = await _database.try_set_schema_version('0.1.0')
    return success





# ---------- Helper -----------

async def __update_schema(version: str, update_function: _Callable) -> bool:
    success = await update_function()
    if not success:
        print(f'Failed to update database schema to version: {version}.')
    return success





# ---------- Testing ----------

async def test() -> bool:
    await _database.init()
    await setup()


if __name__ == '__main__':
    _asyncio.get_event_loop().run_until_complete(test())