# SCRIX — Config
import os

API_ID    = int(os.getenv("API_ID",    "30949016"))
API_HASH  =     os.getenv("API_HASH",  "29610b037ec08cccfcc219057143a818")
BOT_TOKEN =     os.getenv("BOT_TOKEN", "9247620318:AAEkvEbzr5s2K2FlGR1N_dgQmvleB2Qh8xA")

OWNER_ID  = int(os.getenv("OWNER_ID", "8919487892"))

_admin_env = os.getenv("ADMIN_IDS", "").strip()
if _admin_env:
    ADMIN_IDS = [int(x) for x in _admin_env.replace(" ", "").split(",") if x]
else:
    ADMIN_IDS = [8919487892]

DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "10000"))
ADMIN_LIMIT   = int(os.getenv("ADMIN_LIMIT",   "50000"))

# ── User client session (fallback baked in; env wins) ─────────────────────────
_DEFAULT_SESSION = (
    "BQHYPpgApjyhycJyCVz1DaOcgCaSjJGI3xVmmV81sZo_cVH7gcDIYtNNYcKvlciWndfuVBNY2owmZu2qQIgDRpLZjp0SprP0V5lFwrTIW1_k6GXTS-VA53oTyz8c4rewzNoYLmmkwbdJ2p-lFGFrK45Ue4iqaiPTyDfuYrVet_vDRzDwDyPfoDviv8rNdn-b_esV-uAeUeBynukxynDs3gloiSl-U6oE6xN3-v7xOkh4PJmai5lQBA0xMT3_mID261rNPS4YM0w4CjzSTBZbu_CBbopctmdNwKN2vOYRXwSnc_eNCBl2Pe8zck2r7HKxxyDovo5Wa-gF9tEWaVaL_lxAlKUL7QAAAAInM3zeAQ"
)
SESSION_STRING = os.getenv("SESSION_STRING", _DEFAULT_SESSION).strip()
