import asyncio
import json
import logging
import os
from telethon import TelegramClient, events

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s\n' + '=' * 80,
    datefmt='%m-%d %H:%M:%S'
)


# Telegram API 配置
API_ID = 285231945
API_HASH = "54cf100609a3c254350479fb8325a6341"
PHONE_NUMBER = ""


# 敏感词列表
# 您好！这里是ZF-DA组，我们将不定时抽查各组的值班和远程在线情况，以确保能够及时联系到值班或远程员工。请您在看到此消息后尽快回复，以便我们确认您的在线状态。感谢配合！🌸🌸🌸
# 亲，感谢您的回复，~ 请您配合提供右下角包含电脑时间日期的截图吧，谢谢！
SENSITIVE_WORDS = ['ZF-DA组', '不定时抽查', '请您配合', '在线状态', '你好', '您好']


# 时间追踪
last_group_mention = {}
last_private_message = {}
mention_timers = {}
private_timers = {}


# 创建 Telegram 客户端
client = TelegramClient('tg_monitor_bot', API_ID, API_HASH)


# 临时改变音量播放提示音，播放完恢复
def play_sound_with_volume(sound_path, target_volume=90, loop=1):
    # 保存当前音量
    original_volume = int(os.popen('osascript -e "output volume of (get volume settings)"').read())
    # 设置临时音量
    os.system(f'osascript -e "set volume output volume {target_volume}"')
    # 循环播放音频
    for i in range(loop):
        os.system(f'afplay {sound_path}')
    # 恢复原音量
    os.system(f'osascript -e "set volume output volume {original_volume}"')


def play_sound_1():
    logging.info("🔔 提示音1 - 私聊敏感词")
    # play_sound_with_volume('/System/Library/Sounds/Ping.aiff', loop=20)
    play_sound_with_volume('music.mp3')


def play_sound_2():
    logging.info("🔔 提示音2 - 群聊被@")
    play_sound_with_volume('/System/Library/Sounds/Hero.aiff', loop=5)


def play_sound_3():
    logging.info("🔔 提示音3 - 私聊长时间未回复")
    play_sound_with_volume('/System/Library/Sounds/Funk.aiff', loop=5)

# 检查群聊@后3分钟是否回复
async def check_group_mention_timeout(title, username, chat_id, num_minutes=3):
    await asyncio.sleep(num_minutes*60)
    
    if chat_id in last_group_mention:
        play_sound_2()
        logging.info(f"群组 {title} 被 {username} @后{num_minutes}分钟未回复")
        del last_group_mention[chat_id]
        mention_timers.pop(chat_id, None)

# 检查私聊后10分钟是否回复
async def check_private_timeout(username, sender_id, num_minutes=3):
    await asyncio.sleep(num_minutes*60)
    
    if sender_id in last_private_message:
        play_sound_3()
        logging.info(f"用户 {username} 私聊{num_minutes}分钟未回复")
        del last_private_message[sender_id]
        private_timers.pop(sender_id, None)


# 监听新消息
@client.on(events.MessageEdited(incoming=True))
@client.on(events.NewMessage(incoming=True))
async def handle_new_message(event):
    chat = await event.get_chat()
    logging.info(f"群聊消息: \n{json.dumps(chat.__dict__, default=str, ensure_ascii=False)}")
    sender = await event.get_sender()
    logging.info(f"私聊消息: \n{json.dumps(sender.__dict__, default=str, ensure_ascii=False)}")
    sender_id = event.sender_id
    sender_username = sender.username if sender.username else "Unknown"
    sender_first_name = sender.first_name if sender.first_name else "Unknown"
    sender_last_name = sender.last_name if sender.last_name else "Unknown"
    user_name = f"{sender_first_name if sender_first_name else sender_last_name}(@{sender_username})"
    event_message = event.message.message if event.message and event.message.message else "No Text"
    logging.info(f"收到 {sender_id} 的消息 - 来自: {user_name} 内容: {event_message}")

    # 群聊 - 检查是否被@
    if event.is_group:
        me = await client.get_me()
        if event.mentioned or (event_message and f"@{me.username}" in event_message):
            chat_title = chat.title if chat.title else "Unknown"
            logging.info(f"在群组 {chat_title} 中被 {user_name} 给@了")
            
            chat_id = event.chat_id
            last_group_mention[chat_id] = True
            
            # 取消旧定时器，创建新定时器
            if chat_id in mention_timers:
                mention_timers[chat_id].cancel()
            mention_timers[chat_id] = asyncio.create_task(check_group_mention_timeout(chat_title, user_name, chat_id))
    
    # 私聊
    elif event.is_private and not event.is_channel:
        logging.info(f"处理 {user_name} 的私聊消息")
        
        # 检查敏感词
        message_text = event_message or ""
        if any(word in message_text for word in SENSITIVE_WORDS):
            play_sound_1()
            logging.info(f"私聊包含敏感词 - 用户: {user_name}")
        
        # 设置10分钟定时器
        last_private_message[sender_id] = True
        if sender_id in private_timers:
            private_timers[sender_id].cancel()
        private_timers[sender_id] = asyncio.create_task(check_private_timeout(user_name, sender_id))


# 监听自己发送的消息
@client.on(events.NewMessage(outgoing=True))
async def handle_outgoing_message(event):
    # 群组发送消息，取消@提醒
    if event.is_group:
        chat_id = event.chat_id
        if chat_id in mention_timers:
            mention_timers[chat_id].cancel()
            mention_timers.pop(chat_id, None)
            last_group_mention.pop(chat_id, None)
            logging.info(f"已回复群组消息")
    
    # 私聊发送消息，取消私聊提醒
    elif event.is_private and not event.is_channel:
        sender_id = event.chat_id
        if sender_id in private_timers:
            private_timers[sender_id].cancel()
            private_timers.pop(sender_id, None)
            last_private_message.pop(sender_id, None)
            logging.info(f"已回复私聊消息")


async def main():
    """主函数"""
    await client.start(phone=PHONE_NUMBER)
    me = await client.get_me()
    logging.info(f"{me.first_name} (@{me.username}) 账号已登录,开始监控消息...")
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())