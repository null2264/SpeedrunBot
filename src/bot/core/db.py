from __future__ import annotations
import os
from typing import TYPE_CHECKING

from cassandra.cluster import Cluster

from aiocqlengine.models import AioModel as Model
from cassandra.cqlengine import columns, connection
from cassandra.cqlengine import management

from aiocqlengine.session import aiosession_for_cqlengine


if TYPE_CHECKING:
    from .config import Config


class Starboard(Model):
    id = columns.BigInt(primary_key=True, partition_key=True)
    guild_id = columns.BigInt(primary_key=True, partition_key=True)
    amount = columns.Integer(default=3)
    emoji = columns.Text(default="⭐")


class Starred(Model):
    # Types:
    # 0: Legacy
    # 1: Star count update
    type = columns.Integer(default=1)
    id = columns.BigInt(primary_key=True, partition_key=True)
    guild_id = columns.BigInt(primary_key=True, partition_key=True)
    bot_message_id = columns.BigInt(primary_key=True, partition_key=True)


class Star(Model):
    user_id = columns.BigInt(primary_key=True, partition_key=True)
    message_id = columns.BigInt(primary_key=True, partition_key=True)


class RunSent(Model):
    id = columns.Text(primary_key=True)


class GameSubscribed(Model):
    id = columns.Text(primary_key=True)
    name = columns.Text()
    target_id = columns.BigInt(primary_key=True, partition_key=True)
    channel_id = columns.BigInt(primary_key=True, partition_key=True)


def sync(config: Config):
    management.create_keyspace_simple(config.scylla_keyspace, 1)
    management.sync_table(Starred, keyspaces=config.scylla_keyspace)
    management.sync_table(Star, keyspaces=config.scylla_keyspace)
    management.sync_table(RunSent, keyspaces=config.scylla_keyspace)
    management.sync_table(GameSubscribed, keyspaces=config.scylla_keyspace)


def create_session(config: Config):
    cluster = Cluster()
    session = cluster.connect()

    # Create keyspace, if already have keyspace your can skip this
    os.environ["CQLENG_ALLOW_SCHEMA_MANAGEMENT"] = "true"
    connection.register_connection("cqlengine", session=session, default=True)
    sync(config)

    # Wrap cqlengine connection
    aiosession_for_cqlengine(session)
    session.set_keyspace(config.scylla_keyspace)
    connection.set_session(session)
    return session
