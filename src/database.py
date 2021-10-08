from datetime import datetime as _datetime
from typing import Any as _Any
from typing import Callable as _Callable
from typing import Dict as _Dict
from typing import List as _List
from typing import Tuple as _Tuple
from threading import Lock as _Lock

import asyncpg as _asyncpg

import app_settings as _app_settings
import utils as _utils


# ---------- Typehints ----------

"""column name, column type, is primary key, not null, default (can be None)"""
ColumnDefinition = _Tuple[str, str, bool, bool, _Any]


# ---------- Constants ----------

__CONNECTION_POOL: _asyncpg.pool.Pool = None
__CONNECTION_POOL_LOCK: _Lock = _Lock()

__TABLE_NAME_BOT_SETTINGS: str = 'bot_settings'




# ---------- DB Schema ----------

async def init_schema() -> None:
    init_functions = {
        '0.1.0': create_schema
    }
    for version, callable in init_functions.items():
        if not (await update_schema(version, callable)):
            raise Exception('DB initialization failed')

    print('DB initialization succeeded')


async def update_schema(version: str, update_function: _Callable) -> bool:
    success = await update_function()
    if not success:
        print(f'Failed to update database schema to version: {version}.')
    return success


async def create_schema() -> bool:
    column_definition_bot_settings = [
        ('setting_name', 'TEXT' , True, True, None),
        ('modify_date', 'TIMESTAMPTZ', False, True, None),
        ('setting_boolean', 'BOOLEAN', False, False, None),
        ('setting_float', 'FLOAT', False, False, None),
        ('setting_int', 'INT', False, False, None),
        ('setting_text', 'TEXT', False, False, None),
        ('setting_timestamp', 'TIMESTAMPTZ', False, False, None),
    ]

    schema_version = await get_schema_version()
    if schema_version:
        compare_010 = _utils.compare_version(schema_version, '0.1.0')
        if compare_010:
            return True

    print(f'[create_schema] Creating database schema v0.1.0')

    success_bot_settings = await try_create_table(__TABLE_NAME_BOT_SETTINGS, column_definition_bot_settings)
    if not success_bot_settings:
        print('[create_schema] DB initialization failed upon creating the table \'bot_settings\'.')
    else:
        success = await try_set_schema_version('0.1.0')
    return success





# ---------- Helper ----------

async def connect() -> bool:
    __log_db_function_enter('connect')

    with __CONNECTION_POOL_LOCK:
        global __CONNECTION_POOL
        if is_connected(__CONNECTION_POOL) is False:
            try:
                __CONNECTION_POOL = await _asyncpg.create_pool(dsn=_app_settings.DATABASE_URL)
                return True
            except Exception as error:
                error_name = error.__class__.__name__
                print(f'[connect] {error_name} occurred while establishing connection: {error}')
                return False
        else:
            return True


async def disconnect() -> None:
    __log_db_function_enter('disconnect')

    with __CONNECTION_POOL_LOCK:
        global __CONNECTION_POOL
        if is_connected(__CONNECTION_POOL):
            await __CONNECTION_POOL.close()


async def execute(query: str, args: _List = None) -> bool:
    __log_db_function_enter('execute', query=f'\'{query}\'', args=args)

    async with __CONNECTION_POOL.acquire() as connection:
        async with connection.transaction():
            if args:
                await connection.execute(query, *args)
            else:
                await connection.execute(query)


async def fetchall(query: str, args: _List = None) -> _List[_asyncpg.Record]:
    __log_db_function_enter('fetchall', query=f'\'{query}\'', args=args)

    if query and query[-1] != ';':
        query += ';'
    result: _List[_asyncpg.Record] = None
    if await connect():
        try:
            async with __CONNECTION_POOL.acquire() as connection:
                async with connection.transaction():
                    if args:
                        result = await connection.fetch(query, *args)
                    else:
                        result = await connection.fetch(query)
        except (_asyncpg.exceptions.PostgresError, _asyncpg.PostgresError) as pg_error:
            raise pg_error
        except Exception as error:
            print_db_query_error('fetchall', query, args, error)
    else:
        print('[fetchall] could not connect to db')
    return result


def get_column_List(column_definitions: _List[ColumnDefinition]) -> str:
    __log_db_function_enter('get_column_List', column_definitions=column_definitions)

    result = []
    for column_definition in column_definitions:
        result.append(_utils.database.get_column_definition(*column_definition))
    return ', '.join(result)


async def get_column_names(table_name: str) -> _List[str]:
    __log_db_function_enter('get_column_names', table_name=f'\'{table_name}\'')

    result = None
    query = f'SELECT column_name FROM information_schema.columns WHERE table_name = $1'
    result = await fetchall(query, [table_name])
    if result:
        result = [record[0] for record in result]
    return result


async def get_schema_version() -> str:
    __log_db_function_enter('get_schema_version')

    try:
        result, _ = await get_setting('schema_version')
    except:
        result = None
    return result or ''


def is_connected(pool: _asyncpg.pool.Pool) -> bool:
    __log_db_function_enter('is_connected', pool=pool)

    if pool:
        return not (pool._closed or pool._closing)
    return False


