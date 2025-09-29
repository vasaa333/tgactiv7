"""
Улучшенный модуль для работы с различными AI провайдерами
Поддерживает OpenAI, Anthropic, Google Gemini, Pollinations, и другие провайдеры
Включает продвинутые возможности управления параметрами генерации
"""
import random
import asyncio
from datetime import datetime
import re
import aiohttp
import urllib.parse
import json
from loguru import logger
from dotenv import load_dotenv
from data.config import PROMPT_TEMPLATE, DETAILS, TIMEOUT
from loader import db
import os
load_dotenv()

class AIProvider:
    """Базовый класс для AI провайдеров"""
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
    
    async def generate_dialog(self, prompt: str, model: str = None, system_prompt: str = None) -> str:
        """Генерирует диалог через AI API"""
        raise NotImplementedError

class OpenAIProvider(AIProvider):
    """Провайдер для OpenAI API"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(api_key, timeout)
        self.base_url = "https://api.openai.com/v1"
    
    async def generate_dialog(self, prompt: str, model: str = "gpt-4o-mini", system_prompt: str = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.8
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error {response.status}: {error_text}")
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]

class AnthropicProvider(AIProvider):
    """Провайдер для Anthropic Claude API"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(api_key, timeout)
        self.base_url = "https://api.anthropic.com/v1"
    
    async def generate_dialog(self, prompt: str, model: str = "claude-3-haiku-20240307", system_prompt: str = None) -> str:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Anthropic API error {response.status}: {error_text}")
                
                data = await response.json()
                return data["content"][0]["text"]

class GeminiProvider(AIProvider):
    """Провайдер для Google Gemini API"""
    
    def __init__(self, api_key: str, timeout: int = 30):
        super().__init__(api_key, timeout)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    async def generate_dialog(self, prompt: str, model: str = "gemini-1.5-flash", system_prompt: str = None) -> str:
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"parts": [{"text": system_prompt}], "role": "user"})
            contents.append({"parts": [{"text": "Понял, буду следовать этим инструкциям."}], "role": "model"})
        
        contents.append({"parts": [{"text": prompt}], "role": "user"})
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.8,
                "maxOutputTokens": 2000
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=self.timeout
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Gemini API error {response.status}: {error_text}")
                
                data = await response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]

class PollinationsProvider(AIProvider):
    """Провайдер для Pollinations AI"""
    
    def __init__(self, api_key: str = None, timeout: int = 30):
        super().__init__(api_key, timeout)
        self.openai_url = "https://text.pollinations.ai/openai"
        self.simple_url = "https://text.pollinations.ai/"
    
    async def generate_dialog(self, prompt: str, model: str = "openai", system_prompt: str = None) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Попытка через OpenAI-совместимый endpoint
            payload = {"model": model, "messages": messages}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.openai_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                ) as response:
                    text = await response.text()
                    try:
                        data = await response.json()
                        if "choices" in data and data["choices"]:
                            choice = data["choices"][0]
                            if "message" in choice and choice["message"].get("content"):
                                return choice["message"]["content"]
                            elif choice.get("text"):
                                return choice["text"]
                        elif data.get("response"):
                            return data["response"]
                    except:
                        pass
                    return text
        except Exception as e:
            logger.warning(f"Pollinations OpenAI endpoint failed: {e}, trying simple endpoint")
            
        # Fallback к простому GET endpoint
        encoded_prompt = urllib.parse.quote(prompt, safe='')
        url = f"{self.simple_url}{encoded_prompt}?json=true"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=self.timeout) as response:
                text = await response.text()
                try:
                    data = await response.json()
                    if isinstance(data, dict):
                        return data.get("response") or data.get("text") or str(data)
                    return str(data)
                except:
                    return text

async def get_ai_provider():
    """Получает настроенный AI провайдер из базы данных с улучшенной обработкой ошибок"""
    try:
        settings = await db.get_settings()
    except Exception as e:
        logger.warning(f"Не удалось загрузить настройки из БД: {e}, используем значения по умолчанию")
        settings = {}
    
    provider_type = settings.get("ai_provider") or "pollinations"
    timeout = int(settings.get("ai_timeout") or TIMEOUT)
    
    logger.info(f"Инициализация AI провайдера: {provider_type} с timeout {timeout}с")
    
    try:
        if provider_type == "openai":
            api_key = settings.get("openai_token") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OpenAI API ключ не настроен")
                raise ValueError("OpenAI API key not configured")
            return OpenAIProvider(api_key, timeout)
        
        elif provider_type == "anthropic":
            api_key = settings.get("anthropic_token") or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.error("Anthropic API ключ не настроен")
                raise ValueError("Anthropic API key not configured")
            return AnthropicProvider(api_key, timeout)
        
        elif provider_type == "gemini":
            api_key = settings.get("gemini_token") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("Gemini API ключ не настроен")
                raise ValueError("Gemini API key not configured")
            return GeminiProvider(api_key, timeout)
        
        else:  # pollinations или неизвестный провайдер - используем по умолчанию
            # Используем персональный ключ HXVnnLNJ84BFvY7Y по умолчанию
            api_key = settings.get("pollinations_token") or os.getenv("POLLINATIONS_TOKEN") or "HXVnnLNJ84BFvY7Y"
            logger.info(f"Используется Pollinations провайдер с ключом: {api_key[:8]}...")
            return PollinationsProvider(api_key, timeout)
            
    except Exception as e:
        logger.error(f"Ошибка при инициализации провайдера {provider_type}: {e}")
        # Fallback к Pollinations с персональным ключом
        logger.info("Fallback к Pollinations провайдеру с персональным ключом")
        return PollinationsProvider("HXVnnLNJ84BFvY7Y", timeout)

