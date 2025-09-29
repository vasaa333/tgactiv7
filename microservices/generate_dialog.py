import asyncio
import random
from loguru import logger
from loader import db
from utils.misc_func.generator_dialogs import ai_generate_dialog

async def dialog_generator_service() -> None:
    logger.info("Генератор диалогов запущен с динамическими интервалами")
    while True:
        try:
            # Получаем интервалы из БД
            try:
                settings = await db.get_settings()
                min_interval = settings.get("dialog_min_interval") or 11
                max_interval = settings.get("dialog_max_interval") or 20
            except Exception:
                # Fallback к значениям из конфига
                from data.config import DIALOG_MIN_INTERVAL, DIALOG_MAX_INTERVAL
                min_interval = DIALOG_MIN_INTERVAL
                max_interval = DIALOG_MAX_INTERVAL
            
            interval_minutes = random.randint(min_interval, max_interval)
            
            num_roles = random.randint(2, 5)
            logger.info(f"Генерируем диалоги для {num_roles} ролей")
            ai_res = await ai_generate_dialog(num_roles)

            dlg_id = await db.add_dialog(
                name=ai_res["name"],
                messages=ai_res["messages"],
                num_accounts=ai_res["num_accounts"]
            )
            logger.success(f"Диалог сохранён под ID={dlg_id}, roles={ai_res['num_accounts']}")

        except Exception as e:
            logger.error(f"Ошибка при генерации диалога: {e}")
            # При ошибке ждём минимальный интервал
            interval_minutes = min_interval

        # Ждём динамический интервал
        interval_seconds = interval_minutes * 60
        logger.info(f"Следующая генерация диалога через {interval_minutes} минут")
        await asyncio.sleep(interval_seconds)