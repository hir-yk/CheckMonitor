import cv2
import numpy as np
from PIL import ImageGrab
import time
import datetime
import pyautogui
from pynput import mouse
import argparse
import os
import json

CONFIG_FILE = "monitor_config.json"
click_positions = []

# --- 設定ファイルの読み書きとディレクトリ処理 ---

def increment_directory_name(base_dir):
    base_name = os.path.basename(base_dir)
    parent_dir = os.path.dirname(base_dir) or '.'

    if base_name.isdigit():
        try:
            num = int(base_name)
            new_num = num + 1
            while True:
                new_dir = os.path.join(parent_dir, str(new_num))
                if not os.path.exists(new_dir):
                    return new_dir
                new_num += 1
        except ValueError:
            pass
    
    return os.path.join(parent_dir, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))


def save_config(area, args):
    config_data = {
        "monitor_area": area,
        "change_threshold": args.change_threshold,
        "prefix": args.prefix,
        "interval": args.interval,
        "last_directory": args.directory 
    }
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"設定ファイルの保存に失敗しました: {e}")

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        return None

# --- エリア描画関数 ---

def draw_monitor_area(area):
    window_name = "Monitor Area Confirmation (Close the window or press ENTER/ESC)"
    
    try:
        full_screen = np.array(ImageGrab.grab())
        frame = cv2.cvtColor(full_screen, cv2.COLOR_RGB2BGR)
        x1, y1, x2, y2 = area
        
        # 矩形を描画 (緑色: (0, 255, 0), 太さ: 3)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, frame)
        
        while True:
            key = cv2.waitKey(1)
            
            # キーボードによる終了: ESCキー (27) または Enterキー (13)
            if key == 27 or key == 13: 
                break

            # マウスによる終了 (ウィンドウクローズボタン) の検知
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyAllWindows()
        time.sleep(0.1) 
        
    except Exception as e:
        print(f"警告: 監視エリアの描画に失敗しました。OpenCVのウィンドウ表示にはGUI環境が必要です。")
        print(f"エラー詳細: {e}")
    finally:
        cv2.destroyAllWindows()
        time.sleep(0.1) 


# --- スナップショットを保存する関数 ---

def save_snapshot(monitor_area, args):
    if monitor_area[0] >= monitor_area[2] or monitor_area[1] >= monitor_area[3]:
        print("エラー: 監視エリアが無効です (幅または高さがゼロ以下)。")
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    prefix = args.prefix
    filename = f"{prefix}_{timestamp}.png"

    save_dir = args.directory
    os.makedirs(save_dir, exist_ok=True)
    
    full_path = os.path.join(save_dir, filename)
    
    img = ImageGrab.grab(bbox=monitor_area)
    img.save(full_path)
    print(f"Snapshot saved: {full_path}")

# --- メインの監視ループ ---

def monitor_screen(monitor_area, args):
    if monitor_area[0] >= monitor_area[2] or monitor_area[1] >= monitor_area[3]:
        print("エラー: 監視エリアが無効です (幅または高さがゼロ以下)。プログラムを終了します。")
        print(f"設定されたエリア: {monitor_area}")
        return

    last_frame = None
    change_threshold = args.change_threshold

    print(f"--- 監視を開始します ---")
    print("🚨 **監視を終了するには、コンソールで Ctrl+C を押してください。**")
    print(f"監視エリア: {monitor_area}")
    print(f"変化検出閾値: {change_threshold * 100:.2f}%%")
    print(f"保存先ディレクトリ: {args.directory}")
    print(f"ファイル名Prefix: {args.prefix}")
    print(f"監視間隔: {args.interval}秒")
    print("-" * 30)

    try:
        while True:
            current_frame = np.array(ImageGrab.grab(bbox=monitor_area))
            
            if current_frame.size == 0:
                print("エラー: 画面キャプチャに失敗しました (空のフレーム)。エリア設定を確認してください。")
                time.sleep(args.interval)
                continue

            current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

            if last_frame is not None:
                if last_frame.shape == current_frame_gray.shape:
                    # 画像の差分を計算
                    diff = cv2.absdiff(last_frame, current_frame_gray)
                    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

                    # 変化したピクセルの割合を計算
                    change_pixels = np.sum(thresh > 0)
                    total_pixels = thresh.size
                    change_ratio = change_pixels / total_pixels

                    if change_ratio > change_threshold:
                        print(f"画面の変化を検出 ({change_ratio * 100:.2f}%%)。閾値: {change_threshold * 100:.2f}%%")
                        save_snapshot(monitor_area, args)
                else:
                    print("警告: 前のフレームと現在のフレームのサイズが異なります。差分計算をスキップします。")
            
            last_frame = current_frame_gray

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n監視を終了します。")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")


# --- マウスクリックを待つ関数 ---

def on_click(x, y, button, pressed):
    if pressed and button == mouse.Button.left:
        click_positions.append((x, y))
        print(f"クリック位置: ({x}, {y})")
        if len(click_positions) == 2:
            return False

