from typing import Dict, List, Tuple, Union

import aiosqlite

async def get_all_feeds(db_conn : aiosqlite.Connection) -> List[str]:
    """
        Get a list of all currently registered RSS feed links.

        Params:
        - `db_conn` Active async connection to the database

        Returns: list of RSS feed links
    """
    async with db_conn.execute("SELECT url FROM feeds;") as c:
        return [i[0] for i in await c.fetchall()]

async def add_new_feed( db_conn : aiosqlite.Connection
                      , url : str, room_id : str, author : str) -> None:
    """
        Insert a new RSS feed into the database.

        Params:
        - `db_conn` Active async connection to the database
        - `url`     URL of the RSS feed
        - `room_id` Matrix room ID where the RSS feed is updated to
        - `author`  Matrix user ID that first requested the RSS feed.
    """
    await db_conn.execute(
        "INSERT INTO feeds (url, room, author) VALUES (?, ?, ?);",
        (url, room_id, author)
    )
    await db_conn.commit()

async def get_feed(db_conn : aiosqlite.Connection, url : str
                  ) -> Union[None, Dict[str, Union[str, int]]]:
    """
        Get a feed's info from the database.

        Params:
        - `db_conn` Active async connection to the database
        - `url`     URL of the RSS feed

        Returns: either None or a dictionary with the column's keys and the 
        row's values
    """
    headers = [
        'url', 'room', 'author', 'last_updated', 'last_fetch', 'failures'
    ]

    c = await db_conn.execute(
        "SELECT " + ", ".join(headers) + " FROM feeds WHERE url = ?;",
        (url,)
    )

    if not (row := await c.fetchone()):
        return None
    else:
        return { h : r for h, r in zip(headers, row)}


async def update_feed( db_conn : aiosqlite.Connection
                     , url : str, **kwargs) -> None:
    """
        Edit the values of an existing RSS feed.

        Params:
        - `db_conn` Active async connection to the database
        - `url`     URL of the RSS feed
        - `kwargs`  All arguments that need be overwritten
    """
    keys   = list(kwargs.keys())
    values = [kwargs[k] for k in keys]
    f_keys = [k + " = ?" for k in keys]

    await db_conn.execute(
        "UPDATE feeds SET " + ", ".join(f_keys) + " WHERE url = ?;",
        tuple(values) + (url,)
    )
    await db_conn.commit()
