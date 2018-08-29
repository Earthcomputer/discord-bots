import traceback
import sys

async def on_error(bot, event, *args, **kwargs):
    ex_type, ex_value, ex_traceback = sys.exc_info()
    try:
        channel = bot.get_channel('477258067927629824')
        if channel == None:
            raise Exception
        await bot.send_message(channel, ("<@377517798768902145> blame %s for triggering: Exception occurred while processing " + event )%(args[0].author if hasattr(args[0], "author") else "<@377517798768902145>"))
        whole_msg = ''.join(traceback.format_exception(ex_type, ex_value, ex_traceback))
        msg = ''
        for line in whole_msg.split('\n'):
            if len(msg) + len(line) > 1991:
                await bot.send_message(channel, '```\n' + msg + '\n```')
                msg = ''
            if len(msg) > 0:
                msg += '\n'
            msg += line
        if len(msg) > 0:
            await bot.send_message(channel, '```\n' + msg + '\n```')
    except:
        et, ev, etr = sys.exc_info()
        traceback.print_exception(et, ev, etr)
        print('Exception occurred while processing ' + event)
        traceback.print_exception(ex_type, ex_value, ex_traceback)
