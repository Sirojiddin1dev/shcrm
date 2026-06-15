# BalonCRM — Frontend uchun API hujjati

Bu hujjat frontend dasturchilari uchun. Backend bilan integratsiya qilish uchun kerakli barcha ma'lumotlar shu yerda.

---

## Mundarija

1. [Umumiy ma'lumot](#1-umumiy-malumot)
2. [Autentifikatsiya](#2-autentifikatsiya)
3. [Pagination va filtrlar](#3-pagination-va-filtrlar)
4. [Xatoliklar](#4-xatoliklar)
5. [Mahsulotlar](#5-mahsulotlar)
6. [Kategoriyalar](#6-kategoriyalar)
7. [Mijozlar](#7-mijozlar)
8. [Sotuvlar](#8-sotuvlar)
9. [Haridlar](#9-haridlar)
10. [Yetkazib beruvchilar](#10-yetkazib-beruvchilar)
11. [Hisobotlar](#11-hisobotlar)
12. [Telegram bot integratsiyasi](#12-telegram-bot-integratsiyasi)
13. [Ma'lumotnoma (enum qiymatlari)](#13-malumotnoma)

---

## 1. Umumiy ma'lumot

| Narsa | Qiymat |
|-------|--------|
| Base URL | `http://5.189.177.18/api` |
| Format | JSON |
| Kodlash | UTF-8 |
| Sana formati | ISO 8601 (`2026-05-15T10:30:00+05:00`) |
| Pul birligi | so'm (butun son, masalan `15000`) |

**Swagger interaktiv hujjat:** `http://5.189.177.18/api/docs/`
Bu yerda har bir endpointni brauzerdan sinab ko'rish mumkin.

---

## 2. Autentifikatsiya

Tizim **JWT (JSON Web Token)** ishlatadi. Login (`/auth/login/`) dan tashqari **barcha** so'rovlar token talab qiladi.

### 2.1. Login

```
POST /api/auth/login/
```

**So'rov:**
```json
{
  "phone": "+998111111111",
  "password": "nsdadmin123"
}
```

**Javob (200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiІ...",
  "refresh": "eyJhbGciOiJIUzI1NiІ...",
  "user": {
    "id": 1,
    "phone": "+998111111111",
    "full_name": "Admin",
    "is_staff": true,
    "created_at": "2026-05-15T09:00:00+05:00"
  }
}
```

**Xato (400):** telefon yoki parol noto'g'ri.

### 2.2. Tokenni so'rovlarda ishlatish

Har bir so'rovda header qo'shing:
```
Authorization: Bearer <access>
```

### 2.3. Tokenni yangilash

`access` token 1 kun amal qiladi. Tugagach `401` qaytadi — `refresh` orqali yangilang:

```
POST /api/auth/refresh/
```
```json
{ "refresh": "eyJhbGciOiJIUzI1NiІ..." }
```
**Javob:**
```json
{ "access": "yangi-access-token", "refresh": "yangi-refresh-token" }
```

> Tavsiya: `axios` interceptor yozing — `401` kelganda avtomatik `refresh` qiling, keyin so'rovni qайta yuboring. `refresh` ham ishlamasa — login sahifasiga yo'naltiring.

### 2.4. Joriy foydalanuvchi

```
GET /api/auth/me/
```
**Javob:** `user` obyekti (login dagi kabi).

### 2.5. Logout

```
POST /api/auth/logout/
```
```json
{ "refresh": "eyJhbGciOiJIUzI1NiІ..." }
```

---

## 3. Pagination va filtrlar

Ro'yxat qaytaradigan endpointlar **sahifalangan** (har sahifada 20 ta).

**Javob strukturasi:**
```json
{
  "count": 145,
  "next": "http://5.189.177.18/api/products/?page=2",
  "previous": null,
  "results": [ /* ... */ ]
}
```

**Sahifa tanlash:** `?page=2`

**Qidirish:** `?search=balon` (qaysi maydonlar bo'yicha — har bo'limда yozilgan)

**Tartiblash:** `?ordering=name` yoki `?ordering=-created_at` (`-` teskari tartib)

---

## 4. Xatoliklar

| Kod | Ma'nosi |
|-----|---------|
| 200 | OK |
| 201 | Yaratildi |
| 204 | O'chirildi (javob tanasi yo'q) |
| 400 | Noto'g'ri ma'lumot (validatsiya xatosi) |
| 401 | Token yo'q yoki eskirgan |
| 403 | Ruxsat yo'q |
| 404 | Topilmadi |
| 409 | Konflikt |

**Validatsiya xatosi (400) namunasi:**
```json
{
  "phone": ["Bu maydon majburiy."],
  "items": ["Kamida bitta mahsulot kerak"]
}
```

**Umumiy xato namunasi:**
```json
{ "detail": "Telefon yoki parol noto'g'ri" }
```

---

## 5. Mahsulotlar

### 5.1. Ro'yxat

```
GET /api/products/
```
**Filtrlar:** `?category=1`, `?unit=dona`, `?search=balon`, `?ordering=sale_price`

**Javob (`results` ichidagi obyekt — qisqartirilgan):**
```json
{
  "id": 1,
  "name": "Qizil balon 12\"",
  "category_name": "Balon",
  "sale_price": "15000.00",
  "quantity": 45,
  "unit": "dona",
  "status": "good"
}
```

`status`: `good` (yetarli) | `low` (kam qoldi) | `critical` (tugadi/juda kam).

### 5.2. Bitta mahsulot

```
GET /api/products/{id}/
```
**Javob (to'liq):**
```json
{
  "id": 1,
  "name": "Qizil balon 12\"",
  "category": 2,
  "category_name": "Balon",
  "cost_price": "9000.00",
  "sale_price": "15000.00",
  "quantity": 45,
  "unit": "dona",
  "low_stock_threshold": 5,
  "status": "good",
  "image": "http://5.189.177.18/media/products/qizil.jpg",
  "barcode": "4780000000001",
  "description": "",
  "is_active": true,
  "created_at": "2026-05-01T10:00:00+05:00",
  "updated_at": "2026-05-10T12:00:00+05:00"
}
```

> `cost_price` — tan narx (sotib olish narxi), `sale_price` — sotuv narxi. Sof foyda shu ikkisi farqidan hisoblanadi.

### 5.3. Yaratish / tahrirlash / o'chirish

```
POST   /api/products/         — yangi
PUT    /api/products/{id}/    — to'liq tahrirlash
PATCH  /api/products/{id}/    — qisman tahrirlash
DELETE /api/products/{id}/    — o'chirish
```

**POST/PUT tanasi:**
```json
{
  "name": "Yangi balon",
  "category": 2,
  "cost_price": 8000,
  "sale_price": 13000,
  "quantity": 100,
  "unit": "dona",
  "low_stock_threshold": 10,
  "barcode": "",
  "description": ""
}
```

> Rasm yuklash uchun `multipart/form-data` ishlating (`image` maydoni). Boshqa hollarda JSON.

### 5.4. Maxsus endpointlar

```
GET /api/products/low_stock/   — kam qolgan mahsulotlar (status low/critical)
GET /api/products/for_sale/    — sotuv formasi uchun (faqat quantity > 0)
```

`for_sale` javobi (sodda massiv, pagination yo'q):
```json
[
  { "id": 1, "name": "Oddiy balon", "sale_price": "5000.00",
    "cost_price": "3000.00", "quantity": 10, "unit": "dona" }
]
```

---

## 6. Kategoriyalar

```
GET    /api/products/categories/        — ro'yxat
POST   /api/products/categories/        — yangi
GET    /api/products/categories/{id}/   — bitta
PUT    /api/products/categories/{id}/   — tahrirlash
DELETE /api/products/categories/{id}/   — o'chirish
```

**Obyekt:**
```json
{ "id": 2, "name": "Balon", "product_count": 12, "created_at": "..." }
```

**POST tanasi:** `{ "name": "Folga" }`

---

## 7. Mijozlar

### 7.1. Ro'yxat

```
GET /api/customers/
```
**Filtrlar:** `?status=vip`, `?search=Ali`, `?ordering=-debt`

**Obyekt (`results` ichida):**
```json
{
  "id": 1,
  "name": "Dilshodbek",
  "phone": "+998 90 123 45 67",
  "debt": "1200000.00",
  "total_spent": "12450000.00",
  "status": "debtor",
  "status_display": "Qarzdor",
  "is_linked": true
}
```

`is_linked` — mijoz Telegram botga ulanganmi (xabarlar boradi).

### 7.2. Bitta mijoz

```
GET /api/customers/{id}/
```
```json
{
  "id": 1,
  "name": "Dilshodbek",
  "phone": "+998 90 123 45 67",
  "address": "Toshkent, Chilonzor",
  "debt": "1200000.00",
  "total_spent": "12450000.00",
  "status": "debtor",
  "status_display": "Qarzdor",
  "telegram_chat_id": "123456789",
  "is_linked": true,
  "link_token": "AbCdEf123456",
  "notifications_enabled": true,
  "last_debt_reminder_at": "2026-05-12T10:00:00+05:00",
  "note": "",
  "created_at": "...",
  "updated_at": "..."
}
```

### 7.3. Yaratish / tahrirlash / o'chirish

```
POST   /api/customers/
PUT    /api/customers/{id}/
PATCH  /api/customers/{id}/
DELETE /api/customers/{id}/
```

**POST tanasi:**
```json
{
  "name": "Yangi mijoz",
  "phone": "+998901112233",
  "address": "Toshkent",
  "note": ""
}
```

> `debt` ni qo'lda yuborish mumkin (boshlang'ich qarz). `total_spent` faqat o'qiladi — sotuvlardan avtomatik hisoblanadi.

### 7.4. Maxsus endpointlar

```
GET  /api/customers/debtors/   — qarzdor mijozlar (debt > 0)
GET  /api/customers/vip/       — VIP mijozlar
```

**Qarzdan to'lov qabul qilish:**
```
POST /api/customers/{id}/pay-debt/
```
```json
{ "amount": 500000, "note": "Naqd to'lov" }
```
**Javob:**
```json
{ "detail": "To'lov qabul qilindi", "paid": 500000.0, "remaining_debt": 700000.0 }
```
> Bu mijozning qarzini kamaytiradi va unга Telegram orqali tasdiq xabari yuboradi (ulangan bo'lsa).

---

## 8. Sotuvlar

### 8.1. Ro'yxat

```
GET /api/sales/
```
**Filtrlar:**
- `?date_from=2026-05-01&date_to=2026-05-31` — sana oralig'i
- `?payment_method=cash` — to'lov turi
- `?customer=1` — mijoz bo'yicha
- `?ordering=-created_at`

**Obyekt (`results` ichida):**
```json
{
  "id": 42,
  "customer_name": "Dilshodbek",
  "total": "75000.00",
  "discount": "0.00",
  "payment_method_display": "Naqd",
  "item_count": 3,
  "created_at": "2026-05-15T14:30:00+05:00"
}
```

### 8.2. Bitta sotuv (to'liq)

```
GET /api/sales/{id}/
```
```json
{
  "id": 42,
  "customer": 1,
  "customer_name": "Dilshodbek",
  "items": [
    {
      "id": 100,
      "product": 1,
      "product_name": "Qizil balon 12\"",
      "quantity": 3,
      "price": "15000.00",
      "cost_price": "9000.00",
      "subtotal": "45000.00"
    }
  ],
  "total": "45000.00",
  "discount": "0.00",
  "profit": "18000.00",
  "payment_method": "cash",
  "payment_method_display": "Naqd",
  "note": "",
  "created_at": "2026-05-15T14:30:00+05:00"
}
```

> `profit` — shu sotuvning sof foydasi = `total` − (har bandning `cost_price` × `quantity`).

### 8.3. Yangi sotuv yaratish

```
POST /api/sales/
```
**So'rov tanasi:**
```json
{
  "customer": 1,
  "items": [
    { "product": 1, "quantity": 3, "price": 15000 },
    { "product": 5, "quantity": 1, "price": 8000 }
  ],
  "discount": 0,
  "payment_method": "cash",
  "note": ""
}
```

**Muhim qoidalar:**
- `customer` — ixtiyoriy (`null` bo'lsa "noma'lum mijoz" sotuvi).
- `items[].price` — **majburiy**. Bu mahsulot sotuv narxi, foydalanuvchi formada **o'zgartirishi mumkin**. Standart qiymat sifatida mahsulotning `sale_price` ini ko'rsating, lekin user uni tahrirlay olsin.
- `quantity` — mahsulot omborida yetarli bo'lishi kerak, aks holда `400` xato.
- `payment_method` — `cash` | `card` | `debt` | `transfer`. `debt` bo'lsa mijoz qarziga yoziladi.
- `total` ni yuborish **shart emas** — backend o'zi hisoblaydi (`items` summasi − `discount`).

**Javob (201):** to'liq sotuv obyekti (8.2 dagi kabi).

**Avtomatik amallar:** ombordan kamayadi · mijoz qarzi/xaridi yangilanadi · mijozga Telegram chek yuboriladi (ulangan bo'lsa).

### 8.4. O'chirish

```
DELETE /api/sales/{id}/
```

---

## 9. Haridlar

Harid = mahsulotni omborga kiritish (yetkazib beruvchidan sotib olish). **Frontentда yangi qo'shiladigan bo'lim.**

### 9.1. Ro'yxat

```
GET /api/purchases/
```
**Filtrlar:** `?date_from=...&date_to=...`, `?supplier=1`, `?payment_method=cash`

**Obyekt (`results` ichida):**
```json
{
  "id": 7,
  "supplier_name": "Optom baza",
  "total": "800000.00",
  "payment_method_display": "Naqd",
  "item_count": 2,
  "created_at": "2026-05-14T11:00:00+05:00"
}
```

### 9.2. Bitta harid (to'liq)

```
GET /api/purchases/{id}/
```
```json
{
  "id": 7,
  "supplier": 1,
  "supplier_name": "Optom baza",
  "items": [
    {
      "id": 20,
      "product": 1,
      "product_name": "Qizil balon 12\"",
      "quantity": 100,
      "cost_price": "9000.00",
      "subtotal": "900000.00"
    }
  ],
  "total": "900000.00",
  "payment_method": "cash",
  "payment_method_display": "Naqd",
  "note": "",
  "created_at": "2026-05-14T11:00:00+05:00"
}
```

### 9.3. Yangi harid yaratish

```
POST /api/purchases/
```
**So'rov tanasi:**
```json
{
  "supplier": 1,
  "items": [
    { "product": 1, "quantity": 100, "cost_price": 9000 },
    { "product": 5, "quantity": 50, "cost_price": 5000 }
  ],
  "payment_method": "cash",
  "note": ""
}
```

**Harid formasi qanday ishlashi kerak (frontend):**
1. Mahsulot tanlanadi (`GET /api/products/` dan).
2. **Qancha olingani** — `quantity` kiritiladi.
3. **Nech puldan olingani** — `cost_price` kiritiladi (dona narxi).
4. Bir nechta mahsulot qo'shish mumkin.
5. `total` avtomatik = Σ(`cost_price` × `quantity`).

**Avtomatik amallar:**
- Mahsulot **omboriga qo'shiladi** (`quantity` oshadi).
- Mahsulotning `cost_price` (tan narxi) yangi qiymatga **yangilanadi** — bu keyingi sotuvlarda sof foydani to'g'ri hisoblash uchun.

**Javob (201):** to'liq harid obyekti.

> `supplier` — ixtiyoriy (`null` bo'lsa "noma'lum yetkazuvchi").

### 9.4. O'chirish

```
DELETE /api/purchases/{id}/
```

---

## 10. Yetkazib beruvchilar

```
GET    /api/purchases/suppliers/        — ro'yxat
POST   /api/purchases/suppliers/        — yangi
GET    /api/purchases/suppliers/{id}/   — bitta
PUT    /api/purchases/suppliers/{id}/   — tahrirlash
DELETE /api/purchases/suppliers/{id}/   — o'chirish
```

**Obyekt:**
```json
{
  "id": 1,
  "name": "Optom baza",
  "phone": "+998901112233",
  "address": "Toshkent, Sebzor",
  "note": "",
  "created_at": "..."
}
```

---

## 11. Hisobotlar

### 11.1. Dashboard

```
GET /api/reports/dashboard/?period=today
```
**`period`:** `today` | `7kun` | `oylik` | `yillik`

**Javob:**
```json
{
  "revenue": 150000.0,
  "profit": 45000.0,
  "purchase_total": 800000.0,
  "sales_count": 12,
  "debt": 2100000.0,
  "daily_sales": [
    { "date": "08:00", "amount": 15000.0 },
    { "date": "10:00", "amount": 25000.0 }
  ],
  "top_products": [
    { "name": "Katta figurniy balon", "quantity": 18, "revenue": 450000.0 }
  ],
  "top_customers": [
    { "name": "Ali Valiyev", "spent": 320000.0, "orders": 12 }
  ]
}
```

| Maydon | Ma'nosi |
|--------|---------|
| `revenue` | Daromad (sotuvlar jami) |
| `profit` | Sof foyda (daromad − tan narx) |
| `purchase_total` | Haridlarga sarflangan |
| `sales_count` | Sotuvlar soni |
| `debt` | Barcha mijozlar jami qarzi |
| `daily_sales` | Grafik uchun (period `today` da soatlar, qolganda sanalar) |
| `top_products` | Eng ko'p sotilgan 5 mahsulot |
| `top_customers` | Eng ko'p xarid qilgan 5 mijoz |

### 11.2. Foyda hisoboti

```
GET /api/reports/profit/?date_from=2026-05-01&date_to=2026-05-31
```
**Javob:**
```json
{
  "revenue": 5400000.0,
  "purchase_cost": 3200000.0,
  "sale_cost": 3550000.0,
  "gross_profit": 1850000.0,
  "net_profit": 1850000.0,
  "monthly": [
    { "month": "2026-05", "revenue": 5400000.0, "count": 340 }
  ]
}
```

| Maydon | Ma'nosi |
|--------|---------|
| `revenue` | Sotuvlardan tushgan daromad |
| `sale_cost` | Sotilgan mahsulotlarning tan narxi |
| `purchase_cost` | Davr ichida haridlarga sarflangan |
| `net_profit` | **Sof foyda** = `revenue` − `sale_cost` |

> Sof foyda **sotilgan** mahsulotlar tan narxiga asoslanadi (harid summasiga emas). Chunki harid qilingan mahsulot hali sotilmagan bo'lishi mumkin.

### 11.3. Ombor holati

```
GET /api/reports/warehouse/
```
**Javob:**
```json
{
  "total_products": 48,
  "total_value": 12500000.0,
  "low_stock_count": 4,
  "low_stock": [
    { "id": 3, "name": "Geliy ballon", "quantity": 5, "status": "critical" }
  ]
}
```

---

## 12. Telegram bot integratsiyasi

Frontend bu endpointlarni mijoz kartochkasida ishlatadi — mijozni botga ulash uchun.

### 12.1. Mijozga botga ulanish linkini olish

```
GET /api/customers/{id}/bot-link/
```
**Javob:**
```json
{
  "token": "AbCdEf123456",
  "deep_link": "https://t.me/baloncrm_bot?start=cust_AbCdEf123456",
  "is_linked": false,
  "telegram_chat_id": null
}
```

Mijoz kartochkasida `deep_link` ni ko'rsating — uni SMS/WhatsApp orqali mijozга yuborish yoki QR kod qilib chop etish mumkin. Mijoz linkni bossa, bot uни avtomatik bog'laydi.

### 12.2. Botdan ajratish

```
POST /api/customers/{id}/unlink/
```
**Javob:** `{ "detail": "Aloqa uzildi" }`

### 12.3. Qo'lda qarz eslatma yuborish

```
POST /api/customers/{id}/send-debt-reminder/
```
**Javob (200):** `{ "detail": "Eslatma yuborildi" }`
**Xato (400):** mijoz botga ulanmagan yoki qarzi yo'q.

### 12.4. Xabarlar mijozга qachon boradi (avtomatik)

| Hodisa | Xabar |
|--------|-------|
| Sotuv yaratildi (`POST /api/sales/`) | 🧾 Sotuv cheki |
| Qarz to'landi (`POST .../pay-debt/`) | ✅ To'lov tasdig'i |
| Qo'lda eslatma | ⏰ Qarz eslatma |

> Mijoz `is_linked: true` bo'lsa va `notifications_enabled: true` bo'lsa xabarlar boradi. Frontend bularni mijoz kartochkasida ko'rsatishi va `notifications_enabled` ni toggle qilishi mumkin (`PATCH /api/customers/{id}/`).

### 12.5. Bot foydalanuvchilari (xodimlar) — ixtiyoriy

Agar admin panelda Telegram bot xodimlarini boshqarmoqchi bo'lsangiz:

```
GET    /api/bot-users/              — ro'yxat
POST   /api/bot-users/              — qo'shish
GET    /api/bot-users/{chat_id}/    — tekshirish
DELETE /api/bot-users/{chat_id}/    — o'chirish
```
**Obyekt:** `{ id, chat_id, full_name, username, is_active, added_by, created_at, updated_at }`

---

## 13. Ma'lumotnoma

### To'lov turlari (`payment_method`)
| Kod | Nomi |
|-----|------|
| `cash` | Naqd |
| `card` | Karta |
| `debt` | Nasiya |
| `transfer` | O'tkazma |

### Mahsulot birligi (`unit`)
| Kod | Nomi |
|-----|------|
| `dona` | Dona |
| `kg` | Kg |
| `litr` | Litr |
| `metr` | Metr |

### Mahsulot holati (`status`) — faqat o'qiladi
| Kod | Nomi | Sharti |
|-----|------|--------|
| `good` | Yetarli | `quantity > low_stock_threshold` |
| `low` | Kam qoldi | `0 < quantity <= low_stock_threshold` |
| `critical` | Tugadi | `quantity <= 0` |

### Mijoz holati (`status`)
| Kod | Nomi | Sharti |
|-----|------|--------|
| `active` | Faol | oddiy mijoz |
| `vip` | VIP | `total_spent >= 1 000 000` |
| `debtor` | Qarzdor | `debt > 0` |
| `inactive` | Nofaol | qo'lda belgilanadi |

> `status` sotuv/to'lovdan keyin avtomatik yangilanadi. Qo'lda ham `PATCH` bilan o'zgartirish mumkin.

### Hisobot davri (`period`)
`today` | `7kun` | `oylik` | `yillik`

---

## Frontend uchun integratsiya tartibi

1. **Login sahifasi** — `/auth/login/`, tokenни `localStorage` ga saqlang.
2. **Axios instance** — `baseURL` + `Authorization` header + `401` interceptor (refresh).
3. **Dashboard** — `/reports/dashboard/?period=today`.
4. **Mahsulotlar** — `/products/`, kategoriyalar `/products/categories/`.
5. **Mijozlar** — `/customers/`, qarz to'lash `/customers/{id}/pay-debt/`.
6. **Sotuv** — `/products/for_sale/` dan mahsulot tanlanadi, `price` tahrirlanadi, `/sales/` ga POST.
7. **Harid (yangi bo'lim)** — `/products/` dan tanlanadi, `quantity` + `cost_price` kiritiladi, `/purchases/` ga POST.
8. **Hisobot** — `/reports/profit/` sof foyda uchun.
9. **Bot ulash** — mijoz kartochkasida `/customers/{id}/bot-link/` linkini ko'rsating.

Savol bo'lsa — Swagger (`/api/docs/`) da har bir endpointni jonli sinab ko'ring.