async def ai_generate_dialog(num_roles: int) -> dict:
    """
    Генерирует диалог с помощью выбранного AI провайдера с улучшенной обработкой ошибок.
    Возвращаемая структура:
    {
        "name": str,
        "messages": [{"role": "User 1", "text": "..."}, ...],
        "num_accounts": int,
        "raw": raw_text
    }
    """
    try:
        logger.info(f"Запуск генерации диалога для {num_roles} ролей")
        
        # Подготовка prompt
        details_list = []
        if DETAILS:
            try:
                details_list = [d.strip().strip('"') for d in DETAILS if d.strip()]
            except Exception as e:
                logger.warning(f"Ошибка при обработке деталей: {e}")
                details_list = []
        
        detail = random.choice(details_list) if details_list else "случайная бытовая тема"
        prompt = PROMPT_TEMPLATE.format(num=num_roles, detail=detail)
        logger.debug(f"Сгенерированный prompt: {prompt[:100]}...")
        
        # Получаем настройки из БД
        try:
            settings = await db.get_settings()
        except Exception as e:
            logger.warning(f"Не удалось загрузить настройки: {e}, используем значения по умолчанию")
            settings = {}
        
        model = settings.get("ai_model") or "gpt-4o-mini"
        system_prompt = settings.get("ai_system_prompt") or ""
        
        logger.info(f"Используется модель: {model}")
        if system_prompt:
            logger.debug(f"System prompt: {system_prompt[:50]}...")
        
        # Получаем AI провайдер и генерируем диалог
        try:
            provider = await get_ai_provider()
            logger.info(f"Получен провайдер: {type(provider).__name__}")
            
            content = await provider.generate_dialog(prompt, model, system_prompt)
            logger.success(f"Получен ответ от AI ({len(content)} символов)")
            
        except Exception as e:
            logger.error(f"Ошибка при генерации диалога через AI: {e}")
            # Fallback к простому тестовому диалогу
            logger.info("Создание fallback диалога")
            content = f"""User 1: Привет! Как дела?
User 2: Хорошо, спасибо! А у тебя как?
User 1: Тоже всё отлично. Что планируешь на выходные?
User 2: Думаю встретиться с друзьями. А ты?
User 1: Наверное дома буду, отдохну немного."""
        
        # Парсим результат
        lines = []
        try:
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # Поддерживаем форматы: [User 1] text  OR User 1: text
                m = re.match(r"^\\[(?P<role>[^\\]]+)\\]\\s*(?P<text>.+)$", line)
                if not m:
                    m = re.match(r"^(?P<role>User\\s*\\d+)[\\:\\-\\)]*\\s*(?P<text>.+)$", line)
                
                if m:
                    role = m.group("role").strip()
                    text_msg = m.group("text").strip()
                    if text_msg:  # Проверяем что текст не пустой
                        lines.append({"role": role, "text": text_msg})
                        
        except Exception as e:
            logger.error(f"Ошибка при парсинге ответа AI: {e}")
            lines = []
        
        # Если парсинг не дал результата — автоназначение ролей
        if not lines:
            logger.warning("Парсинг не удался, используем автоназначение ролей")
            try:
                chunks = [l.strip() for l in content.splitlines() if l.strip()]
                lines = []
                for i, chunk in enumerate(chunks, start=1):
                    if chunk:  # Проверяем что чанк не пустой
                        role = f"User {((i-1) % num_roles) + 1}"
                        lines.append({"role": role, "text": chunk})
            except Exception as e:
                logger.error(f"Ошибка при автоназначении ролей: {e}")
                # Крайний fallback
                lines = [
                    {"role": "User 1", "text": "Привет!"},
                    {"role": "User 2", "text": "Привет! Как дела?"}
                ]
        
        # Фильтруем только валидные роли User 1..num_roles
        filtered = []
        try:
            for m in lines:
                if not isinstance(m, dict) or "role" not in m or "text" not in m:
                    continue
                    
                mm = re.match(r"User\\s+(\\d+)$", m["role"])
                if mm and 1 <= int(mm.group(1)) <= num_roles:
                    filtered.append(m)
        except Exception as e:
            logger.error(f"Ошибка при фильтрации ролей: {e}")
            filtered = lines[:num_roles]  # Берем первые num_roles сообщений
        
        # Убедимся что есть хотя бы одно сообщение
        if not filtered:
            logger.warning("Нет валидных сообщений, создаем минимальный диалог")
            filtered = [{"role": "User 1", "text": "Привет! Как дела?"}]
        
        name = f"ai_{datetime.now():%Y%m%dT%H%M%SZ}_{random.randint(1000,9999)}"
        
        result = {
            "name": name,
            "messages": filtered,
            "num_accounts": num_roles,
            "raw": content
        }
        
        logger.success(f"Диалог успешно сгенерирован: {name}, сообщений: {len(filtered)}")
        return result
        
    except Exception as e:
        logger.error(f"Критическая ошибка в ai_generate_dialog: {e}")
        # Абсолютный fallback
        name = f"fallback_{datetime.now():%Y%m%dT%H%M%SZ}_{random.randint(1000,9999)}"
        return {
            "name": name,
            "messages": [
                {"role": "User 1", "text": "Привет! Как дела?"},
                {"role": "User 2", "text": "Хорошо, спасибо! А у тебя?"}
            ],
            "num_accounts": num_roles,
            "raw": "Fallback dialog due to generation error"
        }