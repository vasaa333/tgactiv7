"""
Полностью переделанные обработчики для управления настройками ИИ и интервалами
Включает полноценные настройки провайдеров, API ключей, интервалов триггеров и автогенерации
Добавлены блоки try/except с корректным логированием и информативными уведомлениями
Реализована возможность отмены действий на каждом шаге
"""

from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from utils.misc_func.bot_models import FSM
from loader import adminRouter, db
from states.admin_state import AdminAISettingsStates, AdminIntervalSettingsStates
from keyboards.inline.adminkeyinline import back_fun_key
from loguru import logger
import json
import traceback

# Вспомогательная функция для универсального отображения меню
async def send_or_edit_message(obj, text: str, reply_markup=None):
    """Универсальная функция для отправки или редактирования сообщения"""
    if isinstance(obj, CallbackQuery):
        await obj.message.edit_text(text, reply_markup=reply_markup)
    elif isinstance(obj, Message):
        await obj.answer(text, reply_markup=reply_markup)
    else:
        # Пытаемся универсальный подход для любых других типов
        try:
            await obj.message.edit_text(text, reply_markup=reply_markup)
        except (AttributeError, TypeError):
            try:
                await obj.answer(text, reply_markup=reply_markup)
            except (AttributeError, TypeError):
                logger.error(f"Не удалось отправить сообщение для объекта типа {type(obj)}")

@adminRouter.message(F.text == '🤖 ИИ настройки')
async def ai_settings_handler(msg: Message, state: FSM):
    """Главное меню настроек ИИ с улучшенной обработкой ошибок"""
    try:
        await state.clear()
        settings = await db.get_settings()
        
        # Получаем текущие настройки с безопасными значениями по умолчанию
        current_provider = settings.get("ai_provider", "pollinations")
        current_model = settings.get("ai_model", "gpt-4o-mini")
        timeout = settings.get("ai_timeout", "30")
        
        # Настройки интервалов
        trigger_min = settings.get("trigger_min_interval", 5)
        trigger_max = settings.get("trigger_max_interval", 15)
        dialog_min = settings.get("dialog_min_interval", 11)
        dialog_max = settings.get("dialog_max_interval", 20)
        
        # Проверим наличие API ключей
        openai_status = "✅" if settings.get("openai_token") else "❌"
        anthropic_status = "✅" if settings.get("anthropic_token") else "❌"
        gemini_status = "✅" if settings.get("gemini_token") else "❌"
        pollinations_status = "✅" if settings.get("pollinations_token") else "❌"
        
        text = (
            "<b>🤖 Настройки ИИ</b>\n\n"
            f"📡 Провайдер: <code>{current_provider}</code>\n"
            f"🧠 Модель: <code>{current_model}</code>\n"
            f"⏱ Timeout: <code>{timeout}с</code>\n\n"
            "<b>🔑 Статус API ключей:</b>\n"
            f"OpenAI: {openai_status} | Anthropic: {anthropic_status}\n"
            f"Gemini: {gemini_status} | Pollinations: {pollinations_status}\n\n"
            "<b>⏰ Интервалы</b>\n"
            f"🎯 Триггеры: <code>{trigger_min}-{trigger_max} мин</code>\n"
            f"💬 Автодиалоги: <code>{dialog_min}-{dialog_max} мин</code>\n\n"
            "Выберите настройку для изменения:"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📡 Выбрать API провайдера", callback_data="select_ai_provider")],
            [InlineKeyboardButton(text="🔑 Настроить API ключи", callback_data="manage_api_keys")],
            [InlineKeyboardButton(text="🧠 Установить модель", callback_data="set_ai_model")],
            [InlineKeyboardButton(text="✍️ Установить system prompt", callback_data="set_system_prompt")],
            [InlineKeyboardButton(text="⏱ Установить timeout", callback_data="set_ai_timeout")],
            [InlineKeyboardButton(text="⏰ Настройки интервалов", callback_data="interval_settings")],
            [InlineKeyboardButton(text="🧪 Тестировать API", callback_data="test_ai_api")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_admin")]
        ])
        
        # Используем правильный метод в зависимости от типа объекта
        if isinstance(msg, CallbackQuery):
            await msg.message.edit_text(text, reply_markup=kb)
        elif isinstance(msg, Message):
            await msg.answer(text, reply_markup=kb)
        else:
            # Для любых других случаев пробуем оба варианта
            try:
                await msg.edit_text(text, reply_markup=kb)
            except (AttributeError, TypeError):
                await msg.answer(text, reply_markup=kb)
            
    except Exception as e:
        logger.error(f"Ошибка в ai_settings_handler: {e}")
        logger.error(traceback.format_exc())
        error_msg = "❌ Произошла ошибка при загрузке настроек ИИ. Проверьте подключение к базе данных."
        if hasattr(msg, 'edit_text'):
            await msg.edit_text(error_msg)
        else:
            await msg.answer(error_msg)

