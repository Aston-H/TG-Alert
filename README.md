# TG-Alert
Telegram 监控与提醒工具

## 功能特点
- 群聊 @ 提醒：当你被 @ 且未及时回复时播放提示音
- 私聊敏感词监测：检查私聊消息中的敏感词并提醒
- 私聊超时提醒：私聊消息若干分钟内未回复则提醒
- macOS 系统音效：使用系统声音或自定义音频文件

## 安装与设置

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量（可选）：
直接设置变量：
```
API_ID=你的API_ID
API_HASH=你的API_HASH
PHONE_NUMBER=你的手机号
```

## 运行
```bash
python main.py
```

首次运行时，如果未设置环境变量，将使用代码中的默认值。

## 配置说明
- 敏感词列表：编辑 `tg_monitor.py` 中的 `SENSITIVE_WORDS` 列表
- 提示音：可修改 `play_sound_1/2/3` 函数中的音频文件路径
- 提醒时间：调整 `check_group_mention_timeout` 和 `check_private_timeout` 函数中的 `num_minutes` 参数

## 系统要求
- Python 3.8+
- macOS（因使用了 `osascript` 和 `afplay` 命令）
