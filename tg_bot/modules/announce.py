from tg_bot.modules.helper_funcs.chat_status import user_admin

from telegram import Update

from telegram.ext import CallbackContext

from tg_bot import spamcheck

import tg_bot.modules.sql.logger_sql as sql
from tg_bot.modules.helper_funcs.decorators import kigcmd

@kigcmd(command="announce", pass_args=True)
@spamcheck
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes", "true"]:
            sql.enable_chat_log(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled announcemets in this group. Now any admin actions in your group will be announced."
            )
        elif args[0].lower() in ["off", "no", "false"]:
            sql.disable_chat_log(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled announcemets in this group. Now admin actions in your group will not be announced."
            )
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any admin actions in your group will be announced."
            "When False, admin actions in your group will not be announced.".format(sql.does_chat_log(update.effective_chat.id))
        )

