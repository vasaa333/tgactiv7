from aiogram import F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loader import adminRouter, db
from utils.misc_func.bot_models import FSM
from states.admin_state import AdminAISettingsStates
from keyboards.reply.adminkey import kbMainAdmin
from utils.misc_func.config_sync import write_env_var

@adminRouter.message(F.text == '⚙️ AI Настройки')
async def ai_settings_menu(msg: Message, state: FSM):
    await state.clear()
    settings = await db.get_settings()
    
    # Получаем все настройки AI
    api_provider = settings.get("ai_provider") or "pollinations"
    openai_token = settings.get("openai_token") or "не задан"
    anthropic_token = settings.get("anthropic_token") or "не задан"
    gemini_token = settings.get("gemini_token") or "не задан"
    pollinations_token = settings.get("pollinations_token") or "не задан"
    model = settings.get("ai_model") or "gpt-4o-mini"
    system = settings.get("ai_system_prompt") or "не задан"
    timeout = settings.get("ai_timeout") or 10

    # Определяем какой токен показать
    current_token = "не задан"
    if api_provider == "openai":
        current_token = openai_token
    elif api_provider == "anthropic":
        current_token = anthropic_token
    elif api_provider == "gemini":
        current_token = gemini_token
    elif api_provider == "pollinations":
        current_token = pollinations_token

    text = (
        f"<b>⚙️ AI — настройки</b>\n\n"
        f"📡 API провайдер: <b>{api_provider}</b>\n"
        f"🔑 Текущий API ключ: <code>{current_token if len(str(current_token))<40 else (str(current_token)[:36]+'...')}</code>\n"
        f"🧠 Модель: <b>{model}</b>\n"
        f"✍️ System prompt: <code>{system if system else 'не задан'}</code>\n"
        f"⏱ Timeout (s): <b>{timeout}</b>\n\n"
        "Выберите настройку для изменения:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Выбрать API провайдера", callback_data="select_ai_provider")],
        [InlineKeyboardButton(text="🔑 Настроить API ключи", callback_data="manage_api_keys")],
        [InlineKeyboardButton(text="🧠 Установить модель", callback_data="set_ai_model")],
        [InlineKeyboardButton(text="✍️ Установить system prompt", callback_data="set_system_prompt")],
        [InlineKeyboardButton(text="⏱ Установить timeout (сек)", callback_data="set_ai_timeout")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_admin")]
    ])
    await msg.answer(text, reply_markup=kb)

@adminRouter.callback_query(F.data == "back_to_admin")
async def back_to_admin(call: CallbackQuery, state: FSM):
    await state.clear()
    kb = kbMainAdmin()
    await call.message.edit_text("Админ-панель", reply_markup=kb)

@adminRouter.callback_query(F.data == "set_poll_token")
async def set_poll_token(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_poll_token)
    await call.message.edit_text("Введите ваш Pollinations token (полная строка):")

@adminRouter.message(AdminAISettingsStates.waiting_for_poll_token)
async def process_poll_token(msg: Message, state: FSM):
    token = msg.text.strip()
    await db.update_settings(pollinations_token=token)
    # Синхронизируем с .env
    try:
        write_env_var('POLLINATIONS_TOKEN', token)
    except Exception:
        pass
    await state.clear()
    await msg.answer("✅ Token сохранён в настройках и в .env.", reply_markup=kbMainAdmin())

@adminRouter.callback_query(F.data == "set_ai_model")
async def set_ai_model(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_ai_model)
    await call.message.edit_text("Введите название модели (например: openai, mistral, gpt-4o-mini):")

@adminRouter.message(AdminAISettingsStates.waiting_for_ai_model)
async def process_ai_model(msg: Message, state: FSM):
    model = msg.text.strip()
    await db.update_settings(ai_model=model)
    await state.clear()
    await msg.answer(f"✅ Model установлена: {model}", reply_markup=kbMainAdmin())

@adminRouter.callback_query(F.data == "set_system_prompt")
async def set_system_prompt(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_system_prompt)
    await call.message.edit_text("Введите системное сообщение (system prompt) для AI:")

@adminRouter.message(AdminAISettingsStates.waiting_for_system_prompt)
async def process_system_prompt(msg: Message, state: FSM):
    prompt = msg.text.strip()
    await db.update_settings(ai_system_prompt=prompt)
    try:
        write_env_var('POLLINATIONS_SYSTEM_PROMPT', prompt)
    except Exception:
        pass
    await state.clear()
    await msg.answer("✅ System prompt сохранён и синхронизирован.", reply_markup=kbMainAdmin())

@adminRouter.callback_query(F.data == "set_ai_timeout")
async def set_ai_timeout(call: CallbackQuery, state: FSM):
    await state.set_state(AdminAISettingsStates.waiting_for_ai_timeout)
    await call.message.edit_text("Введите таймаут в секундах (целое число):")

@adminRouter.message(AdminAISettingsStates.waiting_for_ai_timeout)
async def process_ai_timeout(msg: Message, state: FSM):
    text = msg.text.strip()
    if not text.isdigit():
        await msg.answer("❌ Введите целое число (например: 10).")
        return
    timeout = int(text)
    await db.update_settings(ai_timeout=timeout)
    try:
        write_env_var('POLLINATIONS_TIMEOUT', str(timeout))
    except Exception:
        pass
    await state.clear()
    await msg.answer(f"✅ Timeout установлен: {timeout}s и сохранён в .env", reply_markup=kbMainAdmin())

