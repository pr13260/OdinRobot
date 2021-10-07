import html
from tg_bot.antispam import GLOBAL_USER_DATA, Owner
import time
import git
import requests
from io import BytesIO
from telegram import Update, MessageEntity, ParseMode
from telegram.error import BadRequest
from telegram.ext import Filters, CallbackContext
from telegram.utils.helpers import mention_html, escape_markdown
from subprocess import Popen, PIPE

from tg_bot.modules.debug import ANTISPAM_TOGGLE
from tg_bot import (
    MESSAGE_DUMP,
    MOD_USERS,
    dispatcher,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    DEV_USERS,
    WHITELIST_USERS,
    INFOPIC,
    spamcheck,
    sw,
    StartTime,
    SYS_ADMIN
)
from tg_bot.__main__ import STATS, USER_INFO, TOKEN
from tg_bot.modules.sql import SESSION
from tg_bot.modules.helper_funcs.chat_status import user_admin, sudo_plus
from tg_bot.modules.helper_funcs.extraction import extract_user
import tg_bot.modules.sql.users_sql as sql
from tg_bot.modules.language import gs
from telegram import __version__ as ptbver, InlineKeyboardMarkup, InlineKeyboardButton
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time
import datetime
import platform
from platform import python_version
from tg_bot.modules.helper_funcs.decorators import kigcmd, kigcallback

MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {dispatcher.bot.first_name} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with '*' will produce bold text
- <code>`code`</code>: wrapping text with '`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
EG: <code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
EG: <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""
@kigcmd(command='id', pass_args=True)
@spamcheck
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"ㅤ<b>Telegram ID:</b>,"
                f"• {html.escape(user2.first_name)} - <code>{user2.id}</code>.\n"
                f"• {html.escape(user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

    else:

        if chat.type == "private":
            msg.reply_text(
                f"Your id is <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )

        else:
            msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.", parse_mode=ParseMode.HTML
            )
@kigcmd(command='gifid')
@spamcheck
def gifid(update: Update, _):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        update.effective_message.reply_text("Please reply to a gif to get its ID.")



# todo: add whois correctly and add warns flood approval perms mute? admeme perms also

