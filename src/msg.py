import asyncio
import datetime
import random
import urllib.parse as parse

import aiohttp
import aiosqlite
from nio import ( AsyncClient, Event, MatrixRoom, RoomCreateError
                , RoomMessageText , RoomPreset, RoomVisibility
                )
import yaml

from src import db, parser


with open('config.yaml', 'r', encoding='utf-8') as fp:
    CONFIG = yaml.safe_load(fp)

DATABASE = CONFIG['database']
UPDATE_INTERVAL = CONFIG['update_interval_minutes'] * 60
DEBUG_MODE = CONFIG['debug_mode']


async def track_rss_feed(client : AsyncClient, url : str) -> None:
    """
        Continuously update an RSS Feed.
    """
    await asyncio.sleep(random.randint(0, UPDATE_INTERVAL-1))
    
    while True:
        async with aiosqlite.connect(DATABASE) as db_conn:
            row = await db.get_feed(db_conn, url)

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            print(
                                "Received status code " + str(resp.status) +
                                " while trying to reach RSS Feed: " + url
                            )
                        
                            raise ConnectionError(
                                "Failed to fetch feed: " + url
                            )
                        
                        feed = parser.RSSFeed(
                            await resp.text()
                        )

                        if not feed.updated:
                            feed.updated = datetime.datetime.now()
        
            # The internet connection failed
            except ConnectionError:
                db.update_feed(db_conn, url, failures = row['failures'] + 1)

            # The RSS Feed didn't parse
            except KeyError:
                print("Failed to parse RSS Feed :" + url)
                db.update_feed(db_conn, url, failures = row['failures'] + 1)

            # ???
            except Exception as e:
                if DEBUG_MODE:
                    raise e
                else:
                    print(
                        "Encountered an unexpected event while trying to " +
                        "update RSS Feed: " + url
                    )
                    print(e)

            # Nothing went wrong, everything went as planned
            else:
                old_fed = parser.RSSFeed(row['last_fetch'])

                new_posts = [
                    post for post in feed.entries if post not in old_fed.entries
                ]

                # Publish new posts
                for post in new_posts:
                    await client.room_send(
                        room_id=row['room'],
                        message_type='m.room.message',
                        content=post.m_json()
                    )

                # Post updates in Matrix
                await db.update_feed(db_conn, url,
                    last_updated = feed.updated,
                    last_fetch   = feed.raw,
                    failures     = 0
                )

                print("Updated RSS Feed: " + url)

        # Wait for the next interval
        await asyncio.sleep(
            random.randint(
                int(0.8 * UPDATE_INTERVAL),
                int(1.2 * UPDATE_INTERVAL)
            )
        )

async def respond_in_thread( client : AsyncClient, room_id : str
                           , event_id : str, text : str) -> None:
    """
        Respond to a message in a thread.

        Params:
        - `client`      Matrix async client
        - `room_id`     Matrix room ID
        - `event_id`    Matrix event ID that the new message responds to
        - `text`        Response message
    """
    await client.room_send(
        room_id=room_id,
        message_type='m.room.message',
        content={
            'msgtype'       : 'm.text',
            'body'          : text,
            'm.relates_to'  : {
                'rel_type'          : 'm.thread',
                'event_id'          : event_id,
                'is_falling_back'   : True
            }
        }
    )

async def send_link_in_thread(client : AsyncClient, room_id : str,
                              event_id : str, room_link : str) -> None:
    """
        Respond to a message in a thread.

        Params:
        - `client`      Matrix async client
        - `room_id`     Matrix room ID
        - `event_id`    Matrix event ID that the new message responds to
        - `text`        Response message
    """
    await respond_in_thread(client, room_id, event_id,
        "I have invited you to a room with the feed."
    )
    await client.room_send(
        room_id=room_id,
        message_type='m.room.message',
        content={
            'msgtype'       : 'm.text',
            'body'          : 'Other users can find the room at ' + room_link,
            'format'        : 'org.matrix.custom.html',
            'formatted_body': ( 'Other users can find the room at <a href="'
                              + 'https://matrix.to/#/' + room_link 
                              + '?via=noordstar.me">' + room_link + '</a>'
                              ),
            'm.relates_to'  : {
                'rel_type'          : 'm.thread',
                'event_id'          : event_id,
                'is_falling_back'   : True
            }
        }
    )

def message_callback(client : AsyncClient):
    """
        Defined behaviour for the Matrix client when receiving a request.
    """
    async def run_message(room : MatrixRoom, event : RoomMessageText) -> None:
        if not event.body.startswith('!rss '):
            return

        url = parse.urlparse(event.body.split(" ")[1], allow_fragments=False)
        url = url._replace(params = '')

        if url.scheme == '':
            url = url._replace(scheme = 'https')
        if url.netloc == '' and url.path != '':
            url = url._replace(
                netloc  = url.path,
                path    = ''
            )

        thread = lambda text : respond_in_thread(client, room.room_id, 
                                                    event.event_id, text)

        # Check for unfit URLs
        if url.scheme not in ['http', 'https'] or url.netloc == '':
            await thread("I'm sorry, that's not a URL I can use.")
            return
        if url.query != '':
            await thread(
                "I'm sorry, I currently do not support feeds with URL params."
            )
            # TODO: Allow queries if adding a query actually renders a
            #       different result from previously added RSS feed URLs.
            return

        url : str = url.geturl()
        
        async with aiosqlite.connect(DATABASE) as db_conn:

            # Create the room if it doesn't exist yet.
            newly_created = False

            if await db.get_feed(db_conn, url) is None:
                newly_created = True

                try:
                    # Get the RSS Feed's content
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                feed = parser.RSSFeed(
                                    await resp.text()
                                )
                            else:
                                raise ConnectionError(
                                    "Failed to catch RSS feed"
                                )
                except ConnectionError:
                    await thread(
                        "That URL didn't give me the right response."
                    )
                    print("Failed to find a new RSS Feed: " + url)
                    return
                except Exception as e:
                    await thread(
                        "That link doesn't look like an RSS Feed. Are you sure?"
                    )
                    print("Failed to interpret a new RSS Feed: " + url)
                    print(e)
                    return
                else:
                    # Once found the appropriate RSS feed,
                    # create a room and invite the user into it.

                    result = await client.room_create(
                        visibility=RoomVisibility.private,
                        name=feed.title,
                        topic=feed.subtitle,
                        invite=[event.sender],
                        preset=RoomPreset.public_chat
                    )

                    if result.__class__ is RoomCreateError:
                        await thread(
                            "ERROR: Failed to create a room for this feed."
                        )
                        print(
                            "Failed to create a room for this RSS Feed: " + url
                        )
                        print(result)
                        return
                    
                    await db.add_new_feed(
                        db_conn, url, result.room_id, event.sender
                    )
                    await db.update_feed(db_conn, url,
                        last_fetch=feed.raw,
                        last_updated=datetime.datetime.now()
                    )
            
            # Invite the user
            room_link = (await db.get_feed(db_conn, url))['room']
            await client.room_invite(room_link, event.sender)
            await send_link_in_thread(
                client, room.room_id, event.event_id, room_link
            )


            # Start a background process if the feed is new
            if newly_created:
                asyncio.get_running_loop().create_task(
                    track_rss_feed(client, url)
                )
                print("Added new RSS Feed: " + url)

    return run_message

def join_room_callback(client : AsyncClient):
    async def enter_room(room : MatrixRoom, event : Event) -> None:
        await client.join(room.room_id)
    return enter_room
        