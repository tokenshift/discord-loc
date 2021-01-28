import atexit
import datetime
import json
import re
import sqlite3

DB = sqlite3.connect("loc.sqlite3")
atexit.register(DB.close)

CURSOR = DB.cursor()
atexit.register(CURSOR.close)

CURSOR.execute("""CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    sticky_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
CURSOR.execute("""CREATE TABLE IF NOT EXISTS entities (
    pk INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    name STRING NOT NULL,
    location_pk INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
CURSOR.execute("""CREATE TABLE IF NOT EXISTS locations (
    pk INTEGER PRIMARY KEY,
    id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    name STRING NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
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
    def __init__(self, row):
        (
            self.pk,
            self.id,
            self.channel_id,
            self.name,
            self.location_pk,
            self.created_at,
            self.updated_at
         ) = row

    def all(channel_id):
        CURSOR.execute("""
            SELECT * FROM entities
            WHERE channel_id=?
            ORDER BY id""",
            (channel_id,))
        for row in CURSOR.fetchall():
            yield Entity(row)

    def get(pk):
        CURSOR.execute("""
            SELECT * FROM entities
            WHERE pk = ?
            LIMIT 1""",
            (pk,))
        row = CURSOR.fetchone()
        if row:
            return Entity(row)
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
                location_pk = ?,
                updated_at = ?
            WHERE pk = ?""",
            (self.name, self.location_pk, now(), self.pk))
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
            yield Entity(row)

    def __repr__(self):
        return json.dumps(vars(self))