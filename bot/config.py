"""
config.py - Bot konfiguratsiyasi
=================================
Bot tokeni, admin ID lar va barcha sozlamalarni .env faylidan o'qiydi.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Loyiha ildiz papkasi
BASE_DIR = Path(__file__).parent.parent

# .env faylini yuklash
load_dotenv(BASE_DIR / ".env")

# ==========================================
# Bot konfiguratsiyasi
# ==========================================
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN .env faylida topilmadi!")

# Admin ID lar (vergul bilan ajratilgan)
_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [
    int(admin_id.strip())
    for admin_id in _admin_ids_raw.split(",")
    if admin_id.strip().isdigit()
]

# ==========================================
# Kanal konfiguratsiyasi (Majburiy obuna)
# ==========================================
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "")
CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "")

# ==========================================
# Ma'lumotlar bazasi konfiguratsiyasi
# ==========================================
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/anime_bot.db"
)
DATABASE_PATH: str = str(BASE_DIR / "anime_bot.db")

# ==========================================
# Kesh konfiguratsiyasi
# ==========================================
CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))

# ==========================================
# Rate Limit konfiguratsiyasi
# ==========================================
RATE_LIMIT: float = float(os.getenv("RATE_LIMIT", "1"))

# ==========================================
# Log konfiguratsiyasi
# ==========================================
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: str = str(BASE_DIR / "bot.log")

# ==========================================
# Papkalar
# ==========================================
IMAGES_DIR: Path = BASE_DIR / "bot" / "images"
VIDEOS_DIR: Path = BASE_DIR / "bot" / "videos"
BACKUP_DIR: Path = BASE_DIR / os.getenv("BACKUP_DIR", "backups")

# Papkalarni yaratish
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# Pagination konfiguratsiyasi
# ==========================================
ANIME_PER_PAGE: int = 20

# ==========================================
# Bot xabarlari (Uzbekcha)
# ==========================================
START_MESSAGE = """
🎌 <b>Anime Bot ga xush kelibsiz!</b>

👋 Salom, <b>{name}</b>!

🔍 Quyidagi imkoniyatlar mavjud:
• <b>Kod orqali qidiruv</b> — anime kodini kiriting
• <b>🎬 Anime</b> — barcha animelarga ko'z tashlang
• <b>🖼 Rasm orqali qidiruv</b> — rasm yuboring
• <b>📚 Qo'llanma</b> — foydalanish bo'yicha yordam

📺 Tomosha qilish va yuklab olish imkoniyati mavjud!
"""

HELP_MESSAGE = """
📖 <b>Foydalanish qo'llanmasi</b>

━━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Kod orqali qidiruv:</b>
• <code>🆔 Kod orqali qidiruv</code> tugmasini bosing
• Anime kodini kiriting (masalan: <code>1</code>)

🎬 <b>Tomosha qilish:</b>
• Anime kartasidagi <b>🎬 Tomosha qilish</b> tugmasini bosing
• Kerakli qismni tanlang

📥 <b>Yuklab olish:</b>
• Anime kartasidagi <b>📥 Yuklab olish</b> tugmasini bosing
• Kerakli qismni tanlang

🖼 <b>Rasm orqali qidiruv:</b>
• <b>🖼 Rasm orqali qidiruv</b> tugmasini bosing
• Anime posteri yoki skrinshoti yuboring

📋 <b>Ro'yxat:</b>
• Barcha mavjud animelar ro'yxati

❓ Muammo bo'lsa: @admin bilan bog'laning
━━━━━━━━━━━━━━━━━━━━━━━━
"""

SUBSCRIPTION_MESSAGE = """
⚠️ <b>Majburiy obuna!</b>

Botdan foydalanish uchun kanalimizga obuna bo'ling:

📢 {channel}

Obuna bo'lgandan so'ng <b>✅ Tekshirish</b> tugmasini bosing.
"""

ADMIN_PANEL_MESSAGE = """
⚙️ <b>Admin Panel</b>

👤 Admin: <b>{name}</b>
🆔 ID: <code>{user_id}</code>

📊 Tizim holati:
• 👥 Foydalanuvchilar: <b>{users}</b>
• 🎬 Animeler: <b>{animes}</b>
• 🎞 Videolar: <b>{videos}</b>
• 🔍 Qidiruvlar: <b>{searches}</b>
"""