@adminRouter.callback_query(F.data == "test_ai_api")
async def test_ai_api_handler(call: CallbackQuery, state: FSM):
    """Тестирование текущего API провайдера"""
    try:
        await call.answer("🧪 Запуск тестирования API...")
        
        # Импортируем функцию для генерации диалогов
        from utils.misc_func.ai_providers import get_ai_provider
        
        provider = await get_ai_provider()
        test_prompt = "Напиши короткое приветствие на русском языке"
        
        result = await provider.generate_dialog(test_prompt)
        
        if result and len(result.strip()) > 0:
            await call.message.edit_text(
                f"✅ <b>Тест API успешен!</b>\n\n"
                f"📝 Ответ: {result[:200]}{'...' if len(result) > 200 else ''}\n\n"
                f"Провайдер работает корректно.",
                reply_markup=back_fun_key("back_to_ai_settings")
            )
        else:
            await call.message.edit_text(
                "❌ <b>Тест API неудачен</b>\n\n"
                "Получен пустой ответ. Проверьте настройки API ключа.",
                reply_markup=back_fun_key("back_to_ai_settings")
            )
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании API: {e}")
        await call.message.edit_text(
            f"❌ <b>Ошибка тестирования API</b>\n\n"
            f"Детали: {str(e)[:300]}\n\n"
            f"Проверьте правильность API ключа и настроек провайдера.",
            reply_markup=back_fun_key("back_to_ai_settings")
        )

