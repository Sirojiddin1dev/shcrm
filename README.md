# BalonCRM — Backend, Bot, Notifications

Balon/bezak do'koni uchun to'liq CRM tizim:
- **Django REST API** (JWT auth, Swagger, sotuv/harid/hisobot)
- **Telegram bot** — xodimlar uchun (sotuv/harid qabul qilish) **va** mijozlar uchun (chek, qarz, tarix)
- **Avtomatik xabarlar** — sotuv cheklari, qarz eslatmalari, to'lov tasdiqlari Telegram orqali (SMS o'rniga)

## Loyiha tuzilmasi

```
bcrm/
├── backend/
│   ├── apps/
│   │   ├── users/        # User + TelegramBotUser (xodimlar)
│   │   ├── products/
│   │   ├── customers/    # Customer + link_token, services.py, cron
│   │   ├── sales/        # Sotuv yaratilganda chek yuboradi
│   │   ├── purchases/
│   │   └── reports/
│   ├── config/
│   └── manage.py
├── bot/
│   ├── handlers/
│   │   ├── customer_handler.py   # /start deep link, contact share, mijoz menyusi
│   │   ├── admin_handler.py       # /adduser, /removeuser, /users
│   │   ├── sale_handler.py
│   │   ├── purchase_handler.py
│   │   └── stats_handler.py
│   └── main.py                    # 4-bosqichli AccessMiddleware
├── nginx.conf
└── deploy.sh                      # + cron (har kuni 10:00 da qarz eslatma)
```

## Swagger / API docs

| URL | Tavsif |
|-----|--------|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI JSON |

## Asosiy API endpointlar

### Auth
- `POST /api/auth/login/` — JWT olish

### Mahsulot, mijoz, sotuv, harid
- `GET/POST /api/products/`
- `GET/POST /api/products/variants/` — mahsulot variantlari (rang, o'lcham va h.k.)
- `GET/POST /api/customers/`
- `GET/POST /api/sales/`
- `GET/POST /api/purchases/`

### Mahsulot variantlari (rang / o'lcham)

Mahsulot **variantli** yoki **variantsiz** bo'lishi mumkin (orqaga moslik saqlangan):

- **Variantsiz mahsulot** — qoldiq (ostatka) `Product.quantity` da, avvalgidek ishlaydi.
- **Variantli mahsulot** — qoldiq har bir variantda alohida (`ProductVariant.quantity`),
  `Product.quantity` esa faol variantlar yig'indisi sifatida avtomatik hisoblanadi.
  Variant narxi (`cost_price`/`sale_price`) `0` bo'lsa — mahsulot narxidan olinadi.

Variantlarni mahsulot bilan birga (`POST /api/products/` ichida `variants: [...]`) yoki
alohida (`/api/products/variants/`) boshqarish mumkin.

**Sotuv/harid bandlarida** ixtiyoriy `variant` maydoni:
- Variant berilsa — qoldiq shu variantdan kamayadi (sotuv) yoki ko'payadi (harid).
- Variantli mahsulotni variantsiz sotish/harid qilish — xatolik (variant majburiy).
- `for_sale` endpoint har mahsulot uchun `has_variants` va `variants[]` ni qaytaradi.

### Telegram bot user (xodimlar)
- `GET/POST /api/bot-users/`
- `GET /api/bot-users/<chat_id>/` — ruxsat tekshirish
- `DELETE /api/bot-users/<chat_id>/`

### Mijozni botga bog'lash
- `POST /api/customers/link-by-phone/` — bot ishlatadi (contact share)
- `POST /api/customers/link-by-token/` — bot ishlatadi (deep link)
- `GET /api/customers/by-chat-id/<chat_id>/` — bot ishlatadi
- `GET /api/customers/{id}/bot-link/` — admin ishlatadi (link yaratish)
- `POST /api/customers/{id}/unlink/` — aloqa uzish
- `POST /api/customers/{id}/send-debt-reminder/` — qo'lda eslatma
- `POST /api/customers/{id}/pay-debt/` — qarz to'lov + tasdiq xabari

## Mijozni botga bog'lash usullari

### 1) Deep link (asosiy usul)
Admin panelda mijoz sahifasidagi `link` ni mijozga jo'natadi (SMS/WhatsApp):
```
https://t.me/your_bot?start=cust_AbCdEf123...
```
Mijoz bossa — bot avtomatik biriktiradi. Hech qanday ma'lumot kiritmasligi shart.

### 2) Telefon raqami orqali
Mijoz `/start` deydi → "📱 Telefon raqamim bilan ulanish" tugmasini bosadi → Telegram contact ulashadi → bot CRM dagi mijozni telefon bo'yicha topib bog'laydi.

## Avtomatik xabarlar

| Hodisa | Xabar | Kim yuboradi |
|--------|-------|-------------|
| Sotuv yaratildi | 🧾 Chek (mahsulotlar, summa, qarz) | Backend (sale create) |
| Qarz to'landi | ✅ "To'lov qabul qilindi" | Backend (`/pay-debt/`) |
| Qo'lda eslatma | ⏰ Qarz eslatma | Admin panel yoki `/send-debt-reminder/` |

## Qarz eslatmalari

Qarz eslatmalari **qo'lda** yuboriladi:
- **Admin panel** — Mijozlar ro'yxatida kerakli mijozlarni belgilab "Tanlanganlarga eslatma yuborish" amalini tanlash
- **API** — `POST /api/customers/{id}/send-debt-reminder/`

Ommaviy yuborish kerak bo'lsa, qo'lda command ishlatish mumkin:
```bash
python manage.py send_debt_reminders --min-debt=10000 --dry-run
```

## Bot rejimlari (AccessMiddleware)

| Foydalanuvchi | Ruxsat |
|---------------|--------|
| Admin (`ADMIN_CHAT_IDS`) | Hammasi |
| Xodim (`TelegramBotUser`) | Sotuv, harid, statistika |
| Mijoz (`Customer.telegram_chat_id`) | Faqat o'z qarzi va sotuvlar tarixi |
| Boshqa | Faqat `/start`, `/myid` |

## Bot buyruqlari

**Admin:** `/adduser <id> [ism]`, `/removeuser <id>`, `/users`, `/help`
**Hamma:** `/start`, `/myid`

## O'rnatish

```bash
# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME ni to'ldiring
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Bot (alohida terminal)
cd bot
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # ADMIN_CHAT_IDS ni to'ldiring
python main.py
```

## Default login (frontend / API)
- Telefon: `+998 11 111 11 11`
- Parol: `nsdadmin123`
