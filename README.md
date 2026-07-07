# Anime Bot - Professional Telegram Bot

## Loyiha haqida
Python va aiogram 3.x yordamida yozilgan professional Telegram anime boti.
SQLite ma'lumotlar bazasidan foydalanadi.

---

## 📁 Loyiha strukturasi
```
anime_bot/
├── main.py                    # Botning asosiy kirish nuqtasi
├── requirements.txt           # Kutubxonalar
├── .env                       # Token va sozlamalar (yaratishingiz kerak)
├── bot.log                    # Log fayli (avtomatik yaratiladi)
│
└── bot/
    ├── config.py              # Konfiguratsiya
    │
    ├── database/
    │   └── db.py              # SQLite asinxron operatsiyalar
    │
    ├── handlers/
    │   ├── user_handler.py    # Foydalanuvchi handlerlari
    │   └── admin_handler.py   # Admin handlerlari
    │
    ├── keyboards/
    │   ├── user_keyboards.py  # Foydalanuvchi klaviaturalari
    │   └── admin_keyboards.py # Admin klaviaturalari
    │
    ├── states/
    │   └── admin_states.py    # FSM holatlari
    │
    └── utils/
        └── helpers.py         # Yordamchi funksiyalar
```

---

## ⚙️ O'rnatish va ishga tushirish

### 1. Python virtual muhit yaratish
```bash
cd E:\anime_bot
python -m venv venv
venv\Scripts\activate
```

### 2. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. .env faylini sozlash
`.env` faylini oching va quyidagilarni kiriting:
```
BOT_TOKEN=sizning_bot_tokeningiz
ADMIN_IDS=sizning_telegram_id_ingiz
```

**Bot token olish:** @BotFather da `/newbot` komandasi bilan.  
**Telegram ID olish:** @userinfobot dan.

### 4. Botni ishga tushirish
```bash
python main.py
```

---

## 🎮 Foydalanish

### Oddiy foydalanuvchi
| Amal | Natija |
|------|--------|
| `1` yozish | 1-kodli anime kartochkasi chiqadi |
| `🎬 Tomosha qilish` | Qismlar ro'yxati (4 ustunli) |
| `📥 Yuklab olish` | Qismlar ro'yxati (download uchun) |
| Qism tugmasi | Video yuboriladi |

### Admin panel (`/admin`)
| Tugma | Vazifasi |
|-------|----------|
| `➕ Anime qo'shish` | 7 bosqichli anime qo'shish |
| `🎬 Qism yuklash` | Video yuklash va file_id saqlash |
| `✏️ Tahrirlash` | Anime maydonlarini o'zgartirish |
| `🗑 O'chirish` | Anime va qismlarini o'chirish |
| `📋 Animlar ro'yxati` | Barcha animeler ro'yxati |

---

## 🗄️ Ma'lumotlar bazasi

**`animes` jadvali:**
| Ustun | Turi | Tavsif |
|-------|------|--------|
| id | INTEGER | Auto ID |
| code | INTEGER | Unikal kod (1, 2, 3...) |
| name | TEXT | Anime nomi |
| poster | TEXT | Telegram photo file_id |
| genre | TEXT | Janr |
| language | TEXT | Til |
| description | TEXT | Tavsif |
| episodes | INTEGER | Qismlar soni |

**`episodes` jadvali:**
| Ustun | Turi | Tavsif |
|-------|------|--------|
| id | INTEGER | Auto ID |
| anime_id | INTEGER | Anime FK |
| episode_num | INTEGER | Qism raqami |
| file_id | TEXT | Telegram video file_id |

---

## 📝 Muhim eslatmalar

- **file_id** — video bir marta yuborilsa, Telegram server saqlaydi. Keyin faqat shu ID orqali yuboriladi.
- **Admin qo'shish** — `.env` faylidagi `ADMIN_IDS` ga Telegram ID larini qo'shing.
- **Video yuklash** — Video fayl sifatida (document) yuborsangiz, sifat yo'qolmaydi.
- **Poster** — Admin poster rasmini oddiy foto sifatida yuboradi.