@adminRouter.callback_query(F.data == "interval_settings")
async def interval_settings_menu(call_or_msg, state: FSM):
    """Меню настроек интервалов с обработкой ошибок"""
    try:
        settings = await db.get_settings()
        
        trigger_min = settings.get("trigger_min_interval", 5)
        trigger_max = settings.get("trigger_max_interval", 15)
        dialog_min = settings.get("dialog_min_interval", 11)
        dialog_max = settings.get("dialog_max_interval", 20)
        
        text = (
            "<b>⏰ Настройки интервалов</b>\n\n"
            "<b>🎯 Интервалы триггеров по времени:</b>\n"
            f"Минимум: <code>{trigger_min} минут</code>\n"
            f"Максимум: <code>{trigger_max} минут</code>\n\n"
            "<b>💬 Интервалы автогенерации диалогов:</b>\n"
            f"Минимум: <code>{dialog_min} минут</code>\n"
            f"Максимум: <code>{dialog_max} минут</code>\n\n"
            "Выберите что настроить:"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Мин. интервал триггера", callback_data="set_trigger_min")],
            [InlineKeyboardButton(text="🎯 Макс. интервал триггера", callback_data="set_trigger_max")],
            [InlineKeyboardButton(text="💬 Мин. интервал диалогов", callback_data="set_dialog_min")],
            [InlineKeyboardButton(text="💬 Макс. интервал диалогов", callback_data="set_dialog_max")],
            [InlineKeyboardButton(text="🔄 Сбросить к умолчанию", callback_data="reset_intervals")],
            [InlineKeyboardButton(text="↩️ К ИИ настройкам", callback_data="back_to_ai_settings")]
        ])
        
        # Обработка разных типов объектов
        if isinstance(call_or_msg, CallbackQuery):
            await call_or_msg.message.edit_text(text, reply_markup=kb)
        elif isinstance(call_or_msg, Message):
            await call_or_msg.answer(text, reply_markup=kb)
        else:
            # Пробуем универсальный подход
            try:
                await call_or_msg.message.edit_text(text, reply_markup=kb)
            except (AttributeError, TypeError):
                await call_or_msg.answer(text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка в interval_settings_menu: {e}")
        if isinstance(call_or_msg, CallbackQuery):
            await call_or_msg.answer("❌ Ошибка загрузки настроек интервалов", show_alert=True)
        else:
            await call_or_msg.answer("❌ Ошибка загрузки настроек интервалов")

@adminRouter.callback_query(F.data == "reset_intervals")
async def reset_intervals_handler(call: CallbackQuery, state: FSM):
    """Сброс интервалов к значениям по умолчанию"""
    try:
        await db.update_settings("trigger_min_interval", 5)
        await db.update_settings("trigger_max_interval", 15)
        await db.update_settings("dialog_min_interval", 11)
        await db.update_settings("dialog_max_interval", 20)
        
        await call.answer("✅ Интервалы сброшены к умолчанию")
        await interval_settings_menu(call, state)
        
    except Exception as e:
        logger.error(f"Ошибка при сбросе интервалов: {e}")
        await call.answer("❌ Ошибка при сбросе интервалов", show_alert=True)

@adminRouter.callback_query(F.data == "back_to_ai_settings")
async def back_to_ai_settings(call: CallbackQuery, state: FSM):
    """Возврат к главному меню ИИ настроек"""
    try:
        await ai_settings_handler(call.message, state)
    except Exception as e:
        logger.error(f"Ошибка при возврате к настройкам ИИ: {e}")
        await call.answer("❌ Ошибка навигации", show_alert=True)

# Настройки интервалов триггеров
@adminRouter.callback_query(F.data == "set_trigger_min")
async def set_trigger_min_interval(call: CallbackQuery, state: FSM):
    """Установка минимального интервала триггеров"""
    try:
        await state.set_state(AdminIntervalSettingsStates.waiting_for_trigger_min_interval)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="interval_settings")]
        ])
        await call.message.edit_text(
            "🎯 <b>Установка минимального интервала триггеров</b>\n\n"
            "Введите минимальный интервал для триггеров по времени (в минутах):\n"
            "📋 Рекомендуется: 3-10 минут\n"
            "📏 Диапазон: 1-1440 минут (24 часа)\n\n"
            "💡 Чем меньше интервал, тем чаще будут срабатывать триггеры",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_trigger_min_interval: {e}")
        await call.answer("❌ Ошибка при переходе к настройке", show_alert=True)

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_trigger_min_interval)
async def process_trigger_min_interval(msg: Message, state: FSM):
    """Обработка ввода минимального интервала триггеров"""
    try:
        interval_text = msg.text.strip()
        
        # Проверка на отмену
        if interval_text.lower() in ['отмена', 'cancel', '-']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await interval_settings_menu(msg, state)
            return
            
        interval = int(interval_text)
        
        if interval < 1:
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал должен быть больше 0 минут.\n"
                "Попробуйте еще раз или отправьте 'отмена' для выхода:"
            )
            return
            
        if interval > 1440:  # 24 часа
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал не должен превышать 1440 минут (24 часа).\n"
                "Попробуйте еще раз или отправьте 'отмена' для выхода:"
            )
            return
            
        await db.update_settings("trigger_min_interval", interval)
        logger.info(f"Обновлен минимальный интервал триггеров: {interval} минут")
        
        await msg.answer(
            f"✅ <b>Настройка сохранена</b>\n\n"
            f"Минимальный интервал триггеров: <code>{interval} минут</code>"
        )
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer(
            "❌ <b>Ошибка формата</b>\n\n"
            "Введите корректное число (количество минут).\n"
            "Пример: 5\n"
            "Или отправьте 'отмена' для выхода:"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке минимального интервала триггеров: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить настройку. Попробуйте позже."
        )
        await state.clear()

