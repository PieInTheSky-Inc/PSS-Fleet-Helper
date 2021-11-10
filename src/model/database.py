from datetime import datetime as _datetime
from typing import Any as _Any
from typing import Dict as _Dict
from typing import List as _List
from typing import Optional as _Optional
from typing import Tuple as _Tuple
from threading import Lock as _Lock

import asyncpg as _asyncpg

from . import model_settings as _model_settings
from .. import utils as _utils


# ---------- Typehints ----------

"""column name, column type, is primary key, not null, default (can be None)"""
ColumnDefinition = _Tuple[str, str, bool, bool, _Any]


# ---------- Constants ----------

__CONNECTION_POOL: _asyncpg.pool.Pool = None
__CONNECTION_POOL_LOCK: _Lock = _Lock()

TABLE_NAME_BOT_SETTINGS: str = 'bot_settings'





# ---------- Helper ----------

async def connect() -> bool:
    __log_db_function_enter('connect')

    with __CONNECTION_POOL_LOCK:
        global __CONNECTION_POOL
        if is_connected(__CONNECTION_POOL) is False:
            try:
                __CONNECTION_POOL = await _asyncpg.create_pool(dsn=_model_settings.DATABASE_URL)
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


async def delete_rows(table_name: str, id_column_name: str, ids: _List[_Any]) -> bool:
    __log_db_function_enter('delete_rows', table_name=table_name, id_column_name=id_column_name, ids=ids)

    result = False
    in_values = ','.join([str(id) for id in ids])
    query = f'DELETE FROM {table_name} WHERE {id_column_name} IN ({in_values})'
    result, _ = await try_execute(query)
    return result


async def insert_row(table_name: str, id_column_name: str, **kwargs) -> _asyncpg.Record:
    __log_db_function_enter('insert_row', table_name=table_name, **kwargs)

    column_names, placeholders, args = __split_kwargs_into_columns_and_values(**kwargs)
    columns = ', '.join(column_names)
    value_placeholders = ','.join(placeholders)
    query = f'INSERT INTO {table_name} ({columns}) VALUES ({value_placeholders}) RETURNING {id_column_name}'
    results = await execute(query, args)
    if results:
        return results[0]
    raise Exception('Database insertion failed')


def __split_kwargs_into_columns_and_values(**kwargs) -> _Tuple[_List[_Any], _List[str], _List[_Any]]:
    column_names = []
    placeholders = []
    args = []
    for i, (column_name, column_value) in enumerate(kwargs.items(), 1):
        column_names.append(column_name)
        placeholders.append(f'${i}')
        args.append(column_value)
    return (column_names, placeholders, args)


async def update_row(table_name: str, id_column_name: str, id: _Any, **kwargs) -> bool:
    __log_db_function_enter('delete_rows', table_name=table_name, id_column_name=id_column_name, id=id, **kwargs)

    result = False
    column_names, _, args = __split_kwargs_into_columns_and_values(**kwargs)
    set_definition = ', '.join([f'{column_name}=${i}' for i, column_name in enumerate(column_names, 1)])
    args.append(id)
    query = f'UPDATE {table_name} SET {set_definition} WHERE {id_column_name} = ${len(args)} RETURNING {id_column_name}'
    result = await execute(query, args)
    return bool(result)


async def drop_table(table_name: str) -> None:
    __log_db_function_enter('drop_table', table_name=table_name)

    query = f'DROP TABLE {table_name}'
    execute(query)


async def execute(query: str, args: _List[_Any] = None) -> _List[_asyncpg.Record]:
    __log_db_function_enter('execute', query=f'\'{query}\'', args=args)

    result = None
    connection: _asyncpg.Connection
    async with __CONNECTION_POOL.acquire() as connection:
        async with connection.transaction():
            if args:
                result = await connection.fetch(query, *args)
            else:
                result = await connection.fetch(query)
    return result


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


