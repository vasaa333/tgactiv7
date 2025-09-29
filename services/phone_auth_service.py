"""
Сервис для авторизации аккаунтов Telegram по номеру телефона
Поддерживает пошаговую авторизацию с сохранением сессии в БД
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from loguru import logger
from telethon import TelegramClient
from telethon.errors import (
    PhoneCodeExpiredError, PhoneCodeInvalidError, 
    SessionPasswordNeededError, PasswordHashInvalidError,
    PhoneNumberInvalidError, FloodWaitError
)
from data.config import API_ID, API_HASH

class PhoneAuthService:
    """Сервис для авторизации по номеру телефона"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.temp_dir = Path("temp_sessions")
        self.temp_dir.mkdir(exist_ok=True)
    
    async def start_auth(self, phone: str, proxy: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Начинает процесс авторизации с улучшенной обработкой ошибок
        Возвращает: (session_id, code_hash)
        """
        try:
            # Создаем временный session ID
            session_id = f"temp_auth_{phone.replace('+', '')}_{int(asyncio.get_event_loop().time())}"
            
            # Настройка прокси
            proxy_config = None
            if proxy and proxy.get('host'):
                proxy_config = {
                    'proxy_type': proxy['type'],
                    'addr': proxy['host'],
                    'port': proxy['port'],
                    'username': proxy.get('username'),
                    'password': proxy.get('password')
                }
                logger.info(f"Используется прокси: {proxy['type']}://{proxy['host']}:{proxy['port']}")
            
            # Создаем временную сессию
            session_file = self.temp_dir / f"{session_id}.session"
            client = TelegramClient(str(session_file), API_ID, API_HASH, proxy=proxy_config)
            
            try:
                logger.info(f"Подключение к Telegram для номера {phone}")
                await client.connect()
                
                # Проверяем подключение
                if not client.is_connected():
                    raise ConnectionError("Не удалось подключиться к серверам Telegram")
                
                # Отправляем код
                logger.info(f"Отправка кода подтверждения на {phone}")
                sent_code = await client.send_code_request(phone)
                
                # Сохраняем информацию о сессии
                self.sessions[session_id] = {
                    'client': client,
                    'phone': phone,
                    'code_hash': sent_code.phone_code_hash,
                    'proxy': proxy,
                    'session_file': session_file,
                    'authenticated': False,
                    'created_at': asyncio.get_event_loop().time()
                }
                
                logger.success(f"Код успешно отправлен на номер {phone}, session_id: {session_id}")
                return session_id, sent_code.phone_code_hash
                
            except PhoneNumberInvalidError:
                await client.disconnect()
                logger.error(f"Неверный номер телефона: {phone}")
                raise ValueError("❌ Неверный номер телефона. Проверьте формат (+79123456789)")
            except FloodWaitError as e:
                await client.disconnect()
                logger.warning(f"Flood limit для номера {phone}, ожидание {e.seconds} секунд")
                raise ValueError(f"⏳ Слишком много попыток. Попробуйте через {e.seconds} секунд")
            except ConnectionError as e:
                await client.disconnect()
                logger.error(f"Ошибка подключения: {e}")
                raise ValueError("🌐 Ошибка подключения к серверам Telegram. Проверьте интернет соединение")
            except Exception as e:
                await client.disconnect()
                logger.error(f"Неожиданная ошибка при отправке кода: {e}")
                raise ValueError(f"❌ Ошибка при отправке кода: {str(e)}")
                
        except Exception as e:
            logger.error(f"Критическая ошибка в start_auth: {e}")
            raise ValueError(f"❌ Критическая ошибка: {str(e)}")
    
    async def verify_code(self, session_id: str, code: str) -> Tuple[bool, bool]:
        """
        Проверяет код подтверждения с улучшенной обработкой ошибок
        Возвращает: (success, needs_password)
        """
        try:
            if session_id not in self.sessions:
                logger.error(f"Сессия не найдена: {session_id}")
                raise ValueError("❌ Сессия не найдена или истекла")
            
            session_data = self.sessions[session_id]
            client = session_data['client']
            
            # Проверяем подключение клиента
            if not client.is_connected():
                logger.warning(f"Клиент не подключен для сессии {session_id}, переподключение...")
                await client.connect()
            
            try:
                logger.info(f"Проверка кода для сессии {session_id}")
                await client.sign_in(
                    phone=session_data['phone'],
                    code=code,
                    phone_code_hash=session_data['code_hash']
                )
                
                session_data['authenticated'] = True
                logger.success(f"Код подтвержден для сессии {session_id}")
                return True, False
                
            except SessionPasswordNeededError:
                logger.info(f"Требуется пароль двухфакторной аутентификации для сессии {session_id}")
                return True, True
                
            except PhoneCodeExpiredError:
                logger.error(f"Код истек для сессии {session_id}")
                raise ValueError("⏰ Код подтверждения истек. Запросите новый код")
            except PhoneCodeInvalidError:
                logger.error(f"Неверный код для сессии {session_id}")
                raise ValueError("❌ Неверный код подтверждения. Проверьте правильность ввода")
            except FloodWaitError as e:
                logger.warning(f"Flood limit при проверке кода для сессии {session_id}")
                raise ValueError(f"⏳ Слишком много попыток. Подождите {e.seconds} секунд")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при проверке кода для сессии {session_id}: {e}")
                raise ValueError(f"❌ Ошибка при проверке кода: {str(e)}")
                
        except Exception as e:
            logger.error(f"Критическая ошибка в verify_code: {e}")
            raise ValueError(f"❌ Критическая ошибка: {str(e)}")
    
    async def verify_password(self, session_id: str, password: str) -> bool:
        """
        Проверяет пароль двухфакторной аутентификации с улучшенной обработкой ошибок
        Возвращает: success
        """
        try:
            if session_id not in self.sessions:
                logger.error(f"Сессия не найдена при проверке пароля: {session_id}")
                raise ValueError("❌ Сессия не найдена или истекла")
            
            session_data = self.sessions[session_id]
            client = session_data['client']
            
            # Проверяем подключение клиента
            if not client.is_connected():
                logger.warning(f"Клиент не подключен для сессии {session_id}, переподключение...")
                await client.connect()
            
            try:
                logger.info(f"Проверка пароля двухфакторной аутентификации для сессии {session_id}")
                await client.sign_in(password=password)
                session_data['authenticated'] = True
                logger.success(f"Пароль подтвержден для сессии {session_id}")
                return True
                
            except PasswordHashInvalidError:
                logger.error(f"Неверный пароль для сессии {session_id}")
                raise ValueError("❌ Неверный пароль двухфакторной аутентификации")
            except FloodWaitError as e:
                logger.warning(f"Flood limit при проверке пароля для сессии {session_id}")
                raise ValueError(f"⏳ Слишком много попыток. Подождите {e.seconds} секунд")
            except Exception as e:
                logger.error(f"Неожиданная ошибка при проверке пароля для сессии {session_id}: {e}")
                raise ValueError(f"❌ Ошибка при проверке пароля: {str(e)}")
                
        except Exception as e:
            logger.error(f"Критическая ошибка в verify_password: {e}")
            raise ValueError(f"❌ Критическая ошибка: {str(e)}")
    
    async def save_session(self, session_id: str, account_name: str) -> str:
        """
        Сохраняет аутентифицированную сессию в постоянное хранилище
        Возвращает: final_session_name
        """
        if session_id not in self.sessions:
            raise ValueError("Сессия не найдена")
        
        session_data = self.sessions[session_id]
        
        if not session_data['authenticated']:
            raise ValueError("Сессия не аутентифицирована")
        
        client = session_data['client']
        
        try:
            # Получаем информацию о пользователе
            me = await client.get_me()
            
            # Создаем финальное имя сессии
            final_session_name = f"{account_name}_{me.id}_{asyncio.get_event_loop().time()}"
            
            # Путь для постоянного хранения сессии
            final_session_path = Path("sessions") / f"{final_session_name}.session"
            final_session_path.parent.mkdir(exist_ok=True)
            
            # Отключаемся и переименовываем файл сессии
            await client.disconnect()
            
            # Перемещаем временную сессию в постоянное место
            session_data['session_file'].rename(final_session_path)
            
            # Возвращаем данные для сохранения в БД
            account_data = {
                'session_name': final_session_name,
                'phone_number': session_data['phone'],
                'account_id': me.id,
                'name': account_name,
                'proxy': json.dumps(session_data['proxy']) if session_data['proxy'] else None,
                'is_active': True
            }
            
            # Очищаем временную сессию
            self.cleanup_session(session_id)
            
            logger.success(f"Сессия сохранена: {final_session_name}")
            return account_data
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении сессии: {e}")
            raise ValueError(f"Ошибка при сохранении сессии: {str(e)}")
    
    def cleanup_session(self, session_id: str):
        """Очищает временную сессию"""
        if session_id in self.sessions:
            session_data = self.sessions[session_id]
            
            # Закрываем клиент если он еще активен
            try:
                client = session_data['client']
                if client.is_connected():
                    asyncio.create_task(client.disconnect())
            except Exception:
                pass
            
            # Удаляем временный файл сессии
            try:
                session_file = session_data['session_file']
                if session_file.exists():
                    session_file.unlink()
            except Exception:
                pass
            
            # Удаляем из памяти
            del self.sessions[session_id]
            logger.info(f"Временная сессия {session_id} очищена")
    
    def cleanup_all_sessions(self):
        """Очищает все временные сессии"""
        for session_id in list(self.sessions.keys()):
            self.cleanup_session(session_id)
        
        # Очищаем директорию временных сессий
        try:
            for file in self.temp_dir.glob("*.session"):
                file.unlink()
        except Exception:
            pass

# Глобальный экземпляр сервиса
phone_auth_service = PhoneAuthService()