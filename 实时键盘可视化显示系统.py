import pygame
import pygame.gfxdraw
import sys
import time
from pynput import keyboard
from threading import Thread, Lock
from collections import defaultdict
import win32api
import win32con
import win32gui

class KeyDisplayApp:
    def __init__(self):
        # 初始化pygame
        pygame.init()
        pygame.display.set_caption("键盘按键显示器")
        
        # 窗口尺寸
        self.width, self.height = 225, 225
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.NOFRAME)
        self.screen.fill((0, 0, 0))  # 黑色背景
        
        # 获取窗口句柄并置顶
        self.hwnd = pygame.display.get_wm_info()["window"]
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                             win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
        # 定义键标签和位置
        self.keys = [
            # 第一排
            'd', 'f', 'j', 'k',
            # 第二排
            'z', 'x', 'numpad_1', 'numpad_2',
            # 第三排
            'space', 'numpad_0',
            # 第四排
            'left', 'up', 'right', 'down'
        ]
        
        # 按键位置配置 (x, y, 宽度比例)
        self.key_positions = [
            # 第一排 (4个按键)
            (5, 5, 1), (60, 5, 1), (115, 5, 1), (170, 5, 1),
            # 第二排 (4个按键)
            (5, 60, 1), (60, 60, 1), (115, 60, 1), (170, 60, 1),
            # 第三排 (2个宽按键)
            (5, 115, 2), (115, 115, 2),
            # 第四排 (4个按键)
            (5, 170, 1), (60, 170, 1), (115, 170, 1), (170, 170, 1)
        ]
        
        # 按键显示标签
        self.key_labels = {
            'd': 'D', 'f': 'F', 'j': 'J', 'k': 'K',
            'z': 'Z', 'x': 'X',
            'numpad_1': '1', 'numpad_2': '2',
            'space': 'Space', 'numpad_0': '0',
            'left': '←', 'up': '↑', 'right': '→', 'down': '↓'
        }
        
        # 按键状态管理
        self.key_state = {key: False for key in self.keys}  # False=松开, True=按下
        self.lock = Lock()  # 线程锁
        
        # 字体设置
        self.font = pygame.font.SysFont('timesnewroman', 20)
        self.big_font = pygame.font.SysFont('timesnewroman', 20)  # 用于长文本
        
        # 拖拽相关变量
        self.dragging = False
        self.drag_start_pos = (0, 0)
        self.window_pos = [0, 0]
        
        # 获取初始窗口位置
        rect = win32gui.GetWindowRect(self.hwnd)
        self.window_pos = [rect[0], rect[1]]
        
        # 启动按键监听器
        self.start_key_listener()
        
        # 主循环
        self.running = True
        self.main_loop()

    def draw_button(self, key, x, y, width_ratio):
        """绘制按键"""
        # 计算按键尺寸
        width = 50 * width_ratio + (5 if width_ratio > 1 else 0)
        height = 50
        
        # 按下状态处理
        pressed = self.key_state[key]
        shrink_factor = 0.9 if pressed else 1.0
        
        # 计算缩小后的尺寸
        new_width = width * shrink_factor
        new_height = height * shrink_factor
        
        # 计算位置偏移（保持中心位置）
        offset_x = (width - new_width) / 2
        offset_y = (height - new_height) / 2
        
        # 绘制按键背景
        button_rect = pygame.Rect(x + offset_x, y + offset_y, new_width, new_height)
        color = (255, 255, 100) if pressed else (255, 255, 255)  # 按下时黄色，否则白色
        pygame.draw.rect(self.screen, color, button_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), button_rect, 2)  # 边框
        
        # 绘制按键标签
        text = self.key_labels[key]
        
        # 根据文本长度选择字体
        if len(text) > 1:
            text_surface = self.big_font.render(text, True, (0, 0, 0))
        else:
            text_surface = self.font.render(text, True, (0, 0, 0))
        
        text_rect = text_surface.get_rect(center=(x + width/2, y + height/2))
        self.screen.blit(text_surface, text_rect)
        
        return button_rect

    def main_loop(self):
        """主循环"""
        clock = pygame.time.Clock()
        
        # 存储按键矩形用于拖拽检测
        button_rects = {}
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # 鼠标事件处理（用于窗口拖拽）
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        # 检查是否点击在按键上
                        pos = pygame.mouse.get_pos()
                        clicked_on_button = False
                        
                        for rect in button_rects.values():
                            if rect.collidepoint(pos):
                                clicked_on_button = True
                                break
                        
                        # 如果没有点击按键，开始拖拽窗口
                        if not clicked_on_button:
                            self.dragging = True
                            self.drag_start_pos = pygame.mouse.get_pos()
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # 左键
                        self.dragging = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        # 计算鼠标移动距离
                        current_pos = pygame.mouse.get_pos()
                        dx = current_pos[0] - self.drag_start_pos[0]
                        dy = current_pos[1] - self.drag_start_pos[1]
                        
                        # 更新窗口位置
                        self.window_pos[0] += dx
                        self.window_pos[1] += dy
                        
                        # 使用win32gui移动窗口
                        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 
                                            int(self.window_pos[0]), int(self.window_pos[1]), 
                                            0, 0, win32con.SWP_NOSIZE)
            
            # 清屏
            self.screen.fill((0, 0, 0))
            
            # 绘制所有按键
            button_rects.clear()
            for i, key in enumerate(self.keys):
                x, y, width_ratio = self.key_positions[i]
                rect = self.draw_button(key, x, y, width_ratio)
                button_rects[key] = rect
            
            pygame.display.flip()
            clock.tick(60)  # 60 FPS
        
        # 退出
        pygame.quit()
        sys.exit()

    def on_press(self, key):
        """处理按键按下事件"""
        try:
            # 处理特殊按键
            if key == keyboard.Key.space:
                key_id = 'space'
            elif key == keyboard.Key.left:
                key_id = 'left'
            elif key == keyboard.Key.up:
                key_id = 'up'
            elif key == keyboard.Key.right:
                key_id = 'right'
            elif key == keyboard.Key.down:
                key_id = 'down'
            # 处理小键盘按键
            elif hasattr(key, 'vk'):
                if key.vk == 96:  # 小键盘0
                    key_id = 'numpad_0'
                elif key.vk == 97:  # 小键盘1
                    key_id = 'numpad_1'
                elif key.vk == 98:  # 小键盘2
                    key_id = 'numpad_2'
                else:
                    # 尝试处理普通按键
                    if hasattr(key, 'char') and key.char:
                        key_id = key.char.lower()
                    else:
                        return
            # 处理普通按键
            else:
                key_id = key.char.lower()
            
            # 只处理我们关心的按键
            if key_id not in self.keys:
                return
                
            # 更新按键状态
            with self.lock:
                self.key_state[key_id] = True
                
        except AttributeError:
            # 忽略无法识别的按键
            pass

    def on_release(self, key):
        """处理按键释放事件"""
        try:
            # 处理特殊按键
            if key == keyboard.Key.space:
                key_id = 'space'
            elif key == keyboard.Key.left:
                key_id = 'left'
            elif key == keyboard.Key.up:
                key_id = 'up'
            elif key == keyboard.Key.right:
                key_id = 'right'
            elif key == keyboard.Key.down:
                key_id = 'down'
            # 处理小键盘按键
            elif hasattr(key, 'vk'):
                if key.vk == 96:  # 小键盘0
                    key_id = 'numpad_0'
                elif key.vk == 97:  # 小键盘1
                    key_id = 'numpad_1'
                elif key.vk == 98:  # 小键盘2
                    key_id = 'numpad_2'
                else:
                    # 尝试处理普通按键
                    if hasattr(key, 'char') and key.char:
                        key_id = key.char.lower()
                    else:
                        return
            # 处理普通按键
            else:
                key_id = key.char.lower()
            
            # 只处理我们关心的按键
            if key_id not in self.keys:
                return
                
            # 更新按键状态
            with self.lock:
                self.key_state[key_id] = False
                
        except AttributeError:
            # 忽略无法识别的按键
            pass

    def start_key_listener(self):
        """启动按键监听器线程"""
        def listen():
            with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            ) as listener:
                listener.join()
        
        thread = Thread(target=listen)
        thread.daemon = True
        thread.start()

# 启动应用
if __name__ == "__main__":
    app = KeyDisplayApp()
