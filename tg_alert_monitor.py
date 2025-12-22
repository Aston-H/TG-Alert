import asyncio
import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
from collections import defaultdict
from telethon import TelegramClient, events
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

# 配置类
@dataclass
class Config:
    """配置类，集中管理所有配置参数"""
    # 告警配置
    GROUP_MENTION_TIMEOUT: int = 60  # 群聊@消息未回复的超时时间（秒）
    PRIVATE_MESSAGE_TIMEOUT: int = 60  # 私聊消息未回复的超时时间（秒）
    MAX_ALERT_COUNT: int = 3  # 单条消息最大告警次数
    ALERT_SOUND_PATH: str = '/System/Library/Sounds/Hero.aiff'  # 告警提示音文件路径
    CANCEL_WINDOW: int = 60  # 自动取消告警的时间窗口（秒）

    # 声音配置
    ALERT_SOUND_INTERVAL: float = 0.3  # 播放提示音的间隔时间
    MUSIC_SOUND_INTERVAL: float = 1.0  # 播放音乐的间隔时间
    SENSITIVE_MUSIC_PATH: str = 'music.mp3'  # 敏感词触发时播放的音乐文件

    # 日志配置
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n' + '=' * 80
    LOG_DATE_FORMAT: str = '%m-%d %H:%M:%S'
    LOG_ENCODING: str = 'utf-8'

    # 敏感词列表
    SENSITIVE_WORDS: list = None

    def __post_init__(self):
        self.SENSITIVE_WORDS = ['ZF-DA组', '不定时抽查', '请您配合', '在线状态', '你好', '您好', '代码review', '@all']

# 创建全局配置实例
config = Config()

# 日志管理类
class LogManager:
    """日志管理类，处理所有日志相关操作"""
    @staticmethod
    def setup():
        logging.basicConfig(
            level=logging.INFO,
            format=config.LOG_FORMAT,
            encoding=config.LOG_ENCODING,
            datefmt=config.LOG_DATE_FORMAT
        )
        return logging.getLogger(__name__)

logger = LogManager.setup()

# 声音管理类
class SoundManager:
    """声音管理类，处理所有声音相关操作"""
    @staticmethod
    async def play_alert_sound_async(target_volume: int = 60, count: int = 1):
        """异步播放提示音"""
        await asyncio.to_thread(SoundManager._play_alert_sound, target_volume, count)

    @staticmethod
    def _play_alert_sound(target_volume: int = 70, count: int = 1):
        """同步播放提示音"""
        original_volume = None
        try:
            original_volume = int(os.popen('osascript -e "output volume of (get volume settings)"').read())
            os.system(f'osascript -e "set volume output volume {target_volume}"')
            for i in range(count):
                os.system(f'afplay {config.ALERT_SOUND_PATH}')
                if i < count - 1:
                    time.sleep(config.ALERT_SOUND_INTERVAL)
            logger.info(f"🔔 播放提示音 {count} 次")
        except Exception as e:
            logger.info(f"❌ 播放提示音失败: {e}")
        finally:
            if original_volume is not None:
                try:
                    os.system(f'osascript -e "set volume output volume {original_volume}"')
                except Exception:
                    logger.debug("恢复音量失败", exc_info=True)

    @staticmethod
    def play_sound(file_path: str, target_volume: int = 70, count: int = 1):
        """播放音频文件并控制音量"""
        original_volume = None
        try:
            original_volume = int(os.popen('osascript -e "output volume of (get volume settings)"').read())
            os.system(f'osascript -e "set volume output volume {target_volume}"')
            for i in range(count):
                os.system(f'afplay {file_path}')
                if i < count - 1:
                    time.sleep(config.MUSIC_SOUND_INTERVAL)
            logger.info(f"🔔 播放音频 {file_path} {count} 次")
        except Exception as e:
            logger.info(f"❌ 播放音频失败: {e}")
        finally:
            if original_volume is not None:
                os.system(f'osascript -e "set volume output volume {original_volume}"')

# 告警记录类
@dataclass
class AlertRecord:
    """告警记录类，存储单个告警的相关信息"""
    message_id: int
    mention_time: float
    is_private: bool
    alert_count: int = 0
    is_cancelled: bool = False
    task: Optional[asyncio.Task] = None
    timeout_interval: int = config.GROUP_MENTION_TIMEOUT

