from aiogram import Router, F
from aiogram.types import Message
import api_client

router = Router()


@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    data = await api_client.get_dashboard()
    text = (
        f"📊 *Bugungi statistika*\n\n"
        f"💰 Daromad: *{float(data['revenue']):,.0f} so'm*\n"
        f"📈 Sof foyda: *{float(data['profit']):,.0f} so'm*\n"
        f"🛒 Sotuvlar soni: *{data['sales_count']} ta*\n"
        f"💸 Jami qarz: *{float(data.get('debt_uzs',0)):,.0f} UZS"
        f"{(' + ' + str(round(float(data.get('debt_usd',0)),2)) + ' USD') if float(data.get('debt_usd',0)) else ''}*\n"
    )
    if data.get('top_products'):
        text += "\n🏆 *Top mahsulotlar:*\n"
        for i, p in enumerate(data['top_products'][:3], 1):
            text += f"  {i}. {p['name']} - {float(p['revenue']):,.0f} so'm\n"
    await message.answer(text, parse_mode='Markdown')


@router.message(F.text == "🏪 Ombor holati")
async def show_warehouse(message: Message):
    from config import API_BASE_URL
    warehouse, _ = await api_client._get(f'{API_BASE_URL}/reports/warehouse/')

    value_uzs = float(warehouse.get('total_value_uzs', 0) or 0)
    value_usd = float(warehouse.get('total_value_usd', 0) or 0)
    value_line = f"{value_uzs:,.0f} so'm"
    if value_usd:
        value_line += f" + {value_usd:,.2f} $"
    text = (
        f"🏪 *Ombor holati*\n\n"
        f"📦 Jami mahsulotlar: *{warehouse['total_products']} tur*"
        f" ({warehouse.get('total_variants', 0)} variant)\n"
        f"💰 Ombor qiymati: *{value_line}*\n"
        f"⚠️ Kam qolganlar: *{warehouse['low_stock_count']} variant*\n"
    )
    if warehouse.get('low_stock'):
        text += "\n⚠️ *Kam qolgan mahsulotlar:*\n"
        for p in warehouse['low_stock'][:10]:
            emoji = "🔴" if p['status'] == 'critical' else "🟡"
            text += f"  {emoji} {p['name']}: {p['quantity']} dona\n"
    await message.answer(text, parse_mode='Markdown')