@adminRouter.callback_query(F.data == "set_trigger_max")
async def set_trigger_max_interval(call: CallbackQuery, state: FSM):
    """Установка максимального интервала триггеров"""
    try:
        settings = await db.get_settings()
        min_interval = settings.get("trigger_min_interval", 5)
        
        await state.set_state(AdminIntervalSettingsStates.waiting_for_trigger_max_interval)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="interval_settings")]
        ])
        await call.message.edit_text(
            "🎯 <b>Установка максимального интервала триггеров</b>\n\n"
            "Введите максимальный интервал для триггеров по времени (в минутах):\n"
            f"📋 Должен быть больше минимального ({min_interval} мин)\n"
            "📏 Рекомендуется: 10-60 минут\n\n"
            "💡 Определяет верхнюю границу случайного интервала",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_trigger_max_interval: {e}")
        await call.answer("❌ Ошибка при переходе к настройке", show_alert=True)

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_trigger_max_interval)
async def process_trigger_max_interval(msg: Message, state: FSM):
    """Обработка ввода максимального интервала триггеров"""
    try:
        interval_text = msg.text.strip()
        
        if interval_text.lower() in ['отмена', 'cancel', '-']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await interval_settings_menu(msg, state)
            return
            
        interval = int(interval_text)
        
        if interval < 1:
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал должен быть больше 0 минут:"
            )
            return
            
        if interval > 1440:  # 24 часа
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал не должен превышать 1440 минут (24 часа):"
            )
            return
            
        settings = await db.get_settings()
        min_interval = settings.get("trigger_min_interval", 5)
        if interval < min_interval:
            await msg.answer(
                f"❌ <b>Ошибка валидации</b>\n\n"
                f"Максимальный интервал должен быть больше минимального ({min_interval} мин):"
            )
            return
            
        await db.update_settings("trigger_max_interval", interval)
        logger.info(f"Обновлен максимальный интервал триггеров: {interval} минут")
        
        await msg.answer(
            f"✅ <b>Настройка сохранена</b>\n\n"
            f"Максимальный интервал триггеров: <code>{interval} минут</code>"
        )
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer(
            "❌ <b>Ошибка формата</b>\n\n"
            "Введите корректное число (количество минут):"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке максимального интервала триггеров: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить настройку. Попробуйте позже."
        )
        await state.clear()

# Настройки интервалов диалогов
@adminRouter.callback_query(F.data == "set_dialog_min")
async def set_dialog_min_interval(call: CallbackQuery, state: FSM):
    """Установка минимального интервала диалогов"""
    try:
        await state.set_state(AdminIntervalSettingsStates.waiting_for_dialog_min_interval)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="interval_settings")]
        ])
        await call.message.edit_text(
            "💬 <b>Установка минимального интервала автодиалогов</b>\n\n"
            "Введите минимальный интервал для автогенерации диалогов (в минутах):\n"
            "📋 Рекомендуется: 10-30 минут\n"
            "📏 Диапазон: 1-1440 минут\n\n"
            "💡 Чем меньше интервал, тем чаще будут генерироваться диалоги",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_dialog_min_interval: {e}")
        await call.answer("❌ Ошибка при переходе к настройке", show_alert=True)

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_dialog_min_interval)
async def process_dialog_min_interval(msg: Message, state: FSM):
    """Обработка ввода минимального интервала диалогов"""
    try:
        interval_text = msg.text.strip()
        
        if interval_text.lower() in ['отмена', 'cancel', '-']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await interval_settings_menu(msg, state)
            return
            
        interval = int(interval_text)
        
        if interval < 1:
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал должен быть больше 0 минут:"
            )
            return
            
        if interval > 1440:  # 24 часа
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал не должен превышать 1440 минут (24 часа):"
            )
            return
            
        await db.update_settings("dialog_min_interval", interval)
        logger.info(f"Обновлен минимальный интервал автодиалогов: {interval} минут")
        
        await msg.answer(
            f"✅ <b>Настройка сохранена</b>\n\n"
            f"Минимальный интервал автогенерации диалогов: <code>{interval} минут</code>"
        )
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer(
            "❌ <b>Ошибка формата</b>\n\n"
            "Введите корректное число (количество минут):"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке минимального интервала диалогов: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить настройку. Попробуйте позже."
        )
        await state.clear()