async def try_set_schema_version(version: str) -> bool:
    __log_db_function_enter('try_set_schema_version', version=f'\'{version}\'')

    prior_version = await get_schema_version()
    utc_now = _utils.datetime.get_utc_now()
    if not prior_version:
        query = f'INSERT INTO {__TABLE_NAME_BOT_SETTINGS} (modify_date, setting_text, setting_name) VALUES ($1, $2, $3)'
    else:
        query = f'UPDATE {__TABLE_NAME_BOT_SETTINGS} SET modify_date = $1, setting_text = $2 WHERE setting_name = $3'
    success = await try_execute(query, [utc_now, version, 'schema_version'])
    return success


async def try_create_table(table_name: str, column_definitions: _List[ColumnDefinition]) -> bool:
    __log_db_function_enter('try_create_table', table_name=f'\'{table_name}\'', column_definitions=column_definitions)

    column_List = get_column_List(column_definitions)
    query_create = f'CREATE TABLE {table_name} ({column_List});'
    success = False
    if await connect():
        try:
            success = await try_execute(query_create, raise_db_error=True)
        except _asyncpg.exceptions.DuplicateTableError:
            success = True
    else:
        print('[try_create_table] could not connect to db')
    return success


async def try_execute(query: str, args: _List = None, raise_db_error: bool = False) -> bool:
    __log_db_function_enter('try_execute', query=f'\'{query}\'', args=args, raise_db_error=raise_db_error)

    if query and query[-1] != ';':
        query += ';'
    success = False
    if await connect():
        try:
            await execute(query, args)
            success = True
        except (_asyncpg.exceptions.PostgresError, _asyncpg.PostgresError) as pg_error:
            if raise_db_error:
                raise pg_error
            else:
                print_db_query_error('try_execute', query, args, pg_error)
                success = False
        except Exception as error:
            print_db_query_error('try_execute', query, args, error)
            success = False
    else:
        print('[try_execute] could not connect to db')
    return success


async def get_setting(setting_name: str) -> _Tuple[object, _datetime]:
    __log_db_function_enter('get_setting', setting_name=f'\'{setting_name}\'')

    modify_date: _datetime = None
    query = f'SELECT * FROM {__TABLE_NAME_BOT_SETTINGS} WHERE setting_name = $1'
    args = [setting_name]
    try:
        records = await fetchall(query, args)
    except Exception as error:
        print_db_query_error('get_setting', query, args, error)
        records = []
    if records:
        result = records[0]
        modify_date = result[1]
        value = None
        for field in result[2:]:
            if field:
                value = field
                break
        setting = (value, modify_date)
        return setting
    else:
        return (None, None)


async def get_settings(setting_names: _List[str] = None) -> _Dict[str, _Tuple[object, _datetime]]:
    __log_db_function_enter('get_settings', setting_names=setting_names)
    setting_names = setting_names or []
    result = {setting_name: (None, None) for setting_name in setting_names}

    db_setting_names = setting_names

    if not result:
        query = f'SELECT * FROM {__TABLE_NAME_BOT_SETTINGS}'
        if db_setting_names:
            where_strings = [f'setting_name = ${i}' for i in range(1, len(db_setting_names) + 1, 1)]
            where_string = ' OR '.join(where_strings)
            query += f' WHERE {where_string}'
            records = await fetchall(query, args=db_setting_names)
        else:
            records = await fetchall(query)

        for record in records:
            setting_name = record[0]
            modify_date = record[1]
            value = None
            for field in record[2:]:
                if field:
                    value = field
                    break
            result[setting_name] = (value, modify_date)
    return result


async def set_setting(setting_name: str, value: _Any, utc_now: _datetime = None) -> bool:
    __log_db_function_enter('set_setting', setting_name=f'\'{setting_name}\'', value=value, utc_now=utc_now)

    column_name = None
    if isinstance(value, bool):
        column_name = 'setting_boolean'
    elif isinstance(value, int):
        column_name = 'setting_int'
    elif isinstance(value, float):
        column_name = 'setting_float'
    elif isinstance(value, _datetime):
        column_name = 'setting_timestamptz'
    else:
        column_name = 'setting_text'

    success = True
    setting, modify_date = await get_setting(setting_name)
    if utc_now is None:
        utc_now = _utils.datetime.get_utc_now()
    query = ''
    if setting is None and modify_date is None:
        query = f'INSERT INTO {__TABLE_NAME_BOT_SETTINGS} ({column_name}, modify_date, setting_name) VALUES ($1, $2, $3)'
    elif setting != value:
        query = f'UPDATE {__TABLE_NAME_BOT_SETTINGS} SET {column_name} = $1, modify_date = $2 WHERE setting_name = $3'
    success = not query or await try_execute(query, [value, utc_now, setting_name])
    return success


def print_db_query_error(function_name: str, query: str, args: _List[_Any], error: _asyncpg.exceptions.PostgresError) -> None:
    if args:
        args = f'\n{args}'
    else:
        args = ''
    print(f'[{function_name}] {error.__class__.__name__} while performing the query: {query}{args}\nMSG: {error}')


def __log_db_function_enter(function_name: str, **kwargs) -> None:
    if _app_settings.PRINT_DEBUG_DB:
        params = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
        print(f'+ {function_name}({params})')





# ---------- Initialization ----------

async def init() -> None:
    await connect()
    await init_schema()