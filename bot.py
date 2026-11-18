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
    InviteRequestSent,
)
from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ADMIN_LIMIT,
    ADMIN_IDS,
    DEFAULT_LIMIT,
    OWNER_ID,
    SESSION_STRING,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("SCRIX")

# ── Clients ───────────────────────────────────────────────────────────────────
app = Client(
    "scrix_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=500,
    max_concurrent_transmissions=50,
)

user = Client(
    "scrix_user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    workers=500,
    max_concurrent_transmissions=50,
)

# ── Persistent channel store ──────────────────────────────────────────────────
CHANNELS_FILE = "channels.json"

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f, indent=2)

CHANNELS = load_channels()

# ── Admin waiting state ───────────────────────────────────────────────────────
ADMIN_WAITING = {}

# ── Helpers ───────────────────────────────────────────────────────────────────
CC_PATTERN = re.compile(r'\d{16}\D*\d{2}\D*\d{2,4}\D*\d{3,4}')

def is_admin(uid):
    return uid in ADMIN_IDS or uid == OWNER_ID

# ── UI builders ───────────────────────────────────────────────────────────────
def admin_panel_text():
    if CHANNELS:
        ch_lines = "".join(
            f"  <code>{i}.</code> {c['title']} — <code>{c['id']}</code>\n"
            for i, c in enumerate(CHANNELS, 1)
        )
    else:
        ch_lines = "  <i>No channels set yet.</i>\n"
    return (
        "╔══════════════════════╗\n"
        "   🛡 <b>𝐒𝐂𝐑𝐈𝐗 𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</b> 🛡\n"
        "╚══════════════════════╝\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📡 <b>𝐒𝐀𝐕𝐄𝐃 𝐂𝐇𝐀𝐍𝐍𝐄𝐋𝐒</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{ch_lines}"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <i>Manage channels below</i>"
    )

def admin_panel_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ 𝐀𝐝𝐝 𝐂𝐡𝐚𝐧𝐧𝐞𝐥",    callback_data="admin_add"),
            InlineKeyboardButton("➖ 𝐑𝐞𝐦𝐨𝐯𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", callback_data="admin_remove"),
        ],
        [
            InlineKeyboardButton("📋 𝐋𝐢𝐬𝐭 𝐂𝐡𝐚𝐧𝐧𝐞𝐥𝐬",  callback_data="admin_list"),
            InlineKeyboardButton("🗑 𝐂𝐥𝐞𝐚𝐫 𝐀𝐥𝐥",      callback_data="admin_clear"),
        ],
        [
            InlineKeyboardButton("🔄 𝐑𝐞𝐟𝐫𝐞𝐬𝐡",         callback_data="admin_refresh"),
        ],
    ])

# ── Start message ─────────────────────────────────────────────────────────────
START_MESSAGE = (
    "╔══════════════════════╗\n"
    "   💠 <b>𝐒 𝐂 𝐑 𝐈 𝐗</b> 💠\n"
    "╚══════════════════════╝\n\n"
    "<b>⚡ 𝐓𝐡𝐞 𝐔𝐥𝐭𝐢𝐦𝐚𝐭𝐞 𝐂𝐂 𝐒𝐜𝐫𝐚𝐩𝐞𝐫 &amp; 𝐂𝐥𝐞𝐚𝐧𝐞𝐫</b>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🔷 <b>𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "🟣 <code>/scr</code>   ➜ Scrape single channel\n"
    "🔵 <code>/mc</code>    ➜ Scrape multiple channels\n"
    "🟢 <code>/clean</code> ➜ Clean &amp; format card file\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "🔶 <b>𝐔𝐒𝐀𝐆𝐄</b>\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "<code>/scr @channel 100</code>\n"
    "<code>/scr @channel 100 515462</code>\n"
    "<code>/scr @channel 100 BankName</code>\n"
    "<code>/scr https://t.me/+Hash 100</code>\n"
    "<code>/mc @ch1 @ch2 @ch3 100</code>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "💎 <i>Powered by SCRIX Engine</i>"
)

# ── /start ────────────────────────────────────────────────────────────────────
@app.on_message(
    filters.command("start", prefixes=["/", ".", ",", "!"])
    & (filters.group | filters.private)
)
async def start(client, message):
    uid = message.from_user.id if message.from_user else None
    buttons = []
    if is_admin(uid):
        buttons.append([InlineKeyboardButton("🛡 𝐀𝐝𝐦𝐢𝐧 𝐏𝐚𝐧𝐞𝐥", callback_data="open_admin")])
    buttons.append([InlineKeyboardButton("👨‍💻 𝐃𝐞𝐯𝐞𝐥𝐨𝐩𝐞𝐫", url="https://t.me/werrorz")])
    await client.send_message(
        message.chat.id,
        START_MESSAGE,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(buttons),
        reply_to_message_id=message.id,
    )