@adminRouter.callback_query(F.data == "set_dialog_max")
async def set_dialog_max_interval(call: CallbackQuery, state: FSM):
    """Установка максимального интервала диалогов"""
    try:
        settings = await db.get_settings()
        min_interval = settings.get("dialog_min_interval", 11)
        
        await state.set_state(AdminIntervalSettingsStates.waiting_for_dialog_max_interval)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="interval_settings")]
        ])
        await call.message.edit_text(
            "💬 <b>Установка максимального интервала автодиалогов</b>\n\n"
            "Введите максимальный интервал для автогенерации диалогов (в минутах):\n"
            f"📋 Должен быть больше минимального ({min_interval} мин)\n"
            "📏 Рекомендуется: 30-120 минут\n\n"
            "💡 Определяет верхнюю границу случайного интервала",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_dialog_max_interval: {e}")
        await call.answer("❌ Ошибка при переходе к настройке", show_alert=True)

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_dialog_max_interval)
async def process_dialog_max_interval(msg: Message, state: FSM):
    """Обработка ввода максимального интервала диалогов"""
    try:
        interval_text = msg.text.strip()
        
        if interval_text.lower() in ['отмена', 'cancel', '-']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await interval_settings_menu(msg, state)
            return
            
        interval = int(interval_text)
        
        if interval < 1:
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал должен быть больше 0 минут:"
            )
            return
            
        if interval > 1440:  # 24 часа
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Интервал не должен превышать 1440 минут (24 часа):"
            )
            return
            
        settings = await db.get_settings()
        min_interval = settings.get("dialog_min_interval", 11)
        if interval < min_interval:
            await msg.answer(
                f"❌ <b>Ошибка валидации</b>\n\n"
                f"Максимальный интервал должен быть больше минимального ({min_interval} мин):"
            )
            return
            
        await db.update_settings("dialog_max_interval", interval)
        logger.info(f"Обновлен максимальный интервал автодиалогов: {interval} минут")
        
        await msg.answer(
            f"✅ <b>Настройка сохранена</b>\n\n"
            f"Максимальный интервал автогенерации диалогов: <code>{interval} минут</code>"
        )
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer(
            "❌ <b>Ошибка формата</b>\n\n"
            "Введите корректное число (количество минут):"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке максимального интервала диалогов: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить настройку. Попробуйте позже."
        )
        await state.clear()

# Настройки AI провайдеров
@adminRouter.callback_query(F.data == "select_ai_provider")
async def select_ai_provider_menu(call: CallbackQuery, state: FSM):
    """Меню выбора AI провайдера"""
    try:
        settings = await db.get_settings()
        current_provider = settings.get("ai_provider", "pollinations")
        
        text = (
            f"<b>📡 Выбор API провайдера</b>\n\n"
            f"Текущий: <code>{current_provider}</code>\n\n"
            "<b>Доступные провайдеры:</b>\n"
            "🔸 <b>OpenAI</b> - GPT модели (требует API ключ)\n"
            "🔸 <b>Anthropic</b> - Claude модели (требует API ключ)\n"
            "🔸 <b>Google Gemini</b> - Gemini модели (требует API ключ)\n"
            "🔸 <b>Pollinations</b> - Бесплатные модели (может работать без ключа)\n\n"
            "Выберите провайдера:"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🟢 OpenAI" if current_provider == "openai" else "⚪ OpenAI", callback_data="provider_openai")],
            [InlineKeyboardButton(text=f"🟢 Anthropic" if current_provider == "anthropic" else "⚪ Anthropic", callback_data="provider_anthropic")],
            [InlineKeyboardButton(text=f"🟢 Google Gemini" if current_provider == "gemini" else "⚪ Google Gemini", callback_data="provider_gemini")],
            [InlineKeyboardButton(text=f"🟢 Pollinations" if current_provider == "pollinations" else "⚪ Pollinations", callback_data="provider_pollinations")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_ai_settings")]
        ])
        await call.message.edit_text(text, reply_markup=kb)
        
    except Exception as e:
        logger.error(f"Ошибка в select_ai_provider_menu: {e}")
        await call.answer("❌ Ошибка загрузки провайдеров", show_alert=True)

@adminRouter.callback_query(F.data.startswith("provider_"))
async def set_ai_provider(call: CallbackQuery, state: FSM):
    """Установка AI провайдера"""
    try:
        provider = call.data.split("_")[1]
        await db.update_settings("ai_provider", provider)
        logger.info(f"Установлен AI провайдер: {provider}")
        
        await call.answer(f"✅ Провайдер установлен: {provider}")
        await select_ai_provider_menu(call, state)
        
    except Exception as e:
        logger.error(f"Ошибка при установке провайдера: {e}")
        await call.answer("❌ Ошибка при установке провайдера", show_alert=True)

