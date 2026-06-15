import json
import os

USERS_FILE = os.path.join(os.path.dirname(__file__), 'allowed_users.json')


def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {'users': {}}
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'users': {}}


def _save(data: dict):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_allowed(user_id: int) -> bool:
    data = _load()
    return str(user_id) in data['users']


def add_user(user_id: int, name: str = '', added_by: int = 0) -> bool:
    data = _load()
    uid = str(user_id)
    if uid in data['users']:
        return False
    data['users'][uid] = {'name': name, 'added_by': added_by}
    _save(data)
    return True


def remove_user(user_id: int) -> bool:
    data = _load()
    uid = str(user_id)
    if uid not in data['users']:
        return False
    del data['users'][uid]
    _save(data)
    return True


def list_users() -> list[dict]:
    data = _load()
    return [
        {'id': int(uid), 'name': info.get('name', ''), 'added_by': info.get('added_by', 0)}
        for uid, info in data['users'].items()
    ]


def user_count() -> int:
    return len(_load()['users'])
