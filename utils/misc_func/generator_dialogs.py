# Импортируем новую функцию из ai_providers
from utils.misc_func.ai_providers import ai_generate_dialog

# Экспортируем функцию для обратной совместимости
__all__ = ['ai_generate_dialog']