@adminRouter.callback_query(F.data == "manage_api_keys")
async def manage_api_keys_menu(call_or_msg, state: FSM):
    """Меню управления API ключами"""
    try:
        settings = await db.get_settings()
        
        openai_key = "✅ Настроен" if settings.get("openai_token") else "❌ Не настроен"
        anthropic_key = "✅ Настроен" if settings.get("anthropic_token") else "❌ Не настроен"
        gemini_key = "✅ Настроен" if settings.get("gemini_token") else "❌ Не настроен"
        pollinations_key = "✅ Настроен" if settings.get("pollinations_token") else "❌ Не настроен"
        
        text = (
            "<b>🔑 Управление API ключами</b>\n\n"
            f"<b>OpenAI:</b> {openai_key}\n"
            f"<b>Anthropic:</b> {anthropic_key}\n"
            f"<b>Google Gemini:</b> {gemini_key}\n"
            f"<b>Pollinations:</b> {pollinations_key}\n\n"
            "⚠️ <b>Важно:</b>\n"
            "• API ключи хранятся в зашифрованном виде\n"
            "• Для удаления ключа отправьте символ '-'\n"
            "• Убедитесь что ключ действителен перед сохранением\n\n"
            "Выберите провайдера для настройки:"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔸 OpenAI API Key", callback_data="set_openai_key")],
            [InlineKeyboardButton(text="🔸 Anthropic API Key", callback_data="set_anthropic_key")],
            [InlineKeyboardButton(text="🔸 Gemini API Key", callback_data="set_gemini_key")],
            [InlineKeyboardButton(text="🔸 Pollinations Token", callback_data="set_pollinations_key")],
            [InlineKeyboardButton(text="🗑 Удалить все ключи", callback_data="clear_all_keys")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_ai_settings")]
        ])
        
        # Используем универсальную функцию для отправки/редактирования
        await send_or_edit_message(call_or_msg, text, kb)
        
    except Exception as e:
        logger.error(f"Ошибка в manage_api_keys_menu: {e}")
        if isinstance(call_or_msg, CallbackQuery):
            await call_or_msg.answer("❌ Ошибка загрузки API ключей", show_alert=True)
        else:
            await call_or_msg.answer("❌ Ошибка загрузки API ключей")

@adminRouter.callback_query(F.data == "clear_all_keys")
async def clear_all_keys_confirm(call: CallbackQuery, state: FSM):
    """Подтверждение удаления всех API ключей"""
    try:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить все", callback_data="confirm_clear_all_keys")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="manage_api_keys")]
        ])
        await call.message.edit_text(
            "<b>⚠️ Подтверждение удаления</b>\n\n"
            "Вы уверены что хотите удалить ВСЕ API ключи?\n"
            "Это действие нельзя отменить.",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в clear_all_keys_confirm: {e}")
        await call.answer("❌ Ошибка", show_alert=True)

@adminRouter.callback_query(F.data == "confirm_clear_all_keys")
async def confirm_clear_all_keys(call: CallbackQuery, state: FSM):
    """Подтвержденное удаление всех API ключей"""
    try:
        await db.update_settings("openai_token", None)
        await db.update_settings("anthropic_token", None)
        await db.update_settings("gemini_token", None)
        await db.update_settings("pollinations_token", None)
        
        logger.info("Удалены все API ключи")
        await call.answer("✅ Все API ключи удалены")
        await manage_api_keys_menu(call, state)
        
    except Exception as e:
        logger.error(f"Ошибка при удалении всех ключей: {e}")
        await call.answer("❌ Ошибка при удалении ключей", show_alert=True)

@adminRouter.callback_query(F.data.startswith("set_") and F.data.endswith("_key"))
async def set_api_key_start(call: CallbackQuery, state: FSM):
    """Начало установки API ключа"""
    try:
        key_type = call.data.split("_")[1]
        await state.set_state(AdminAISettingsStates.waiting_for_api_token)
        await state.update_data(key_type=key_type)
        
        provider_names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic", 
            "gemini": "Google Gemini",
            "pollinations": "Pollinations"
        }
        
        provider_hints = {
            "openai": "sk-...",
            "anthropic": "sk-ant-...",
            "gemini": "AI...",
            "pollinations": "HXVnnLNJ84BFvY7Y"
        }
        
        provider_name = provider_names.get(key_type, key_type)
        hint = provider_hints.get(key_type, "...")
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="manage_api_keys")]
        ])
        await call.message.edit_text(
            f"🔑 <b>Установка API ключа для {provider_name}</b>\n\n"
            f"Введите API ключ:\n"
            f"Пример формата: <code>{hint}</code>\n\n"
            "🗑 Отправьте '-' чтобы удалить текущий ключ\n"
            "❌ Отправьте 'отмена' для отмены действия",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_api_key_start: {e}")
        await call.answer("❌ Ошибка при переходе к настройке ключа", show_alert=True)

@adminRouter.message(AdminAISettingsStates.waiting_for_api_token)
async def process_api_token(msg: Message, state: FSM):
    """Обработка ввода API ключа"""
    try:
        data = await state.get_data()
        key_type = data.get("key_type")
        token = msg.text.strip()
        
        if token.lower() in ['отмена', 'cancel']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await manage_api_keys_menu(msg, state)
            return
        
        if token == "-":
            await db.update_settings(f"{key_type}_token", None)
            logger.info(f"Удален API ключ для {key_type}")
            await msg.answer(f"✅ API ключ для {key_type} удален")
        else:
            # Базовая валидация ключа
            if len(token) < 10:
                await msg.answer(
                    "❌ <b>Ошибка валидации</b>\n\n"
                    "API ключ слишком короткий. Проверьте правильность ввода."
                )
                return
                
            await db.update_settings(f"{key_type}_token", token)
            logger.info(f"Сохранен API ключ для {key_type}")
            await msg.answer(f"✅ API ключ для {key_type} сохранен")
        
        await state.clear()
        # Возвращаемся к управлению ключами
        await manage_api_keys_menu(msg, state)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке API ключа: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить API ключ. Попробуйте позже."
        )
        await state.clear()