# ── /admin ────────────────────────────────────────────────────────────────────
@app.on_message(
    filters.command("admin", prefixes=["/", ".", ",", "!"])
    & (filters.group | filters.private)
)
async def admin_cmd(client, message):
    uid = message.from_user.id if message.from_user else None
    if not is_admin(uid):
        await message.reply_text("<b>🚫 𝐍𝐨 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧.</b>", parse_mode=ParseMode.HTML)
        return
    await client.send_message(
        message.chat.id,
        admin_panel_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=admin_panel_buttons(),
        reply_to_message_id=message.id,
    )

# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^open_admin$"))
async def cb_open_admin(client, cq):
    if not is_admin(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    await cq.message.edit_text(admin_panel_text(), parse_mode=ParseMode.HTML, reply_markup=admin_panel_buttons())
    await cq.answer()

@app.on_callback_query(filters.regex("^admin_refresh$"))
async def cb_refresh(client, cq):
    if not is_admin(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    await cq.message.edit_text(admin_panel_text(), parse_mode=ParseMode.HTML, reply_markup=admin_panel_buttons())
    await cq.answer("✅ Refreshed.")

@app.on_callback_query(filters.regex("^admin_list$"))
async def cb_list(client, cq):
    if not is_admin(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    if not CHANNELS:
        await cq.answer("📋 No channels saved yet.", show_alert=True); return
    lines = "\n".join(f"{i}. {c['title']} — {c['id']}" for i, c in enumerate(CHANNELS, 1))
    await cq.answer(f"📡 Channels:\n{lines}", show_alert=True)

@app.on_callback_query(filters.regex("^admin_clear$"))
async def cb_clear(client, cq):
    if not is_admin(cq.from_user.id):
        await cq.answer("🚫 No permission.", show_alert=True); return
    CHANNELS.clear()
    save_channels(CHANNELS)
    await cq.message.edit_text(admin_panel_text(), parse_mode=ParseMode.HTML, reply_markup=admin_panel_buttons())
    await cq.answer("🗑 All channels cleared.")

@app.on_callback_query(filters.regex("^admin_add$"))
async def cb_add(client, cq):
    uid = cq.from_user.id
    if not is_admin(uid):
        await cq.answer("🚫 No permission.", show_alert=True); return
    ADMIN_WAITING[uid] = "add_channel"
    await cq.message.edit_text(
        "╔══════════════════════╗\n"
        "   💠 <b>𝐒𝐂𝐑𝐈𝐗</b> 💠\n"
        "╚══════════════════════╝\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "➕ <b>𝐀𝐃𝐃 𝐂𝐇𝐀𝐍𝐍𝐄𝐋</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send the channel username or link:\n\n"
        "<code>@channelname</code>\n"
        "<code>https://t.me/channelname</code>\n"
        "<code>https://t.me/+InviteHash</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <i>Send /cancel to abort</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥", callback_data="admin_cancel")
        ]]),
    )
    await cq.answer()

@app.on_callback_query(filters.regex("^admin_remove$"))
async def cb_remove_menu(client, cq):
    uid = cq.from_user.id
    if not is_admin(uid):
        await cq.answer("🚫 No permission.", show_alert=True); return
    if not CHANNELS:
        await cq.answer("📋 No channels to remove.", show_alert=True); return
    rows = [[InlineKeyboardButton(f"🗑 {c['title']}", callback_data=f"admin_del_{c['id']}")] for c in CHANNELS]
    rows.append([InlineKeyboardButton("🔙 𝐁𝐚𝐜𝐤", callback_data="open_admin")])
    await cq.message.edit_text(
        "╔══════════════════════╗\n"
        "   💠 <b>𝐒𝐂𝐑𝐈𝐗</b> 💠\n"
        "╚══════════════════════╝\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "➖ <b>𝐑𝐄𝐌𝐎𝐕𝐄 𝐂𝐇𝐀𝐍𝐍𝐄𝐋</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Tap a channel to remove it:\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 <i>Select below</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(rows),
    )
    await cq.answer()

