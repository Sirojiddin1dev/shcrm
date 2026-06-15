import aiohttp
from config import API_BASE_URL, API_PHONE, API_PASSWORD

_token = None


async def _fetch_token() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{API_BASE_URL}/auth/login/',
            json={'phone': API_PHONE, 'password': API_PASSWORD}
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"API login xato: {data}")
            return data['access']


async def get_token() -> str:
    global _token
    if not _token:
        _token = await _fetch_token()
    return _token


async def _headers():
    token = await get_token()
    return {'Authorization': f'Bearer {token}'}


async def _get(url: str) -> tuple[dict | list, int]:
    """GET so'rov — token muddati o'tsa qayta login qiladi."""
    global _token
    headers = await _headers()
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 401:
                _token = await _fetch_token()
                headers = {'Authorization': f'Bearer {_token}'}
                async with session.get(url, headers=headers) as resp2:
                    return await resp2.json(), resp2.status
            return await resp.json(), resp.status


async def _post(url: str, payload: dict) -> tuple[dict, int]:
    """POST so'rov — token muddati o'tsa qayta login qiladi."""
    global _token
    headers = await _headers()
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 401:
                _token = await _fetch_token()
                headers = {'Authorization': f'Bearer {_token}'}
                async with session.post(url, json=payload, headers=headers) as resp2:
                    try:
                        data = await resp2.json()
                    except Exception:
                        data = {}
                    return data, resp2.status
            try:
                data = await resp.json()
            except Exception:
                data = {}
            return data, resp.status


async def get_products() -> list:
    data, _ = await _get(f'{API_BASE_URL}/products/for_sale/')
    return data if isinstance(data, list) else []


async def get_customers() -> list:
    data, _ = await _get(f'{API_BASE_URL}/customers/')
    if isinstance(data, dict):
        return data.get('results', [])
    return data


async def create_sale(payload: dict) -> tuple[dict, int]:
    return await _post(f'{API_BASE_URL}/sales/', payload)


async def create_purchase(payload: dict) -> tuple[dict, int]:
    return await _post(f'{API_BASE_URL}/purchases/', payload)


async def get_dashboard() -> dict:
    data, _ = await _get(f'{API_BASE_URL}/reports/dashboard/?period=today')
    return data



async def is_bot_user_allowed(chat_id: int) -> bool:
    data, status = await _get(f'{API_BASE_URL}/bot-users/{chat_id}/')
    if status != 200:
        return False
    return bool(data.get('allowed'))


async def add_bot_user(chat_id: int, full_name: str = '', username: str = '') -> tuple[dict, int]:
    return await _post(f'{API_BASE_URL}/bot-users/', {
        'chat_id': chat_id,
        'full_name': full_name,
        'username': username,
        'is_active': True,
    })


async def remove_bot_user(chat_id: int) -> int:
    global _token
    headers = await _headers()
    async with aiohttp.ClientSession() as session:
        async with session.delete(
            f'{API_BASE_URL}/bot-users/{chat_id}/',
            headers=headers
        ) as resp:
            if resp.status == 401:
                _token = await _fetch_token()
                headers = {'Authorization': f'Bearer {_token}'}
                async with session.delete(
                    f'{API_BASE_URL}/bot-users/{chat_id}/', headers=headers
                ) as resp2:
                    return resp2.status
            return resp.status


async def verify_staff_by_phone(
    phone: str, chat_id: int, full_name: str = '', username: str = ''
) -> dict:
    """Telefon staff ekanini tekshiradi va TelegramBotUser ga qo'shadi."""
    data, status = await _post(f'{API_BASE_URL}/auth/verify-staff/', {
        'phone': phone, 'chat_id': chat_id, 'full_name': full_name, 'username': username,
    })
    if status == 200:
        return data
    return {'is_staff': False, 'full_name': ''}


async def get_customers_list(page: int = 1) -> dict:
    data, _ = await _get(f'{API_BASE_URL}/customers/?page={page}')
    return data if isinstance(data, dict) else {}


async def get_debtors() -> list:
    data, _ = await _get(f'{API_BASE_URL}/customers/debtors/')
    return data if isinstance(data, list) else []


async def get_products_list() -> list:
    data, _ = await _get(f'{API_BASE_URL}/products/')
    return data.get('results', []) if isinstance(data, dict) else []


async def get_profit_report() -> dict:
    data, _ = await _get(f'{API_BASE_URL}/reports/profit/')
    return data if isinstance(data, dict) else {}


async def list_bot_users() -> list[dict]:
    data, status = await _get(f'{API_BASE_URL}/bot-users/')
    if status != 200:
        return []
    return data if isinstance(data, list) else []


# ===== Mijozni botga bog'lash =====

async def link_customer_by_phone(phone: str, chat_id: int, full_name: str = '') -> tuple[dict, int]:
    return await _post(f'{API_BASE_URL}/customers/link-by-phone/', {
        'phone': phone, 'chat_id': str(chat_id), 'full_name': full_name,
    })


async def link_customer_by_token(token: str, chat_id: int, full_name: str = '') -> tuple[dict, int]:
    return await _post(f'{API_BASE_URL}/customers/link-by-token/', {
        'token': token, 'chat_id': str(chat_id), 'full_name': full_name,
    })


async def get_customer_by_chat_id(chat_id: int) -> dict | None:
    data, status = await _get(f'{API_BASE_URL}/customers/by-chat-id/{chat_id}/')
    return data if status == 200 else None


async def get_customer_sales(customer_id: int) -> list[dict]:
    data, status = await _get(f'{API_BASE_URL}/sales/?customer={customer_id}')
    if status != 200:
        return []
    if isinstance(data, dict):
        return data.get('results', [])
    return data