async def try_add_column(table_name: str, column_name: str, column_type: str, is_primary: bool, not_null: bool, default: _Optional[_Any] = None) -> bool:
    __log_db_function_enter('try_add_column', table_name=f'\'{table_name}\'', column_name=f'\'{column_name}\'', column_type=f'\'{column_type}\'', is_primary=is_primary, not_null=not_null, default=default)

    is_primary_str = ' PRIMARY KEY' if is_primary else ''
    not_null_str = ' NOT NULL' if not_null else ''
    default_str = f' DEFAULT {default}' if default else ''
    query = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type.upper()}{is_primary_str}{not_null_str}{default_str}'
    success, _ = await try_execute(query)
    return success


async def try_set_schema_version(version: str) -> bool:
    __log_db_function_enter('try_set_schema_version', version=f'\'{version}\'')

    prior_version = await get_schema_version()
    if not prior_version:
        success = bool(await insert_row(TABLE_NAME_BOT_SETTINGS, 'setting_name', setting_name='schema_version', setting_text=version))
    else:
        utc_now = _utils.datetime.get_utc_now()
        success = await update_row(TABLE_NAME_BOT_SETTINGS, 'setting_name', 'schema_version', modified_at=utc_now, setting_text=version)
    return success


async def try_create_table(table_name: str, column_definitions: _List[ColumnDefinition]) -> bool:
    __log_db_function_enter('try_create_table', table_name=f'\'{table_name}\'', column_definitions=column_definitions)

    column_List = get_column_List(column_definitions)
    query_create = f'CREATE TABLE {table_name} ({column_List});'
    success = False
    if await connect():
        try:
            success, _ = await try_execute(query_create, raise_db_error=True)
        except _asyncpg.exceptions.DuplicateTableError:
            success = True
    else:
        print('[try_create_table] could not connect to db')
    return success


async def try_execute(query: str, args: _List = None, raise_db_error: bool = False) -> _Tuple[bool, _List[_asyncpg.Record]]:
    __log_db_function_enter('try_execute', query=f'\'{query}\'', args=args, raise_db_error=raise_db_error)

    results = None
    if query and query[-1] != ';':
        query += ';'
    success = False
    if await connect():
        try:
            results = await execute(query, args)
            success = True
        except _asyncpg.PostgresError as pg_error:
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
    return (success, results)


async def get_setting(setting_name: str) -> _Tuple[object, _datetime]:
    __log_db_function_enter('get_setting', setting_name=f'\'{setting_name}\'')

    modify_date: _datetime = None
    query = f'SELECT * FROM {TABLE_NAME_BOT_SETTINGS} WHERE setting_name = $1'
    args = [setting_name]
    try:
        records = await fetchall(query, args)
    except Exception as error:
        print_db_query_error('get_setting', query, args, error)
        records = []
    if records:
        result = records[0]
        modify_date = result[2]
        value = None
        for field in result[3:]:
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
        query = f'SELECT * FROM {TABLE_NAME_BOT_SETTINGS}'
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

    kwargs = {
        'setting_name': setting_name
    }
    if isinstance(value, bool):
        kwargs['setting_boolean'] = value
    elif isinstance(value, int):
        kwargs['setting_int'] = value
    elif isinstance(value, float):
        kwargs['setting_float'] = value
    elif isinstance(value, _datetime):
        kwargs['setting_timestamptz'] = value
    else:
        kwargs['setting_text'] = value

    setting, _ = await get_setting(setting_name)
    success = True
    if setting is None:
        success = bool(await insert_row(TABLE_NAME_BOT_SETTINGS, 'setting_name', **kwargs))
    elif setting != value:
        kwargs['modified_at'] = _utils.datetime.get_utc_now()
        success = await update_row(TABLE_NAME_BOT_SETTINGS, **kwargs)
    return success


def print_db_query_error(function_name: str, query: str, args: _List[_Any], error: _asyncpg.exceptions.PostgresError) -> None:
    if args:
        args = f'\n{args}'
    else:
        args = ''
    print(f'[{function_name}] {error.__class__.__name__} while performing the query: {query}{args}\nMSG: {error}')


def __log_db_function_enter(function_name: str, **kwargs) -> None:
    if _model_settings.PRINT_DEBUG_DB:
        params = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
        print(f'+ {function_name}({params})')





# ---------- Initialization ----------

async def init() -> None:
    await connect()