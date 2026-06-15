"""
Staff (is_staff=True) foydalanuvchilar uchun qo'shimcha funksiyalar:
  👥 Mijozlar      — so'nggi mijozlar ro'yxati
  💰 Qarzdorlar    — qarzlari bor mijozlar
  📋 Mahsulotlar   — mahsulotlar va stok holati
  📈 Oylik hisobot — daromad va foyda hisoboti
"""
from aiogram import Router, F
from aiogram.types import Message
import api_client

router = Router()


@router.message(F.text == "👥 Mijozlar")
async def show_customers(message: Message):
    data = await api_client.get_customers_list()
    results = data.get('results', [])
    total = data.get('count', 0)

    if not results:
        await message.answer("👥 Hozircha mijozlar yo'q.")
        return

    lines = [f"👥 *Mijozlar (jami {total} ta, so'nggi {len(results)} ta):*\n"]
    for c in results[:15]:
        status_icon = {'active': '🟢', 'vip': '⭐', 'debtor': '🔴', 'inactive': '⚫'}.get(c.get('status', ''), '⚪')
        debt_uzs = float(c.get('debt_uzs', 0))
        debt_usd = float(c.get('debt_usd', 0))
        debt_str = ''
        if debt_uzs > 0 or debt_usd > 0:
            parts = []
            if debt_uzs > 0:
                parts.append(f"{debt_uzs:,.0f} UZS")
            if debt_usd > 0:
                parts.append(f"{debt_usd:,.2f} USD")
            debt_str = f" | 💳 {' + '.join(parts)}"
        lines.append(f"{status_icon} {c['name']} {c.get('phone','')}{debt_str}")

    await message.answer('\n'.join(lines), parse_mode='Markdown')


@router.message(F.text == "💰 Qarzdorlar")
async def show_debtors(message: Message):
    customers = await api_client.get_debtors()

    if not customers:
        await message.answer("✅ Hozircha qarzdor mijozlar yo'q!")
        return

    lines = [f"💰 *Qarzdorlar ({len(customers)} ta):*\n"]
    for c in customers[:20]:
        debt_uzs = float(c.get('debt_uzs', 0))
        debt_usd = float(c.get('debt_usd', 0))
        parts = []
        if debt_uzs > 0:
            parts.append(f"*{debt_uzs:,.0f} UZS*")
        if debt_usd > 0:
            parts.append(f"*{debt_usd:,.2f} USD*")
        debt_str = ' + '.join(parts) if parts else '0'
        lines.append(f"🔴 {c['name']} — {debt_str}")
        if c.get('phone'):
            lines[-1] += f" | 📱 {c['phone']}"

    await message.answer('\n'.join(lines), parse_mode='Markdown')


@router.message(F.text == "📋 Mahsulotlar")
async def show_products(message: Message):
    products = await api_client.get_products_list()

    if not products:
        await message.answer("📋 Mahsulotlar yo'q.")
        return

    lines = [f"📋 *Mahsulotlar ({len(products)} ta):*\n"]
    for p in products[:20]:
        qty = p.get('total_quantity', 0)
        status = p.get('status', '')
        icon = {'good': '🟢', 'low': '🟡', 'critical': '🔴'}.get(status, '⚪')
        variants = p.get('variants') or []
        lines.append(f"{icon} *{p['name']}* — jami {qty} dona ({len(variants)} variant)")
        for v in variants[:5]:
            cur = (v.get('currency') or 'uzs').upper()
            price = float(v.get('sale_price', 0))
            lines.append(
                f"    • {v['name']}: {v.get('quantity', 0)} {v.get('unit','dona')}"
                f" | {price:,.0f} {cur}"
            )

    await message.answer('\n'.join(lines), parse_mode='Markdown')


@router.message(F.text == "📈 Oylik hisobot")
async def show_monthly_report(message: Message):
    data = await api_client.get_profit_report()

    if not data:
        await message.answer("❌ Hisobot ma'lumotlari topilmadi.")
        return

    rev_uzs = float(data.get('revenue_uzs', 0))
    rev_usd = float(data.get('revenue_usd', 0))
    cost_uzs = float(data.get('sale_cost_uzs', 0))
    profit_uzs = float(data.get('gross_profit_uzs', 0))
    profit_usd = float(data.get('gross_profit_usd', 0))

    text = (
        f"📈 *Jami foyda hisoboti*\n\n"
        f"💰 Daromad:\n"
        f"  • UZS: *{rev_uzs:,.0f}*\n"
        f"  • USD: *{rev_usd:,.2f}*\n\n"
        f"📦 Tan narx (UZS): {cost_uzs:,.0f}\n\n"
        f"📊 Sof foyda:\n"
        f"  • UZS: *{profit_uzs:,.0f}*\n"
        f"  • USD: *{profit_usd:,.2f}*\n"
    )

    monthly = data.get('monthly', [])
    if monthly:
        text += "\n🗓 *Oylik ko'rsatkichlar:*\n"
        for m in monthly[-3:]:
            text += (
                f"  {m['month']}: "
                f"{float(m.get('revenue_uzs',0)):,.0f} UZS"
                f" + {float(m.get('revenue_usd',0)):,.2f} USD"
                f" ({m['count']} ta sotuv)\n"
            )

    await message.answer(text, parse_mode='Markdown')
