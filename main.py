import asyncio
from tg_alert_monitor import main as monitor_main



def monitor_TG():
    """启动项目的入口点。"""
    try:
        asyncio.run(monitor_main())
    except KeyboardInterrupt:
        print("收到中断信号，正在退出...")
    except Exception as e:
        # 捕获未处理的异常并打印，以便日志记录或调试
        raise


if __name__ == '__main__':
    monitor_TG()
