from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loader import db
from typing import List, Dict, Set
from loguru import logger

PAGE_SIZE = 5

def two_factor_delete_media(acc_id: int, add_id: int) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(
		InlineKeyboardButton(text='⬅️ Назад', callback_data=f'viewmedia_{add_id}_{acc_id}'),
		InlineKeyboardButton(text='🗑 Да, удалить', callback_data=f'sucdelmedia_{add_id}_{acc_id}')
	)
	return key.as_markup()

def func_media_key(acc_id: int, add_id: int, one_ex: bool, is_active: bool) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(
		InlineKeyboardButton(
			text=f'📢 Рассылка: {"🟢 включена" if is_active else "🔴 выключена"}',
			callback_data=f'spammedia_{"0" if is_active else "1"}_{add_id}_{acc_id}'
		)
	)
	if not one_ex:
		key.row(
			InlineKeyboardButton(text='♻️ Редактировать текст', callback_data=f'mediaedittext_{add_id}_{acc_id}')
		)
	key.row(
		InlineKeyboardButton(text='🗑 Отправить сейчас', callback_data=f'media_send_{add_id}_{acc_id}')
	)
	key.row(
		InlineKeyboardButton(text='⬅️ Назад', callback_data=f'acc_media_{acc_id}'),
		InlineKeyboardButton(text='🗑 Удалить', callback_data=f'media_trash_{add_id}_{acc_id}')
	)
	return key.as_markup()

def view_media_key(acc_id: int, media_dict: dict, start: int = 0, total: int = 0) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()
	keys = list(media_dict.keys())[start:start + PAGE_SIZE]

	for key_dict in keys:
		records = media_dict[key_dict]
		photo, video, gif, document, video_note, voice_note = 0, 0, 0, 0, 0, 0
		media_text = False

		for rec in records:
			if rec['media_text']:
				media_text = True
			match rec['media_type']:
				case 'video':
					video += 1
				case 'photo':
					photo += 1
				case 'gif':
					gif += 1
				case 'document':
					document += 1
				case 'video_note':
					video_note += 1
				case 'voice_note':
					voice_note += 1

		text_parts = []
		if photo > 0:
			text_parts.append(f"{photo} фото")
		if video > 0:
			text_parts.append(f"{video} видео")
		if gif > 0:
			text_parts.append(f"{gif} гиф")
		if document > 0:
			text_parts.append(f"{document} документ")
		if video_note > 0:
			text_parts.append(f"{video_note} кружкок")
		if voice_note > 0:
			text_parts.append(f"{voice_note} голосовое")

		text_btn = "Текст + " + ", ".join(text_parts) if media_text else ", ".join(text_parts)
		kb.row(InlineKeyboardButton(text=text_btn, callback_data=f'viewmedia_{key_dict}_{acc_id}'))

	kb.row(
		InlineKeyboardButton(text="⬅️", callback_data=f"vmdeia_back_{max(0, start-PAGE_SIZE)}_{acc_id}"),
		InlineKeyboardButton(text=f"{min(start+PAGE_SIZE, total)}/{total}", callback_data="noop"),
		InlineKeyboardButton(text="➡️", callback_data=f"vmdeia_next_{min(start+PAGE_SIZE, total)}_{acc_id}")
	)
	kb.row(
		InlineKeyboardButton(text="⬅️ Вернуться", callback_data=f"getacc_{acc_id}"),
		InlineKeyboardButton(text="➕ Добавить медиа", callback_data=f"media_add_{acc_id}")
	)
	return kb.as_markup()

def account_detail_key(acc: Dict) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()
	acc_id = acc['id']

	kb.row(
		InlineKeyboardButton(text="✏️ Изменить прокси", callback_data=f"acc_edit_proxy_{acc_id}"),
		InlineKeyboardButton(text="🗑 Удалить прокси", callback_data=f"acc_remove_proxy_{acc_id}")
	)
	kb.row(
		InlineKeyboardButton(text="♻️ Сменить имя", callback_data=f"upacc_name_{acc_id}"),
		InlineKeyboardButton(text="♻️ Сменить фото", callback_data=f"upacc_photo_{acc_id}")
	)
	kb.row(
		InlineKeyboardButton(text="♻️ Сменить описание", callback_data=f"upacc_about_{acc_id}")
	)

	status = '❌ Отключить' if acc['is_active'] else '✅ Включить'
	kb.row(
		InlineKeyboardButton(text=f"{status} аккаунт", callback_data=f"acc_toggle_active_{acc_id}"),
		InlineKeyboardButton(text="🚫 Удалить аккаунт", callback_data=f"acc_delete_{acc_id}")
	)
	kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="accounts_all"))
	return kb.as_markup()