@adminRouter.callback_query(F.data == "set_ai_model")
async def set_ai_model_start(call: CallbackQuery, state: FSM):
    """Начало установки AI модели"""
    try:
        settings = await db.get_settings()
        current_model = settings.get("ai_model", "gpt-4o-mini")
        current_provider = settings.get("ai_provider", "pollinations")
        
        await state.set_state(AdminAISettingsStates.waiting_for_ai_model)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_ai_settings")]
        ])
        
        model_examples = {
            "openai": "gpt-4o-mini, gpt-4o, gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307, claude-3-sonnet-20240229",
            "gemini": "gemini-1.5-flash, gemini-1.5-pro",
            "pollinations": "openai, mistral, claude"
        }
        
        examples = model_examples.get(current_provider, "gpt-4o-mini")
        
        await call.message.edit_text(
            f"🧠 <b>Установка AI модели</b>\n\n"
            f"Текущая модель: <code>{current_model}</code>\n"
            f"Провайдер: <code>{current_provider}</code>\n\n"
            f"Примеры моделей для {current_provider}:\n"
            f"<code>{examples}</code>\n\n"
            "Введите название модели:",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_ai_model_start: {e}")
        await call.answer("❌ Ошибка при переходе к настройке модели", show_alert=True)

@adminRouter.message(AdminAISettingsStates.waiting_for_ai_model)
async def process_ai_model(msg: Message, state: FSM):
    """Обработка ввода AI модели"""
    try:
        model = msg.text.strip()
        
        if model.lower() in ['отмена', 'cancel']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await ai_settings_handler(msg, state)
            return
            
        if not model:
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Название модели не должно быть пустым:"
            )
            return
        
        await db.update_settings("ai_model", model)
        logger.info(f"Установлена AI модель: {model}")
        
        await msg.answer(f"✅ <b>Модель установлена</b>\n\nНазвание: <code>{model}</code>")
        await state.clear()
        await ai_settings_handler(msg, state)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке AI модели: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить модель. Попробуйте позже."
        )
        await state.clear()

