import asyncio
import counting_check_bot

counting_check = counting_check_bot.create_counting_check_bot()

bots = [
    counting_check
]

loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(asyncio.gather(*[bot.start(bot.access_token) for bot in bots]))
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

