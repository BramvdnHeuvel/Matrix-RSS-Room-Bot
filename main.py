import asyncio
import os

import aiosqlite
from nio import AsyncClient, InviteEvent, RoomMessageText
import yaml

from src import db, msg


with open(os.getenv('CONFIG_FILE', 'config.yaml'), 'r', encoding='utf-8') as fp:
    CONFIG = yaml.safe_load(fp)

HOMESERVER = CONFIG['homeserver']
USERNAME   = CONFIG['username']
PASSWORD   = CONFIG['password']


async def main():
    client = AsyncClient(HOMESERVER, USERNAME)
    client.add_event_callback(msg.message_callback(client), RoomMessageText)
    client.add_event_callback(msg.join_room_callback(client), InviteEvent)

    print(await client.login(PASSWORD))

    tasks = [client.sync_forever(timeout=30000)]

    async with aiosqlite.connect(msg.DATABASE) as db_conn:
        tasks += [
            msg.track_rss_feed(client, url)
            for url in await db.get_all_feeds(db_conn)
        ]

    await asyncio.gather(*tasks)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