def acc_delete_confirm_key(acc_id: int) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(
		InlineKeyboardButton(text="✅ Подтвердить удаление", callback_data=f"acc_confirm_delete_{acc_id}"),
		InlineKeyboardButton(text="❌ Отмена", callback_data=f"getacc_{acc_id}")
	)
	return key.as_markup()

def view_proxy_main_key(proxies: List[str], start: int = 0, total: int = 0) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()

	for rec in proxies[start:start+PAGE_SIZE]:
		kb.row(InlineKeyboardButton(text=rec["proxy"], callback_data="noop"))

	kb.row(
		InlineKeyboardButton(text="⬅️", callback_data=f"proxy_back_{max(0, start-PAGE_SIZE)}"),
		InlineKeyboardButton(text=f"{min(start+PAGE_SIZE, total)}/{total}", callback_data="noop"),
		InlineKeyboardButton(text="➡️", callback_data=f"proxy_next_{min(start+PAGE_SIZE, total)}")
	)
	kb.row(
		InlineKeyboardButton(text="➕ Добавить прокси", callback_data="proxy_add"),
		InlineKeyboardButton(text="🗑 Удалить прокси", callback_data="proxy_del")
	)
	return kb.as_markup()

def view_proxy_delete_key(proxies: List[str], start: int = 0, total: int = 0) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()
	for rec in proxies[start:start+PAGE_SIZE]:
		kb.row(InlineKeyboardButton(text=rec["proxy"], callback_data=f"proxy_delete_sel_{rec['id']}"))
	kb.row(
		InlineKeyboardButton(text="⬅️", callback_data=f"proxy_del_back_{max(0, start-PAGE_SIZE)}"),
		InlineKeyboardButton(text=f"{min(start+PAGE_SIZE, total)}/{total}", callback_data="noop"),
		InlineKeyboardButton(text="➡️", callback_data=f"proxy_del_next_{min(start+PAGE_SIZE, total)}")
	)
	kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="proxys"))
	return kb.as_markup()

def view_proxy_confirm_key(proxy_id: int) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(
		InlineKeyboardButton(text="✅ Удалить", callback_data=f"proxy_confirm_delete_{proxy_id}"),
		InlineKeyboardButton(text="❌ Отменить", callback_data="proxys")
	)
	return key.as_markup()

def view_accounts_not_in_chat_key(
	chat_id: int,
	accounts: List[Dict],
	start: int = 0,
	page_size: int = 5,
	total: int = 0,
	selected: Set[int] | None = None
) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()
	selected = selected or set()
	for acc in accounts:
		kb.row(
			InlineKeyboardButton(
				text=f"{'✅ ' if acc['account_id'] in selected else ''}{acc['name']}",
				callback_data=f"select_acc_{chat_id}_{acc['account_id']}"
			)
		)

	kb.row(
		InlineKeyboardButton(text='⬅️ Назад', callback_data=f"add_acc_back_{chat_id}_{max(0, start-page_size)}"),
		InlineKeyboardButton(text=f"{min(start+page_size, total)}/{total}", callback_data='noop'),
		InlineKeyboardButton(text='Вперед ➡️', callback_data=f"add_acc_next_{chat_id}_{min(start+page_size, total)}")
	)
	kb.row(InlineKeyboardButton(text='✅ Завершить добавление', callback_data=f"complete_add_{chat_id}"))
	kb.row(InlineKeyboardButton(text='↩️ Вернуться', callback_data=f'getcc_{chat_id}'))
	return kb.as_markup()

def view_chat_account_delete_key(
	chat_id: int,
	accounts: List[Dict],
	start: int = 0,
	page_size: int = 5,
	total: int = 0,
	selected: Set[int] | None = None
) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()
	selected = selected or set()
	for acc in accounts:
		kb.row(
			InlineKeyboardButton(
				text=f"{'✅ ' if acc['account_id'] in selected else ''}{acc['name']}",
				callback_data=f"toggle_rem_{chat_id}_{acc['account_id']}_{start}"
			)
		)

	kb.row(
		InlineKeyboardButton(text='⬅️ Назад', callback_data=f"accounts_rem_back_{chat_id}_{max(0, start-page_size)}"),
		InlineKeyboardButton(text=f"{min(start+page_size, total)}/{total}", callback_data='noop'),
		InlineKeyboardButton(text='Вперед ➡️', callback_data=f"accounts_rem_next_{chat_id}_{min(start+page_size, total)}")
	)

	if selected:
		kb.row(InlineKeyboardButton(text='✅ Удалить выбранные', callback_data=f"complete_remove_{chat_id}"))
	else:
		kb.row(InlineKeyboardButton(text='❌ Удалить все', callback_data=f"remove_all_{chat_id}"))
	kb.row(InlineKeyboardButton(text='↩️ Вернуться', callback_data=f'getcc_{chat_id}'))
	return kb.as_markup()

