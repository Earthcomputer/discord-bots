import sys
import re
import codecs
import discord
import threading
import json
import datetime
import os

import bot_utils

THINKING_EMOJI = "\U0001F914"
NUMBER_REGEX = r'-?\d+(?![>\d])'
DELETE_MESSAGE = "\n(`count/deletelast` will delete this message)"

def create_counting_check_bot():

    try:
        with open("config/counting_check_bot.json") as f:
            config = json.loads(f.read())
    except:
        config = {}

    def get_guild_config(guild):
        if guild not in config:
            config[guild] = {}
        return config[guild]
    def get_config(guild, key, default):
        if key not in get_guild_config(guild):
            get_guild_config(guild)[key] = default
        return get_guild_config(guild)[key]

    def save_config():
        string = json.dumps(config, indent=2)
        if not os.path.exists("config"):
            os.makedirs("config")
        with open("config/counting_check_bot.json", "w") as f:
            f.write(string)

    client = discord.Client()
    with open("access_tokens/counting_check_bot.txt") as f:
        client.access_token = f.read()

    def check_permission(user):
        if isinstance(user, discord.Member):
            return user.server_permissions.manage_server
        else:
            return True

    @client.event
    async def on_error(event, *args, **kwargs):
        await bot_utils.on_error(client, event, args, kwargs)

    @client.event
    async def on_ready():
        print("COUNTING CHECK BOT")
        await client.change_presence(game=discord.Game(name="count/help",type=2),status=discord.Status.dnd,afk=False)
        for guild in config:
            for channel_id in config[guild]["channels"]:
                channel = client.get_channel(channel_id)
                if channel == None:
                    continue
                incorrect_message_start = None
                incorrect_message_users = set()
                print("=====")
                print("Channel: " + channel.name)
                print("Loading from " + str(datetime.datetime.utcfromtimestamp(config[guild]["channels"][channel_id]["lastmsg"])))
                async for msg in client.logs_from(channel, after = datetime.datetime.utcfromtimestamp(config[guild]["channels"][channel_id]["lastmsg"]), limit = 2147483647, reverse = True):
                    if msg.author.bot:
                        continue
                    anynum = False
                    found = False
                    for match in re.finditer(NUMBER_REGEX, msg.content):
                        anynum = True
                        if config[guild]["channels"][channel_id]["lastnum"] + 1 == int(match.group(0)):
                            found = True
                            break
                    if anynum:
                        config[guild]["channels"][channel_id]["lastnum"] = config[guild]["channels"][channel_id]["lastnum"] + 1
                        config[guild]["channels"][channel_id]["lastmsg"] = msg.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
                        save_config()
                        if not found:
                            if incorrect_message_start == None:
                                incorrect_message_start = msg.timestamp
                            incorrect_message_users.add(msg.author.id)
                if incorrect_message_start != None:
                    warn_msg = "Incorrect message at " + str(incorrect_message_start) + ". " + ", ".join(map(lambda i: "<@" + i + ">", sorted(incorrect_message_users))) + " you may have some messages to fix."
                    await client.send_message(channel, warn_msg + DELETE_MESSAGE)
        print("Client ready")

    @client.event
    async def on_message_delete(message):
        if message.author.bot:
            return

        conf = get_config(message.server.id, "channels", {})
        if message.channel.id not in conf:
            return
        conf = conf[message.channel.id]

        if message.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp() == conf["lastmsg"]:
            del conf["lastauthor"]

        if "listened_messages" in conf and message.id in conf["listened_messages"]:
            users_to_warn = set()
            async for msg in client.logs_from(message.channel, after = message, limit = 10000):
                if not msg.author.bot:
                    if re.search(NUMBER_REGEX, msg.content) != None:
                        users_to_warn.add(msg.author.id)
            if len(users_to_warn) != 0:
                warn_msg = "<@" + message.author.id + "> deleted their message. " + ", ".join(map(lambda i: "<@" + i + ">", sorted(users_to_warn))) + " you may have to edit your messages accordingly."
                await client.send_message(message.channel, warn_msg + DELETE_MESSAGE)
            conf["lastnum"] = conf["lastnum"] - 1
            save_config()
            msg_to_delete = await client.get_message(message.channel, conf["listened_messages"][message.id]["response"])
            if msg_to_delete != None:
                await client.delete_message(msg_to_delete)
        else:
            if re.search(NUMBER_REGEX, message.content) != None:
                conf["lastnum"] = conf["lastnum"] - 1
                save_config()
                await client.send_message(message.channel, "<@" + message.author.id + "> deleted a correct message, others may have to edit!" + DELETE_MESSAGE)

    @client.event
    async def on_message_edit(msg_before, msg_after):
        if msg_after.author.bot:
            return

        conf = get_config(msg_after.server.id, "channels", {})
        if msg_after.channel.id not in conf:
            return
        conf = conf[msg_after.channel.id]
        
        if "listened_messages" in conf and msg_before.id in conf["listened_messages"]:
            found = False
            for match in re.finditer(NUMBER_REGEX, msg_after.content):
                if conf["listened_messages"][msg_before.id]["expected"] == int(match.group(0)):
                    found = True
                    break
            if found:
                to_delete = conf["listened_messages"][msg_before.id]["response"]
                await client.wait_until_ready()
                to_delete = await client.get_message(msg_before.channel, to_delete)
                await client.delete_message(to_delete)
                await client.remove_reaction(msg_after, THINKING_EMOJI, client.user)
                del conf["listened_messages"][msg_before.id]
                save_config()
        else:
            before_on_topic = re.search(NUMBER_REGEX, msg_before.content) != None
            after_on_topic = re.search(NUMBER_REGEX, msg_after.content) != None
            if before_on_topic != after_on_topic:
                if before_on_topic:
                    conf["lastnum"] = conf["lastnum"] - 1
                else:
                    conf["lastnum"] = conf["lastnum"] + 1
                await client.send_message(msg_after.channel, "<@" + msg_after.author.id + "> edited their message so that subsequent numbers may be shifted." + DELETE_MESSAGE)
                save_config()


    @client.event
    async def on_message(message):
        if message.author.bot:
            return

        content = message.content
        if content.startswith("count/help"):
            print("Printing help")
            h = "```\ncount/addchannel #counting_channel\ncount/removechannel #counting_channel\ncount/whereami\ncount/deletelast\n```"
            await client.send_message(message.channel, h + DELETE_MESSAGE)
        elif content.startswith("count/addchannel "):
            if not check_permission(message.author):
                await client.send_message(message.channel, "No permission" + DELETE_MESSAGE)
                return
            content = content[len("count/addchannel "):]
            regex = r'<#(\d+)>'
            match = re.match(regex, content)
            if match != None:
                channel = message.server.get_channel(match.group(1))
                if channel == None:
                    await client.send_message(message.channel, "Channel not found" + DELETE_MESSAGE)
                else:
                    conf = {}
                    conf["lastnum"] = 0
                    conf["lastmsg"] = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc).timestamp()
                    async for msg in client.logs_from(channel, limit=1):
                        content = msg.content
                        match = re.search(NUMBER_REGEX, content)
                        if match == None:
                            await client.send_message(message.channel, "Latest message in that channel does not contain a number" + DELETE_MESSAGE)
                            return
                        else:
                            conf["lastnum"] = int(match.group(0))
                            conf["lastmsg"] = msg.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
                    get_config(message.server.id, "channels", {})[channel.id] = conf
                    save_config()
                    await client.send_message(message.channel, "Channel added" + DELETE_MESSAGE)
            else:
                await client.send_message(message.channel, "Invalid channel" + DELETE_MESSAGE)
        elif content.startswith("count/removechannel "):
            if not check_permission(message.author):
                await client.send_message(message.channel, "No permission" + DELETE_MESSAGE)
                return
            content = content[len("count/removechannel "):]
            regex = r'<#(\d+)>'
            match = re.match(regex, content)
            if match != None:
                if match.group(1) in get_config(message.server.id, "channels", {}):
                    del get_config(message.server.id, "channels", {})[match.group(1)]
                    save_config()
                    await client.send_message(message.channel, "Channel removed" + DELETE_MESSAGE)
                else:
                    await client.send_message(message.channel, "That is not a counting channel" + DELETE_MESSAGE)
            else:
                await client.send_message(message.channel, "Invalid channel" + DELETE_MESSAGE)
        elif content.startswith("count/whereami"):
            conf = get_config(message.server.id, "channels", {})
            if message.channel.id not in conf:
                await client.send_message(message.channel, "Not a counting channel" + DELETE_MESSAGE)
            else:
                await client.send_message(message.channel, str(conf[message.channel.id]["lastnum"] + 1) + DELETE_MESSAGE)
        elif content.startswith("count/deletelast"):
            try:
                await client.delete_message(message)
            except discord.errors.Forbidden:
                pass
            async for msg in client.logs_from(message.channel):
                if msg.author == client.user:
                    await client.delete_message(msg)
                    break
        else:
            if message.channel.id not in get_config(message.server.id, "channels", {}):
                return
            conf = get_config(message.server.id, "channels", {})[message.channel.id]
            found = False
            found_num = False
            for match in re.finditer(NUMBER_REGEX, content):
                found_num = True
                if conf["lastnum"] + 1 == int(match.group(0)):
                    found = True
                    break
            if found_num:
                if "lastauthor" in conf and message.author.id == conf["lastauthor"]:
                    await client.send_message(message.channel, "<@" + message.author.id + "> no self-counting" + DELETE_MESSAGE)
                
                conf["lastmsg"] = message.timestamp.replace(tzinfo=datetime.timezone.utc).timestamp()
                conf["lastnum"] = conf["lastnum"] + 1
                conf["lastauthor"] = message.author.id
                if not found:
                    if "listened_messages" not in conf:
                        conf["listened_messages"] = {}
                    conf["listened_messages"][message.id] = {"expected": conf["lastnum"]}
                    msg = await client.send_message(message.channel, "<@" + message.author.id + "> fix ^" + DELETE_MESSAGE)
                    await client.add_reaction(message, THINKING_EMOJI)
                    conf["listened_messages"][message.id]["response"] = msg.id
                save_config()

    return client
    client.run(access_token)

    print("Logging out...")
    client.close()

