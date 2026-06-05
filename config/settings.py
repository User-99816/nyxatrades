import os
from dotenv import load_dotenv

# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

# ==========================================
# APPLICATION
# ==========================================

APP_NAME = "NyxaTrades API"
APP_VERSION = "1.0.0"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ==========================================
# SERVER
# ==========================================

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# ==========================================
# SUPABASE
# ==========================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# ==========================================
# LICENSE SETTINGS
# ==========================================

TRIAL_DURATION_HOURS = 1

LICENSE_PREFIX = "NYXA"

# ==========================================
# RISK ENGINE
# ==========================================

MAX_DAILY_LOSS_PERCENT = 3.0

MAX_DRAWDOWN_PERCENT = 10.0

MIN_CONFIDENCE = 0.80

MAX_DAILY_TRADES_TRIAL = 3

MAX_DAILY_TRADES_PRO = 5

TRIAL_RISK_PER_TRADE = 0.5

PRO_RISK_PER_TRADE = 1.0

# ==========================================
# TRADING SESSIONS
# ==========================================

ALLOWED_SESSIONS = [
    "LONDON",
    "NEW_YORK",
    "OVERLAP"
]

# ==========================================
# ATR VOLATILITY FILTER
# ==========================================

MIN_ATR = 0.0005
MAX_ATR = 0.0100

# ==========================================
# API SECURITY
# ==========================================

API_RATE_LIMIT_PER_MINUTE = 60

# ==========================================
# SIGNAL ENGINE
# ==========================================

DEFAULT_SYMBOL = "EURUSD"

DEFAULT_TIMEFRAME = "H1"

EMA_FAST_PERIOD = 20
EMA_SLOW_PERIOD = 50

RSI_PERIOD = 14

RSI_BUY_THRESHOLD = 55
RSI_SELL_THRESHOLD = 45

# ==========================================
# KILL SWITCH
# ==========================================

AUTO_ENABLE_KILL_SWITCH = True

# ==========================================
# LOGGING
# ==========================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)