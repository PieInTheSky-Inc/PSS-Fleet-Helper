import asyncio as _asyncio
from typing import Callable as _Callable

from . import database as _database
from . import chat_log as _chat_log
from . import fleet as _fleet
from . import reaction_role as _reaction_role
from .. import utils as _utils


# ---------- Initialization ----------

async def setup() -> None:
    await _database.init()
    await __setup_db_schema()





# ---------- DB Schema ----------

async def __setup_db_schema() -> None:
    init_functions = [
        ('0.1.0', __create_db_schema),
        ('0.2.0', __update_db_schema_0_2_0),
        ('0.3.0', __update_db_schema_0_3_0),
        ('0.4.0', __update_db_schema_0_4_0),
        ('0.7.0', __update_db_schema_0_7_0),
        ('0.7.1', __update_db_schema_0_7_1),
    ]
    for version, callable in init_functions:
        if not (await __update_schema(version, callable)):
            raise Exception('DB initialization failed')

    print('DB initialization succeeded')


async def __update_db_schema_0_7_1() -> bool:
    target_version = '0.7.1'
    column_definition_fleet_fleet_name = _database.ColumnDefinition('fleet_name', _database.ColumnType.STRING, False, False)

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_7_1 = _utils.compare_versions(schema_version, target_version)
        if compare_0_7_1 < 1:
            return True

    print(f'[update_schema_0_7_1] Updating to database schema v{target_version}')

    success_fleet = await _database.try_add_column(_fleet.Fleet.TABLE_NAME, *column_definition_fleet_fleet_name)
    if not success_fleet:
        print(f'[update_schema_0_7_1] Could not update table \'{_fleet.Fleet.TABLE_NAME}\'')
        return False

    success = await _database.try_set_schema_version(target_version)
    return success


