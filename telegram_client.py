# telegram_client.py
import asyncio
import logging
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from config import API_ID, API_HASH
from database import save_groups_cache, log_operation

async def add_account_async(session_str, phone, code, password=None):
    """تسجيل الدخول إلى Telegram"""
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.sign_in(phone, code)
        if password:
            await client.sign_in(password=password)
        session_str = client.session.save()
        await client.disconnect()
        return True, session_str
    except Exception as e:
        await client.disconnect()
        return False, str(e)

async def fetch_groups_async(session_str, user_id, account_id):
    """جلب المجموعات من حساب Telegram"""
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    groups = []
    try:
        await client.connect()
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                groups.append({
                    'id': dialog.id,
                    'title': dialog.title,
                    'username': dialog.entity.username if hasattr(dialog.entity, 'username') and dialog.entity.username else None
                })
        await client.disconnect()
        save_groups_cache(user_id, account_id, groups)
        return groups
    except Exception as e:
        logging.error(f"Error fetching groups: {e}")
        await client.disconnect()
        return []

async def send_post_to_groups_async(session_str, user_id, account_id, post_id, content, group_ids):
    """إرسال منشور إلى مجموعة من المجموعات"""
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    results = []
    try:
        await client.connect()
        for group_id in group_ids:
            try:
                entity = await client.get_entity(group_id)
                await client.send_message(entity, content)
                results.append({'group_id': group_id, 'status': 'success'})
                log_operation(user_id, None, account_id, post_id, group_id, 'success')
            except errors.FloodWaitError as e:
                results.append({'group_id': group_id, 'status': 'flood_wait', 'error': str(e)})
                log_operation(user_id, None, account_id, post_id, group_id, 'failed', str(e))
                await asyncio.sleep(e.seconds)
            except errors.ChatWriteForbiddenError:
                results.append({'group_id': group_id, 'status': 'no_permission'})
                log_operation(user_id, None, account_id, post_id, group_id, 'failed', 'لا توجد صلاحية')
            except errors.UserBannedInChannelError:
                results.append({'group_id': group_id, 'status': 'banned'})
                log_operation(user_id, None, account_id, post_id, group_id, 'failed', 'محظور في المجموعة')
            except Exception as e:
                results.append({'group_id': group_id, 'status': 'error', 'error': str(e)})
                log_operation(user_id, None, account_id, post_id, group_id, 'failed', str(e))
        await client.disconnect()
        return results
    except Exception as e:
        await client.disconnect()
        return {'error': str(e)}
