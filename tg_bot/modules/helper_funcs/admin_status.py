# admin status module by Luke (@itsLuuke - t.me/itsLuuke)
# written for OdinRobot
# copyright 2022

from functools import wraps
from typing import Optional
from threading import RLock

from telegram import Chat, Update, ChatMember, ParseMode
from telegram.ext import CallbackContext

from tg_bot import dispatcher

from ..helper_funcs.decorators import kigcallback

from .admin_status_helpers import (
	ADMINS_CACHE,
	BOT_ADMIN_CACHE,
	SUDO_USERS,
	MOD_USERS,
	AdminPerms,
	UserClass,
	anon_reply_markup,
	anon_reply_text,
	anon_callbacks,
	edit_anon_msg as eam
)


def bot_is_admin(chat: Chat, perm: Optional[AdminPerms] = None) -> bool:
	bot_id: int = dispatcher.bot.id
	if chat.type == "private" or chat.all_members_are_administrators:
		return True

	try:  # try to get from cache
		bot_member = BOT_ADMIN_CACHE[chat.id]
	except KeyError:  # if not in cache, get from API and save to cache
		bot_member = dispatcher.bot.getChatMember(chat.id, bot_id)
		BOT_ADMIN_CACHE[chat.id] = bot_member

	if perm:
		return getattr(bot_member, perm.value)

	return bot_member.status == "administrator"  # bot can't be owner

# decorator, can be used as
# @bot_perm_check() with no perm to check for admin-ship only
# or as @bot_perm_check(AdminPerms.value) to check for a specific permission
def bot_admin_check(permission: Optional[AdminPerms] = None):
	def wrapper(func):
		@wraps(func)
		def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
			nonlocal permission
			chat = update.effective_chat
			if chat.type == "private" or chat.all_members_are_administrators:
				return func(update, context, *args, **kwargs)
			bot_id = dispatcher.bot.id
			try:  # try to get from cache
				bot_member = BOT_ADMIN_CACHE[chat.id]
			except KeyError:  # if not in cache, get from API and save to cache
				bot_member = dispatcher.bot.getChatMember(chat.id, bot_id)
				BOT_ADMIN_CACHE[chat.id] = bot_member
			if permission:  # if a perm is required, check for it
				if getattr(bot_member, permission.value):
					update.effective_message.reply_text("I have enough permissions to do that!")
					return func(update, context, *args, **kwargs)
				return update.effective_message.reply_text(
						f"I can't perform this action due to missing the following permission: `{permission.name}`\n\
						Make sure i am an admin and {permission.name.replace('is_', 'am ').replace('_', ' ')}!")
			if bot_member.status == "administrator":  # if no perm is required, check for admin-ship only
				update.effective_message.reply_text("I am admin here!")
				return func(update, context, *args, **kwargs)
			else:  # not admin
				return update.effective_message.reply_text("I can't perform this action because I'm not admin!")

		return wrapped

	return wrapper


def user_is_admin(update: Update,
					user_id: int,
					channels: bool = False,  # if True, returns True if user is anonymous
					allow_moderators: bool = False,  # if True, returns True if user is a moderator
					perm: AdminPerms = None  # if not None, returns True if user has the specified permission
					) -> bool:
	chat = update.effective_chat
	message = update.effective_message
	if chat.type == "private" or user_id in MOD_USERS if allow_moderators else SUDO_USERS:
		return True

	if channels and (message.sender_chat is not None and message.sender_chat.type != "channel"):
		return True  # return true if user is anonymous

	member: ChatMember = get_mem_from_cache(user_id, chat.id)

	if not member:  # not in cache so not an admin
		return False

	if perm:  # check perm if its required
		return getattr(member, perm.value)

	return member.status in ["administrator", "creator"]  # check if user is admin


RLOCK = RLock()


def get_mem_from_cache(user_id: int, chat_id: int) -> ChatMember:
	with RLOCK:
		try:
			for i in ADMINS_CACHE[chat_id]:
				if i.user.id == user_id:
					return i

		except KeyError:
			admins = dispatcher.bot.getChatAdministrators(chat_id)
			ADMINS_CACHE[chat_id] = admins
			for i in admins:
				if i.user.id == user_id:
					return i


# decorator, can be used as @bot_admin_check() to check user is admin
# or @bot_admin_check(AdminPerms.value) to check for a specific permission
# ustat can be used in both cases to allow moderators to use the command
def user_admin_check(permission: AdminPerms = None, ustat: UserClass = UserClass.ADMIN):
	def wrapper(func):
		@wraps(func)
		def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
			nonlocal permission
			if update.effective_chat.type == 'private':
				return func(update, context, *args, **kwargs)
			message = update.effective_message

			if update.effective_message.sender_chat:  # anonymous sender
				# callback contains chat_id, message_id, and the required perm
				callback_id = f'perm/{message.chat.id}/{message.message_id}/{permission.value if permission else "None"}'
				# store the function to be called in a (chat_id, message_id) tuple
				# stored data will be (update, context), func, callback message_id
				anon_callbacks[(message.chat.id, message.message_id)] = (
					(update, context),
					func,
					message.reply_text(
							text=anon_reply_text,
							reply_markup=anon_reply_markup(callback_id)).message_id
				)

			# not anon so just check for admin/perm
			else:
				user_id = message.from_user.id
				if user_is_admin(
							update,
							user_id,
							allow_moderators=ustat == UserClass.MOD,  # allow moderators only if ustat is MOD_USERS
							perm=permission):
					return func(update, context, *args, **kwargs)

				return message.reply_text(
						f"You lack the following permission for this command:\n`{permission.value}`!",
						parse_mode=ParseMode.MARKDOWN
				)

		return wrapped

	return wrapper


@kigcallback(pattern="perm")
def perm_callback_check(upd: Update, _: CallbackContext):
	callback = upd.callback_query
	perm = callback.data.split('/')[3]
	chat_id = int(callback.data.split('/')[1])
	message_id = int(callback.data.split('/')[2])
	user_id = callback.from_user.id
	msg = upd.effective_message

	mem = user_is_admin(upd, user_id, perm=perm if perm != 'None' else None)

	if perm == 'None':  # just check for admin

		if not mem:
			eam(msg, "You need to be an admin to perform this action!")
			return

		elif cb := anon_callbacks.pop((chat_id, message_id), None):
			message_id = cb[2]
			if message_id is not None:
				dispatcher.bot.delete_message(chat_id, message_id)

				# update the `Update` attributes by the correct values, so they can be used properly
				setattr(cb[0][0], "_effective_user", upd.effective_user)
				setattr(cb[0][0], "_effective_message", upd.effective_message)

			return cb[1](cb[0][0], cb[0][1])
		else:
			eam(msg, "This message is no longer valid.")

	elif mem:
		if cb := anon_callbacks.pop((chat_id, message_id), None):
			message_id = cb[2]
			if message_id is not None:
				dispatcher.bot.delete_message(chat_id, message_id)

				# update the `Update` attributes by the correct values, so they can be used properly
				setattr(cb[0][0], "_effective_user", upd.effective_user)
				setattr(cb[0][0], "_effective_message", upd.effective_message)

			return cb[1](cb[0][0], cb[0][1])
		else:
			eam(msg, "This message is no longer valid.")
	else:
		eam(msg, f"You lack the permission: `{perm}`!")
