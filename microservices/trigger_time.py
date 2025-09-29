import asyncio
import json
import random
from datetime import datetime, timedelta
from loader import db, account_manager, logger
#from config import Config  # Импортируем конфиг
from data.config import DIALOG_MIN_INTERVAL, DIALOG_MAX_INTERVAL



async def _play_and_mark(chat_id: int, dialog_text: str, num_roles: int, dialog_id: int):
    try:
        await account_manager.play_dialog(chat_id, dialog_text, num_roles)
    except Exception as e:
        logger.exception(f"Ошибка при проигрывании диалога в чате {chat_id}: {e}")

async def run_time_triggers():
    chats = await db.get_time_trigger_chats()
    for entry in chats:
        chat_id = entry["chat_id"]
        accounts = await db.get_accounts_in_chat(chat_id)
        cnt = len(accounts)
        if cnt == 0:
            logger.info(f"Чат {chat_id}: нет активных аккаунтов — пропускаем")
            continue

        dialogs = await db.get_all_dialogs()
        valid = [d for d in dialogs if d["num_accounts"] <= cnt]
        if not valid:
            logger.info(f"Чат {chat_id}: нет диалогов для {cnt} аккаунтов")
            continue

        dlg = random.choice(valid)
        msgs = dlg["messages"]
        if isinstance(msgs, str):
            try:
                msgs = json.loads(msgs)
            except json.JSONDecodeError:
                msgs = []

        dialog_text = "\n".join(f"[{m['role']}] {m['text']}" for m in msgs)
        logger.info(f"Чат {chat_id}: запускаем диалог «{dlg['name']}»")
        await db.update_dialog_usage(dlg['id'], True)

        asyncio.create_task(_play_and_mark(chat_id, dialog_text, dlg["num_accounts"], dlg["id"]))

async def scheduler_time_trigger_loop():
    await run_time_triggers()
    while True:
        # Получаем интервалы из БД
        try:
            settings = await db.get_settings()
            min_interval = settings.get("trigger_min_interval") or 5
            max_interval = settings.get("trigger_max_interval") or 15
        except Exception:
            # Fallback к значениям из конфига
            min_interval = 5
            max_interval = 15
        
        # Генерируем случайный интервал в минутах
        random_interval_minutes = random.randint(min_interval, max_interval)
        
        # Переводим в секунды для sleep
        random_interval_seconds = random_interval_minutes * 60
        
        logger.info(f"Следующий запуск триггеров через {random_interval_minutes} минут")
        
        # Ждем случайный интервал
        await asyncio.sleep(random_interval_seconds)
        
        # Запускаем триггеры
        await run_time_triggers()