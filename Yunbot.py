import discord
import bot_utils

import asyncio
import re
import time

def create_yunbot():
    client = discord.Client()

    message_timestamps = {}

    with open("access_tokens/yunbot.txt") as f:
        client.access_token = f.read()

    @client.async_event
    async def on_error(event, *args, **kwargs):
        await bot_utils.on_error(client, event, *args, **kwargs)
    
    @client.async_event
    async def on_ready():
        print("YUNBOT")
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')

    @client.async_event
    async def on_message(message):
        if not message.author.bot:

            if isinstance(message.channel, discord.PrivateChannel):
                read_messages_perm = True
            else:
                read_messages_perm = message.channel.overwrites_for(message.server.default_role).read_messages
            if not (read_messages_perm == None or read_messages_perm == True):
                return
            
            if message.author.id == '310231043762290700': # Acheron
                if '\u2764' in message.content:
                    for emoji in ['\U0001F494', '\U0001F498', '\U0001F499', '\U0001F49A', '\U0001F49C', '\U0001F49D', '\U0001F49B', '\U0001F5A4', '\U0001F60D', '\U0001F618']:
                        await client.add_reaction(message, emoji)

            
            person = None
            sentences = re.split(r'[\.,!\?:;]', message.content)

            for sentence in sentences:
                sentence.strip()
                words = sentence.split(" ")
                imIdx = -1
                for i, word in enumerate(words):
                    word = word.lower()
                    if (word in ['im', 'i\'m', 'i’m', 'i‘m', 'i`m'] or (i != 0 and word == 'am' and words[i - 1].lower() == 'i')):
                        if i != len(words) - 1:
                            imIdx = i

                if imIdx != -1:
                    person = " ".join(words[(imIdx+1):])

            if person != None:
                if person.lower() == 'yun':
                    yun = 'No, im yun, you\'re ' + message.author.name + '!'
                else:
                    yun = 'Hi ' + person + ', im yun!'

                if hasattr(message.author, "server_permissions") and not message.author.server_permissions.mention_everyone:
                    if "@everyone" in yun:
                        return
                    elif "@here" in yun:
                        return

                if message.channel.id not in message_timestamps:
                    message_timestamps[message.channel.id] = []
                while len(message_timestamps[message.channel.id]) >= 5:
                    now = time.process_time()
                    if now - message_timestamps[message.channel.id][0] > 300:
                        del message_timestamps[message.channel.id][0]
                if len(message_timestamps[message.channel.id]) >= 5:
                    return
                message_timestamps[message.channel.id].append(time.process_time())
                
                await client.send_message(message.channel, yun)

    return client
