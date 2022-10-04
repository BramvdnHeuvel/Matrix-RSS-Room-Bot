# Matrix RSS Room Bot

A [Matrix](matrix.org) bot that creates and manages public rooms for RSS feeds.

## Why?

Most bots serve any feed in any channel; this bot serves every feed in a separate channel. This means it's most useful for:

1. Users who prefer to have separate RSS feeds in separate Matrix rooms
2. Users who wish to find other people with the same interests and discuss the topics of the RSS feed

## How to run

You can run the program

1. Using Docker
2. Using Docker compose
3. By running Python directly from your computer

### Using Docker

1. Download `sample.config.yml` and `sample.database.db` and rename them to `config.yml` and `database.db`, respectively.
2. Fill in the details in your `config.yml` file. Leave `database.db` unchanged.
3. Open a terminal in the directory of your files and run the following command:

```sh
docker run -it -v ./config.yml:/config.yml -v ./database.db:/database.db noordstar/matrix-rss-room-bot
```

## Using Docker compose

Instead of running the command directly, you can run the program in a compose file.

```yml
version: '3'
services:
    matrix-rss-room-bot:
        image: noordstar/matrix-rss-room-bot:latest
        restart: unless-stopped
        volumes:
            - ./config.yml:/config.yml
            - ./database.db:/database.db

```

## Using Python

1. Download this repository.
2. Install dependencies by running the following command:

```sh
pip install -r requirements.txt
```

3. Copy `sample.config.yml` to `config.yml` and fill it with your desired settings.
4. Run the following command to set up a new database:

```sh
python update.py
```

You have now set up the Matrix-RSS Room Bot. You can start the bot by running `python main.py` in your terminal indefinitely or until you interrupt the process.

## Potential features

Feel free to contribute! The following features would be useful to have added.

- [ ] Bot moderation channel to monitor spam
- [ ] Allow URL links with parameters if they render different RSS feeds
- [ ] User blacklist so the bot ignores misbehaving users
