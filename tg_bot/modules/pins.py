import html


from telegram import Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters
from telegram.utils.helpers import mention_html

from tg_bot import SUDO_USERS, spamcheck, dispatcher

from tg_bot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    connection_status,
    user_admin,
    user_mod, is_user_mod,
)
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.language import gs
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg, kigcallback
from tg_bot.modules.helper_funcs.misc import get_message_type,\
    build_keyboard_alternate
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from tg_bot.modules.connection import connected
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.parsemode import ParseMode


@kigcmd(command="pin", can_disable=False)
@spamcheck
@bot_admin
@can_pin
@user_mod
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    message = update.effective_message
    pinner = chat.get_member(user.id)

    if (
        not (pinner.can_pin_messages or pinner.status == "creator")
        and user.id not in SUDO_USERS
    ):
        message.reply_text("You don't have the necessary rights to do that!")
        return


    if prev_message and is_group:
        try:
            pinn = prev_message.message_id
            bot.pinChatMessage(
                chat.id, pinn, disable_notification=is_silent
            )

            if chat.username:
                pinmsg = "https://t.me/{}/{}".format(chat.username, pinn)
            else:
                pinmsg = "https://t.me/c/{}/{}".format(str(chat.id)[4:], pinn)

            dispatcher.bot.sendMessage(chat.id, "I have pinned [this message]({})".format(pinmsg), parse_mode="markdown", disable_web_page_preview=True)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"I couldn't pin the message from some reason.")
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message

@kigcmd(command="unpin", can_disable=False)
@spamcheck
@bot_admin
@can_pin
@user_mod
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    message = update.effective_message
    unpinner = chat.get_member(user.id)

    if (
        not (unpinner.can_pin_messages or unpinner.status == "creator")
        and user.id not in SUDO_USERS
    ):
        message.reply_text("You don't have the necessary rights to do that!")
        return

    reply_msg = message.reply_to_message
    if not reply_msg:
        print("not rp")
        try:
            bot.unpinChatMessage(chat.id)
            dispatcher.bot.sendMessage(chat.id, "Unpinned the last pinned message successfully!", parse_mode="markdown")
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"I couldn't unpin the message from some reason.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNPINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message

    else:
        print("rp")
        unpinthis = reply_msg.message_id
        try:
            bot.unpinChatMessage(chat.id, unpinthis)

            if chat.username:
                pinmsg = "https://t.me/{}/{}".format(chat.username, unpinthis)
            else:
                pinmsg = "https://t.me/c/{}/{}".format(str(chat.id)[4:], unpinthis)

            dispatcher.bot.sendMessage(chat.id, "I have unpinned [this message]({})".format(pinmsg), parse_mode="markdown")
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                dispatcher.bot.sendMessage(chat.id, f"I couldn't unpin the message from some reason.")
                pass
            else:
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNPINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )
        return log_message

@spamcheck
@bot_admin
@kigcmd(command="unpinall", filters=Filters.chat_type.groups)
@spamcheck
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Only the chat owner can unpin all messages at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Unpin all messages", callback_data="pinned_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="pinned_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"Are you sure you would like unpin all pinned messages in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )

