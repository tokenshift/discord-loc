from commands import Commands
import db
import discord
from dotenv import load_dotenv
import json_log_formatter
import logging
import os
from pampy import match, _, TAIL
import re
import shlex

logging.basicConfig(level=logging.INFO)
logging.getLogger().handlers[0].setFormatter(json_log_formatter.JSONFormatter())

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

client = discord.Client()

@client.event
async def on_ready():
    logging.info(f'{client.user} has connected to Discord', extra ={
        "user": f'{client.user.name}#{client.user.discriminator}'
    })

    await client.change_presence(activity = discord.Activity(
        name = "loc help",
        type = discord.ActivityType.watching))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if re.match(r"^\s*loc\s+", msg.content):
        channel_id = msg.channel.id
        commands = Commands(channel_id)

        args = shlex.split(msg.content)[1:]

        logging.info("Received loc command", extra = {
            "author": f'{msg.author.name}#{msg.author.discriminator}',
            "content": msg.content,
            "command": args
        })

        action = match(args,
            ["help", TAIL],   lambda *args: commands.help(),
            ["show", TAIL],   lambda *args: commands.show(),
            ["move", _, _],   commands.move,
            ["mv", _, _],     commands.move,
            ["remove", _],    commands.remove,
            ["rm", _],        commands.remove,
            ["kill", _],      commands.kill,
            ["res", _],       commands.resurrect,
            ["resurrect", _], commands.resurrect,
            ["rename", _, _], commands.rename,
            ["create", _],    commands.create,
            ["delete", _],    commands.delete,
            ["update", _, _], commands.update,
            ["tag", _, _],    commands.tag,
            ["untag", _, _],  commands.untag,
            ["reset", TAIL],  lambda *args: commands.reset(),
            _,                lambda *args: None)

        if action == None:
            return

        send = action.get("send")
        update = action.get("update")

        if send:
            if update:
                # Delete the old message, if there is one.
                sticky_id = commands.get_sticky_id()
                if sticky_id:
                    try:
                        old_message = await msg.channel.fetch_message(sticky_id)
                        await old_message.delete()
                    except:
                        pass

            sent = await msg.channel.send(**send)

            if update:
                # Record the new message ID.
                commands.set_sticky_id(sent.id)


def move_command(entity_name, location_name):
    entity = db.find_or_create_entity

client.run(TOKEN)