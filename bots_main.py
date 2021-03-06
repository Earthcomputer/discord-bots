#!/usr/bin/env python3

import asyncio
import logging
import time

import counting_check_bot
import Yunbot

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

counting_check = counting_check_bot.create_counting_check_bot()
yunbot = Yunbot.create_yunbot()

bots = [
    counting_check,
    yunbot
]

loop = asyncio.get_event_loop()

try:
    while True:
        try:
            loop.run_until_complete(asyncio.gather(*[bot.start(bot.access_token) for bot in bots]))
        except KeyboardInterrupt:
            raise
        except:
            logger.info("Exception occurred, assuming disconnect, waiting 1 minute...")
            time.sleep(60)
except KeyboardInterrupt:
    loop.run_until_complete(asyncio.gather(*[bot.logout() for bot in bots]))
    pending = asyncio.Task.all_tasks()
    gathered = asyncio.gather(*pending)
    try:
        gathered.cancel()
        loop.run_until_complete(gathered)
        gathered.exception()
    except:
        pass
finally:
    loop.close()

