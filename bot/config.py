import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8668051733:AAGqskR9yhMQjNRcv2PHe3tWB5lqSBhyUFc')
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')
API_PHONE = os.getenv('API_PHONE', '')
API_PASSWORD = os.getenv('API_PASSWORD', '')
ADMIN_CHAT_IDS = [
    int(x.strip()) for x in os.getenv('ADMIN_CHAT_IDS', '').split(',')
    if x.strip().isdigit()
]