@app.on_callback_query(filters.regex("^admin_del_"))
async def cb_del_channel(client, cq):
    uid = cq.from_user.id
    if not is_admin(uid):
        await cq.answer("🚫 No permission.", show_alert=True); return
    ch_id   = cq.data.replace("admin_del_", "")
    removed = [c for c in CHANNELS if c["id"] == ch_id]
    if removed:
        CHANNELS[:] = [c for c in CHANNELS if c["id"] != ch_id]
        save_channels(CHANNELS)
        await cq.answer(f"✅ Removed: {removed[0]['title']}", show_alert=True)
    else:
        await cq.answer("⚠️ Not found.", show_alert=True)
    await cq.message.edit_text(admin_panel_text(), parse_mode=ParseMode.HTML, reply_markup=admin_panel_buttons())

@app.on_callback_query(filters.regex("^admin_cancel$"))
async def cb_cancel(client, cq):
    ADMIN_WAITING.pop(cq.from_user.id, None)
    await cq.message.edit_text(admin_panel_text(), parse_mode=ParseMode.HTML, reply_markup=admin_panel_buttons())
    await cq.answer("Cancelled.")

# ── Admin text input (private only) ──────────────────────────────────────────
@app.on_message(filters.private & filters.text)
async def admin_input_handler(client, message):
    uid = message.from_user.id if message.from_user else None
    if uid not in ADMIN_WAITING:
        return
    action = ADMIN_WAITING.pop(uid)
    if message.text.strip().lower() in ("/cancel", "cancel"):
        await message.reply_text("<b>❌ Cancelled.</b>", parse_mode=ParseMode.HTML)
        return
    if action == "add_channel":
        identifier = message.text.strip()
        slug = (
            identifier.replace("https://t.me/", "").replace("http://t.me/", "")
            .replace("t.me/", "").lstrip("@")
        )
        status = await message.reply_text("<b>⏳ Resolving channel...</b>", parse_mode=ParseMode.HTML)
        try:
            chat     = await user.get_chat(identifier if identifier.startswith("https://t.me/+") else slug)
            ch_id    = str(chat.id)
            ch_title = chat.title or slug
            if any(c["id"] == ch_id for c in CHANNELS):
                await status.edit_text(
                    f"╔══════════════════════╗\n"
                    f"   💠 <b>𝐒𝐂𝐑𝐈𝐗</b> 💠\n"
                    f"╚══════════════════════╝\n\n"
                    f"⚠️ <b>Already saved:</b> <code>{ch_title}</code>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💎 <i>Use /admin to manage</i>",
                    parse_mode=ParseMode.HTML,
                )
                return
            CHANNELS.append({"id": ch_id, "title": ch_title})
            save_channels(CHANNELS)
            await status.edit_text(
                f"╔══════════════════════╗\n"
                f"   💠 <b>𝐒𝐂𝐑𝐈𝐗</b> 💠\n"
                f"╚══════════════════════╝\n\n"
                f"✅ <b>𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐀𝐝𝐝𝐞𝐝!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📡 <b>𝐍𝐀𝐌𝐄 :</b> <code>{ch_title}</code>\n"
                f"🔑 <b>𝐈𝐃 :</b> <code>{ch_id}</code>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 <i>Use /admin to manage</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🛡 𝐁𝐚𝐜𝐤 𝐭𝐨 𝐏𝐚𝐧𝐞𝐥", callback_data="open_admin")
                ]]),
            )
            logger.info(f"Admin {uid} added channel: {ch_title} ({ch_id})")
        except Exception as e:
            logger.error(f"admin add_channel: {e}")
            await status.edit_text(
                f"╔══════════════════════╗\n"
                f"   💠 <b>𝐒𝐂𝐑𝐈𝐗</b> 💠\n"
                f"╚══════════════════════╝\n\n"
                f"❌ <b>Failed to resolve channel.</b>\n\n"
                f"<code>{e}</code>\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"💎 <i>Check the username and try again</i>",
                parse_mode=ParseMode.HTML,
            )