@kigcallback(pattern=r"pinned_.*")
@loggable
def unpin_callback(update, context: CallbackContext) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    bot = context.bot
    member = chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "pinned_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:

            try:
                bot.unpinAllChatMessages(chat.id)
            except BadRequest as excp:
                if excp.message == "Chat_not_modified":
                    pass
                else:
                    raise
            msg.edit_text(f"Unpinned all messages in {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNPINNED_ALL\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        if member.status == "administrator":
            query.answer("Only owner of the chat can do this.")
            return ""

        if member.status == "member":
            query.answer("You need to be admin to do this.")
            return ""
    elif query.data == "pinned_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("Unpinning all pinned messages has been cancelled.")
            return
        if member.status == "administrator":
            query.answer("Only owner of the chat can do this.")
            return ""
        if member.status == "member":
            query.answer("You need to be admin to do this.")
            return ""




# cherry-picked from emilia hikari (https://github.com/AyraHikari/EmiliaHikari)
# commits:
# 4ad807aa1d9615993db0e135d910d70bc4cbf767
# 049e735dd51694ae736749b9c9523499aaca8862
# cb9194dffc588c564f3dd6bdf75c1e712dc05e59
# ab26b958adca851eb749398d1683280896cfb633
# 94348c615c5364c13d32393d588838eaf1501f59
# ab26b958adca851eb749398d1683280896cfb633


ENUM_FUNC_MAP = {
	'Types.TEXT': dispatcher.bot.send_message,
	'Types.BUTTON_TEXT': dispatcher.bot.send_message,
	'Types.STICKER': dispatcher.bot.send_sticker,
	'Types.DOCUMENT': dispatcher.bot.send_document,
	'Types.PHOTO': dispatcher.bot.send_photo,
	'Types.AUDIO': dispatcher.bot.send_audio,
	'Types.VOICE': dispatcher.bot.send_voice,
	'Types.VIDEO': dispatcher.bot.send_video
}

import tg_bot.modules.sql.admin_sql as sql




@kigcmd(command="permapin", filters=Filters.chat_type.groups, run_async=True)
@spamcheck
@can_pin
@user_admin
@connection_status
def permapin(update, context):

    message = update.effective_message  # type: Optional[Message]

    chat_id = update.effective_chat.id

    text, data_type, content, buttons = get_message_type(message)
    tombol = build_keyboard_alternate(buttons)
    try:
        message.delete()
    except BadRequest:
        pass
    if str(data_type) in ('Types.BUTTON_TEXT', 'Types.TEXT'):
        try:
            sendingmsg = context.bot.send_message(chat_id, text, parse_mode="markdown",
                                 disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(tombol))
        except BadRequest:
            context.bot.send_message(chat_id, "Incorrect markdown text!\nIf you don't know what markdown is, please send `/markdownhelp` in PM.", parse_mode="markdown")
            return
    else:
        sendingmsg = ENUM_FUNC_MAP[str(data_type)](chat_id, content, caption=text, parse_mode="markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(tombol))
    if sendingmsg is None:
        context.bot.send_message(chat_id, "Specify what to pin!")
        
    try:
        context.bot.pinChatMessage(chat_id, sendingmsg.message_id)
    except BadRequest:
        context.bot.send_message(chat_id, "I don't have access to message pins!")



@kigcmd(command="cleanlinked", pass_args=True, filters=Filters.chat_type.groups, run_async=True)
@spamcheck
@can_pin
@user_admin
@loggable
def permanent_pin_set(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        if not args:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = "Cleanlinked is currently set to: `{}`".format(bool(int(get_permapin)))
            if get_permapin:
                if chat.username:
                    old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
                else:
                    old_pin = "https://t.me/c/{}/{}".format(str(chat.id)[4:], get_permapin)
                text_maker += "\nTo disable cleanlinked send: `/cleanlinked off`"
                text_maker += "\n\n[The permanent pinned message is here]({})".format(old_pin)
            dispatcher.bot.send_message(chat_id, text_maker, parse_mode="markdown")
            return ""
        prev_message = args[0]
        if prev_message == "off":
            sql.set_permapin(chat_id, 0)
            dispatcher.bot.send_message(chat_id, "Cleanlinked has been disabled!")
            return
        if "/" in prev_message:
            prev_message = prev_message.split("/")[-1]
    else:
        if update.effective_message.chat.type == "private":
            dispatcher.bot.send_message(chat_id, "This command is meant to use in group not in PM")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title
        if update.effective_message.reply_to_message:
            prev_message = update.effective_message.reply_to_message.message_id
        elif len(args) >= 1 and args[0] in ["off", "false"]:
            sql.set_permapin(chat.id, 0)
            dispatcher.bot.send_message(chat_id, "Cleanlinked has been disabled!")
            return
        elif len(args) >= 1 and args[0] in ["on", "true"]:
            sql.set_permapin(chat.id, 1)
            dispatcher.bot.send_message(chat_id, "Cleanlinked has been enabled!")
            return
        else:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = "Cleanlinked is currently set to: `{}`".format(bool(int(get_permapin)))
            if get_permapin:
                if chat.username:
                    old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
                else:
                    old_pin = "https://t.me/c/{}/{}".format(str(chat.id)[4:], get_permapin)
                text_maker += "\nTo disable cleanlinked send: `/cleanlinked off`"
                text_maker += "\n\n[The permanent pinned message is here]({})".format(old_pin)
            dispatcher.bot.send_message(chat_id, text_maker, parse_mode="markdown")
            return ""

    is_group = chat.type != "private" and chat.type != "channel"

    if prev_message and is_group:
        sql.set_permapin(chat.id, prev_message)
        dispatcher.bot.send_message(chat_id, "Cleanlinked successfully set!")
        return "<b>{}:</b>" \
               "\n#PERMANENT_PIN" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""



@kigmsg(Filters.status_update.pinned_message | Filters.user(777000), run_async=True)
def permanent_pin(update, context):
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message
    args = context.args

    get_permapin = sql.get_permapin(chat.id)
    if get_permapin and user.id != context.bot.id:
        try:
            to_del = context.bot.pinChatMessage(chat.id, get_permapin, disable_notification=True)
        except BadRequest:
            sql.set_permapin(chat.id, 0)
            if chat.username:
                old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
            else:
                old_pin = "https://t.me/c/{}/{}".format(str(chat.id)[4:], get_permapin)
                print(old_pin)
            dispatcher.bot.send_message(chat.id, "*Cleanlinked error:*\nI can't pin messages here!\nMake sure I'm an admin and can pin messages.\n\nClean linked has been disabled, [The old permanent pinned message is here]({})".format(old_pin), parse_mode="markdown")
            return

        if to_del:
            try:
                print(message.message_id)
                context.bot.deleteMessage(chat.id, message.message_id)
            except BadRequest:
                dispatcher.bot.send_message(chat.id, "Cleanlinked error: cannot delete pinned msg")
                print("Cleanlinked error: cannot delete pin msg")
    




def get_help(chat):
    return gs(chat, "pins_help")

__mod_name__ = "Pins"
