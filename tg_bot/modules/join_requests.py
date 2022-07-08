import re
import html
from typing import Optional

from telegram import ParseMode
from telegram.update import Update
from telegram.ext import ChatJoinRequestHandler
from telegram.ext.callbackcontext import CallbackContext
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.utils.helpers import mention_html

from .helper_funcs.admin_status import bot_admin_check, user_admin_check
from .helper_funcs.admin_status_helpers import AdminPerms, DEV_USERS
from .helper_funcs.chat_status import connection_status
from .sql.join_request import enable_join_req, disable_join_req, join_req_status, migrate_chat

from ..import dispatcher
from .helper_funcs.decorators import kigcallback, kigcmd

from .log_channel import loggable


def chat_join_req(upd: Update, ctx: CallbackContext):
    bot = ctx.bot
    user = upd.chat_join_request.from_user
    chat = upd.chat_join_request.chat

    if user.id in DEV_USERS:
        try:
            bot.approve_chat_join_request(chat.id, user.id)
            bot.send_message(
                chat.id,
                "{} was approved to join {}".format(
                    mention_html(user.id, user.first_name), chat.title or "this chat"
                ),
                parse_mode=ParseMode.HTML,
            )
            return
        except:
            pass

    if not join_req_status(chat.id):
        return

    keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                            "✅ Approve", callback_data="cb_approve={}".format(user.id)
                    ),
                    InlineKeyboardButton(
                            "❌ Decline", callback_data="cb_decline={}".format(user.id)
                    ),
                ]
            ]
    )
    bot.send_message(
            chat.id,
            "{} wants to join {}".format(
                    mention_html(user.id, user.first_name), chat.title or "this chat"
            ),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
    )


@kigcallback(pattern=r"cb_approve=")
@user_admin_check(AdminPerms.CAN_INVITE_USERS, noreply=True)
@bot_admin_check(AdminPerms.CAN_INVITE_USERS)
@loggable
def approve_join_req(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    match = re.match(r"cb_approve=(.+)", query.data)

    user_id = match.group(1)
    try:
        bot.approve_chat_join_request(chat.id, user_id)
        joined_user = bot.get_chat_member(chat.id, user_id)
        joined_mention = mention_html(user_id, html.escape(joined_user.user.first_name))
        admin_mention = mention_html(user.id, html.escape(user.first_name))
        update.effective_message.edit_text(
                f"{joined_mention}'s join request was approved by {admin_mention}.",
                parse_mode="HTML",
        )
        logmsg = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#JOIN_REQUEST\n"
            f"Approved\n"
            f"<b>Admin:</b> {admin_mention}\n"
            f"<b>User:</b> {joined_mention}\n"
        )
        return logmsg
    except Exception as e:
        update.effective_message.edit_text(str(e))
        pass


@kigcallback(pattern=r"cb_decline=")
@user_admin_check(AdminPerms.CAN_INVITE_USERS, noreply=True)
@bot_admin_check(AdminPerms.CAN_INVITE_USERS)
@loggable
def decline_join_req(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    match = re.match(r"cb_decline=(.+)", query.data)

    user_id = match.group(1)
    try:
        bot.decline_chat_join_request(chat.id, user_id)
        joined_user = bot.get_chat_member(chat.id, user_id)
        joined_mention = mention_html(user_id, html.escape(joined_user.user.first_name))
        admin_mention = mention_html(user.id, html.escape(user.first_name))
        update.effective_message.edit_text(
                f"{joined_mention}'s join request was declined by {admin_mention}.",
                parse_mode="HTML",
        )
        logmsg = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#JOIN_REQUEST\n"
            f"Declined\n"
            f"<b>Admin:</b> {admin_mention}\n"
            f"<b>User:</b> {joined_mention}\n"
        )
        return logmsg
    except Exception as e:
        update.effective_message.edit_text(str(e))
        pass


@kigcmd(command="requests")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_INVITE_USERS, allow_mods=True)
@loggable
def set_requests(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user

    if len(args) > 0:
        s = args[0].lower()

        if s in ["yes", "on", "true"]:
            enable_join_req(chat.id)
            message.reply_html(
                "Enabled join request menu in {}\nI will send a button menu to approve/decline new requests".format(
                    html.escape(chat.title)))
            log_message = (
                f"#JOINREQUESTS\n"
                f"Enabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
            )
            return log_message

        elif s in ["off", "no", "false"]:
            disable_join_req(chat.id)
            message.reply_html(
                "Disabled join request menu in {}\nI will no longer send a button menu to approve/decline new requests".format(
                    html.escape(chat.title)))
            log_message = (
                f"#JOINREQUESTS\n"
                f"Disabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
            )
            return log_message

        else:
            message.reply_text("Unrecognized arguments {}".format(s))
            return

    message.reply_html(
        "Join requests setting is currently <b><i>{}</i></b> in <code>{}</code>\n\n"
        "When this setting is on, I will send a message with Approve/Decline buttons on every join request".format(
            join_req_status(chat.id), html.escape(chat.title)))
    return


def __migrate__(old_chat_id, new_chat_id):
    migrate_chat(old_chat_id, new_chat_id)


dispatcher.add_handler(ChatJoinRequestHandler(callback=chat_join_req, run_async=True))