class TelegramAlertSystem:
    """Telegram 告警系统主类"""
    
    def __init__(self, api_id: int, api_hash: str, phone: str):
        """初始化告警系统"""
        self.client = TelegramClient('tg_monitor_bot', api_id, api_hash)
        self.my_id = None
        self.my_username = None
        self.pending_alerts: Dict[int, AlertRecord] = {}
        self.last_interactions: Dict[int, float] = {}
        self.play_counts: Dict[int, int] = defaultdict(int)

    def _log_debug_info(self, event, chat, sender, message_text):
        """记录调试信息"""
        logging.info(f"event消息: \n{json.dumps(event.message.__dict__, default=str, ensure_ascii=False)}")
        logging.info(f"chat消息: \n{json.dumps(chat.__dict__, default=str, ensure_ascii=False)}")
        logging.info(f"sender消息: \n{json.dumps(sender.__dict__, default=str, ensure_ascii=False)}")
        logging.info(f"收到新消息: {message_text}")
        
    def _get_sender_info(self, sender):
        """获取发送者信息"""
        username = sender.username or "Unknown"
        first_name = sender.first_name or "Unknown"
        last_name = sender.last_name or "Unknown"
        return f"{first_name if first_name else last_name}(@{username})"

    async def _handle_message(self, event) -> None:
        """处理新消息"""
        # 获取消息相关信息
        chat = await event.get_chat()
        sender = await event.get_sender()
        message_text = event.message.message if event.message else ""
        chat_id = chat.id
        event_id = event.id
        
        # 记录调试信息
        self._log_debug_info(event, chat, sender, message_text)
        
        # 如果是自己发的消息，更新互动时间并返回
        if sender.id == self.my_id:
            self.last_interactions[chat_id] = time.time()
            return

        # 处理群组消息
        if event.is_group:
            await self._handle_group_message(event, chat, sender, message_text, chat_id, event_id)
        # 处理私聊消息
        elif event.is_private:
            await self._handle_private_message(event, chat, sender, message_text, chat_id, event_id)
        else:
            logging.info("非群聊或私聊消息，忽略处理")

    async def _handle_group_message(self, event, chat, sender, message_text, chat_id, event_id):
        """处理群组消息"""
        # 检查是否是@消息或者提到了我们
        is_mention = event.mentioned or (message_text and f"@{self.my_username}" in message_text)
        
        # 对于@消息，我们需要特殊处理
        if is_mention:
            sender_info = self._get_sender_info(sender)
            chat_title = chat.title or "Unknown"
            logging.info(f"群组 {chat_title} 来自 {sender_info} 的消息")
            
            # 对于@消息，我们只检查是否有自己回复过这个@，而不是任意消息
            now_ts = time.time()
            last_inter = self.last_interactions.get(chat_id, 0)
            
            # 只有当这个@消息是对之前@消息的回复时，才考虑取消窗口
            if last_inter and (now_ts - last_inter) <= config.CANCEL_WINDOW:
                # 检查这条消息是否是回复之前的@消息
                if event.message.reply_to:
                    reply_msg = await event.message.get_reply_message()
                    if reply_msg and (reply_msg.mentioned or (reply_msg.message and f"@{self.my_username}" in reply_msg.message)):
                        logger.info(f"检测到对之前@消息的回复，在取消窗口内，跳过创建提醒")
                        return
            
            self._add_alert(chat_id, event_id, is_private=False)

    async def _handle_private_message(self, event, chat, sender, message_text, chat_id, event_id):
        """处理私聊消息"""
        sender_info = self._get_sender_info(sender)
        logging.info(f"来自私聊 {sender_info} 的消息")
        
        now_ts = time.time()
        # 检查敏感词
        if await self._check_sensitive_words(message_text, sender_info, chat_id):
            # 敏感词检查时已经更新了最后互动时间
            return
            
        # 获取现有告警记录
        existing_record = self.pending_alerts.get(chat_id)
        if existing_record and not existing_record.is_cancelled:
            # 如果已有未取消的告警任务，仅更新时间
            existing_record.mention_time = now_ts
            logger.info(f"更新私聊 {sender_info} 的提醒时间，重新开始计时 {config.PRIVATE_MESSAGE_TIMEOUT}s")
        else:
            # 如果没有活动的告警任务，创建新的
            self._add_alert(chat_id, event_id, is_private=True)

    async def _check_sensitive_words(self, message_text: str, sender_info: str, chat_id: int) -> bool:
        """检查敏感词"""
        if not message_text:
            return False

        try:
            msg_lower = message_text.lower()
            if any(word.lower() in msg_lower for word in config.SENSITIVE_WORDS):
                logger.info(f"私聊包含敏感词 - 用户: {sender_info} 内容: {message_text[:200]}")
                await SoundManager.play_sound(config.SENSITIVE_MUSIC_PATH)  # 播放音乐
                self.last_interactions[chat_id] = time.time()
                return True
        except Exception:
            logger.debug("敏感词检测失败", exc_info=True)
        return False

    def _add_alert(self, chat_id: int, message_id: int, is_private: bool):
        """添加告警任务"""
        try:
            now_ts = time.time()
            # 检查最近互动
            last_inter = self.last_interactions.get(chat_id)
            
            # 对于私聊消息，只在回复对方消息时才会更新互动时间，所以这里不需要检查
            # 对于群组消息，保持原有的取消窗口检查逻辑
            if not is_private and last_inter and (now_ts - last_inter) <= config.CANCEL_WINDOW:
                logger.info(f"检测到群组 chat {chat_id} 的最后一次互动在取消窗口内，跳过创建提醒")
                return

            # 获取超时时间
            timeout = config.PRIVATE_MESSAGE_TIMEOUT if is_private else config.GROUP_MENTION_TIMEOUT

            # 检查是否已有告警任务
            existing_record = self.pending_alerts.get(chat_id)
            if existing_record and not existing_record.is_cancelled:
                # 如果已有任务还在运行，更新最后提醒时间并延长等待时间
                existing_record.mention_time = now_ts
                # 不取消现有任务，让它继续运行，但会更新下一次提醒的时间
                logger.info(f"更新 chat {chat_id} 的提醒时间，重新开始计时 {timeout}s")
                return

            # 如果没有现有任务，则创建新的告警记录
            record = AlertRecord(
                message_id=message_id,
                mention_time=now_ts,
                is_private=is_private,
                timeout_interval=timeout
            )
            
            self.pending_alerts[chat_id] = record
            record.task = asyncio.create_task(self._alert_worker(chat_id))
            logger.info(f"为 chat {chat_id} 创建提醒任务，超时 {timeout}s")
            
        except Exception:
            logger.error("add_alert 执行失败", exc_info=True)

    def _cancel_existing_alert(self, chat_id: int):
        """取消现有告警"""
        record = self.pending_alerts.get(chat_id)
        if record and record.task and not record.task.done():
            try:
                record.task.cancel()
            except Exception:
                logger.debug("取消已有提醒任务时出错", exc_info=True)
        self.pending_alerts.pop(chat_id, None)

    async def _alert_worker(self, chat_id: int):
        """告警工作协程"""
        record = self.pending_alerts.get(chat_id)
        if not record:
            return

        try:
            while (not record.is_cancelled and 
                   record.alert_count < config.MAX_ALERT_COUNT):
                
                waiting = True
                while waiting and not record.is_cancelled:
                    # 计算需要等待的时间
                    now = time.time()
                    wait_time = record.mention_time + record.timeout_interval - now
                    
                    if wait_time <= 0:
                        waiting = False
                    else:
                        # 使用较短的等待时间，以便能够及时响应mention_time的更新
                        sleep_time = min(wait_time, 1.0)
                        await asyncio.sleep(sleep_time)
                        # 重新获取记录，以防在等待期间被更新或取消
                        record = self.pending_alerts.get(chat_id)
                        if not record or record.is_cancelled:
                            return
                
                # 检查是否应该取消告警
                if self._should_cancel_alert(chat_id, record):
                    break

                # 播放告警声音
                await self._play_alert(chat_id, record)
                
                if record.alert_count >= config.MAX_ALERT_COUNT:
                    break

                # 更新下一次提醒的基准时间为当前时间
                record.mention_time = time.time()
                logger.info(f"更新下一次提醒时间为: {datetime.fromtimestamp(record.mention_time).strftime('%H:%M:%S')}")

        except asyncio.CancelledError:
            logger.info(f"alert worker for chat {chat_id} 被取消")
        except Exception:
            logger.error("alert worker 未处理的异常", exc_info=True)
        finally:
            self.pending_alerts.pop(chat_id, None)
            logger.info(f"已清理 chat {chat_id} 的提醒任务")

    def _should_cancel_alert(self, chat_id: int, record: AlertRecord) -> bool:
        """检查是否应该取消告警"""
        last_inter = self.last_interactions.get(chat_id, 0)
        now_ts = time.time()
        
        if (last_inter > record.mention_time and 
            (now_ts - last_inter) <= config.CANCEL_WINDOW):
            logger.info(f"检测到 chat {chat_id} 的最后一次互动在取消窗口内，取消提醒")
            record.is_cancelled = True
            return True
        return False

    async def _play_alert(self, chat_id: int, record: AlertRecord):
        """播放告警声音"""
        try:
            await SoundManager.play_alert_sound_async(count=1)
            self.play_counts[chat_id] += 1
            record.alert_count += 1
            logger.info(f"触发提醒 #{record.alert_count} for chat {chat_id}")
        except Exception as e:
            logger.error(f"播放提示音失败: {e}", exc_info=True)

    async def run(self):
        """运行告警系统"""
        try:
            # 启动客户端
            await self.client.start()
            self.my_id = (await self.client.get_me()).id
            self.my_username = (await self.client.get_me()).username
            
            # 注册事件处理器
            @self.client.on(events.MessageEdited)
            @self.client.on(events.NewMessage)
            async def message_handler(event):
                await self._handle_message(event)

            logger.info(f"\n🚀 Telegram 告警系统已启动" +
                      f"\n✅ 已登录，用户ID: {self.my_id}")

            # 保持运行
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"运行时发生错误: {e}", exc_info=True)

async def main():
    """主函数"""
    client = TelegramAlertSystem(
        os.getenv("API_ID"),
        os.getenv("API_HASH"),
        os.getenv("PHONE")
    )
    
    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("❌ 程序已停止")
    except asyncio.CancelledError:
        logger.info("👋 按了 Ctrl+C 停止程序")
    finally:
        await client.client.disconnect()
        logger.info("🔌 客户端断开连接")

if __name__ == '__main__':
    asyncio.run(main())