# ── Channel resolver ──────────────────────────────────────────────────────────
async def resolve_channel(user_client, bot_client, identifier, message):
    if identifier.lstrip("-").isdigit():
        try:
            chat = await user_client.get_chat(int(identifier))
            return chat, chat.title
        except Exception as e:
            await bot_client.send_message(message.chat.id, "<b>❌ Invalid chat ID</b>")
            logger.error(e)
            return None, None
    if identifier.startswith("https://t.me/+"):
        tmp = await bot_client.send_message(
            message.chat.id, "<b>⏳ Checking invite link...</b>", reply_to_message_id=message.id
        )
        joined = await join_private_chat(user_client, identifier)
        if not joined:
            await send_join_request(user_client, identifier, tmp)
            return None, None
        await tmp.delete()
        try:
            chat = await user_client.get_chat(identifier)
            return chat, chat.title
        except Exception as e:
            await bot_client.send_message(message.chat.id, "<b>❌ Could not fetch chat.</b>")
            logger.error(e)
            return None, None
    slug = (
        identifier.replace("https://t.me/", "").replace("http://t.me/", "")
        .replace("t.me/", "").lstrip("@")
    )
    try:
        chat = await user_client.get_chat(slug)
        return chat, chat.title
    except Exception as e:
        await bot_client.send_message(message.chat.id, "<b>❌ Incorrect username or chat ID</b>")
        logger.error(e)
        return None, None

# ── Scrape helpers ────────────────────────────────────────────────────────────
async def scrape_messages(client, channel_id, limit, start_number=None, bank_name=None):
    messages = []
    count    = 0
    logger.info(f"Scraping {channel_id}  limit={limit}")
    async for msg in client.search_messages(channel_id):
        if count >= limit:
            break
        text = msg.text or msg.caption
        if not text:
            continue
        if bank_name and bank_name.lower() not in text.lower():
            continue
        for matched in CC_PATTERN.findall(text):
            parts = re.findall(r'\d+', matched)
            if len(parts) == 4:
                cc, mo, yr, cvv = parts
                yr = yr[-2:]
                if start_number and not cc.startswith(start_number[:6]):
                    continue
                messages.append(f"{cc}|{mo}|{yr}|{cvv}")
                count += 1
                if count >= limit:
                    break
    logger.info(f"Scraped {len(messages)} cards from {channel_id}")
    return messages[:limit]

def remove_duplicates(messages):
    unique  = list(set(messages))
    removed = len(messages) - len(unique)
    logger.info(f"Deduped: removed {removed}")
    return unique, removed

async def get_user_link(message):
    if message.from_user is None:
        return '<a href="https://t.me/SCRIX">SCRIX</a>'
    fn   = message.from_user.first_name
    ln   = message.from_user.last_name or ""
    full = f"{fn} {ln}".strip()
    return f'<a href="tg://user?id={message.from_user.id}">{full}</a>'

