from utils.postgres_db import DB
from dotenv import load_dotenv
import os
import base64

load_dotenv()

db_host = os.getenv("DB_HOST"), # БЕРЕТСЯ ИЗ .ENV ФАЙЛА 
db_port = os.getenv("DB_PORT") # БЕРЕТСЯ ИЗ .ENV ФАЙЛА 
db_user = os.getenv("DB_USER") # БЕРЕТСЯ ИЗ .ENV ФАЙЛА 
db_passwd = os.getenv("DB_PASSWORD") # БЕРЕТСЯ ИЗ .ENV ФАЙЛА 
db_name = os.getenv("DB_NAME") # БЕРЕТСЯ ИЗ .ENV ФАЙЛА 
TOKEN = os.getenv("TOKEN") # БЕРЕТСЯ ИЗ .ENV ФАЙЛА 

db = DB(db_host[0], db_port, db_user, db_passwd, db_name)


NAME_PROJECT = '🚀 Auto Dialog'

DOMAIN = "" # ЕСЛИ ХОТИТЕ ЗАПУСТИТЬ НА ХУКАХ, НУЖНО ПРИВЯЗЫВАТЬ ДОМЕН, ЕСЛИ НЕ ЗНАЕТЕ ЧТО ЭТО ТО НЕ ТРОГАЙТЕ

ADMIN = [7163923025, 7294902374] # АЙДИШНИКИ АДМИНОВ ЧЕРЕЗ ЗАПЯТУЮ^M
API_ID = 25866764 # API ID, можно взять на my.telegram.org^M
API_HASH = '1795570debf8e5f2b2e5e1883f388a05'  #API HASH, можно взять на my.telegram.org^M

DETAILS = '"случайный анекдот и затем разбор его на смешные фрагменты", "один участник советуется с остальными участниками диалога на случайные бытовые темы", "друзья детства обсуждающие воспоминания из прошлого", "играют в угадывание случайной загадки"'.split(",") # через запятую перечислите темы для генерации диалога





PROMPT_TEMPLATE = os.getenv(
    "PROMPT_TEMPLATE",
    """
Сгенерируй диалог ровно между {num} уникальными участниками в открытом общем Telegram-чате. Тема: {detail}.
• Используй только роли User 1, User 2, …, User {num} — ни одной дополнительной.
• Реплики участников могут идти в любом порядке (например: User 1, User 3, User 1, User 2, User 2, User 3, User 1), НО НЕ обязательно последовательнвм циклом 1→2→3.
• Ответь на русском языке в разговорном стиле со сленгом.
• Строго форматируй по одной строке на сообщение, например:

[User 1] Первое сообщение  
[User 3] Второе сообщение  
[User 1] Третье сообщение  
…  
[User {num}] Последнее сообщение  

• Нужно иногда допускать опечатки.
• Никаких дополнительных описаний или пояснений — только сами строки диалога.
• {num} это количество ролей для ввбранного диалога. один участник может занять одну роль. Нужно делать строго указанное количество участников.
"""
)

BOT_TIMEZONE = "Europe/Moscow"

COOLDOWN_MINUTES = 10

TIMEOUT = int(os.getenv("AI_TIMEOUT", "10"))

DIALOG_MIN_INTERVAL = int(os.getenv('DIALOG_MIN_INTERVAL', 11))
DIALOG_MAX_INTERVAL = int(os.getenv('DIALOG_MAX_INTERVAL', 20))

