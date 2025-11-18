# Screen Change Monitor (Screen Change Monitoring Tool)

A Python tool that periodically monitors a specified area of the screen and automatically saves a snapshot when a change (pixel difference) is detected.

## Required libraries

The following libraries are required to run this program:

```bash
pip install opencv-python numpy Pillow pynput pyautogui
```

## Usage

### 1. First run (select monitoring area)

Run without any arguments to enter mouse selection mode to choose the monitoring area.

```bash
python this_script_name.py
# After running, follow the console instructions and click the top-left and bottom-right corners of the area with the mouse.
```

### 2. Continuous run (use previous settings)

Start monitoring immediately using the previously saved monitoring area and parameters.

```bash
python your_script_name.py -c
```

## Options

| Short | Full name | Default | Description |
| :---: | :--- | :---: | :--- |
| `-c` | `--continuous` | (none) | Continuous mode. Use the area settings and parameters saved from the previous run. |
| `-d` | `--directory` | timestamp | Specify the directory to save image files. |
| `-t` | `--change-threshold` | `0.05` (5%) | Threshold of the proportion of pixels that changed to detect a change (0.0 to 1.0). |
| `-p` | `--prefix` | `screenshot` | Specify the filename prefix for saved images. |
| `-i` | `--interval` | `1.0` (seconds) | Specify the monitoring interval in seconds. |
| `-ca` | `--confirm-area` | (none) | When running in continuous mode (`-c`), show a green rectangle indicating the monitoring area for confirmation. Default is off. |

### Example

- Start monitoring with a stricter change threshold (1%) and a shorter interval (0.5 seconds):

```bash
python this_script_name.py -c -t 0.01 -i 0.5
```

## How to stop monitoring

After monitoring has started, press the following key in the console (terminal):

- Ctrl + C: Stop monitoring and exit the program.
