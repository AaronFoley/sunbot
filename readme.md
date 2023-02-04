# SunBot

A Simple discord bot using [hikari](https://github.com/hikari-py/hikari) and [lightbulb](https://github.com/tandemdude/hikari-lightbulb)
This bot was written to add some fun to my personl discord server, and it not intended to be run in production.

## Lavalinnk

Music commands are implemented using the [lavaplayer-py](https://github.com/HazemMeqdad/lavaplayer) and require a Lavalink server to run.

You can run a simple lavalink server using docker:

```
$ wget https://github.com/freyacodes/Lavalink/blob/master/LavalinkServer/application.yml.example -O application.yml
$ docker run -v $(pwd)/application.yml:/opt/Lavalink/application.yaml fredboat/lavalink:3.6.2
```

For more information see [Lavalink](https://github.com/freyacodes/Lavalink)

## Database

Database support is done using [ormar](https://github.com/collerek/ormar) which supports Postgres MySQL and SQLite
Migrations are done using [alembic](https://alembic.sqlalchemy.org/en/latest/)

Once you have configured your database URL in the config.json file, you can run the migrations using the Alembic CLI:

```
$ alembic upgrade head
```