@kigcmd(command=['infoo', 'u'], pass_args=True, filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def fullinfo(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)
    if user_id:
        user = bot.get_chat(user_id)
    elif not message.reply_to_message and not args:
        user = message.from_user
    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("I can't extract a user from this.")
        return
    else:
        return

    temp = message.reply_text("<code>Scraping Info...</code>", parse_mode=ParseMode.HTML)

    text = (
        f"<b>User Info:</b>\n"
        f"ㅤ<b>First Name:</b> {mention_html(user.id, user.first_name)}"
    )
    if user.last_name:
        text += f"\nㅤ<b>Last Name:</b> {html.escape(user.last_name)}"
    if user.username:
        text += f"\nㅤ<b>Username:</b> @{html.escape(user.username)}"
    text += f"\nㅤ<b>User ID:</b> <code>{user.id}</code>"
    if not user.id == OWNER_ID:
        if ANTISPAM_TOGGLE is False:
            text += "\nAntispam module is currently turned off."
        else:
            try:
                detecting = GLOBAL_USER_DATA["AntiSpam"][user.id]['status']
                if detecting:
                    status = "\nㅤ<b>Flood Status:</b>"
                    status += "\nㅤ❗ <b>Flood Enforced:</b> "
                    status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['status'])
                    status += "\nㅤ❗ <b>Value:</b> "
                    status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['value'])
                    if GLOBAL_USER_DATA["AntiSpamHard"][user.id]['restrict'] == None:
                        status += "\nㅤ❗ <b>Time:</b> N/A"
                    else:
                        status += "\nㅤ❗ <b>Time:</b> "
                        status += get_readable_time(time.time() - float(GLOBAL_USER_DATA["AntiSpamHard"][user.id]['restrict']))
                    status += "\nㅤ❗ <b>Level:</b> "
                    status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['level'])
                    text += status
                else:
                    status = "\nㅤ<b>Flood Status:</b>"
                    status += "\nㅤ<b>Flood Enforced:</b> "
                    status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['status'])
                    status += "\nㅤ<b>Value:</b> "
                    status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['value'])
                    status += "\nㅤ<b>Level:</b> "
                    status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['level'])
                    text += status
            except Exception:
                text += "\nㅤ<b>Flood Status:</b>"
                text += "\nㅤ<b>Flood Enforced:</b> False"

    if chat.type != "private":
        try:   #? warns
            from tg_bot.modules.sql import warns_sql as wsql
            result = wsql.get_warns(user_id, chat.id)
            if result and result[0] != 0:
                num_warns, reasons = result
                limit, soft_warn = wsql.get_warn_setting(chat.id)
                text += f"\nㅤ<b>Warns:</b> {num_warns}/{limit}"
        except:
            pass
        try:   #? approval
            from tg_bot.modules.sql import approve_sql as asql
            if asql.is_approved(chat.id, user.id):
                text += "\nㅤ<b>Approved:</b> True"
            else:
                text += "\nㅤ<b>Approved:</b> False"
        except:
            pass

    if user.id == OWNER_ID:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Owner</a>"
    elif user.id in DEV_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Developer</a>"
    elif user.id in SUDO_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Sudo</a>"
    elif user.id in SUPPORT_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Support</a>"
    elif user.id in MOD_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Moderator</a>"
    elif user.id in WHITELIST_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Whitelist</a>"
        

    if user.id in [777000, 1087968824]:
        text += ""
    else:
        num_chats = sql.get_user_num_chats(user.id)
        text += f"\nㅤ<b>Chats:</b> <code>{num_chats}</code>"
    try:
        user_member = chat.get_member(user.id)
        if user_member.status == "left":
                text += f"\nㅤ<b>Presence:</b> Not here"
        if user_member.status == "kicked":
                text += f"\nㅤ<b>Presence:</b> Banned"
        elif user_member.status == "member":
                text += f"\nㅤ<b>Presence:</b> Detected"
        elif user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\nㅤ<b>Title:</b> '<code>{custom_title}</code>'"
            else:
                text += f"\nㅤ<b>Presence:</b> Admin"
    except BadRequest:
        pass


    text += "\n"
    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue
        try:
            mod_info = mod.__user_info__(user.id)
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id)
        if mod_info:
            text += mod_info
    if (
        user.id
        in [777000, 1087968824, dispatcher.bot.id, OWNER_ID]
        + DEV_USERS
        + SUDO_USERS
        + WHITELIST_USERS
        + SUPPORT_USERS
        + MOD_USERS
        ):
            pass #text += ""
    else:
        try:
            spamwtc = sw.get_ban(int(user.id))
            if sw.get_ban(int(user.id)):
                text += "<b>\nSpamWatch:\n</b>"
                text += "ㅤ<b>This person is banned in Spamwatch!</b>"
                text += f"\nㅤ<b>Reason:</b> <pre>{spamwtc.reason}</pre>"
                text += "\nㅤ<b>Appeal:</b>  @SpamWatchSupport"
        except:
            pass # don't crash if api is down somehow...
        else:
            text += ""
    temp.edit_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )



