import keyboard
import time
import threading
from collections import deque

# ==================== 配置区 ====================
REPLACE_RULES = {
    "jj": "ĵ", "JJ": "Ĵ", 
    "uu": "ŭ", "UU": "Ŭ",
    "ss": "ŝ", "SS": "Ŝ",
    "hh": "ĥ", "HH": "Ĥ",
    "gg": "ĝ", "GG": "Ĝ",
    "cc": "ĉ", "CC": "Ĉ"
}

VALID_CHARS = {'u', 's', 'g', 'h', 'j', 'c', 'U', 'S', 'G', 'H', 'J', 'C'}
SPACE_CHARS = {' ', '\t', '\n', '\xa0'}  # 包括各种空白字符
Q_PREFIX = 'q'

# ==================== 核心类 ====================
class InputContext:
    """输入上下文管理器，跟踪文本状态和光标位置"""
    def __init__(self):
        self.buffer = []        # 字符缓冲区
        self.cursor_pos = 0     # 当前光标位置
        self.last_event_time = 0  # 最后事件时间
        self.lock = threading.Lock()  # 线程锁
        self.skip_next = False  # 用于跳过空格后的下一个字符
    
    def update_state(self, event):
        """更新内部状态并返回是否需要检查替换规则"""
        with self.lock:
            current_time = time.time()
            
            # 处理特殊按键
            if event.name == 'backspace' and event.event_type == 'down':
                if self.cursor_pos > 0:
                    self.buffer.pop(self.cursor_pos - 1)
                    self.cursor_pos -= 1
                self.last_event_time = current_time
                return True
            
            # 方向键处理
            if event.name in ['left', 'right'] and event.event_type == 'down':
                if event.name == 'left' and self.cursor_pos > 0:
                    self.cursor_pos -= 1
                elif event.name == 'right' and self.cursor_pos < len(self.buffer):
                    self.cursor_pos += 1
                self.last_event_time = current_time
                return False
            
            # 空格键处理 - 重置状态 (需求8)
            if event.name == 'space' and event.event_type == 'down':
                # 插入空格到缓冲区
                self.buffer.insert(self.cursor_pos, ' ')
                self.cursor_pos += 1
                self.skip_next = True  # 设置跳过下一个字符的标记
                self.last_event_time = current_time
                return False
            
            # 处理字符输入
            if len(event.name) == 1 and event.event_type == 'down':
                # 如果是空格后的第一个字符，跳过替换检查
                if self.skip_next:
                    self.buffer.insert(self.cursor_pos, event.name)
                    self.cursor_pos += 1
                    self.skip_next = False  # 重置标记
                    return False
                
                self.buffer.insert(self.cursor_pos, event.name)
                self.cursor_pos += 1
                self.last_event_time = current_time
                return True
            
            self.last_event_time = current_time
            return False
    
    def get_context(self, length):
        """获取光标前的文本上下文"""
        with self.lock:
            start = max(0, self.cursor_pos - length)
            return ''.join(self.buffer[start:self.cursor_pos])
    
    def has_space_between(self, start, end):
        """检查两个位置之间是否有空格"""
        with self.lock:
            if start < 0 or end > len(self.buffer) or start >= end:
                return False
            
            # 检查字符之间是否有空格
            for i in range(start, end):
                if self.buffer[i] in SPACE_CHARS:
                    return True
            return False
    
    def is_valid_pair(self, char1, char2):
        """检查字符对是否有效（无空格且属于有效字符）"""
        # 检查是否为有效字符
        if char1 not in VALID_CHARS or char2 not in VALID_CHARS:
            return False
        
        # 检查两个字符是否连续且无空格
        pos1 = self.cursor_pos - 2
        pos2 = self.cursor_pos - 1
        
        # 确保位置有效
        if pos1 < 0 or pos2 >= len(self.buffer):
            return False
        
        # 检查字符之间是否有空格
        return not self.has_space_between(pos1, pos2 + 1)

# ==================== 全局实例 ====================
input_ctx = InputContext()

# ==================== 替换逻辑 ====================
def perform_replacement(replace_length, new_text):
    """执行替换操作并更新状态"""
    # 临时禁用钩子，避免递归
    keyboard.unhook(on_key_event)
    
    # 发送退格键删除旧字符
    for _ in range(replace_length):
        keyboard.send('backspace')
        time.sleep(0.01)  # 短暂延迟确保系统处理
    
    # 写入新文本
    keyboard.write(new_text)
    
    # 重新启用钩子
    keyboard.hook(on_key_event)

def handle_q_prefix_replacement():
    """处理q前缀的特殊替换逻辑"""
    context = input_ctx.get_context(3)
    if len(context) < 3:
        return False
    
    # 检查q前缀格式: q + 双写字母
    if context[0].lower() != Q_PREFIX:
        return False
    
    char_pair = context[1:]
    if char_pair[0] != char_pair[1]:
        return False
    
    # 检查是否为有效字符对
    if not input_ctx.is_valid_pair(char_pair[0], char_pair[1]):
        return False
    
    # 执行替换: qxx -> xx
    with input_ctx.lock:
        # 从缓冲区中移除旧字符
        start = input_ctx.cursor_pos - 3
        del input_ctx.buffer[start:input_ctx.cursor_pos]
        input_ctx.cursor_pos -= 3
        
        # 添加新字符
        for char in char_pair:
            input_ctx.buffer.insert(input_ctx.cursor_pos, char)
            input_ctx.cursor_pos += 1
    
    # 执行实际替换
    perform_replacement(3, char_pair)
    return True

def handle_double_char_replacement():
    """处理双字符替换逻辑"""
    context = input_ctx.get_context(2)
    if len(context) < 2:
        return False
    
    # 检查是否匹配替换规则
    if context not in REPLACE_RULES:
        return False
    
    # 检查是否为有效字符对
    if not input_ctx.is_valid_pair(context[0], context[1]):
        return False
    
    # 获取替换字符
    new_char = REPLACE_RULES[context]
    
    with input_ctx.lock:
        # 从缓冲区中移除旧字符
        start = input_ctx.cursor_pos - 2
        del input_ctx.buffer[start:input_ctx.cursor_pos]
        input_ctx.cursor_pos -= 2
        
        # 添加新字符
        input_ctx.buffer.insert(input_ctx.cursor_pos, new_char)
        input_ctx.cursor_pos += 1
    
    # 执行实际替换
    perform_replacement(2, new_char)
    return True

# ==================== 退出控制 ====================
exit_event = threading.Event()

def check_exit_hotkey():
    """检查退出热键(Ctrl+Shift+Esc)"""
    while not exit_event.is_set():
        if keyboard.is_pressed('ctrl+shift+esc'):
            exit_event.set()
        time.sleep(0.1)

# ==================== 主逻辑 ====================
def on_key_event(event):
    """键盘事件处理主函数"""
    # 忽略所有非按下事件
    if event.event_type != 'down':
        return
    
    # 更新状态并检查是否需要处理
    if input_ctx.update_state(event):
        # 先尝试处理q前缀替换
        if handle_q_prefix_replacement():
            return
        
        # 再尝试处理普通双字符替换
        handle_double_char_replacement()

# ==================== 启动程序 ====================
if __name__ == '__main__':
    # 启动热键检查线程
    exit_thread = threading.Thread(target=check_exit_hotkey, daemon=True)
    exit_thread.start()
    
    # 设置键盘钩子
    keyboard.hook(on_key_event)
    
    # 等待退出事件
    exit_event.wait()
    
    # 清理资源
    keyboard.unhook_all()
    print("程序已通过Ctrl+Shift+Esc退出")
