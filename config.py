# SCRIX — Config
import os

# ── Telegram API ──────────────────────────────────────────────────────────────
API_ID    = int(os.getenv("API_ID",    "30949016"))
API_HASH  =     os.getenv("API_HASH",  "29610b037ec08cccfcc219057143a818")
BOT_TOKEN =     os.getenv("BOT_TOKEN", "9247620318:AAEkvEbzr5s2K2FlGR1N_dgQmvleB2Qh8xA")

# ── Access ────────────────────────────────────────────────────────────────────
OWNER_ID  = int(os.getenv("OWNER_ID", "8919487892"))

_admin_env = os.getenv("ADMIN_IDS", "").strip()
if _admin_env:
    ADMIN_IDS = [int(x) for x in _admin_env.replace(" ", "").split(",") if x]
else:
    ADMIN_IDS = [8919487892]

# ── Limits ────────────────────────────────────────────────────────────────────
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "10000"))
ADMIN_LIMIT   = int(os.getenv("ADMIN_LIMIT",   "50000"))

# ── User client session ───────────────────────────────────────────────────────
# Generate this once via gen_session.py, then set it as SESSION_STRING in Render.
SESSION_STRING = os.getenv("SESSION_STRING", "").strip()
if not SESSION_STRING:
    raise SystemExit(
        "\n[FATAL] SESSION_STRING env var is missing.\n"
        "  1. Run `python gen_session.py` locally (phone + code + 2FA if set).\n"
        "  2. Copy the printed string into Render -> Environment -> SESSION_STRING.\n"
        "  3. Redeploy.\n"
    )