@kigcmd(command="resetantispam", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def resetglobaldata(update: Update, context: CallbackContext):
    bot = context.bot
    from tg_bot.modules.eval import log_input, send
    log_input(update)
    gd = str(GLOBAL_USER_DATA)
    dispatcher.bot.sendMessage(Owner, "`{}`".format(gd), parse_mode="markdown")
    try:
        GLOBAL_USER_DATA = {}
    except Exception as e:
        dispatcher.bot.sendMessage(Owner, "global error\n`{}`".format(str(e)), parse_mode="markdown")
    send("done", bot, update)

@kigcmd(command='whois', pass_args=True, filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
@spamcheck
def whois(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot = context.bot
    args = context.args
    message = update.effective_message
    user_id = extract_user(update.effective_message, args)
    if message.from_user == (OWNER_ID|SYS_ADMIN):
        pass
    else:
        if user_id:
            user = bot.get_chat(user_id)
        elif not message.reply_to_message and not args:
            user = message.from_user
        elif not message.reply_to_message and (
            not args
            or (
                len(args) >= 1
                and not args[0].startswith("@")
                and not args[0].isdigit()
                and not message.parse_entities([MessageEntity.TEXT_MENTION])
            )
        ):
            message.reply_text("I can't extract a user from this.")
            return
        else:
            return
        temp = message.reply_text("<code>Checking Info...</code>", parse_mode=ParseMode.HTML)

        text = (
            f"<b>User Info:</b>\n"
            f"First Name: {mention_html(user.id, user.first_name)}"
        )

        if user.last_name:
            text += f"\nLast Name: {html.escape(user.last_name)}"

        if user.username:
            text += f"\nUsername: @{html.escape(user.username)}"

        text += f"\nID: <code>{user.id}</code>\n"
        temp.edit_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

@kigcmd(command='info', pass_args=True)
@spamcheck
def info(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)
    if user_id:
        user = bot.get_chat(user_id)
    elif not message.reply_to_message and not args:
        user = message.from_user
    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("I can't extract a user from this.")
        return
    else:
        return

    temp = message.reply_text("<code>Checking Info...</code>", parse_mode=ParseMode.HTML)

    text = (
        f"<b>User Info:</b>\n"
        f"ㅤ<b>First Name:</b> {mention_html(user.id, user.first_name)}"
    )
    if user.last_name:
        text += f"\nㅤ<b>Last Name:</b> {html.escape(user.last_name)}"
    if user.username:
        text += f"\nㅤ<b>Username:</b> @{html.escape(user.username)}"
    text += f"\nㅤ<b>User ID:</b> <code>{user.id}</code>"

##################################################################
#?    OWNER ONLY INFO GOES HERE
##################################################################

    if update.effective_user.id == (OWNER_ID or SYS_ADMIN):
        if not user.id == OWNER_ID:
            if ANTISPAM_TOGGLE is False:
                text += "\nAntispam module is currently turned off."
            else:
                try:
                    detecting = GLOBAL_USER_DATA["AntiSpam"][user.id]['status']
                    if detecting:
                        status = "\nㅤ<b>Flood Status:</b>"
                        status += "\nㅤ❗ <b>Flood Enforced:</b> "
                        status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['status'])
                        status += "\nㅤ❗ <b>Value:</b> "
                        status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['value'])
                        if GLOBAL_USER_DATA["AntiSpamHard"][user.id]['restrict'] == None:
                            status += "\nㅤ❗ <b>Time:</b> N/A"
                        else:
                            status += "\nㅤ❗ <b>Time:</b> "
                            status += get_readable_time(time.time() - float(GLOBAL_USER_DATA["AntiSpamHard"][user.id]['restrict']))
                        status += "\nㅤ❗ <b>Level:</b> "
                        status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['level'])
                        text += status
                    else:
                        status = "\nㅤ<b>Flood Status:</b>"
                        status += "\nㅤ<b>Flood Enforced:</b> "
                        status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['status'])
                        status += "\nㅤ<b>Value:</b> "
                        status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['value'])
                        status += "\nㅤ<b>Level:</b> "
                        status += str(GLOBAL_USER_DATA["AntiSpam"][user.id]['level'])
                        text += status
                except Exception:
                    text += "\nㅤ<b>Flood Status:</b>"
                    text += "\nㅤ<b>Flood Enforced:</b> False"


        if chat.type != "private":
            try:   #? warns
                from tg_bot.modules.sql import warns_sql as wsql
                result = wsql.get_warns(user_id, chat.id)
                if result and result[0] != 0:
                    num_warns, reasons = result
                    limit, soft_warn = wsql.get_warn_setting(chat.id)
                    text += f"\nㅤ<b>Warns:</b> {num_warns}/{limit}"
            except:
                pass
            try:   #? approval
                from tg_bot.modules.sql import approve_sql as asql
                if asql.is_approved(chat.id, user.id):
                    text += "\nㅤ<b>Approved:</b> True"
                else:
                    text += "\nㅤ<b>Approved:</b> False"
            except:
                pass
        if user.id in [777000, 1087968824]:
            text += ""
        else:
            num_chats = sql.get_user_num_chats(user.id)
            text += f"\nㅤ<b>Chats:</b> <code>{num_chats}</code>"