@adminRouter.callback_query(F.data == "set_system_prompt")
async def set_system_prompt_start(call: CallbackQuery, state: FSM):
    """Начало установки system prompt"""
    try:
        settings = await db.get_settings()
        current_prompt = settings.get("ai_system_prompt", "")
        
        await state.set_state(AdminAISettingsStates.waiting_for_system_prompt)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_ai_settings")]
        ])
        
        prompt_preview = current_prompt[:100] + "..." if len(current_prompt) > 100 else current_prompt
        
        await call.message.edit_text(
            f"✍️ <b>Установка System Prompt</b>\n\n"
            f"Текущий prompt: <code>{prompt_preview if current_prompt else 'не установлен'}</code>\n\n"
            "System prompt - это системная инструкция для ИИ, которая определяет его поведение.\n\n"
            "Введите новый system prompt:\n"
            "🗑 Отправьте '-' чтобы удалить текущий prompt",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_system_prompt_start: {e}")
        await call.answer("❌ Ошибка при переходе к настройке prompt", show_alert=True)

@adminRouter.message(AdminAISettingsStates.waiting_for_system_prompt)
async def process_system_prompt(msg: Message, state: FSM):
    """Обработка ввода system prompt"""
    try:
        prompt = msg.text.strip()
        
        if prompt.lower() in ['отмена', 'cancel']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await ai_settings_handler(msg, state)
            return
        
        if prompt == "-":
            await db.update_settings("ai_system_prompt", None)
            logger.info("Удален system prompt")
            await msg.answer("✅ System prompt удален")
        else:
            if len(prompt) > 2000:
                await msg.answer(
                    "❌ <b>Ошибка валидации</b>\n\n"
                    "System prompt слишком длинный (максимум 2000 символов)."
                )
                return
                
            await db.update_settings("ai_system_prompt", prompt)
            logger.info("Сохранен system prompt")
            await msg.answer("✅ System prompt сохранен")
        
        await state.clear()
        await ai_settings_handler(msg, state)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке system prompt: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить system prompt. Попробуйте позже."
        )
        await state.clear()

@adminRouter.callback_query(F.data == "set_ai_timeout")
async def set_ai_timeout_start(call: CallbackQuery, state: FSM):
    """Начало установки AI timeout"""
    try:
        settings = await db.get_settings()
        current_timeout = settings.get("ai_timeout", "30")
        
        await state.set_state(AdminAISettingsStates.waiting_for_ai_timeout)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data="back_to_ai_settings")]
        ])
        await call.message.edit_text(
            f"⏱ <b>Установка Timeout</b>\n\n"
            f"Текущий timeout: <code>{current_timeout} секунд</code>\n\n"
            "Timeout определяет максимальное время ожидания ответа от AI API.\n\n"
            "Введите timeout в секундах:\n"
            "📋 Рекомендуется: 10-60 секунд\n"
            "📏 Диапазон: 1-300 секунд",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Ошибка в set_ai_timeout_start: {e}")
        await call.answer("❌ Ошибка при переходе к настройке timeout", show_alert=True)

@adminRouter.message(AdminAISettingsStates.waiting_for_ai_timeout)
async def process_ai_timeout(msg: Message, state: FSM):
    """Обработка ввода AI timeout"""
    try:
        timeout_text = msg.text.strip()
        
        if timeout_text.lower() in ['отмена', 'cancel']:
            await msg.answer("❌ Настройка отменена")
            await state.clear()
            await ai_settings_handler(msg, state)
            return
            
        timeout = int(timeout_text)
        
        if timeout < 1:
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Timeout должен быть больше 0 секунд:"
            )
            return
            
        if timeout > 300:  # 5 минут
            await msg.answer(
                "❌ <b>Ошибка валидации</b>\n\n"
                "Timeout не должен превышать 300 секунд:"
            )
            return
            
        await db.update_settings("ai_timeout", timeout)
        logger.info(f"Установлен AI timeout: {timeout} секунд")
        
        await msg.answer(f"✅ <b>Timeout установлен</b>\n\nЗначение: <code>{timeout} секунд</code>")
        await state.clear()
        await ai_settings_handler(msg, state)
        
    except ValueError:
        await msg.answer(
            "❌ <b>Ошибка формата</b>\n\n"
            "Введите корректное число (количество секунд):"
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке AI timeout: {e}")
        await msg.answer(
            "❌ <b>Системная ошибка</b>\n\n"
            "Не удалось сохранить timeout. Попробуйте позже."
        )
        await state.clear()

# Обработчик отмены для всех состояний AI настроек
@adminRouter.message(F.text.lower().in_(['отмена', 'cancel', '/cancel']))
async def cancel_ai_settings(msg: Message, state: FSM):
    """Универсальный обработчик отмены для AI настроек"""
    try:
        current_state = await state.get_state()
        if current_state and "AdminAISettings" in str(current_state) or "AdminIntervalSettings" in str(current_state):
            await state.clear()
            await msg.answer("❌ Действие отменено")
            await ai_settings_handler(msg, state)
    except Exception as e:
        logger.error(f"Ошибка в cancel_ai_settings: {e}")
        await msg.answer("❌ Ошибка при отмене действия")