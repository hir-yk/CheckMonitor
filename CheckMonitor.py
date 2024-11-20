import cv2
import numpy as np
from PIL import ImageGrab
import time
import datetime
import pyautogui
from pynput import mouse

# 変化を検出するための閾値
CHANGE_THRESHOLD = 0.05  # 5%の変化を検出

# グローバル変数
click_positions = []

# スナップショットを保存する関数
def save_snapshot():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshot_{timestamp}.png"
    img = ImageGrab.grab(bbox=monitor_area)  # 指定したエリアをキャプチャ
    img.save(filename)
    print(f"Snapshot saved: {filename}")

# メインの監視ループ
def monitor_screen():
    last_frame = None

    while True:
        # 現在の画面を取得
        current_frame = np.array(ImageGrab.grab(bbox=monitor_area))
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

# マウスクリックを待つ関数
def on_click(x, y, button, pressed):
    if pressed:
        click_positions.append((x, y))
        print(f"クリック位置: ({x}, {y})")
        if len(click_positions) == 1:
            # 1回クリックされたらリスナーを停止
            return False

def select_monitor_area():
    print("左上の角をクリックしてください...")
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()  # クリックを待つ

    x1, y1 = click_positions[0]
    print("右下の角をクリックしてください...")
    click_positions.clear()  # クリック位置をクリア

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()  # クリックを待つ

    x2, y2 = click_positions[0]

    # 座標を正しく設定
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    return (x1, y1, x2, y2)

if __name__ == "__main__":
    monitor_area = select_monitor_area()  # 監視エリアを指定
    print(f"監視エリア: {monitor_area}")
    monitor_screen()  # 監視を開始
