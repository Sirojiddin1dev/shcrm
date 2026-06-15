#!/bin/bash
# BalonCRM serverga o'rnatish scripti
# Ubuntu 22.04 uchun
# Ishlatish: bash deploy.sh

set -e

PROJECT_DIR="/var/www/bcrm"
BACKEND_DIR="$PROJECT_DIR/backend"
BOT_DIR="$PROJECT_DIR/bot"

echo "=== BalonCRM o'rnatish ==="

# 1. Paketlarni yangilash
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3-pip nginx

# 2. Loyiha papkasini yaratish
mkdir -p $PROJECT_DIR
mkdir -p /var/log/bcrm

# 3. Fayllarni ko'chirish (agar hali ko'chirilmagan bo'lsa)
# rsync -av ./backend/ $BACKEND_DIR/
# rsync -av ./bot/ $BOT_DIR/
# cp ./nginx.conf /etc/nginx/sites-available/bcrm

echo "Fayllarni $PROJECT_DIR ga ko'chiring..."
echo "Keyin davom eting:"

# 4. Backend virtual environment
cd $BACKEND_DIR
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 5. .env fayl yaratish (namunadan)
if [ ! -f .env ]; then
    cp .env.example .env
    echo "!!! .env faylini to'ldiring: nano $BACKEND_DIR/.env"
fi

# 6. Django migrate va static
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput

# 7. Superuser yaratish
echo "Superuser yaratish:"
python manage.py shell -c "
from apps.users.models import User
if not User.objects.filter(phone='+998111111111').exists():
    User.objects.create_superuser(phone='+998111111111', password='nsdadmin123')
    print('Superuser yaratildi')
else:
    print('Superuser mavjud')
"

# 8. Gunicorn systemd service
cat > /etc/systemd/system/bcrm-backend.service << 'EOF'
[Unit]
Description=BalonCRM Django Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/bcrm/backend
ExecStart=/var/www/bcrm/backend/venv/bin/gunicorn config.wsgi:application -c gunicorn.conf.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 9. Bot systemd service
cat > /etc/systemd/system/bcrm-bot.service << 'EOF'
[Unit]
Description=BalonCRM Telegram Bot
After=network.target bcrm-backend.service

[Service]
User=www-data
WorkingDirectory=/var/www/bcrm/bot
ExecStart=/var/www/bcrm/bot/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 10. Bot virtual environment
cd $BOT_DIR
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 11. Bot .env
if [ ! -f $BOT_DIR/.env ]; then
    cp $BOT_DIR/.env.example $BOT_DIR/.env
    echo "!!! Bot .env faylini to'ldiring: nano $BOT_DIR/.env"
fi

# 12. Nginx konfiguratsiya
ln -sf /etc/nginx/sites-available/bcrm /etc/nginx/sites-enabled/bcrm
rm -f /etc/nginx/sites-enabled/default
nginx -t

# 13. Servicelarni ishga tushirish
chown -R www-data:www-data $PROJECT_DIR
systemctl daemon-reload
systemctl enable bcrm-backend bcrm-bot
systemctl start bcrm-backend
systemctl start bcrm-bot
systemctl restart nginx

echo ""
echo "=== O'rnatish tugadi ==="
echo "Backend: http://5.189.177.18/api/"
echo "Admin panel: http://5.189.177.18/admin/"
echo ""
echo "Status tekshirish:"
echo "  systemctl status bcrm-backend"
echo "  systemctl status bcrm-bot"