##################################################################
#?    OWNER ONLY INFO GOES HERE
##################################################################

    else:
        if user.id == OWNER_ID:
            text += f""
        elif user.id in [777000, 1087968824]:
            text += ""
        elif user.id is bot.id:
            text += ""
        else:
            num_chats = sql.get_user_num_chats(user.id)
            text += f"\nㅤ<b>Chats:</b> <code>{num_chats}</code>"



    if user.id == OWNER_ID:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Owner</a>"
    elif user.id in DEV_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Developer</a>"
    elif user.id in SUDO_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Sudo</a>"
    elif user.id in SUPPORT_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Support</a>"
    elif user.id in MOD_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Moderator</a>"
    elif user.id in WHITELIST_USERS:
        text += f"\nㅤ<b>User status:</b> <a href='https://t.me/L4k3Bot?start=nations'>Whitelist</a>"

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == "left":
                text += f"\nㅤ<b>Presence:</b> Not here"
        if user_member.status == "kicked":
                text += f"\nㅤ<b>Presence:</b> Banned"
        elif user_member.status == "member":
                text += f"\nㅤ<b>Presence:</b> Detected"
        elif user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\nㅤ<b>Title:</b> '<code>{custom_title}</code>'"
            else:
                text += f"\nㅤ<b>Presence:</b> Admin"
    except BadRequest:
        pass

    text += "\n"
    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue
        try:
            mod_info = mod.__user_info__(user.id)
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id)
        if mod_info:
            text += mod_info

    if (
        user.id
        in [777000, 1087968824, dispatcher.bot.id, OWNER_ID]
        + DEV_USERS
        + SUDO_USERS
        + SUPPORT_USERS
        + WHITELIST_USERS
        + MOD_USERS
        ):
            pass #text += ""
    else:
        try:
            spamwtc = sw.get_ban(int(user.id))
            if sw.get_ban(int(user.id)):
                text += "<b>\nSpamWatch:\n</b>"
                text += "ㅤ<b>This person is banned in Spamwatch!</b>"
                text += f"\nㅤ<b>Reason:</b> <pre>{spamwtc.reason}</pre>"
                text += "\nㅤ<b>Appeal:</b>  @SpamWatchSupport"
        except:
            pass # don't crash if api is down somehow...
        else:
            text += ""


    temp.edit_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )



@kigcmd(command='pfp', pass_args=True)
@spamcheck
def infopfp(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot = context.bot
    args = context.args
    message = update.effective_message
    user_id = extract_user(update.effective_message, args)
    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    #temp = message.reply_text("<code>Stealing this user's Profile picture...</code>", parse_mode=ParseMode.HTML)
    
    text = (
        f"ID: <code>{user.id}</code>\n"
        f"First Name: {mention_html(user.id, user.first_name)}"
    )

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    if not INFOPIC:
        text += f"\nThis Person doesn't have a Profile picture\n"
    if INFOPIC:
        try:
            profile = bot.get_user_profile_photos(user.id).photos[0][-1]
            _file = bot.get_file(profile["file_id"])

            _file = _file.download(out=BytesIO())
            _file.seek(0)

            message.reply_document(
                document=_file,
                caption=(text),
                parse_mode=ParseMode.HTML,
            )
#    temp.delete()
        # Incase user don't have profile pic, send normal text
        except IndexError:
            message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )



@kigcmd(command='echo', pass_args=True)
@sudo_plus
def echo(update: Update, _):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)
    try:
        message.delete()
    except BadRequest:
        pass

def shell(command):
    process = Popen(command, stdout=PIPE, shell=True, stderr=PIPE)
    stdout, stderr = process.communicate()
    return (stdout, stderr)

@kigcmd(command='markdownhelp', filters=Filters.chat_type.private)
def markdown_help(update: Update, _):
    chat = update.effective_chat
    update.effective_message.reply_text((gs(chat.id, "markdown_help_text")), parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Try forwarding the following message to me, and you'll see!"
    )
    update.effective_message.reply_text(
        "/save test This is a markdown test. _italics_, *bold*, `code`, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

stats_str = '''
'''

@kigcmd(command='uptime', can_disable=False, filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def uptimee(update: Update, _):
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    msg = update.effective_message
    rspnc = "*• Uptime:* " + str(botuptime) + "\n"
    rspnc += "*• System Start time:* " + str(uptime)
    msg.reply_text(rspnc, parse_mode=ParseMode.MARKDOWN)

@kigcmd(command='stats', can_disable=False, filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def stats(update, context):
    db_size = SESSION.execute("SELECT pg_size_pretty(pg_database_size(current_database()))").scalar_one_or_none()
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    status = "*╒═══「 System statistics: 」*\n\n"
    status += "*• System Start time:* " + str(uptime) + "\n"
    uname = platform.uname()
    status += "*• System:* " + str(uname.system) + "\n"
    status += "*• Node name:* " + escape_markdown(str(uname.node)) + "\n"
    status += "*• Release:* " + escape_markdown(str(uname.release)) + "\n"
    status += "*• Machine:* " + escape_markdown(str(uname.machine)) + "\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "*• CPU:* " + str(cpu) + " %\n"
    status += "*• RAM:* " + str(mem[2]) + " %\n"
    status += "*• Storage:* " + str(disk[3]) + " %\n\n"
    status += "*• Python version:* " + python_version() + "\n"
    status += "*• python-telegram-bot:* " + str(ptbver) + "\n"
    status += "*• Uptime:* " + str(botuptime) + "\n"
    status += "*• Database size:* " + str(db_size) + "\n"
    kb = [
          [
           InlineKeyboardButton('Ping', callback_data='pingCB')
          ]
    ]
    #repo = git.Repo(search_parent_directories=True)
    #sha = repo.head.object.hexsha
    #status += f"*• Commit*: `{sha[0:9]}`\n"
    try:
        update.effective_message.reply_text(status +
            "\n*╒═══「 Bot statistics: 」*\n"
            + "\n".join([mod.__stats__() for mod in STATS]) +
            "\n\n[⍙ GitHub ⍚](https://github.com/AbOuLfOoOoOuF)\n\n" +
            "╘══「 by [ルーク](https://t.me/itsLuuke) 」\n",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True)
    except BaseException:
        update.effective_message.reply_text(
            (
                (
                    (
                        "\n*Bot statistics*:\n"
                        + "\n".join(mod.__stats__() for mod in STATS)
                    )
                    + "\n\n⍙ [GitHub](https://github.com/AbOuLfOoOoOuF) ⍚\n\n"
                )
                + "╘══「 by [ルーク](https://t.me/itsLuuke) 」\n"
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb),
            disable_web_page_preview=True,
        )

@kigcmd(command='ping')
def ping(update: Update, _):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    message.edit_text(
        "*Pong!!!*\n`{}ms`".format(ping_time), parse_mode=ParseMode.MARKDOWN
    )


@kigcallback(pattern=r'^pingCB')
def pingCallback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user.id
    if user != (OWNER_ID|SYS_ADMIN):
        query.answer('Not authorised to use this!')
    else:
        start_time = time.time()
        requests.get('https://api.telegram.org')
        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000, 3)
        query.answer('Telegram API Responce: {}ms'.format(ping_time))


def get_help(chat):
    return gs(chat, "misc_help")



__mod_name__ = "Misc"
