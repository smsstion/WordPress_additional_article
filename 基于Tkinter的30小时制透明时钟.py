import tkinter as tk
from datetime import datetime, timedelta
import ctypes
from tkinter import font
import time

def get_30_hour_time():
    now = datetime.now()
    if now.hour < 6:
        # 将小时调整为24小时格式，并将日期向后移动一天
        adjusted_time = now - timedelta(days=1)
        hour = now.hour + 24
    else:
        # 使用当前时间
        adjusted_time = now
        hour = now.hour

    # 设置30小时的时间
    return adjusted_time.strftime(f"%Y/%m/%d {hour:02d}:%M:%S")

def update_time():
    current_time = get_30_hour_time()
    time_label.config(text=current_time)
    root.after(1000, update_time)

def start_move(event):
    global last_click_x, last_click_y
    last_click_x = event.x
    last_click_y = event.y

def move_window(event):
    x = event.x_root - last_click_x
    y = event.y_root - last_click_y
    root.geometry(f"+{x}+{y}")

# 设置主窗口
root = tk.Tk()
root.overrideredirect(True)  # 拆除窗户装饰
root.attributes("-topmost", True)  # 把窗户放在上面
root.attributes("-alpha", 0.5)  # 将透明度设置为0.5

# 函数使窗口点击穿透
def make_window_clickthrough(hwnd):
    # 用于点击的常量
    GWL_EXSTYLE = -20
    WS_EX_TRANSPARENT = 0x20
    WS_EX_LAYERED = 0x80000
    
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_TRANSPARENT | WS_EX_LAYERED
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

# 功能逐渐改变透明度
def fade_to_alpha(target_alpha):
    current_alpha = root.attributes('-alpha')
    step = 0.05 if target_alpha > current_alpha else -0.05
    while abs(current_alpha - target_alpha) > 0.05:
        current_alpha += step
        root.attributes('-alpha', current_alpha)
        root.update()
        time.sleep(0.01)
    root.attributes('-alpha', target_alpha)

# 函数检查鼠标是否与窗口重叠
def check_mouse_overlap():
    root.update_idletasks()
    mouse_x, mouse_y = root.winfo_pointerxy()
    window_x = root.winfo_rootx()
    window_y = root.winfo_rooty()
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    if window_x <= mouse_x <= window_x + window_width and window_y <= mouse_y <= window_y + window_height:
        fade_to_alpha(0.0)  # 淡出(完全透明)
    else:
        fade_to_alpha(0.5)  # 逐渐淡入(透明度为50%)

    root.after(50, check_mouse_overlap)  # 每50毫秒检查一次

# 固定位置
x_pos, y_pos = 980, 760
root.geometry(f"+{x_pos}+{y_pos}")

# 添加标签以显示时间
time_label = tk.Label(root, font=("Helvetica", 24), fg="white", bg="black")
time_label.pack(fill="both", expand=True)

# 获取窗口句柄并应用点击通过
root.update_idletasks()  # 确保窗口已创建
hwnd = ctypes.windll.user32.FindWindowW(None, "Hanging Clock")
make_window_clickthrough(hwnd)

# 开始检查鼠标重叠
check_mouse_overlap()

# 开始更新时间
update_time()

# 运行应用程序
root.mainloop()
