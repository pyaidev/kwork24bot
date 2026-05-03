# Kwork 24/7 Bot

Kwork.ru freelance platformasi uchun avtomatlashtirilgan Telegram bot. Proektlarni monitoring qiladi, Claude AI bilan taklif yozadi, online holatni saqlaydi.

## Imkoniyatlari

- **Proekt monitoring** — 18 ta kalit so'z bo'yicha yangi proektlarni qidiradi (har 5 daqiqa)
- **Claude AI javob** — proektga mos professional taklif + narx generatsiya qiladi
- **Tasdiqlash tizimi** — AI taklif Telegram ga yuboriladi, siz tasdiqlaysiz yoki bekor qilasiz
- **Inbox monitoring** — yangi xabarlarni kuzatib, Telegram ga xabar beradi (har 2 daqiqa)
- **Online tutish** — sahifalarni ochib, faollik ko'rsatadi (har 7-10 daqiqa)
- **SEO monitoring** — kworklaringiz qidiruv pozitsiyasini tekshiradi (har 6 soat)
- **Cookie auto-refresh** — session eskirmasligi uchun cookie yangilaydi (har 2 soat)
- **Anti-detection** — inson xatti-harakatini simulatsiya qiladi (scroll, mouse, typing delay)
- **Filtr** — faqat Предложений < 5 bo'lgan proektlar yuboriladi

## Texnologiyalar

- Python 3.12+
- Aiogram 3.x (Telegram Bot)
- Playwright (Web scraping)
- Anthropic Claude AI (Taklif generatsiyasi)
- systemd (Deployment)

## Strukturasi

```
kwork24bot/
├── bot.py                    # Entry point
├── app/
│   ├── core/
│   │   ├── config.py         # Sozlamalar, kalit so'zlar, prompt
│   │   └── state.py          # Global holat
│   ├── handlers/
│   │   ├── commands.py       # Telegram komandalar
│   │   └── callbacks.py      # Inline tugmalar
│   └── services/
│       ├── browser.py        # Playwright brauzer
│       ├── claude.py         # Claude AI integratsiya
│       ├── human.py          # Anti-detection simulatsiya
│       ├── kwork.py          # Kwork monitoring, SEO, javob
│       └── scheduler.py      # Background tasklar
├── get_cookies.py            # Cookie olish skripti
├── requirements.txt
└── .env                      # Maxfiy ma'lumotlar (gitda yo'q)
```

## O'rnatish

### 1. Clone va dependencies

```bash
git clone https://github.com/pyaidev/kwork24bot.git
cd kwork24bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

### 2. .env fayl yaratish

```bash
cp .env.example .env
```

```env
TELEGRAM_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id
COOKIES_FILE=cookies.json
CLAUDE_API_KEY=sk-ant-api03-...
```

### 3. Cookie olish

```bash
python get_cookies.py
```

Brauzer ochiladi, Kwork ga login qiling, terminalda ENTER bosing.

### 4. Ishga tushirish

```bash
python bot.py
```

### 5. Server deploy (systemd)

```bash
sudo cat > /etc/systemd/system/kwork-bot.service << EOF
[Unit]
Description=Kwork Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/kwork-bot
ExecStart=/root/kwork-bot/venv/bin/python bot.py
Restart=always
RestartSec=30
Environment=TZ=Europe/Moscow

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now kwork-bot
```

## Telegram komandalar

| Komanda | Tavsif |
|---------|--------|
| `/start` | Bosh menyu |
| `/status` | Bot holati |
| `/stats` | Statistika |
| `/projects` | Proektlarni tekshirish |
| `/inbox` | Inbox tekshirish |
| `/online` | Online ping |
| `/keywords` | Kalit so'zlar ro'yxati |
| `/addkw` | Kalit so'z qo'shish |
| `/delkw` | Kalit so'z o'chirish |
| `/autoresp` | AI javob yoqish/o'chirish |
| `/pending` | Kutayotgan javoblar |
| `/seo` | SEO pozitsiyalar |
| `/cookie` | Cookie yangilash |
| `/logs` | Oxirgi loglar |
| `/restart` | Brauzerni qayta tushirish |

## CI/CD

GitHub Actions orqali avtomatik deploy. `main` branch ga push qilinganda server avtomatik yangilanadi.
