"""
Расширенный сервис для автоматической генерации диалогов
Поддерживает динамические интервалы из БД и улучшенную логику генерации
"""

import asyncio
import random
from datetime import datetime, timedelta
from loguru import logger
from loader import db
from utils.misc_func.ai_providers import ai_generate_dialog

class AutoDialogService:
    """Сервис автоматической генерации диалогов"""
    
    def __init__(self):
        self.is_running = False
        self.last_generation = None
        
    async def start(self):
        """Запускает сервис автогенерации диалогов"""
        if self.is_running:
            logger.warning("Сервис автогенерации уже запущен")
            return
            
        self.is_running = True
        logger.info("🤖 Запуск сервиса автогенерации диалогов с ИИ")
        
        while self.is_running:
            try:
                await self._generate_dialog_cycle()
            except Exception as e:
                logger.error(f"Критическая ошибка в сервисе автогенерации: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед повтором
                
    async def stop(self):
        """Останавливает сервис"""
        self.is_running = False
        logger.info("Сервис автогенерации диалогов остановлен")
        
    async def _generate_dialog_cycle(self):
        """Один цикл генерации диалога"""
        try:
            # Получаем настройки интервалов из БД
            settings = await self._get_settings()
            min_interval = settings.get("dialog_min_interval", 11)
            max_interval = settings.get("dialog_max_interval", 20)
            
            # Генерируем случайный интервал
            interval_minutes = random.randint(min_interval, max_interval)
            
            # Проверяем, включена ли автогенерация
            auto_generation_enabled = settings.get("auto_generation_enabled", True)
            
            if not auto_generation_enabled:
                logger.info("Автогенерация диалогов отключена в настройках")
                await asyncio.sleep(300)  # Ждем 5 минут и проверяем снова
                return
            
            # Генерируем диалог
            await self._generate_and_save_dialog()
            self.last_generation = datetime.now()
            
            # Ждем до следующей генерации
            interval_seconds = interval_minutes * 60
            logger.info(f"⏰ Следующая автогенерация диалога через {interval_minutes} минут")
            await asyncio.sleep(interval_seconds)
            
        except Exception as e:
            logger.error(f"Ошибка в цикле генерации диалога: {e}")
            await asyncio.sleep(300)  # Ждем 5 минут при ошибке
            
    async def _get_settings(self):
        """Получает настройки из БД с fallback значениями"""
        try:
            return await db.get_settings()
        except Exception as e:
            logger.warning(f"Не удалось получить настройки из БД: {e}")
            # Fallback к дефолтным значениям
            return {
                "dialog_min_interval": 11,
                "dialog_max_interval": 20,
                "auto_generation_enabled": True
            }
            
    async def _generate_and_save_dialog(self):
        """Генерирует и сохраняет диалог"""
        try:
            # Определяем количество ролей (2-5)
            num_roles = random.randint(2, 5)
            
            logger.info(f"🎭 Генерируем диалог для {num_roles} участников")
            
            # Генерируем диалог через ИИ
            ai_result = await ai_generate_dialog(num_roles)
            
            if not ai_result or not ai_result.get("messages"):
                logger.warning("ИИ вернул пустой результат")
                return
                
            # Сохраняем диалог в БД
            dialog_id = await db.add_dialog(
                name=ai_result["name"],
                messages=ai_result["messages"],
                num_accounts=ai_result["num_accounts"]
            )
            
            logger.success(
                f"✅ Диалог успешно сгенерирован и сохранен "
                f"(ID: {dialog_id}, участников: {ai_result['num_accounts']}, "
                f"сообщений: {len(ai_result['messages'])})"
            )
            
            # Обновляем статистику
            await self._update_generation_stats()
            
        except Exception as e:
            logger.error(f"Ошибка при генерации диалога: {e}")
            raise
            
    async def _update_generation_stats(self):
        """Обновляет статистику генерации"""
        try:
            # Получаем текущую статистику
            settings = await db.get_settings()
            current_count = settings.get("generated_dialogs_count", 0)
            
            # Увеличиваем счетчик
            await db.update_settings("generated_dialogs_count", current_count + 1)
            await db.update_settings("last_dialog_generation", datetime.now().isoformat())
            
        except Exception as e:
            logger.warning(f"Не удалось обновить статистику генерации: {e}")
            
    async def get_status(self):
        """Возвращает статус сервиса"""
        settings = await self._get_settings()
        
        return {
            "running": self.is_running,
            "last_generation": self.last_generation,
            "auto_generation_enabled": settings.get("auto_generation_enabled", True),
            "min_interval": settings.get("dialog_min_interval", 11),
            "max_interval": settings.get("dialog_max_interval", 20),
            "total_generated": settings.get("generated_dialogs_count", 0)
        }

# Глобальный экземпляр сервиса
auto_dialog_service = AutoDialogService()

# Функция-обертка для обратной совместимости
async def dialog_generator_service():
    """Запускает сервис автогенерации диалогов"""
    await auto_dialog_service.start()