def select_monitor_area():
    click_positions.clear()

    print("--- 監視エリアの指定 ---")
    print("左上の角と右下の角を順番にクリックしてください...")

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    if len(click_positions) < 2:
        print("エラー: 2点の座標が取得できませんでした。プログラムを終了します。")
        exit()

    x1, y1 = click_positions[0]
    x2, y2 = click_positions[1]

    x_min = min(x1, x2)
    y_min = min(y1, y2)
    x_max = max(x1, x2)
    y_max = max(y1, y2)

    area = (x_min, y_min, x_max, y_max)
    print(f"監視エリア: {area}")
    return area

# --- メイン処理 ---

if __name__ == "__main__":
    
    config = load_config()
    
    # ディレクトリのデフォルト値を決定
    default_dir = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if config and 'last_directory' in config:
        last_dir = config['last_directory']
        base_name = os.path.basename(last_dir)
        
        if base_name.isdigit():
            default_dir = increment_directory_name(last_dir)
    
    # argparseによる引数処理
    
    parser = argparse.ArgumentParser(description="画面の変化を監視し、変化があった場合にスナップショットを保存します。")
    parser.add_argument(
        '-c', '--continuous', 
        action='store_true', 
        help='連続モード: 前回保存したエリア設定とパラメータを使用し、エリア選択をスキップします。'
    )
    parser.add_argument(
        '-d', '--directory', 
        type=str, 
        default=default_dir, 
        help=f'画像ファイルを保存するディレクトリを指定します。デフォルト: {default_dir}'
    )
    parser.add_argument(
        '-t', '--change-threshold', 
        type=float, 
        default=config.get('change_threshold', 0.05) if config else 0.05, 
        help='変化を検出するピクセルの割合の閾値を指定します (0.0から1.0)。デフォルト: 0.05 (5%%)'
    )
    parser.add_argument(
        '-p', '--prefix', 
        type=str, 
        default=config.get('prefix', 'screenshot') if config else 'screenshot', 
        help='保存するファイル名のPrefixを指定します。デフォルト: screenshot'
    )
    parser.add_argument(
        '-i', '--interval', 
        type=float, 
        default=config.get('interval', 1.0) if config else 1.0, 
        help='監視間隔を秒単位で指定します。デフォルト: 1.0 (1秒)'
    )
    parser.add_argument(
        '-ca', '--confirm-area', 
        action='store_true', 
        help='連続モード(-c)実行時に、監視エリアの緑枠表示を確認します。デフォルトは非表示です。'
    )

    args = parser.parse_args()

    # 閾値のバリデーション
    if not (0.0 <= args.change_threshold <= 1.0):
        print("エラー: 変化検出閾値は0.0から1.0の範囲で指定してください。")
        exit()

    monitor_area = None

    if args.continuous and config and 'monitor_area' in config:
        # 連続モードでの実行確認
        monitor_area = tuple(config['monitor_area'])
        
        print("-" * 40)
        print("💡 連続モードで実行します。")
        print("--- 前回の設定 ---")
        print(f"エリア: {monitor_area}")
        print(f"閾値: {args.change_threshold * 100:.2f}%%")
        print(f"Prefix: {args.prefix}")
        print(f"間隔: {args.interval}秒")
        print(f"保存先: {args.directory}")
        print("-" * 40)
        
        if args.confirm_area:
            print("🖼️ 監視エリアを画面上に緑の枠で表示します。エリアを確認してください。")
            print("👉 確認後、**Enterキー** または **ESCキー** を押すか、**ウィンドウの X ボタンを押して**ウィンドウを閉じてください。")
            print("-" * 40)
            draw_monitor_area(monitor_area)
        
        response = input("上記の設定で監視を開始しますか？ (y/n): ")
        if response.lower() not in ['y', 'yes']:
            print("実行をキャンセルしました。")
            exit()
    
    else:
        # エリアを選択
        monitor_area = select_monitor_area()

    
    # 監視エリアが有効な場合に監視を開始
    if monitor_area and monitor_area[0] < monitor_area[2] and monitor_area[1] < monitor_area[3]:
        
        # 💾 上書き確認
        save_dir = args.directory
        
        if os.path.exists(save_dir) and os.path.isdir(save_dir):
            print("-" * 40)
            print(f"⚠️ **保存先ディレクトリ '{save_dir}' はすでに存在します。**")
            
            if not os.listdir(save_dir):
                print("（ディレクトリは空です。）")
                response = input("このディレクトリに上書き保存を開始しますか？ (y/n): ")
            else:
                print("（ディレクトリにはファイルが含まれています。内容が上書き・追加されます。）")
                response = input("このディレクトリにファイルを**追加**して続行しますか？ (y/n): ")
            
            if response.lower() not in ['y', 'yes']:
                print("実行をキャンセルしました。")
                exit()
            print("-" * 40)
        
        save_config(monitor_area, args)
        monitor_screen(monitor_area, args)
    else:
        print("エラー: 監視エリアが無効なため、監視を開始できません。")