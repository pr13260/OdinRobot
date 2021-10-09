import html


from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from telegram.utils.helpers import escape_markdown, mention_html

from tg_bot import SUDO_USERS, spamcheck
from tg_bot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_promote,
    connection_status,
    user_admin,
    ADMIN_CACHE,
    user_mod,
)

from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.language import gs
from tg_bot.modules.helper_funcs.decorators import kigcmd

@kigcmd(command="promote", can_disable=False)
@spamcheck
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and not user.id in SUDO_USERS
    ):
        message.reply_text("You lack the CAN_ADD_ADMINS right!")
        return

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status in ("administrator", "creator"):
        message.reply_text("This user is already an admin!")
        return

    if user_id == bot.id:
        message.reply_text("Yeah I wish I could promote myself...")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_voice_chats=bot_member.can_manage_voice_chats,
        )
        if title:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        try:
            ADMIN_CACHE.pop(update.effective_chat.id)
        except KeyError:
            pass
        bot.sendMessage(
            chat.id,
            f"<b>{user_member.user.first_name or user_id}</b> was promoted by <b>{message.from_user.first_name}</b>.",
            parse_mode=ParseMode.HTML,
        ) 
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("How am I mean to promote someone who isn't in the group?")
        else:
            message.reply_text("An error occured while promoting.")
        return



    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message

@kigcmd(command="demote", can_disable=False)
@spamcheck
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        message.reply_text("This user isn't an admin!")
        return

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_voice_chats=False,
        )

        try:
            ADMIN_CACHE.pop(update.effective_chat.id)          
        except KeyError:
            pass
        bot.sendMessage(
            chat.id,
            f"<b>{user_member.user.first_name or user_id or None}</b> was demoted by <b>{message.from_user.first_name or None}</b>.",
            parse_mode=ParseMode.HTML,
        )  

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        message.reply_text(
            f"Could not demote!\n{str(e)}"
        )
        return
 
@kigcmd(command="admincache", can_disable=False)
@user_mod
def refresh_admin(update, context):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass
    update.effective_message.reply_text("Admins cache is up to date!")

@kigcmd(command="title", can_disable=False)
@spamcheck
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "This person is the chat CREATOR, only they can set their title."
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "Titles can only be set to admins."
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "I can't set my own title myself! Get the one who made me admin to do it for me."
        )
        return

    if not title:
        message.reply_text("You can't set an empty title!")
        return

    if len(title) > 16:
        message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("I can only set titles for the admins I promote!")
        return


@kigcmd(command=["invitelink", "link"], can_disable=False)
@spamcheck
@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "I don't have access to the invite link, try changing my permissions!"
            )
    else:
        update.effective_message.reply_text(
            "I can only give you invite links for supergroups and channels, sorry!"
        )



@kigcmd(command=["admin", "admins", "staff", "adminlist"])
@spamcheck
def adminlist(update, context):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user


        if user.first_name == "":
            name = "☠ Zombie"

        if admin.status == "creator":
            name = "[{}](tg://user?id={})".format(user.first_name, user.id)
            text += "\n*Creator:*"
            text += "\nㅤ👑 {}".format(name)
        else:
            name = "[{}](tg://user?id={})".format(user.first_name, user.id)
            text += "\nㅤ{}".format(name)

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)




def get_help(chat):
    return gs(chat, "admin_help")

__mod_name__ = "Admin"