async def __update_db_schema_0_7_0() -> bool:
    target_version = '0.7.0'
    column_definitions_fleet = [
        _database.ColumnDefinition(_fleet.Fleet.ID_COLUMN_NAME, _database.ColumnType.BIGINT, True, True),
        _database.ColumnDefinition('created_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('modified_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('guild_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('short_name', _database.ColumnType.STRING, False, False),
    ]

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_7_0 = _utils.compare_versions(schema_version, target_version)
        if compare_0_7_0 < 1:
            return True

    print(f'[update_schema_0_7_0] Updating to database schema v{target_version}')

    success_fleet = await _database.try_create_table(_fleet.Fleet.TABLE_NAME, column_definitions_fleet)
    if not success_fleet:
        print(f'[update_schema_0_7_0] Could not create table \'{_fleet.Fleet.TABLE_NAME}\'')
        return False

    success = await _database.try_set_schema_version(target_version)
    return success


async def __update_db_schema_0_4_0() -> bool:
    target_version = '0.4.0'
    column_definitions_chat_log = [
        _database.ColumnDefinition(_chat_log.PssChatLogger.ID_COLUMN_NAME, _database.ColumnType.AUTO_INCREMENT, True, True),
        _database.ColumnDefinition('created_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('modified_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('guild_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('channel_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('pss_channel_key', _database.ColumnType.STRING, False, True),
        _database.ColumnDefinition('last_pss_message_id', _database.ColumnType.INT, False, True, default=0),
        _database.ColumnDefinition('name', _database.ColumnType.STRING, False, True),
    ]

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_4_0 = _utils.compare_versions(schema_version, target_version)
        if compare_0_4_0 < 1:
            return True

    print(f'[update_schema_0_4_0] Updating to database schema v{target_version}')

    success_chat_log = await _database.try_create_table(_chat_log.PssChatLogger.TABLE_NAME, column_definitions_chat_log)
    if not success_chat_log:
        print(f'[update_schema_0_4_0] Could not create table \'{_chat_log.PssChatLogger.TABLE_NAME}\'')
        return False

    success = await _database.try_set_schema_version(target_version)
    return success


async def __update_db_schema_0_3_0() -> bool:
    target_version = '0.3.0'
    column_definition = _database.ColumnDefinition('message_embed', 'TEXT', False, False)

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_3_0 = _utils.compare_versions(schema_version, target_version)
        if compare_0_3_0 < 1:
            return True

    print(f'[update_schema_0_3_0] Updating to database schema v{target_version}')

    success_reaction_role = await _database.try_add_column(_reaction_role.ReactionRoleChange.TABLE_NAME, *column_definition)
    if not success_reaction_role:
        print(f'[update_schema_0_3_0] Could not add column \'{column_definition[0]}\' to table \'{_reaction_role.ReactionRoleChange.TABLE_NAME}\'')
        return False

    success = await _database.try_set_schema_version(target_version)
    return success


async def __update_db_schema_0_2_0() -> bool:
    target_version = '0.2.0'
    column_definitions_reaction_role = [
        _database.ColumnDefinition(_reaction_role.ReactionRole.ID_COLUMN_NAME, _database.ColumnType.AUTO_INCREMENT, True, True),
        _database.ColumnDefinition('created_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('modified_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('guild_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('channel_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('message_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('name', _database.ColumnType.STRING, False, True),
        _database.ColumnDefinition('reaction', _database.ColumnType.STRING, False, True),
        _database.ColumnDefinition('is_active', _database.ColumnType.BOOLEAN, False, True, default=False),
    ]
    column_definitions_reaction_role_change = [
        _database.ColumnDefinition(_reaction_role.ReactionRoleChange.ID_COLUMN_NAME, _database.ColumnType.AUTO_INCREMENT, True, True),
        _database.ColumnDefinition('created_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('modified_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition(_reaction_role.ReactionRole.ID_COLUMN_NAME, _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('role_id', _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('add', _database.ColumnType.BOOLEAN, False, True, default=True), # True to add, False to remove
        _database.ColumnDefinition('allow_toggle', _database.ColumnType.BOOLEAN, False, True, default=False),
        _database.ColumnDefinition('message_content', _database.ColumnType.STRING, False, True),
        _database.ColumnDefinition('message_channel_id', _database.ColumnType.INT, False, True),
    ]
    column_definitions_reaction_role_requirement = [
        _database.ColumnDefinition(_reaction_role.ReactionRoleRequirement.ID_COLUMN_NAME, _database.ColumnType.AUTO_INCREMENT, True, True),
        _database.ColumnDefinition('created_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('modified_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition(_reaction_role.ReactionRole.ID_COLUMN_NAME, _database.ColumnType.INT, False, True),
        _database.ColumnDefinition('role_id', _database.ColumnType.INT, False, True),
    ]

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_2_0 = _utils.compare_versions(schema_version, target_version)
        if compare_0_2_0 < 1:
            return True

    print(f'[update_schema_0_2_0] Updating to database schema v{target_version}')

    success_reaction_role = await _database.try_create_table(_reaction_role.ReactionRole.TABLE_NAME, column_definitions_reaction_role)
    if not success_reaction_role:
        print(f'[update_schema_0_2_0] Could not create table \'{_reaction_role.ReactionRole.TABLE_NAME}\'')
        return False

    success_reaction_role_change = await _database.try_create_table(_reaction_role.ReactionRoleChange.TABLE_NAME, column_definitions_reaction_role_change)
    if not success_reaction_role_change:
        print(f'[update_schema_0_2_0] Could not create table \'{_reaction_role.ReactionRoleChange.TABLE_NAME}\'. Rolling back changes made.')
        await _database.drop_table(_reaction_role.ReactionRole.TABLE_NAME)
        return False

    success_reaction_role_requirement = await _database.try_create_table(_reaction_role.ReactionRoleRequirement.TABLE_NAME, column_definitions_reaction_role_requirement)
    if not success_reaction_role_requirement:
        print(f'[update_schema_0_2_0] Could not create table \'{_reaction_role.ReactionRoleRequirement.TABLE_NAME}\'. Rolling back changes made.')
        await _database.drop_table(_reaction_role.ReactionRole.TABLE_NAME)
        await _database.drop_table(_reaction_role.ReactionRoleChange.TABLE_NAME)
        return False

    success = await _database.try_set_schema_version(target_version)
    return success


async def __create_db_schema() -> bool:
    target_version = '0.1.0'
    column_definition_bot_settings = [
        _database.ColumnDefinition('setting_name', _database.ColumnType.STRING, True, True),
        _database.ColumnDefinition('created_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('modified_at', _database.ColumnType.DATETIME, False, True, default='CURRENT_TIMESTAMP'),
        _database.ColumnDefinition('setting_boolean', _database.ColumnType.BOOLEAN, False, False),
        _database.ColumnDefinition('setting_float', _database.ColumnType.FLOAT, False, False),
        _database.ColumnDefinition('setting_int', _database.ColumnType.INT, False, False),
        _database.ColumnDefinition('setting_text', _database.ColumnType.STRING, False, False),
        _database.ColumnDefinition('setting_timestamp', _database.ColumnType.DATETIME, False, False),
    ]

    schema_version = await _database.get_schema_version()
    if schema_version:
        compare_0_1_0 = _utils.compare_versions(schema_version, target_version)
        if compare_0_1_0 < 1:
            return True

    print(f'[create_schema] Creating database schema v{target_version}')

    success_bot_settings = await _database.try_create_table(_database.TABLE_NAME_BOT_SETTINGS, column_definition_bot_settings)
    if not success_bot_settings:
        print(f'[create_schema] Could not create table \'{_database.TABLE_NAME_BOT_SETTINGS}\'')
        return False

    success = await _database.try_set_schema_version(target_version)
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