def view_accounts_key(accounts_list: List[Dict], start_index: int = 0, page_size: int = 5, total: int = 0) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()
	for acc in accounts_list:
		kb.row(InlineKeyboardButton(text=acc['name'], callback_data=f"getacc_{acc['id']}"))

	kb.row(
		InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_acc_back_{start_index}"),
		InlineKeyboardButton(text=f"{min(start_index+page_size, total)}/{total}", callback_data="noop"),
		InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_acc_next_{start_index+page_size}")
	)
	kb.row(InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="add_account"))
	return kb.as_markup()

def switcher_status_notification_key(status: bool) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	text = "🔴 Выключить" if status else "🟢 Включить"
	status_int = 0 if status else 1
	key.row(
		InlineKeyboardButton(text='↩️ Назад', callback_data="autonotif"),
		InlineKeyboardButton(text=text, callback_data=f"swithcnt_{status_int}")
	)
	return key.as_markup()

def set_chat_key() -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text='🔑 Задать чат', callback_data='set_chat_support'))
	key.row(InlineKeyboardButton(text='↩️ Назад', callback_data='opensettings'))
	return key.as_markup()

def add_chat_key(chat_id: int) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text='✅ Задать', callback_data=f'addchat_{chat_id}'))
	key.row(InlineKeyboardButton(text='↩️ Назад', callback_data='set_chat_support'))
	return key.as_markup()

def add_bot_in_chat(link: str) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text='🔰 Добавить в чат', url=link))
	key.row(InlineKeyboardButton(text='↩️ Назад', callback_data='chatscc'))
	return key.as_markup()

def add_bot_in_chat_admin(link: str) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text='↗️ Добавить бота в чат', url=link))
	key.row(InlineKeyboardButton(text='👁 Проверить', callback_data='check_bot_in_chat'))
	key.row(InlineKeyboardButton(text='↩️ Назад', callback_data='chat_support'))
	return key.as_markup()

def two_factor_del_chat_key(chat_id: str, account_id: int) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(
		InlineKeyboardButton(text='🗑 Да, удалить', callback_data=f'sucdelacc_{account_id}')
	)
	key.row(InlineKeyboardButton(text='↩️ Назад', callback_data=f'getcc_{chat_id}'))
	return key.as_markup()

def chat_menu(chat_id: int, trigger_invite: bool, trigger_time: bool) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	str_trigger_invite = '🟢' if trigger_invite else '🔴'
	str_trigger_time = '🟢' if trigger_time else '🔴'
	key.row(
		InlineKeyboardButton(
			text=f'{str_trigger_invite} Вступление',
			callback_data=f'trigger_invite_switch_{chat_id}_{0 if trigger_invite else 1}'
		),
		InlineKeyboardButton(
			text=f'{str_trigger_time} По времени',
			callback_data=f'trigger_time_switch_{chat_id}_{0 if trigger_time else 1}'
		)
	)
	key.row(InlineKeyboardButton(text='➕ Добавить аккаунты', callback_data=f'accounts_add_{chat_id}'))
	key.row(InlineKeyboardButton(text='🗑 Удалить аккаунты', callback_data=f'trash_accounts_{chat_id}'))
	key.row(InlineKeyboardButton(text='🗑 Удалить чат', callback_data=f'trash_chat_{chat_id}'))
	key.row(InlineKeyboardButton(text='↩️ Назад', callback_data='chats'))
	return key.as_markup()

def two_factor_key_del_chat(chat_id: int) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(
		InlineKeyboardButton(text='↩️ Назад', callback_data=f'getcc_{chat_id}'),
		InlineKeyboardButton(text='🗑 Да, удалить', callback_data=f'suctrash_chat_{chat_id}')
	)
	return key.as_markup()

