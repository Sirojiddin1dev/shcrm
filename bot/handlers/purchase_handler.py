from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import PurchaseStates
from keyboards import (
    purchase_products_keyboard, variants_keyboard, payment_keyboard, confirm_keyboard,
)
import api_client

router = Router()


@router.message(F.text == "📦 Yangi harid")
async def start_purchase(message: Message, state: FSMContext):
    await state.set_state(PurchaseStates.adding_items)
    await state.update_data(items=[])
    products = await api_client.get_products()
    await state.update_data(all_products={str(p['id']): p for p in products})
    await message.answer(
        "📦 Qaysi mahsulotni sotib olasiz?",
        reply_markup=purchase_products_keyboard(products)
    )


@router.callback_query(PurchaseStates.adding_items, F.data.startswith("buy_product_"))
async def buy_product_chosen(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split("_")[2]
    data = await state.get_data()
    products = data.get('all_products', {})
    product = products.get(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi")
        return

    variants = product.get('variants') or []
    if product.get('has_variants') and variants:
        await state.update_data(current_product_id=product_id, current_variant=None)
        await state.set_state(PurchaseStates.choosing_variant)
        await callback.message.answer(
            f"🎨 *{product['name']}* — qaysi variantni sotib olasiz?",
            reply_markup=variants_keyboard(variants, mode="purchase"),
            parse_mode='Markdown'
        )
        return

    await state.update_data(current_product_id=product_id, current_variant=None)
    await state.set_state(PurchaseStates.entering_quantity)
    await callback.message.answer(
        f"🔢 *{product['name']}* uchun miqdorni kiriting (nechta olasiz):",
        parse_mode='Markdown'
    )


@router.callback_query(PurchaseStates.choosing_variant, F.data == "variant_back")
async def purchase_variant_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    products = data.get('all_products', {})
    await state.set_state(PurchaseStates.adding_items)
    await callback.message.answer(
        "📦 Qaysi mahsulotni sotib olasiz?",
        reply_markup=purchase_products_keyboard(list(products.values()))
    )


@router.callback_query(PurchaseStates.choosing_variant, F.data.startswith("variant_"))
async def purchase_variant_chosen(callback: CallbackQuery, state: FSMContext):
    variant_id = callback.data.split("_", 1)[1]
    data = await state.get_data()
    product = data.get('all_products', {}).get(data['current_product_id'])
    variant = next(
        (v for v in (product.get('variants') or []) if str(v['id']) == variant_id),
        None,
    )
    if not variant:
        await callback.answer("Variant topilmadi")
        return
    await state.update_data(current_variant=variant)
    await state.set_state(PurchaseStates.entering_quantity)
    await callback.message.answer(
        f"🔢 *{product['name']} ({variant['name']})* uchun miqdorni kiriting (nechta olasiz):",
        parse_mode='Markdown'
    )


@router.message(PurchaseStates.entering_quantity)
async def purchase_quantity_entered(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❗ Iltimos, musbat son kiriting")
        return
    await state.update_data(current_quantity=int(message.text))
    await state.set_state(PurchaseStates.entering_cost_price)
    data = await state.get_data()
    products = data.get('all_products', {})
    product = products.get(data['current_product_id'])
    variant = data.get('current_variant')
    label = f"{product['name']} ({variant['name']})" if variant else product['name']
    current_cost = float(variant['cost_price']) if variant else float(product.get('cost_price', 0))
    await message.answer(
        f"💰 *{label}* ning sotib olish narxini kiriting:\n"
        f"(Hozirgi tan narxi: {current_cost:,.0f} so'm)",
        parse_mode='Markdown'
    )


@router.message(PurchaseStates.entering_cost_price)
async def cost_price_entered(message: Message, state: FSMContext):
    text = message.text.replace(' ', '').replace(',', '.')
    try:
        cost_price = float(text)
        if cost_price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Iltimos, to'g'ri narx kiriting (masalan: 5000)")
        return

    data = await state.get_data()
    product_id = data['current_product_id']
    quantity = data['current_quantity']
    products = data.get('all_products', {})
    product = products.get(product_id)
    variant = data.get('current_variant')
    variant_id = variant['id'] if variant else None
    display_name = f"{product['name']} ({variant['name']})" if variant else product['name']

    items = data.get('items', [])
    for item in items:
        if item['product_id'] == product_id and item.get('variant_id') == variant_id:
            item['quantity'] += quantity
            item['cost_price'] = cost_price
            break
    else:
        items.append({
            'product_id': product_id,
            'variant_id': variant_id,
            'product_name': display_name,
            'quantity': quantity,
            'cost_price': cost_price,
        })
    await state.update_data(items=items, current_variant=None)
    await state.set_state(PurchaseStates.adding_items)

    items_text = '\n'.join(
        f"  • {i['product_name']} x{i['quantity']} = {i['cost_price'] * i['quantity']:,.0f} so'm"
        for i in items
    )
    total = sum(i['cost_price'] * i['quantity'] for i in items)
    await message.answer(
        f"✅ Qo'shildi!\n\n📋 Hozirgi ro'yxat:\n{items_text}\n\n💰 Jami: {total:,.0f} so'm\n\n"
        "Yana qo'shing yoki 'Yakunlash' tugmasini bosing:",
        reply_markup=purchase_products_keyboard(list(products.values()))
    )


@router.callback_query(PurchaseStates.adding_items, F.data == "purchase_finish")
async def finish_purchase_items(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get('items', [])
    if not items:
        await callback.answer("❗ Kamida bitta mahsulot qo'shing!")
        return
    await state.set_state(PurchaseStates.choosing_payment)
    total = sum(i['cost_price'] * i['quantity'] for i in items)
    await callback.message.edit_text(
        f"💰 Jami summa: *{total:,.0f} so'm*\n\nTo'lov turini tanlang:",
        reply_markup=payment_keyboard(),
        parse_mode='Markdown'
    )


@router.callback_query(PurchaseStates.choosing_payment, F.data.startswith("pay_"))
async def purchase_payment_chosen(callback: CallbackQuery, state: FSMContext):
    method_map = {'pay_cash': 'cash', 'pay_card': 'card', 'pay_debt': 'debt', 'pay_transfer': 'transfer'}
    method = method_map[callback.data]
    await state.update_data(payment_method=method)
    await state.set_state(PurchaseStates.confirming)

    data = await state.get_data()
    items = data['items']
    items_text = '\n'.join(
        f"  • {i['product_name']} x{i['quantity']} = {i['cost_price'] * i['quantity']:,.0f} so'm"
        for i in items
    )
    total = sum(i['cost_price'] * i['quantity'] for i in items)
    method_labels = {'cash': 'Naqd', 'card': 'Karta', 'debt': 'Nasiya', 'transfer': "O'tkazma"}
    note = data.get('note', '')

    text = (
        f"📋 *Harid tasdiqlash*\n\n"
        f"📦 Mahsulotlar:\n{items_text}\n\n"
        f"💰 Jami: *{total:,.0f} so'm*\n"
        f"💳 To'lov: {method_labels[method]}\n"
    )
    if note:
        text += f"📝 Izoh: {note}\n"
    text += "\nTasdiqlaysizmi?"

    await callback.message.edit_text(text, reply_markup=confirm_keyboard(), parse_mode='Markdown')


@router.callback_query(PurchaseStates.confirming, F.data == "confirm")
async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data['items']
    payload = {
        'items': [
            {
                'product': int(i['product_id']),
                'variant': int(i['variant_id']) if i.get('variant_id') else None,
                'quantity': i['quantity'],
                'cost_price': i['cost_price'],
            }
            for i in items
        ],
        'payment_method': data.get('payment_method', 'cash'),
        'note': data.get('note', ''),
    }
    result, status_code = await api_client.create_purchase(payload)
    await state.clear()
    if status_code == 201:
        total = sum(i['cost_price'] * i['quantity'] for i in items)
        await callback.message.edit_text(
            f"✅ *Harid #{result['id']} muvaffaqiyatli yakunlandi!*\n"
            f"💰 Jami: *{total:,.0f} so'm*\n"
            f"📦 Mahsulotlar omborga qo'shildi!",
            parse_mode='Markdown'
        )
    else:
        await callback.message.edit_text(f"❌ Xato yuz berdi: {result}")
