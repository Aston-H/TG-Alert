import subprocess
import time
import threading

SOUNDS_DIR = "/System/Library/Sounds/"
MIN_INTERVAL = 0.05  # 两次触发之间的最小间隔秒数
# 格式：(音效文件, 播放前等待秒数)
SEQUENCES = {
    "knock": {
        "sound": "Sosumi",
        "beats": [0.0, 0.18, 0.55, 0.73, 1.2],
    },
    "accelerate": {
        "sound": "Sosumi",
        "beats": [0.0, 0.5, 0.9, 1.2, 1.4, 1.55, 1.65],
    },
    "phrase": {
        "sound": "Sosumi",
        "beats": [0.0, 0.15, 0.3, 0.8, 0.95, 1.1, 1.6],
    },
    "morse": {
        "sound": "Sosumi",
        "beats": [0.0, 0.5, 0.7, 1.2, 1.7, 1.9],
    },
}


_lock = threading.Lock()

def play_sequence(name: str = "knock", repeat: int = 1, repeat_interval: float = 0.8):
    if not _lock.acquire(blocking=False):
        return  # 上一次还在播，直接跳过

    try:
        seq = SEQUENCES.get(name)
        if not seq:
            print(f"Unknown sequence '{name}', available: {list(SEQUENCES.keys())}")
            return

        filepath = f"{SOUNDS_DIR}{seq['sound']}.aiff"
        beats = seq["beats"]

        corrected = [beats[0]]
        for i in range(1, len(beats)):
            corrected.append(max(beats[i], corrected[-1] + MIN_INTERVAL))

        for i in range(repeat):
            if i > 0:
                time.sleep(repeat_interval)

            start = time.perf_counter()
            procs = []
            for offset in corrected:
                wait = (start + offset) - time.perf_counter()
                if wait > 0:
                    time.sleep(wait)
                p = subprocess.Popen(
                    ["afplay", filepath],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                procs.append(p)
            for p in procs:
                p.wait()
    finally:
        _lock.release()

if __name__ == "__main__":
    # 示例：温和提醒，重播 3 次，每次间隔 1 秒
    play_sequence("phrase", repeat=3, repeat_interval=1.0)