def view_account_by_chat_id_key(
	chat_id: int,
	accounts_list: List[Dict],
	start_count: int = 0,
	step_count: int = 0,
	total: int = 0
) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	for item in accounts_list:
		title = f"{item['name']}"
		account_id = item['account_id']
		key.row(
			InlineKeyboardButton(text=title, callback_data=f"vacc_{account_id}_{item['chat_id']}"),
			InlineKeyboardButton(text='🗑 Удалить', callback_data=f'delacc_{account_id}_{chat_id}')
		)
	key.row(
		InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_vacc_back_{start_count}"),
		InlineKeyboardButton(text=f"{step_count}/{total}", callback_data="kkkk"),
		InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_vacc_{step_count}_{chat_id}")
	)
	key.row(InlineKeyboardButton(text='➕ Добавить аккаунт', callback_data=f'acc_cc_chat_{chat_id}'))
	return key.as_markup()

def view_chats_key(
	chats_list: List[int],
	start_count: int = 0,
	step_count: int = 0,
	allChats: int = 0
) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	for item in chats_list:
		title = f"{item['title']}"
		key.row(InlineKeyboardButton(text=title, callback_data=f"getcc_{item['chat_id']}"))

	key.row(
		InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_cc_back_{start_count}"),
		InlineKeyboardButton(text=f"{step_count}/{allChats}", callback_data="kkkk"),
		InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_cc_next_{step_count}")
	)
	key.row(InlineKeyboardButton(text='➕ Добавить чат', callback_data='add_chat'))
	return key.as_markup()




def view_dialogs_key(dialogs, start_index=0, page_size=5, total=0):
    """Клавиатура для просмотра диалогов в один столбец с кнопкой очистки"""
    builder = InlineKeyboardBuilder()

    # Кнопки диалогов — выводим в один столбец (каждая кнопка в своей строке)
    for dialog in dialogs:
        builder.row(
            InlineKeyboardButton(text=f"📜 {dialog['name']}", callback_data=f"getdlg_{dialog['id']}")
        )

    # Кнопки навигации
    nav_buttons = []
    if start_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Назад", 
            callback_data=f"list_dlg_back_{start_index}"
        ))
    if start_index + page_size < total:
        nav_buttons.append(InlineKeyboardButton(
            text="Вперёд ▶️", 
            callback_data=f"list_dlg_next_{start_index + page_size}"
        ))

    if nav_buttons:
        builder.row(*nav_buttons)

    # Кнопки действий (в одну строку — добавление/генерация/очистка)
    action_buttons = [
        InlineKeyboardButton(text="🆕 Добавить", callback_data="add_dialog"),
        InlineKeyboardButton(text="🔀 Сгенерировать", callback_data="generate_dialog"),
        InlineKeyboardButton(text="🗑️ Очистить всё", callback_data="clear_dialogs")
    ]
    builder.row(*action_buttons, width=3)

    return builder.as_markup()


def view_proxy_key(proxies: List[str]) -> InlineKeyboardMarkup:
	kb = InlineKeyboardBuilder()

	for p in proxies:
		kb.row(InlineKeyboardButton(text=p, callback_data="noop"))
	kb.row(
		InlineKeyboardButton(text="▶️ Новый прокси", callback_data="get_next_proxy"),
		InlineKeyboardButton(text="➕ Добавить", callback_data="add_proxy"),
		InlineKeyboardButton(text="🗑 Удалить", callback_data="del_proxy")
	)
	return kb.as_markup()

def save_dialog_key(result: Dict) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text="✅ Сохранить в БД", callback_data=f"save_ai_dialog_{result['name']}"))
	key.row(InlineKeyboardButton(text="❌ Отменить", callback_data="dialogs"))
	return key.as_markup()

def back_fun_key(call: str) -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text="↩️ Назад", callback_data=call))
	return key.as_markup()

def wait_key() -> InlineKeyboardMarkup:
	key = InlineKeyboardBuilder()
	key.row(InlineKeyboardButton(text="⏳ Подождите", callback_data="wait"))
	return key.as_markup()

def clear_html(get_text: str) -> str:
	if get_text is not None:
		get_text = (
			get_text.replace("<code>", "")
			.replace("</code>", "")
			.replace("<b>", "")
			.replace("</b>", "")
			.replace("<i>", "")
			.replace("</i>", "")
		)
	else:
		get_text = ""
	return get_text

def clear_dialogs_confirm_key():
    """Клавиатура подтверждения очистки диалогов"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить всё", callback_data="confirm_clear_dialogs"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_clear_dialogs")
        ]
    ])
    return keyboard