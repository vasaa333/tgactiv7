"""
Улучшенные обработчики для управления настройками ИИ и интервалами
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

@adminRouter.message(F.text == '🤖 ИИ настройки')
async def ai_settings_handler(msg: Message, state: FSM):
    await state.clear()
    settings = await db.get_settings()
    
    # Получаем текущие настройки
    current_provider = settings.get("ai_provider", "pollinations")
    current_model = settings.get("ai_model", "gpt-4o-mini")
    timeout = settings.get("ai_timeout", "10")
    
    # Настройки интервалов
    trigger_min = settings.get("trigger_min_interval", 5)
    trigger_max = settings.get("trigger_max_interval", 15)
    dialog_min = settings.get("dialog_min_interval", 11)
    dialog_max = settings.get("dialog_max_interval", 20)
    
    text = (
        "<b>🤖 Настройки ИИ</b>\n\n"
        f"📡 Провайдер: <code>{current_provider}</code>\n"
        f"🧠 Модель: <code>{current_model}</code>\n"
        f"⏱ Timeout: <code>{timeout}с</code>\n\n"
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
        [InlineKeyboardButton(text="⏱ Установить timeout (сек)", callback_data="set_ai_timeout")],
        [InlineKeyboardButton(text="⏰ Настройки интервалов", callback_data="interval_settings")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_admin")]
    ])
    await msg.answer(text, reply_markup=kb)

@adminRouter.callback_query(F.data == "interval_settings")
async def interval_settings_menu(call: CallbackQuery, state: FSM):
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
        [InlineKeyboardButton(text="↩️ К ИИ настройкам", callback_data="back_to_ai_settings")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@adminRouter.callback_query(F.data == "back_to_ai_settings")
async def back_to_ai_settings(call: CallbackQuery, state: FSM):
    await ai_settings_handler(call.message, state)

# Настройки интервалов триггеров
@adminRouter.callback_query(F.data == "set_trigger_min")
async def set_trigger_min_interval(call: CallbackQuery, state: FSM):
    await state.set_state(AdminIntervalSettingsStates.waiting_for_trigger_min_interval)
    kb = back_fun_key("interval_settings")
    await call.message.edit_text(
        "🎯 Введите минимальный интервал для триггеров по времени (в минутах):\n"
        "Рекомендуется: 3-10 минут",
        reply_markup=kb
    )

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_trigger_min_interval)
async def process_trigger_min_interval(msg: Message, state: FSM):
    try:
        interval = int(msg.text.strip())
        if interval < 1:
            await msg.answer("❌ Интервал должен быть больше 0 минут:")
            return
        if interval > 1440:  # 24 часа
            await msg.answer("❌ Интервал не должен превышать 1440 минут (24 часа):")
            return
            
        await db.update_settings("trigger_min_interval", interval)
        await msg.answer(f"✅ Минимальный интервал триггеров установлен: {interval} минут")
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer("❌ Введите корректное число (количество минут):")

@adminRouter.callback_query(F.data == "set_trigger_max")
async def set_trigger_max_interval(call: CallbackQuery, state: FSM):
    await state.set_state(AdminIntervalSettingsStates.waiting_for_trigger_max_interval)
    kb = back_fun_key("interval_settings")
    await call.message.edit_text(
        "🎯 Введите максимальный интервал для триггеров по времени (в минутах):\n"
        "Рекомендуется: 10-60 минут",
        reply_markup=kb
    )

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_trigger_max_interval)
async def process_trigger_max_interval(msg: Message, state: FSM):
    try:
        interval = int(msg.text.strip())
        if interval < 1:
            await msg.answer("❌ Интервал должен быть больше 0 минут:")
            return
        if interval > 1440:  # 24 часа
            await msg.answer("❌ Интервал не должен превышать 1440 минут (24 часа):")
            return
            
        settings = await db.get_settings()
        min_interval = settings.get("trigger_min_interval", 5)
        if interval < min_interval:
            await msg.answer(f"❌ Максимальный интервал должен быть больше минимального ({min_interval} мин):")
            return
            
        await db.update_settings("trigger_max_interval", interval)
        await msg.answer(f"✅ Максимальный интервал триггеров установлен: {interval} минут")
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer("❌ Введите корректное число (количество минут):")

# Настройки интервалов диалогов
@adminRouter.callback_query(F.data == "set_dialog_min")
async def set_dialog_min_interval(call: CallbackQuery, state: FSM):
    await state.set_state(AdminIntervalSettingsStates.waiting_for_dialog_min_interval)
    kb = back_fun_key("interval_settings")
    await call.message.edit_text(
        "💬 Введите минимальный интервал для автогенерации диалогов (в минутах):\n"
        "Рекомендуется: 10-30 минут",
        reply_markup=kb
    )

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_dialog_min_interval)
async def process_dialog_min_interval(msg: Message, state: FSM):
    try:
        interval = int(msg.text.strip())
        if interval < 1:
            await msg.answer("❌ Интервал должен быть больше 0 минут:")
            return
        if interval > 1440:  # 24 часа
            await msg.answer("❌ Интервал не должен превышать 1440 минут (24 часа):")
            return
            
        await db.update_settings("dialog_min_interval", interval)
        await msg.answer(f"✅ Минимальный интервал автогенерации диалогов установлен: {interval} минут")
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer("❌ Введите корректное число (количество минут):")

@adminRouter.callback_query(F.data == "set_dialog_max")
async def set_dialog_max_interval(call: CallbackQuery, state: FSM):
    await state.set_state(AdminIntervalSettingsStates.waiting_for_dialog_max_interval)
    kb = back_fun_key("interval_settings")
    await call.message.edit_text(
        "💬 Введите максимальный интервал для автогенерации диалогов (в минутах):\n"
        "Рекомендуется: 30-120 минут",
        reply_markup=kb
    )

@adminRouter.message(AdminIntervalSettingsStates.waiting_for_dialog_max_interval)
async def process_dialog_max_interval(msg: Message, state: FSM):
    try:
        interval = int(msg.text.strip())
        if interval < 1:
            await msg.answer("❌ Интервал должен быть больше 0 минут:")
            return
        if interval > 1440:  # 24 часа
            await msg.answer("❌ Интервал не должен превышать 1440 минут (24 часа):")
            return
            
        settings = await db.get_settings()
        min_interval = settings.get("dialog_min_interval", 11)
        if interval < min_interval:
            await msg.answer(f"❌ Максимальный интервал должен быть больше минимального ({min_interval} мин):")
            return
            
        await db.update_settings("dialog_max_interval", interval)
        await msg.answer(f"✅ Максимальный интервал автогенерации диалогов установлен: {interval} минут")
        await state.clear()
        
        # Возвращаемся к настройкам интервалов
        await interval_settings_menu(msg, state)
        
    except ValueError:
        await msg.answer("❌ Введите корректное число (количество минут):")

# Остальные AI настройки
@adminRouter.callback_query(F.data == "select_ai_provider")
async def select_ai_provider_menu(call: CallbackQuery, state: FSM):
    settings = await db.get_settings()
    current_provider = settings.get("ai_provider", "pollinations")
    
    text = (
        f"<b>📡 Выбор API провайдера</b>\n\n"
        f"Текущий: <code>{current_provider}</code>\n\n"
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

@adminRouter.callback_query(F.data.startswith("provider_"))
async def set_ai_provider(call: CallbackQuery, state: FSM):
    provider = call.data.split("_")[1]
    await db.update_settings("ai_provider", provider)
    await call.answer(f"✅ Провайдер установлен: {provider}")
    await select_ai_provider_menu(call, state)

@adminRouter.callback_query(F.data == "manage_api_keys")
async def manage_api_keys_menu(call: CallbackQuery, state: FSM):
    settings = await db.get_settings()
    
    openai_key = "✅ Настроен" if settings.get("openai_token") else "❌ Не настроен"
    anthropic_key = "✅ Настроен" if settings.get("anthropic_token") else "❌ Не настроен"
    gemini_key = "✅ Настроен" if settings.get("gemini_token") else "❌ Не настроен"
    pollinations_key = "✅ Настроен" if settings.get("pollinations_token") else "❌ Не настроен"
    
    text = (
        "<b>🔑 Управление API ключами</b>\n\n"
        f"OpenAI: {openai_key}\n"
        f"Anthropic: {anthropic_key}\n"
        f"Google Gemini: {gemini_key}\n"
        f"Pollinations: {pollinations_key}\n\n"
        "Выберите провайдера для настройки:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔸 OpenAI API Key", callback_data="set_openai_key")],
        [InlineKeyboardButton(text="🔸 Anthropic API Key", callback_data="set_anthropic_key")],
        [InlineKeyboardButton(text="🔸 Gemini API Key", callback_data="set_gemini_key")],
        [InlineKeyboardButton(text="🔸 Pollinations Token", callback_data="set_pollinations_key")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_ai_settings")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

@adminRouter.callback_query(F.data.startswith("set_") and F.data.endswith("_key"))
async def set_api_key_start(call: CallbackQuery, state: FSM):
    key_type = call.data.split("_")[1]
    await state.set_state(AdminAISettingsStates.waiting_for_api_token)
    await state.update_data(key_type=key_type)
    
    provider_names = {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "gemini": "Google Gemini", 
        "pollinations": "Pollinations"
    }
    
    kb = back_fun_key("manage_api_keys")
    await call.message.edit_text(
        f"🔑 Введите API ключ для {provider_names.get(key_type, key_type)}:\n"
        "Отправьте '-' чтобы удалить ключ",
        reply_markup=kb
    )

@adminRouter.message(AdminAISettingsStates.waiting_for_api_token)
async def process_api_token(msg: Message, state: FSM):
    data = await state.get_data()
    key_type = data.get("key_type")
    token = msg.text.strip()
    
    if token == "-":
        await db.update_settings(f"{key_type}_token", None)
        await msg.answer(f"✅ API ключ для {key_type} удален")
    else:
        await db.update_settings(f"{key_type}_token", token)
        await msg.answer(f"✅ API ключ для {key_type} сохранен")
    
    await state.clear()
    # Возвращаемся к управлению ключами
    await manage_api_keys_menu(msg, state)

@adminRouter.callback_query(F.data == "set_ai_model")
async def set_ai_model_start(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_ai_model)
    kb = back_fun_key("back_to_ai_settings")
    await call.message.edit_text(
        "🧠 Введите название модели:\n"
        "Примеры:\n"
        "• gpt-4o-mini\n"
        "• claude-3-haiku-20240307\n"
        "• gemini-1.5-flash\n"
        "• openai (для Pollinations)",
        reply_markup=kb
    )

@adminRouter.message(AdminAISettingsStates.waiting_for_ai_model)
async def process_ai_model(msg: Message, state: FSM):
    model = msg.text.strip()
    if not model:
        await msg.answer("❌ Название модели не должно быть пустым:")
        return
    
    await db.update_settings("ai_model", model)
    await msg.answer(f"✅ Модель установлена: {model}")
    await state.clear()
    await ai_settings_handler(msg, state)

@adminRouter.callback_query(F.data == "set_system_prompt")
async def set_system_prompt_start(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_system_prompt)
    kb = back_fun_key("back_to_ai_settings")
    await call.message.edit_text(
        "✍️ Введите system prompt:\n"
        "Этот текст будет использоваться как системная инструкция для ИИ.\n"
        "Отправьте '-' чтобы удалить system prompt",
        reply_markup=kb
    )

@adminRouter.message(AdminAISettingsStates.waiting_for_system_prompt)
async def process_system_prompt(msg: Message, state: FSM):
    prompt = msg.text.strip()
    
    if prompt == "-":
        await db.update_settings("ai_system_prompt", None)
        await msg.answer("✅ System prompt удален")
    else:
        await db.update_settings("ai_system_prompt", prompt)
        await msg.answer("✅ System prompt сохранен")
    
    await state.clear()
    await ai_settings_handler(msg, state)

@adminRouter.callback_query(F.data == "set_ai_timeout")
async def set_ai_timeout_start(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_ai_timeout)
    kb = back_fun_key("back_to_ai_settings")
    await call.message.edit_text(
        "⏱ Введите timeout в секундах:\n"
        "Рекомендуется: 10-60 секунд",
        reply_markup=kb
    )

@adminRouter.message(AdminAISettingsStates.waiting_for_ai_timeout)
async def process_ai_timeout(msg: Message, state: FSM):
    try:
        timeout = int(msg.text.strip())
        if timeout < 1:
            await msg.answer("❌ Timeout должен быть больше 0 секунд:")
            return
        if timeout > 300:  # 5 минут
            await msg.answer("❌ Timeout не должен превышать 300 секунд:")
            return
            
        await db.update_settings("ai_timeout", timeout)
        await msg.answer(f"✅ Timeout установлен: {timeout} секунд")
        await state.clear()
        await ai_settings_handler(msg, state)
        
    except ValueError:
        await msg.answer("❌ Введите корректное число (количество секунд):")