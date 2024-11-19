import cv2
import numpy as np
from PIL import ImageGrab
import time
import datetime

# 変化を検出するための閾値
CHANGE_THRESHOLD = 0.1  # 10%の変化を検出

# スナップショットを保存する関数
def save_snapshot():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    img = ImageGrab.grab()
    img.save(filename)
    print(f"Snapshot saved: {filename}")

# メインの監視ループ
def monitor_screen():
    last_frame = None

    while True:
        # 現在の画面を取得
        current_frame = np.array(ImageGrab.grab())
        current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

        if last_frame is not None:
            # 画像の差分を計算
            diff = cv2.absdiff(last_frame, current_frame_gray)
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

            # 変化したピクセルの割合を計算
            change_pixels = np.sum(thresh > 0)
            total_pixels = thresh.size
            change_ratio = change_pixels / total_pixels

            # 変化が閾値を超えた場合、スナップショットを保存
            if change_ratio > CHANGE_THRESHOLD:
                save_snapshot()

        # 現在のフレームを次のループのために保存
        last_frame = current_frame_gray

        # 監視の間隔を設定（例: 1秒）
        time.sleep(1)

if __name__ == "__main__":
    monitor_screen()
