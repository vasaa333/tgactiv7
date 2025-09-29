"""
Минимальные обработчики для аккаунтов с авторизацией по телефону
"""

from aiogram import F
from aiogram.types import Message, CallbackQuery
from utils.misc_func.bot_models import FSM
from loader import adminRouter, db, account_manager
from states.admin_state import AdminPhoneAuthStates
from keyboards.inline.adminkeyinline import *
from services.phone_auth_service import phone_auth_service
from loguru import logger
import re

@adminRouter.message(F.text == '👤 Аккаунты')
async def view_all_accounts(msg: Message, state: FSM):
    """Просмотр всех аккаунтов"""
    try:
        await state.clear()
        accounts = await db.get_all_telegram_accounts()
        
        if not accounts:
            text = "📋 Список аккаунтов пуст. Добавьте первый аккаунт для начала работы."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="add_account_phone")]
            ])
        else:
            text = f"👤 Аккаунты ({len(accounts)}):\n\n"
            for i, account in enumerate(accounts[:5], 1):
                status = "🟢" if account.get('is_active') else "🔴"
                name = account.get('name') or 'Без имени'
                text += f"{i}. {status} {name}\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="add_account_phone")]
            ])
        
        await msg.answer(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке аккаунтов: {e}")
        await msg.answer("❌ Ошибка при загрузке списка аккаунтов")

@adminRouter.callback_query(F.data == "add_account_phone")
async def start_phone_auth(call: CallbackQuery, state: FSM):
    """Начало процесса авторизации по номеру телефона"""
    try:
        await state.set_state(AdminPhoneAuthStates.waiting_for_phone)
        await call.message.edit_text(
            "📱 Авторизация по номеру телефона\n\n"
            "Введите номер телефона в международном формате:\n"
            "Например: +79123456789"
        )
    except Exception as e:
        logger.error(f"Ошибка в start_phone_auth: {e}")
        await call.answer("❌ Ошибка", show_alert=True)

@adminRouter.message(AdminPhoneAuthStates.waiting_for_phone)
async def process_phone_number(msg: Message, state: FSM):
    """Обработка номера телефона"""
    try:
        phone = msg.text.strip()
        
        if not re.match(r'^\+\d{10,15}$', phone):
            await msg.answer("❌ Неверный формат номера. Используйте +79123456789")
            return
        
        session_id, code_hash = await phone_auth_service.start_auth(phone)
        
        await state.update_data(
            phone=phone,
            session_id=session_id,
            code_hash=code_hash
        )
        
        await state.set_state(AdminPhoneAuthStates.waiting_for_code)
        await msg.answer(f"✅ SMS код отправлен на номер {phone}\nВведите полученный код:")
        
    except ValueError as e:
        await msg.answer(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при обработке номера телефона: {e}")
        await msg.answer("❌ Ошибка при отправке кода")

@adminRouter.message(AdminPhoneAuthStates.waiting_for_code)
async def process_verification_code(msg: Message, state: FSM):
    """Обработка SMS кода"""
    try:
        code = msg.text.strip()
        data = await state.get_data()
        session_id = data['session_id']
        
        success, needs_2fa = await phone_auth_service.verify_code(session_id, code)
        
        if success:
            if needs_2fa:
                await state.set_state(AdminPhoneAuthStates.waiting_for_two_factor)
                await msg.answer("🔐 Требуется код двухфакторной аутентификации:")
            else:
                await state.set_state(AdminPhoneAuthStates.waiting_for_account_name)
                await msg.answer("✅ Авторизация успешна. Введите имя для аккаунта:")
        else:
            await msg.answer("❌ Неверный код. Попробуйте еще раз")
            
    except ValueError as e:
        await msg.answer(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при проверке кода: {e}")
        await msg.answer("❌ Ошибка при проверке кода")

@adminRouter.message(AdminPhoneAuthStates.waiting_for_two_factor)
async def process_two_factor_auth(msg: Message, state: FSM):
    """Обработка двухфакторной аутентификации"""
    try:
        auth_code = msg.text.strip()
        data = await state.get_data()
        session_id = data['session_id']
        
        success = await phone_auth_service.verify_password(session_id, auth_code)
        
        if success:
            await state.set_state(AdminPhoneAuthStates.waiting_for_account_name)
            await msg.answer("✅ Двухфакторная аутентификация пройдена. Введите имя для аккаунта:")
        else:
            await msg.answer("❌ Неверный код. Попробуйте еще раз")
            
    except ValueError as e:
        await msg.answer(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при проверке 2FA: {e}")
        await msg.answer("❌ Ошибка при проверке кода")

@adminRouter.message(AdminPhoneAuthStates.waiting_for_account_name)
async def process_account_name(msg: Message, state: FSM):
    """Обработка имени аккаунта"""
    try:
        account_name = msg.text.strip()
        data = await state.get_data()
        session_id = data['session_id']
            
        if not account_name or len(account_name) < 2:
            await msg.answer("❌ Имя аккаунта должно содержать минимум 2 символа")
            return
        
        await state.update_data(account_name=account_name)
        await state.set_state(AdminPhoneAuthStates.waiting_for_proxy)
        await msg.answer("🌐 Введите прокси или отправьте '-' если прокси не нужен")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке имени аккаунта: {e}")
        await msg.answer("❌ Ошибка при сохранении имени")

@adminRouter.message(AdminPhoneAuthStates.waiting_for_proxy)
async def process_proxy_and_finish(msg: Message, state: FSM):
    """Обработка прокси и завершение"""
    try:
        proxy_text = msg.text.strip()
        data = await state.get_data()
        session_id = data['session_id']
        account_name = data['account_name']
        
        # Сохраняем аккаунт
        account_data = await phone_auth_service.save_session(session_id, account_name)
        
        # Добавляем в БД
        session_name = await account_manager.add_account_from_data(account_data)
        
        await state.clear()
        await msg.answer(
            f"✅ Аккаунт успешно добавлен\n\n"
            f"Имя: {account_name}\n"
            f"Сессия: {session_name}"
        )
        
        # Показываем обновленный список
        accounts = await db.get_all_telegram_accounts()
        text = f"👤 Обновлённый список аккаунтов ({len(accounts)}):\n\n"
        for i, account in enumerate(accounts, 1):
            status = "🟢" if account.get('is_active') else "🔴"
            name = account.get('name') or 'Без имени'
            text += f"{i}. {status} {name}\n"
        
        await msg.answer(text)
        
    except ValueError as e:
        await msg.answer(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при завершении добавления аккаунта: {e}")
        await msg.answer("❌ Ошибка при сохранении аккаунта")
        # Очищаем сессию при ошибке
        data = await state.get_data()
        if 'session_id' in data:
            phone_auth_service.cleanup_session(data['session_id'])
        await state.clear()