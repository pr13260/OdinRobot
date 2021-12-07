
from tg_bot.modules.helper_funcs.chat_status import u_can_change_info

from telegram import Update

from telegram.ext import CallbackContext

from tg_bot import spamcheck
from tg_bot.modules.log_channel import loggable

import tg_bot.modules.sql.logger_sql as sql
from tg_bot.modules.helper_funcs.decorators import kigcmd

import html
from telegram.utils.helpers import mention_html

from ..modules.helper_funcs.anonymous import user_admin as u_admin, AdminPerms, resolve_user as res_user, UserClass

@kigcmd(command="announce", pass_args=True)
@spamcheck
@u_admin(UserClass.ADMIN, AdminPerms.CAN_CHANGE_INFO)
@loggable
def announcestat(update: Update, context: CallbackContext) -> str:
    args = context.args
    if len(args) > 0:
        u = update.effective_user
        message = update.effective_message
        chat = update.effective_chat
        user = res_user(u, message.message_id, chat)
        if u_can_change_info(chat, user):
            if args[0].lower() in ["on", "yes", "true"]:
                sql.enable_chat_log(update.effective_chat.id)
                update.effective_message.reply_text(
                    "I've enabled announcemets in this group. Now any admin actions in your group will be announced."
                )
                logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#ANNOUNCE_TOGGLED\n"
                    f"Admin actions announcement has been <b>enabled</b>\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                )
                return logmsg
            elif args[0].lower() in ["off", "no", "false"]:
                sql.disable_chat_log(update.effective_chat.id)
                update.effective_message.reply_text(
                    "I've disabled announcemets in this group. Now admin actions in your group will not be announced."
                )
                logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#ANNOUNCE_TOGGLED\n"
                    f"Admin actions announcement has been <b>disabled</b>\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                )
                return logmsg
        else:
            message.reply_text("You lack the {} right!".format('can_change_info'.upper()))
            return ''
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any admin actions in your group will be announced."
            "When False, admin actions in your group will not be announced.".format(sql.does_chat_log(update.effective_chat.id))
        )
        return ''


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