async def send_results(client, message, unique_messages, duplicates_removed,
                       source_name, bin_filter=None, bank_filter=None):
    if not unique_messages:
        try:
            await message.delete()
            await client.send_message(
                message.chat.id,
                "<b>❌ 𝐍𝐎 𝐂𝐑𝐄𝐃𝐈𝐓 𝐂𝐀𝐑𝐃𝐒 𝐅𝐎𝐔𝐍𝐃</b>",
                reply_to_message_id=getattr(message, "replied_to_message_id", None),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            logger.error(f"send_results (empty): {e}")
        return
    file_name = f"x{len(unique_messages)}_{source_name.replace(' ', '_')}.txt"
    try:
        async with aiofiles.open(file_name, "w") as f:
            await f.write("\n".join(unique_messages))
        user_link = await get_user_link(message)
        caption = (
            f"╔══════════════════════╗\n"
            f"   💠 <b>𝐒 𝐂 𝐑 𝐈 𝐗</b> 💠\n"
            f"╚══════════════════════╝\n\n"
            f"✅ <b>𝐒𝐂𝐑𝐀𝐏𝐏𝐄𝐃 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>𝐒𝐎𝐔𝐑𝐂𝐄 :</b> <code>{source_name}</code>\n"
            f"💳 <b>𝐀𝐌𝐎𝐔𝐍𝐓 :</b> <code>{len(unique_messages)}</code>\n"
            f"🗑 <b>𝐃𝐔𝐏𝐄𝐒 𝐑𝐌𝐕𝐃 :</b> <code>{duplicates_removed}</code>\n"
        )
        if bin_filter:
            caption += f"🔍 <b>𝐁𝐈𝐍 :</b> <code>{bin_filter}</code>\n"
        if bank_filter:
            caption += f"🏦 <b>𝐁𝐀𝐍𝐊 :</b> <code>{bank_filter}</code>\n"
        caption += (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>𝐁𝐘 :</b> {user_link}\n"
            f"💠 <b>𝐃𝐄𝐕 :</b> <a href='https://t.me/werrorz'>@werrorz</a>\n"
        )
        chat_id  = message.chat.id
        reply_id = getattr(message, "replied_to_message_id", None)
        await message.delete()
        send_kwargs = dict(document=file_name, caption=caption, parse_mode=ParseMode.HTML)
        if reply_id:
            send_kwargs["reply_to_message_id"] = reply_id
        await client.send_document(chat_id, **send_kwargs)
        logger.info(f"Results sent for {source_name}")
    except Exception as e:
        logger.error(f"send_results: {e}")
        try:
            await client.send_message(message.chat.id, f"<b>❌ 𝐄𝐑𝐑𝐎𝐑:</b> <code>{e}</code>", parse_mode=ParseMode.HTML)
        except Exception:
            pass
    finally:
        try:
            if os.path.exists(file_name):
                os.remove(file_name)
        except Exception as e:
            logger.error(f"cleanup: {e}")

# ── Join helpers ───────────────────────────────────────────────────────────────
async def join_private_chat(client, invite_link):
    try:
        await client.join_chat(invite_link); return True
    except UserAlreadyParticipant:
        return True
    except InviteRequestSent:
        return False
    except (InviteHashExpired, InviteHashInvalid) as e:
        logger.error(f"join_private_chat: {e}"); return False

async def send_join_request(client, invite_link, message):
    try:
        await client.join_chat(invite_link); return True
    except PeerIdInvalid as e:
        logger.error(f"send_join_request: {e}"); return False
    except InviteRequestSent:
        await message.edit_text("<b>𝐉𝐨𝐢𝐧 𝐑𝐞𝐪𝐮𝐞𝐬𝐭 𝐒𝐞𝐧𝐭 ✅</b>"); return False

# ── /scr + /mc ────────────────────────────────────────────────────────────────
def setup_scr_handler(app):
    @app.on_message(
        filters.command(["scr", "ccscr", "scrcc"], prefixes=["/", ".", ",", "!"])
        & (filters.group | filters.private)
    )
    async def scr_cmd(client, message):
        args    = message.text.split()[1:]
        user_id = message.from_user.id if message.from_user else None
        if len(args) < 2:
            await client.send_message(message.chat.id, "<b>⚠️ Usage: /scr @channel amount [bin/bank]</b>", reply_to_message_id=message.id)
            return
        chat, channel_name = await resolve_channel(user, client, args[0], message)
        if chat is None:
            return
        try:
            limit = int(args[1])
        except ValueError:
            await client.send_message(message.chat.id, "<b>⚠️ Invalid limit value</b>"); return
        max_lim = ADMIN_LIMIT if user_id in ADMIN_IDS else DEFAULT_LIMIT
        if limit > max_lim:
            await client.send_message(message.chat.id, f"<b>❌ Max limit is {max_lim}</b>"); return
        start_number = bank_name = bin_filter = None
        if len(args) > 2:
            if args[2].isdigit():
                start_number = args[2]; bin_filter = args[2][:6]
            else:
                bank_name = " ".join(args[2:])
        tmp = await client.send_message(message.chat.id, "<b>⏳ Scraping in progress...</b>", reply_to_message_id=message.id)
        tmp.replied_to_message_id = message.id
        results = await scrape_messages(user, chat.id, limit, start_number=start_number, bank_name=bank_name)
        unique, dupes = remove_duplicates(results)
        if not unique:
            await tmp.delete()
            await client.send_message(message.chat.id, "<b>❌ No credit cards found</b>", reply_to_message_id=message.id)
        else:
            await send_results(client, tmp, unique, dupes, channel_name, bin_filter=bin_filter, bank_filter=bank_name)

    @app.on_message(
        filters.command(["mc", "multiscr", "mscr"], prefixes=["/", ".", ",", "!"])
        & (filters.group | filters.private)
    )
    async def mc_cmd(client, message):
        args    = message.text.split()[1:]
        user_id = message.from_user.id if message.from_user else None
        if len(args) < 2:
            await client.send_message(message.chat.id, "<b>⚠️ Usage: /mc @ch1 @ch2 ... amount</b>", reply_to_message_id=message.id)
            return
        channel_identifiers = args[:-1]
        try:
            limit = int(args[-1])
        except ValueError:
            await client.send_message(message.chat.id, "<b>⚠️ Invalid limit value</b>"); return
        max_lim = ADMIN_LIMIT if user_id in ADMIN_IDS else DEFAULT_LIMIT
        if limit > max_lim:
            await client.send_message(message.chat.id, f"<b>❌ Max limit is {max_lim}</b>"); return
        tmp = await client.send_message(message.chat.id, "<b>⏳ Scraping in progress...</b>", reply_to_message_id=message.id)
        tmp.replied_to_message_id = message.id
        tasks   = [_scrape_task(user, ci, limit, client, message) for ci in channel_identifiers]
        results = await asyncio.gather(*tasks)
        all_msgs = [card for sublist in results for card in sublist]
        unique, dupes = remove_duplicates(all_msgs)
        unique = unique[:limit]
        if not unique:
            await tmp.delete()
            await client.send_message(message.chat.id, "<b>❌ No credit cards found</b>", reply_to_message_id=message.id)
        else:
            await send_results(client, tmp, unique, dupes, "Multiple Chats")

async def _scrape_task(client, identifier, limit, bot_client, message):
    try:
        chat, _ = await resolve_channel(client, bot_client, identifier, message)
        if chat is None:
            return []
        return await scrape_messages(client, chat.id, limit)
    except Exception as e:
        logger.error(f"_scrape_task {identifier}: {e}"); return []

# ── /clean ────────────────────────────────────────────────────────────────────
def normalize_card(text):
    text    = re.sub(r'[\n\r|\/]', ' ', text)
    numbers = re.findall(r'\d+', text)
    cc = mm = yy = cvv = ''
    for num in numbers:
        if 13 <= len(num) <= 19 and not cc:
            cc = num
        elif len(num) == 4 and num.startswith('20') and not yy:
            yy = num
        elif len(num) == 2 and int(num) <= 12 and not mm:
            mm = num
        elif len(num) == 2 and not yy:
            yy = '20' + num
        elif len(num) in (3, 4) and not cvv:
            cvv = num
    if cc and mm and yy and cvv:
        if len(yy) == 2:
            yy = '20' + yy
        return f"{cc}|{mm}|{yy}|{cvv}"
    return None

@app.on_message(
    filters.command(["clean"], prefixes=["/", ".", ",", "!"])
    & (filters.group | filters.private)
)
async def clean_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text("<b>⚠️ Reply to a .txt file</b>"); return
    doc = message.reply_to_message.document
    if not doc.file_name.endswith('.txt'):
        await message.reply_text("<b>⚠️ Only .txt files accepted</b>"); return
    status    = await message.reply_text("<b>⏳ Processing file...</b>")
    file_path = output_filename = None
    try:
        file_path = await client.download_media(doc)
        async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
        cleaned = [normalize_card(ln) for ln in content.strip().split('\n') if ln.strip()]
        cleaned = [c for c in cleaned if c]
        unique, dupes = remove_duplicates(cleaned)
        if not unique:
            await status.delete()
            await client.send_message(message.chat.id, "<b>❌ No valid cards found</b>", reply_to_message_id=message.id)
            return
        output_filename = f"cleaned_x{len(unique)}.txt"
        async with aiofiles.open(output_filename, 'w') as f:
            await f.write('\n'.join(unique))
        user_link = await get_user_link(message)
        caption = (
            f"╔══════════════════════╗\n"
            f"   💠 <b>𝐒 𝐂 𝐑 𝐈 𝐗</b> 💠\n"
            f"╚══════════════════════╝\n\n"
            f"🟢 <b>𝐂𝐋𝐄𝐀𝐍𝐄𝐃 𝐒𝐔𝐂𝐂𝐄𝐒𝐒𝐅𝐔𝐋𝐋𝐘</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 <b>𝐒𝐎𝐔𝐑𝐂𝐄 :</b> <code>File Cleaning 🧹</code>\n"
            f"💳 <b>𝐀𝐌𝐎𝐔𝐍𝐓 :</b> <code>{len(unique)}</code>\n"
            f"🗑 <b>𝐃𝐔𝐏𝐄𝐒 𝐑𝐌𝐕𝐃 :</b> <code>{dupes}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>𝐁𝐘 :</b> {user_link}\n"
            f"💠 <b>𝐃𝐄𝐕 :</b> <a href='https://t.me/werrorz'>@werrorz</a>\n"
        )
        await status.delete()
        await client.send_document(message.chat.id, output_filename, caption=caption, parse_mode=ParseMode.HTML, reply_to_message_id=message.id)
    except Exception as e:
        logger.error(f"clean_cmd: {e}")
        try: await status.delete()
        except Exception: pass
        await client.send_message(message.chat.id, f"<b>❌ Error: <code>{e}</code></b>", reply_to_message_id=message.id)
    finally:
        for p in [file_path, output_filename]:
            if p and os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

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
