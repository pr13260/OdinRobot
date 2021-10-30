import datetime
import os
from telethon import events
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

from tg_bot import GLOBALANNOUNCE, IS_DEBUG, telethn, dispatcher, ANTISPAM_TOGGLE
from tg_bot.modules.helper_funcs.chat_status import dev_plus
from tg_bot.modules.helper_funcs.decorators import kigcmd

DEBUG_MODE = False

@kigcmd(command='debug')
@dev_plus
def debug(update: Update, context: CallbackContext):
    global DEBUG_MODE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(DEBUG_MODE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            DEBUG_MODE = True
            message.reply_text("Debug mode is now on.")
        elif args[1] in ("no", "off"):
            DEBUG_MODE = False
            message.reply_text("Debug mode is now off.")
    elif DEBUG_MODE:
        message.reply_text("Debug mode is currently on.")
    else:
        message.reply_text("Debug mode is currently off.")

@kigcmd(command='spamdebug')
@dev_plus
def asdebug(update: Update, context: CallbackContext):
    global IS_DEBUG
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(IS_DEBUG)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            IS_DEBUG = True
            message.reply_text("Antispam Debug mode is now on.")
        elif args[1] in ("no", "off"):
            IS_DEBUG = False
            message.reply_text("Antispam Debug mode is now off.")
    elif IS_DEBUG:
        message.reply_text("Antispam Debug mode is currently on.")
    else:
        message.reply_text("Antispam Debug mode is currently off.")

@kigcmd(command='gannounce')
@dev_plus
def asdebug(update: Update, context: CallbackContext):
    global GLOBALANNOUNCE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(GLOBALANNOUNCE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            GLOBALANNOUNCE = True
            message.reply_text("Global announcemet is now on.")
        elif args[1] in ("no", "off"):
            GLOBALANNOUNCE = False
            message.reply_text("Global announcemet is now off.")
    elif GLOBALANNOUNCE:
        message.reply_text("Global announcemet is currently on.")
    else:
        message.reply_text("Global announcemet is currently off.")

@kigcmd(command='spamcheck')
@dev_plus
def astoggle(update: Update, context: CallbackContext):
    global ANTISPAM_TOGGLE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(ANTISPAM_TOGGLE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            ANTISPAM_TOGGLE = True
            message.reply_text("Antispam module is now on.")
        elif args[1] in ("no", "off"):
            ANTISPAM_TOGGLE = False
            message.reply_text("Antispam module is now off.")
    elif ANTISPAM_TOGGLE:
        message.reply_text("Antispam module is currently on.")
    else:
        message.reply_text("Antispam module is currently off.")


@telethn.on(events.NewMessage(pattern="[/!>].*"))
async def i_do_nothing_yes(event):
    global DEBUG_MODE
    if DEBUG_MODE:
        print(f"-{event.from_id} ({event.chat_id}) : {event.text}")
        if os.path.exists("updates.txt"):
            with open("updates.txt", "r") as f:
                text = f.read()
            with open("updates.txt", "w+") as f:
                f.write(text + f"\n-{event.from_id} ({event.chat_id}) : {event.text}")
        else:
            with open("updates.txt", "w+") as f:
                f.write(
                    f"- {event.from_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}"
                )


@kigcmd(command='logs')
@dev_plus
def logs(update: Update, context: CallbackContext):
    user = update.effective_user
    with open("logs.txt", "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)

@kigcmd(command='updates')
@dev_plus
def logs(update: Update, context: CallbackContext):
    user = update.effective_user
    with open("updates.txt", "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


'''DEBUG_HANDLER = CommandHandler("debug", debug)
dispatcher.add_handler(DEBUG_HANDLER)'''

__mod_name__ = "Debug"
'''__command_list__ = ["debug"]
__handlers__ = [DEBUG_HANDLER]'''
