# Kwork Botlarini Ubuntu VPS ga Deploy qilish

## Nima bor?

| Fayl | Vazifa |
|------|--------|
| `kwork_monitor.py` | Django/Python proektlarini kuzatadi → Telegramga yuboradi |
| `kwork_inbox.py` | Yangi xabarlarni kuzatadi → Telegramga yuboradi |
| `kwork_stay_online.py` | Har 7-10 daqiqada sahifalarni aylanib, online ko'rinadi |

---

## 1. VPS ga ulanish

```bash
ssh root@YOUR_SERVER_IP
```

---

## 2. Tizimni yangilash va kerakli paketlarni o'rnatish

```bash
apt update && apt upgrade -y

# Python, pip, venv
apt install -y python3 python3-pip python3-venv

# Playwright uchun kerakli kutubxonalar
apt install -y \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 libxkbcommon0 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2
```

---

## 3. Fayllarni serverga yuklash

**Mahalliy kompyuterdan** (Mac/Linux terminalida):

```bash
scp -r ~/Desktop/kwork-online root@YOUR_SERVER_IP:/opt/kwork
```

Yoki git orqali (agar repo bo'lsa):
```bash
git clone YOUR_REPO /opt/kwork
```

---

## 4. Virtual muhit va kutubxonalar

```bash
cd /opt/kwork

python3 -m venv venv
source venv/bin/activate

pip install playwright aiohttp
python3 -m playwright install chromium
python3 -m playwright install-deps chromium
```

---

## 5. Test qilib ko'rish

```bash
cd /opt/kwork
source venv/bin/activate

# Har birini alohida test qiling
python3 kwork_stay_online.py
# Ctrl+C bilan to'xtatib, keyin boshqasini test qiling
```

---

## 6. Systemd service — avtomatik ishga tushurish

Har bir skript uchun alohida service yaratamiz.

### 6.1 Stay Online service

```bash
nano /etc/systemd/system/kwork-online.service
```

Quyidagini yozing:

```ini
[Unit]
Description=Kwork Stay Online
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kwork
ExecStart=/opt/kwork/venv/bin/python3 /opt/kwork/kwork_stay_online.py
Restart=always
RestartSec=30
StandardOutput=append:/opt/kwork/online.log
StandardError=append:/opt/kwork/online.log

[Install]
WantedBy=multi-user.target
```

### 6.2 Inbox Monitor service

```bash
nano /etc/systemd/system/kwork-inbox.service
```

```ini
[Unit]
Description=Kwork Inbox Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kwork
ExecStart=/opt/kwork/venv/bin/python3 /opt/kwork/kwork_inbox.py
Restart=always
RestartSec=30
StandardOutput=append:/opt/kwork/inbox.log
StandardError=append:/opt/kwork/inbox.log

[Install]
WantedBy=multi-user.target
```

### 6.3 Projects Monitor service

```bash
nano /etc/systemd/system/kwork-monitor.service
```

```ini
[Unit]
Description=Kwork Projects Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kwork
ExecStart=/opt/kwork/venv/bin/python3 /opt/kwork/kwork_monitor.py
Restart=always
RestartSec=30
StandardOutput=append:/opt/kwork/monitor.log
StandardError=append:/opt/kwork/monitor.log

[Install]
WantedBy=multi-user.target
```

---

## 7. Servicelarni yoqish va ishga tushirish

```bash
# Systemd ni yangilash
systemctl daemon-reload

# Servicelarni yoqish (server qayta ishga tushganda ham avtomatik start)
systemctl enable kwork-online kwork-inbox kwork-monitor

# Ishga tushirish
systemctl start kwork-online kwork-inbox kwork-monitor

# Holat tekshirish
systemctl status kwork-online kwork-inbox kwork-monitor
```

---

## 8. Loglarni kuzatish

```bash
# Barcha loglar bir vaqtda
tail -f /opt/kwork/online.log /opt/kwork/inbox.log /opt/kwork/monitor.log

# Faqat bitta log
tail -f /opt/kwork/inbox.log
```

---

## 9. Foydali buyruqlar

```bash
# To'xtatish
systemctl stop kwork-online kwork-inbox kwork-monitor

# Qayta ishga tushirish
systemctl restart kwork-online

# Oxirgi xatolarni ko'rish
journalctl -u kwork-inbox -n 50
```

---

## Muammolar va yechimlar

| Muamlo | Yechim |
|--------|--------|
| `playwright install` ishlmaydi | `python3 -m playwright install-deps` ni qayta run qiling |
| Service start bo'lmaydi | `journalctl -u kwork-online -n 30` bilan xatoni ko'ring |
| Login ishlamaydi | Email/parolni skript ichida tekshiring |
| Telegram xabar kelmaydi | Bot token va chat ID ni tekshiring |
