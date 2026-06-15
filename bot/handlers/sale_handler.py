from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from states import SaleStates
from keyboards import (
    products_keyboard, variants_keyboard, customers_keyboard,
    payment_keyboard, confirm_keyboard,
)
import api_client

router = Router()


@router.message(F.text == "🛒 Yangi sotuv")
async def start_sale(message: Message, state: FSMContext):
    await state.set_state(SaleStates.choosing_customer)
    await state.update_data(items=[], current_product=None)
    customers = await api_client.get_customers()
    await message.answer(
        "👤 Mijozni tanlang:",
        reply_markup=customers_keyboard(customers)
    )


@router.callback_query(SaleStates.choosing_customer, F.data.startswith("customer_"))
async def customer_chosen(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_", 1)[1]
    customer_id = None if data == "none" else int(data)
    await state.update_data(customer_id=customer_id)

    products = await api_client.get_products()
    await state.update_data(products={str(p['id']): p for p in products})
    await state.set_state(SaleStates.adding_items)
    await callback.message.edit_text(
        "📦 Mahsulot tanlang (bir nechta tanlab, 'Yakunlash' tugmasini bosing):",
        reply_markup=products_keyboard(products)
    )


@router.callback_query(SaleStates.adding_items, F.data.startswith("product_"))
async def product_chosen(callback: CallbackQuery, state: FSMContext):
    product_id = callback.data.split("_", 1)[1]
    data = await state.get_data()
    products = data.get('products', {})
    product = products.get(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi")
        return

    variants = product.get('variants') or []
    if product.get('has_variants') and variants:
        # Variantli mahsulot — variant tanlash bosqichi
        await state.update_data(current_product_id=product_id, current_variant=None)
        await state.set_state(SaleStates.choosing_variant)
        await callback.message.answer(
            f"🎨 *{product['name']}* — variantni tanlang:",
            reply_markup=variants_keyboard(variants, mode="sale"),
            parse_mode='Markdown'
        )
        return

    await state.update_data(
        current_product_id=product_id,
        current_price=product['sale_price'],
        current_variant=None,
    )
    await state.set_state(SaleStates.entering_quantity)
    await callback.message.answer(
        f"🔢 *{product['name']}* uchun miqdorni kiriting:\n"
        f"(Mavjud: {product['quantity']} dona)",
        parse_mode='Markdown'
    )


@router.callback_query(SaleStates.choosing_variant, F.data == "variant_back")
async def variant_back_to_products(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    products = data.get('products', {})
    await state.set_state(SaleStates.adding_items)
    await callback.message.answer(
        "📦 Mahsulot tanlang:",
        reply_markup=products_keyboard(list(products.values()))
    )


@router.callback_query(SaleStates.choosing_variant, F.data.startswith("variant_"))
async def variant_chosen(callback: CallbackQuery, state: FSMContext):
    variant_id = callback.data.split("_", 1)[1]
    data = await state.get_data()
    product = data.get('products', {}).get(data['current_product_id'])
    variant = next(
        (v for v in (product.get('variants') or []) if str(v['id']) == variant_id),
        None,
    )
    if not variant:
        await callback.answer("Variant topilmadi")
        return
    await state.update_data(current_variant=variant, current_price=variant['sale_price'])
    await state.set_state(SaleStates.entering_quantity)
    await callback.message.answer(
        f"🔢 *{product['name']} ({variant['name']})* uchun miqdorni kiriting:\n"
        f"(Mavjud: {variant['quantity']} dona)",
        parse_mode='Markdown'
    )


@router.message(SaleStates.entering_quantity)
async def quantity_entered(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❗ Iltimos, musbat son kiriting")
        return
    quantity = int(message.text)
    data = await state.get_data()
    product_id = data['current_product_id']
    products = data.get('products', {})
    product = products.get(product_id)
    variant = data.get('current_variant')
    available = variant['quantity'] if variant else product['quantity']
    if quantity > available:
        await message.answer(
            f"❗ Yetarli mahsulot yo'q. Mavjud: {available} dona"
        )
        return
    await state.update_data(current_quantity=quantity)
    await state.set_state(SaleStates.entering_price)
    default_price = float(data.get('current_price') or product['sale_price'])
    label = f"{product['name']} ({variant['name']})" if variant else product['name']
    await message.answer(
        f"💰 *{label}* ning sotuv narxini kiriting:\n"
        f"(Standart narx: {default_price:,.0f} so'm — o'zgartirmasangiz shu narxni yuboring)",
        parse_mode='Markdown'
    )


@router.message(SaleStates.entering_price)
async def price_entered(message: Message, state: FSMContext):
    text = message.text.replace(' ', '').replace(',', '.')
    try:
        price = float(text)
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Iltimos, to'g'ri narx kiriting (masalan: 15000)")
        return

    data = await state.get_data()
    product_id = data['current_product_id']
    quantity = data['current_quantity']
    products = data.get('products', {})
    product = products.get(product_id)
    variant = data.get('current_variant')
    variant_id = variant['id'] if variant else None
    display_name = f"{product['name']} ({variant['name']})" if variant else product['name']

    items = data.get('items', [])
    for item in items:
        if item['product_id'] == product_id and item.get('variant_id') == variant_id:
            item['quantity'] += quantity
            item['price'] = price
            break
    else:
        items.append({
            'product_id': product_id,
            'variant_id': variant_id,
            'product_name': display_name,
            'quantity': quantity,
            'price': price,
        })
    await state.update_data(items=items, current_variant=None)
    await state.set_state(SaleStates.adding_items)

    items_text = '\n'.join(
        f"  • {i['product_name']} x{i['quantity']} = {i['price'] * i['quantity']:,.0f} so'm"
        f" ({i['price']:,.0f} so'm/dona)"
        for i in items
    )
    total = sum(i['price'] * i['quantity'] for i in items)
    await message.answer(
        f"✅ Qo'shildi!\n\n📋 Hozirgi ro'yxat:\n{items_text}\n\n💰 Jami: {total:,.0f} so'm\n\n"
        "Yana mahsulot qo'shing yoki 'Yakunlash' tugmasini bosing:",
        reply_markup=products_keyboard(list(products.values()))
    )


@router.callback_query(SaleStates.adding_items, F.data == "sale_finish")
async def finish_items(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get('items', [])
    if not items:
        await callback.answer("❗ Kamida bitta mahsulot qo'shing!")
        return
    await state.set_state(SaleStates.choosing_payment)
    total = sum(i['price'] * i['quantity'] for i in items)
    await callback.message.edit_text(
        f"💰 Jami summa: *{total:,.0f} so'm*\n\nTo'lov turini tanlang:",
        reply_markup=payment_keyboard(),
        parse_mode='Markdown'
    )


@router.callback_query(SaleStates.choosing_payment, F.data.startswith("pay_"))
async def payment_chosen(callback: CallbackQuery, state: FSMContext):
    method_map = {'pay_cash': 'cash', 'pay_card': 'card', 'pay_debt': 'debt', 'pay_transfer': 'transfer'}
    method = method_map[callback.data]
    await state.update_data(payment_method=method)
    await state.set_state(SaleStates.confirming)

    data = await state.get_data()
    items = data['items']
    items_text = '\n'.join(
        f"  • {i['product_name']} x{i['quantity']} = {i['price'] * i['quantity']:,.0f} so'm"
        for i in items
    )
    total = sum(i['price'] * i['quantity'] for i in items)
    method_labels = {'cash': 'Naqd', 'card': 'Karta', 'debt': 'Nasiya', 'transfer': "O'tkazma"}

    await callback.message.edit_text(
        f"📋 *Sotuv tasdiqlash*\n\n"
        f"📦 Mahsulotlar:\n{items_text}\n\n"
        f"💰 Jami: *{total:,.0f} so'm*\n"
        f"💳 To'lov: {method_labels[method]}\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=confirm_keyboard(),
        parse_mode='Markdown'
    )


@router.callback_query(SaleStates.confirming, F.data == "confirm")
async def confirm_sale(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data['items']
    payload = {
        'customer': data.get('customer_id'),
        'items': [
            {
                'product': int(i['product_id']),
                'variant': int(i['variant_id']) if i.get('variant_id') else None,
                'quantity': i['quantity'],
                'price': i['price'],
            }
            for i in items
        ],
        'payment_method': data.get('payment_method', 'cash'),
        'discount': 0,
    }
    result, status_code = await api_client.create_sale(payload)
    await state.clear()
    if status_code == 201:
        total = sum(i['price'] * i['quantity'] for i in items)
        await callback.message.edit_text(
            f"✅ *Sotuv #{result['id']} muvaffaqiyatli yakunlandi!*\n"
            f"💰 Jami: *{total:,.0f} so'm*",
            parse_mode='Markdown'
        )
    else:
        await callback.message.edit_text(
            f"❌ Xato yuz berdi: {result}"
        )


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi")