# Новые обработчики для выбора API провайдера
@adminRouter.callback_query(F.data == "select_ai_provider")
async def select_ai_provider(call: CallbackQuery, state: FSM):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Pollinations AI", callback_data="provider_pollinations")],
        [InlineKeyboardButton(text="🤖 OpenAI", callback_data="provider_openai")],
        [InlineKeyboardButton(text="🧠 Anthropic Claude", callback_data="provider_anthropic")],
        [InlineKeyboardButton(text="💎 Google Gemini", callback_data="provider_gemini")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_ai_settings")]
    ])
    await call.message.edit_text("📡 Выберите API провайдера для генерации диалогов:", reply_markup=kb)

@adminRouter.callback_query(F.data.startswith("provider_"))
async def set_provider(call: CallbackQuery, state: FSM):
    provider = call.data.replace("provider_", "")
    await db.update_settings(ai_provider=provider)
    await call.answer(f"✅ Установлен провайдер: {provider}")
    await ai_settings_menu_callback(call, state)

@adminRouter.callback_query(F.data == "back_to_ai_settings")
async def ai_settings_menu_callback(call: CallbackQuery, state: FSM):
    settings = await db.get_settings()
    
    # Получаем все настройки AI
    api_provider = settings.get("ai_provider") or "pollinations"
    openai_token = settings.get("openai_token") or "не задан"
    anthropic_token = settings.get("anthropic_token") or "не задан"
    gemini_token = settings.get("gemini_token") or "не задан"
    pollinations_token = settings.get("pollinations_token") or "не задан"
    model = settings.get("ai_model") or "gpt-4o-mini"
    system = settings.get("ai_system_prompt") or "не задан"
    timeout = settings.get("ai_timeout") or 10

    # Определяем какой токен показать
    current_token = "не задан"
    if api_provider == "openai":
        current_token = openai_token
    elif api_provider == "anthropic":
        current_token = anthropic_token
    elif api_provider == "gemini":
        current_token = gemini_token
    elif api_provider == "pollinations":
        current_token = pollinations_token

    text = (
        f"<b>⚙️ AI — настройки</b>\n\n"
        f"📡 API провайдер: <b>{api_provider}</b>\n"
        f"🔑 Текущий API ключ: <code>{current_token if len(str(current_token))<40 else (str(current_token)[:36]+'...')}</code>\n"
        f"🧠 Модель: <b>{model}</b>\n"
        f"✍️ System prompt: <code>{system if system else 'не задан'}</code>\n"
        f"⏱ Timeout (s): <b>{timeout}</b>\n\n"
        "Выберите настройку для изменения:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📡 Выбрать API провайдера", callback_data="select_ai_provider")],
        [InlineKeyboardButton(text="🔑 Настроить API ключи", callback_data="manage_api_keys")],
        [InlineKeyboardButton(text="🧠 Установить модель", callback_data="set_ai_model")],
        [InlineKeyboardButton(text="✍️ Установить system prompt", callback_data="set_system_prompt")],
        [InlineKeyboardButton(text="⏱ Установить timeout (сек)", callback_data="set_ai_timeout")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_admin")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

# Управление API ключами
@adminRouter.callback_query(F.data == "manage_api_keys")
async def manage_api_keys(call: CallbackQuery, state: FSM):
    settings = await db.get_settings()
    provider = settings.get("ai_provider") or "pollinations"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Pollinations Token", callback_data="set_token_pollinations")],
        [InlineKeyboardButton(text="🤖 OpenAI API Key", callback_data="set_token_openai")],
        [InlineKeyboardButton(text="🧠 Anthropic API Key", callback_data="set_token_anthropic")],
        [InlineKeyboardButton(text="💎 Gemini API Key", callback_data="set_token_gemini")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_ai_settings")]
    ])
    await call.message.edit_text(
        f"🔑 Управление API ключами\n\n"
        f"Текущий провайдер: <b>{provider}</b>\n"
        f"Выберите какой ключ хотите изменить:",
        reply_markup=kb
    )

@adminRouter.callback_query(F.data.startswith("set_token_"))
async def set_token_start(call: CallbackQuery, state: FSM):
    provider = call.data.replace("set_token_", "")
    await state.update_data(setting_provider=provider)
    
    provider_names = {
        "pollinations": "Pollinations AI",
        "openai": "OpenAI",
        "anthropic": "Anthropic Claude",
        "gemini": "Google Gemini"
    }
    
    provider_name = provider_names.get(provider, provider)
    await state.set_state(AdminAISettingsStates.waiting_for_api_token)
    await call.message.edit_text(f"🔑 Введите API ключ для {provider_name}:")

@adminRouter.message(AdminAISettingsStates.waiting_for_api_token)
async def process_api_token(msg: Message, state: FSM):
    data = await state.get_data()
    provider = data.get("setting_provider")
    token = msg.text.strip()
    
    # Сохраняем токен в соответствующее поле базы данных
    if provider == "pollinations":
        await db.update_settings(pollinations_token=token)
        write_env_var('POLLINATIONS_TOKEN', token)
    elif provider == "openai":
        await db.update_settings(openai_token=token)
        write_env_var('OPENAI_API_KEY', token)
    elif provider == "anthropic":
        await db.update_settings(anthropic_token=token)
        write_env_var('ANTHROPIC_API_KEY', token)
    elif provider == "gemini":
        await db.update_settings(gemini_token=token)
        write_env_var('GEMINI_API_KEY', token)
    
    await state.clear()
    await msg.answer(f"✅ API ключ для {provider} сохранён!", reply_markup=kbMainAdmin())
