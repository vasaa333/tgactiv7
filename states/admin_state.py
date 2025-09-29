from aiogram.fsm.state import StatesGroup,State
from typing import Union

class AdminDialogStates(StatesGroup):
    waiting_for_dialog_name = State()        
    waiting_for_dialog_messages = State()    
    waiting_for_num_accounts = State()

class AdminDialogGenerateStates(StatesGroup):
    waiting_for_num_roles = State()   

class AdminAccountStates(StatesGroup):
    waiting_for_account_name = State()     
    waiting_for_session_str = State()      
    waiting_for_proxy = State()   
    waiting_for_proxy_edit = State()   
    waiting_for_name_update = State()  
    waiting_for_about_update = State()
    waiting_for_photo_update = State()      

class AdminChatAccountAddStates(StatesGroup):
    selecting_accounts = State()      

class AdminChatAccountDeleteStates(StatesGroup):
    deleting_accounts = State() 

class AdminAIGenerateStates(StatesGroup):
    waiting_for_num_roles = State()


class AdminProxyStates(StatesGroup):
    waiting_for_proxy_input  = State()  
    waiting_for_proxy_delete = State()

class AdminProxyStates(StatesGroup):
    waiting_for_proxy_add = State()


class AdminUpdateTextMedia(StatesGroup):
    add_id = State()
    acc_id = State()
    text = State()

class AdminAISettingsStates(StatesGroup):
    waiting_for_poll_token = State()
    waiting_for_ai_model = State()
    waiting_for_system_prompt = State()
    waiting_for_ai_timeout = State()
    waiting_for_api_token = State()

class AdminPhoneAuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()
    waiting_for_account_name = State()
    waiting_for_proxy = State()
    waiting_for_two_factor = State()

class AdminIntervalSettingsStates(StatesGroup):
    waiting_for_trigger_min_interval = State()
    waiting_for_trigger_max_interval = State()
    waiting_for_dialog_min_interval = State()
    waiting_for_dialog_max_interval = State()
