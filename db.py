import atexit
import datetime
from glob import glob
import json
import logging
import os
import re
import sqlite3

DB = sqlite3.connect(os.getenv("DATABASE_FILE", "loc.sqlite3"))
atexit.register(DB.close)

CURSOR = DB.cursor()
atexit.register(CURSOR.close)

CURSOR.execute("""CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY,
    migration_file STRING NOT NULL,
    applied DATETIME DEFAULT CURRENT_TIMESTAMP)""");
DB.commit()

for migration_file in sorted(glob("./migrations/*.sql")):
    CURSOR.execute("""
        SELECT COUNT(*) FROM migrations
        WHERE migration_file = ?""",
        (migration_file,))
    (count,) = CURSOR.fetchone()

    if count > 0:
        continue

    print(f'Applying migration: {migration_file}')

    with open(migration_file) as f:
        CURSOR.executescript(f.read())
        CURSOR.execute("""
            INSERT INTO migrations (migration_file)
            VALUES (?)""",
            (migration_file,))
        DB.commit()

def now():
    return datetime.datetime.now()

class Channel:
    def __init__(self, row):
        (
            self.id,
            self.sticky_id,
            self.created_at,
            self.updated_at
         ) = row

    def find(channel_id):
        CURSOR.execute("""
            SELECT * FROM channels
            WHERE id = ?""",
            (channel_id,))

        row = CURSOR.fetchone()

        if row:
            return Channel(row)
        else:
            return None

    def create(channel_id):
        CURSOR.execute("""
            INSERT INTO channels (id)
            SELECT ?
            WHERE NOT EXISTS (
                SELECT 1 FROM channels
                WHERE id = ?
            )
            """,
            (channel_id, channel_id))
        DB.commit()
        return Channel.find(channel_id)

    def find_or_create(channel_id):
        channel = Channel.find(channel_id)
        if channel:
            return channel
        else:
            return Channel.create(channel_id)

    def save(self):
        CURSOR.execute("""
            UPDATE channels
            SET sticky_id = ?,
                updated_at = ?
            WHERE id = ?""",
            (self.sticky_id, now(), self.id))
        DB.commit()
        return self


class Entity:
    def __init__(self, attrs):
        for k, v in attrs.items():
            setattr(self, k, v)

    def all(channel_id):
        CURSOR.execute("""
            SELECT * FROM entities
            WHERE channel_id=?
            ORDER BY id""",
            (channel_id,))
        for row in CURSOR.fetchall():
            yield Entity(to_dict(row, CURSOR.description))

    def get(pk):
        CURSOR.execute("""
            SELECT * FROM entities
            WHERE pk = ?
            LIMIT 1""",
            (pk,))
        row = CURSOR.fetchone()
        if row:
            return Entity(to_dict(row, CURSOR.description))
        else:
            return None

    def find(channel_id, entity_name):
        entity_name = entity_name.strip()
        entity_id = None

        if re.match(r"^\d+$", entity_name):
            entity_id = int(entity_name)

        for entity in Entity.all(channel_id):
            if entity_id and entity_id == entity.id:
                return entity
            if entity_name == entity.name:
                return entity

        return None

    def create(channel_id, entity_name):
        CURSOR.execute("""
            INSERT INTO entities (id, channel_id, name)
            VALUES((
                SELECT IFNULL(MAX(id)+1,1)
                FROM entities
                WHERE channel_id = ?),
                ?,
                ?)""",
            (channel_id, channel_id, entity_name))
        DB.commit()
        return Entity.get(CURSOR.lastrowid)

    def find_or_create(channel_id, entity_name):
        entity = Entity.find(channel_id, entity_name)
        if entity:
            return entity
        else:
            return Entity.create(channel_id, entity_name)

    def save(self):
        CURSOR.execute("""
            UPDATE entities
            SET name = ?,
                killed = ?,
                location_pk = ?,
                updated_at = ?
            WHERE pk = ?""",
            (self.name, self.killed, self.location_pk, now(), self.pk))
        DB.commit()
        return self

    def destroy(self):
        CURSOR.execute("""
            DELETE FROM entities
            WHERE pk = ?""",
            (self.pk,))
        DB.commit()

    def __repr__(self):
        return json.dumps(vars(self))

def to_dict(row, columns):
    return {columns[i][0]: row[i] for i, _ in enumerate(row)}

class Location:
    def __init__(self, row):
        (
            self.pk,
            self.id,
            self.channel_id,
            self.name,
            self.created_at,
            self.updated_at
        ) = row

    def all(channel_id):
        CURSOR.execute("""
            SELECT * FROM locations
            WHERE channel_id=?
            ORDER BY id""",
            (channel_id,))
        for row in CURSOR.fetchall():
            yield Location(row)

    def get(pk):
        CURSOR.execute("""
            SELECT * FROM locations
            WHERE pk = ?
            LIMIT 1""",
            (pk,))
        row = CURSOR.fetchone()
        if row:
            return Location(row)
        else:
            return None

    def find(channel_id, location_name):
        location_name = location_name.strip()
        location_id = None

        if re.match(r"^\d+$", location_name):
            location_id = int(location_name)

        for location in Location.all(channel_id):
            if location_id and location_id == location.id:
                return location
            if location_name == location.name:
                return location

        return None

    def create(channel_id, location_name):
        location_name = location_name.strip()

        CURSOR.execute("""
            INSERT INTO locations (id, channel_id, name)
            VALUES((
                SELECT IFNULL(MAX(id)+1,1)
                FROM locations
                WHERE channel_id = ?),
                ?,
                ?)""",
            (channel_id, channel_id, location_name))
        DB.commit()
        return Location.get(CURSOR.lastrowid)

    def find_or_create(channel_id, location_name):
        location = Location.find(channel_id, location_name)
        if location:
            return location
        else:
            return Location.create(channel_id, location_name)

    def save(self):
        CURSOR.execute("""
            UPDATE locations
            SET name = ?,
                updated_at = ?
            WHERE pk = ?""",
            (self.name, now(), self.pk))
        DB.commit()
        return self

    def destroy(self):
        for entity in self.get_entities():
            entity.location_pk = None
            entity.save()

        CURSOR.execute("""
            DELETE FROM locations
            WHERE pk = ?""",
            (self.pk,))
        DB.commit()

    def get_entities(self):
        for row in CURSOR.execute("""
            SELECT * FROM entities
            WHERE location_pk = ?
            ORDER BY id""",
            (self.pk,)):
            yield Entity(to_dict(row, CURSOR.description))

    def __repr__(self):
        return json.dumps(vars(self))