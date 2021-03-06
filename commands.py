from db import Channel, Entity, Location
import discord

HELP_TEXT = """`loc help`
Display all available commands.

`loc show`
Display all entities and locations.

`loc move {entity} {location}`
Sets an entity's location. `{entity}` and `{location}` can be either names or
numbers assigned by loc.

`loc remove {entity}`
Removes an entity from location tracking.

`loc kill {entity}`
Marks an entity as ~~dead~~ without removing them.

`loc res[urrect] {entity}`
Bring a ~~dead~~ entity back to life.

`loc rename {entity} {new name}`
Renames an entity.

`loc create {location}`
Creates a new location without assigning anyone to it yet.

`loc delete {location}`
Deletes a location from tracking.

`loc update {location} {new name}`
Renames a location.

`log [un]tag {entity} {tag}`
Tag or untag an entity with e.g. a status effect.

`loc reset`
Clear out all locations and entities."""

class Commands:
    def __init__(self, channel_id):
        self.channel_id = channel_id

    def help(self):
        return {
            "send": {
                "embed": discord.Embed(
                    type = "Rich",
                    title = "Commands",
                    description = HELP_TEXT
                )
            },
            "update": False
        }

    def show(self):
        """Display the current status."""
        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def move(self, entity_name, location_name):
        """Move an entity to a new location."""
        entity   = Entity.find_or_create(self.channel_id, entity_name)
        location = Location.find_or_create(self.channel_id, location_name)
        entity.location_pk = location.id
        entity.save()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def remove(self, entity_name):
        """Remove an entity from tracking."""
        entity = Entity.find(self.channel_id, entity_name)

        if entity:
            entity.destroy()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def kill(self, entity_name):
        """Mark an entity as killed."""
        entity = Entity.find(self.channel_id, entity_name)

        if entity:
            entity.killed = True
            entity.save()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def resurrect(self, entity_name):
        """Remove the `killed` mark from an entity."""
        entity = Entity.find(self.channel_id, entity_name)

        if entity:
            entity.killed = False
            entity.save()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }


    def rename(self, entity_name, new_name):
        """Rename an entity."""
        entity = Entity.find(self.channel_id, entity_name)
        if entity:
            entity.name = new_name.strip()
            entity.save()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def create(self, location_name):
        """Create a new location."""
        Location.create(self.channel_id, location_name)

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def delete(self, location_name):
        """Deletes a location."""
        location = Location.find(self.channel_id, location_name)
        if location:
            location.destroy()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def update(self, location_name, new_name):
        """Renames a location."""
        location = Location.find(self.channel_id, location_name)
        if location:
            location.name = new_name.strip()
            location.save()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def tag(self, entity_name, tag):
        """Tags an entity."""
        entity = Entity.find(self.channel_id, entity_name)
        if entity:
            entity.add_tag(tag.strip())

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def untag(self, entity_name, tag):
        """Untags an entity."""
        entity = Entity.find(self.channel_id, entity_name)
        if entity:
            entity.remove_tag(tag.strip())

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }


    def reset(self):
        """Clear out all locations and entities."""
        for entity in Entity.all(self.channel_id):
            entity.destroy()
        for location in Location.all(self.channel_id):
            location.destroy()

        return {
            "send": {
                "embed": self.generate_embed()
            },
            "update": True
        }

    def get_sticky_id(self):
        channel = Channel.find_or_create(self.channel_id)
        return channel.sticky_id

    def set_sticky_id(self, sticky_id):
        channel = Channel.find_or_create(self.channel_id)
        channel.sticky_id = sticky_id
        channel.save()

    def generate_embed(self):
        lines = []

        for i, location in enumerate(Location.all(self.channel_id)):
            if i > 0:
                lines.append("")
            lines.append(f'**{location.name} ({location.id})**')

            entities = list(location.get_entities())
            if len(entities) == 0:
                lines.append("*Empty*")

            for entity in location.get_entities():
                entity_name = entity.name
                entity_tags = entity.get_tags()

                if entity.killed:
                    entity_name = f'~~{entity_name}~~'

                if len(entity_tags) > 0:
                    lines.append(f'{entity_name} ({entity.id}) - {", ".join(entity_tags)}')
                else:
                    lines.append(f'{entity_name} ({entity.id})')

        unassigned_entities = list([e for e in Entity.all(self.channel_id) if e.location_pk == None])
        if len(unassigned_entities) > 0:
            if len(lines) > 0:
                lines.append("")
            lines.append("***--Unassigned--***")
            for entity in unassigned_entities:
                lines.append(f'{entity.name} ({entity.id})')

        if len(lines) == 0:
            lines.append("Nothing tracked!")

        return discord.Embed(
            type = "Rich",
            description = "\n".join(lines)
        )