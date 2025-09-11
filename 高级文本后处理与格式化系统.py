import re
import os
import glob

# ==================== 后处理阶段函数 ====================
# 全局标点符号定义
PUNCTUATIONS = r'[！？。，、；：“”‘’（）【】《》〈〉「」『』〔〕…—～・．·＊※!?,.;:"\'()\[\]{}<>…\-~*#\s\u3000]'
FULL_WIDTH_PUNCTUATIONS = "！？。，、；：“”‘’（）【】《》〈〉「」『」〔〕…—～・．·＊※"
ENDING_PUNCTUATIONS = "！？。.!?…"  # 结尾标点
CLOSING_SYMBOLS = "」』）】]〉》\"'~"  # 需要特殊处理的结尾符号

# 定义所有可能的空白字符（包括特殊空白）
WHITESPACE_CHARS = [
    ' ',        # 普通空格 (U+0020)
    '\u00A0',   # 不换行空格 (U+00A0)
    '\u2000',   # 半身空铅 (U+2000)
    '\u2001',   # 全身空铅 (U+2001)
    '\u2002',   # 半方空铅 (U+2002)
    '\u2003',   # 方空铅 (U+2003)
    '\u2004',   # 三分之一方空铅 (U+2004)
    '\u2005',   # 四分之一方空铅 (U+2005)
    '\u2006',   # 六分之一方空铅 (U+2006)
    '\u2007',   # 数字空格 (U+2007)
    '\u2008',   # 标点空格 (U+2008)
    '\u2009',   # 细空格 (U+2009)
    '\u200A',   # 极细空格 (U+200A)
    '\u202F',   # 窄不换行空格 (U+202F)
    '\u205F',   # 中等数学空格 (U+205F)
    '\u3000',   # 全角空格 (U+3000)
    '\uFEFF',   # 零宽不换行空格 (U+FEFF)
    '\t',       # 制表符 (U+0009)
    '\v',       # 垂直制表符 (U+000B)
    '\f',       # 换页符 (U+000C)
    '\r',       # 回车符 (U+000D)
    '\n',       # 换行符 (U+000A)
]

def remove_special_whitespace(lines):
    """预处理：移除包含特殊空白的段落"""
    cleaned_lines = []
    for line in lines:
        # 检查是否只包含空白字符（包括特殊空白）
        is_whitespace_only = True
        for char in line:
            if char not in WHITESPACE_CHARS:
                is_whitespace_only = False
                break
        
        if is_whitespace_only:
            # 保留换行结构，添加空行
            cleaned_lines.append('\n')
        else:
            cleaned_lines.append(line)
    return cleaned_lines

def post_process_content(lines):
    """后处理内容：1. 合并重复标点行 2. 添加句号 3. 段尾标点处理"""
    # 第一步：移除包含特殊空白的段落
    cleaned_lines = remove_special_whitespace(lines)
    
    # 第二步：合并重复标点行
    merged_lines = merge_repeated_punctuation_lines(cleaned_lines)
    
    # 第三步：在特殊符号前添加句号
    step1_lines = []
    for line in merged_lines:
        processed_line = add_period_at_closing_symbols(line)
        step1_lines.append(processed_line)
    
    # 第四步：确保段尾有标点
    processed_lines = []
    for line in step1_lines:
        processed_line = add_period_at_end(line)
        processed_lines.append(processed_line)
    
    return processed_lines

def merge_repeated_punctuation_lines(lines):
    """合并连续的重复标点行"""
    if not lines:
        return []
    
    # 检测是否为纯标点行
    def is_punctuation_only(line):
        cleaned = re.sub(r'\s', '', line)
        if not cleaned:
            return False
        return all(char in PUNCTUATIONS or char in FULL_WIDTH_PUNCTUATIONS for char in cleaned)
    
    result = []
    i = 0
    n = len(lines)
    
    while i < n:
        current_line = lines[i].strip()
        
        if is_punctuation_only(current_line):
            j = i + 1
            while j < n and lines[j].strip() == current_line:
                j += 1
            
            repeat_count = j - i
            num_to_keep = (repeat_count + 1) // 2
            
            for _ in range(num_to_keep):
                result.append(lines[i])
            i = j
        else:
            result.append(lines[i])
            i += 1
    
    return result

def add_period_at_closing_symbols(line):
    """在段尾特殊符号前添加句号"""
    stripped_line = line.rstrip()
    if not stripped_line:
        return line
    
    last_char = stripped_line[-1]
    if last_char not in CLOSING_SYMBOLS:
        return line
    
    prev_index = len(stripped_line) - 2
    while prev_index >= 0 and stripped_line[prev_index] in WHITESPACE_CHARS:
        prev_index -= 1
    
    if prev_index < 0:
        return line
    
    prev_char = stripped_line[prev_index]
    if prev_char in ENDING_PUNCTUATIONS:
        return line
    
    new_content = stripped_line[:prev_index+1] + '。' + stripped_line[prev_index+1:]
    return new_content + line[len(stripped_line):]

def add_period_at_end(line):
    """确保段尾有结束标点"""
    stripped_line = line.rstrip()
    if not stripped_line:
        return line
    
    last_char = stripped_line[-1]
    if last_char in ENDING_PUNCTUATIONS or last_char in CLOSING_SYMBOLS:
        return line
    
    if last_char == '~':
        return stripped_line + '。' + line[len(stripped_line):]
    
    return stripped_line + '。' + line[len(stripped_line):]

def format_with_blank_lines(lines):
    """格式化输出：确保非空段落间有且仅有一个空行"""
    if not lines:
        return ""
    
    # 第一步：移除连续的空行，保留单个空行
    condensed_lines = []
    prev_was_empty = False
    for line in lines:
        # 检查是否为空行（只包含空白字符）
        is_empty = all(char in WHITESPACE_CHARS for char in line.rstrip())
        
        if is_empty:
            # 如果是空行，但前一行不是空行，则保留一个空行
            if not prev_was_empty:
                condensed_lines.append('\n')
            prev_was_empty = True
        else:
            # 非空行直接保留
            condensed_lines.append(line)
            prev_was_empty = False
    
    # 第二步：构建最终输出，确保非空段落间有且仅有一个空行
    formatted_lines = []
    prev_was_content = False
    
    for line in condensed_lines:
        # 检查当前行是否为内容行（非空行）
        is_content = not all(char in WHITESPACE_CHARS for char in line.rstrip())
        
        if is_content:
            # 如果前一行是内容行，则在中间添加一个空行
            if prev_was_content:
                formatted_lines.append('\n')
            # 添加当前内容行（保留原始内容）
            formatted_lines.append(line.rstrip() + '\n')
            prev_was_content = True
        else:
            # 空行保留（但我们已经在上一步确保只有一个空行）
            formatted_lines.append(line)
            prev_was_content = False
    
    # 第三步：处理首尾空行
    # 移除开头的空行
    while formatted_lines and formatted_lines[0] == '\n':
        formatted_lines.pop(0)
    
    # 移除结尾的连续空行，保留一个换行符
    while len(formatted_lines) > 1 and formatted_lines[-1] == '\n' and formatted_lines[-2] == '\n':
        formatted_lines.pop()
    
    return ''.join(formatted_lines)

# ==================== 主处理流程 ====================
def process_single_txt_file(input_path, output_path):
    """处理单个文本文件"""
    try:
        print(f"处理文件: {os.path.basename(input_path)}")
        
        # 读取文件内容（保留原始空白字符）
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        print(f"  读取完成，共 {len(lines)} 行文本")
        
        # 执行后处理
        processed_lines = post_process_content(lines)
        print(f"  后处理完成，保留 {len(processed_lines)} 行内容")
        
        # 格式化输出
        formatted_text = format_with_blank_lines(processed_lines)
        
        # 写入输出文件（保留特殊空白处理）
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        print(f"  输出文件: {os.path.basename(output_path)}")
        print("-" * 60)
        return True
    
    except Exception as e:
        print(f"  处理失败: {str(e)}")
        print("-" * 60)
        return False

def process_all_txt_in_directory():
    """处理当前目录下所有文本文件"""
    # 获取当前目录下所有.txt文件
    txt_files = glob.glob("*.txt")
    
    # 排除已经处理过的文件
    txt_files = [f for f in txt_files if not f.startswith("rewrite-")]
    
    if not txt_files:
        print("当前目录下未找到需要处理的.txt文件")
        return
    
    print(f"找到 {len(txt_files)} 个文本文件")
    print("=" * 60)
    
    success_count = 0
    for file_path in txt_files:
        # 创建输出文件名（rewrite-xxx.txt）
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = f"rewrite-{base_name}.txt"
        
        # 处理单个文件
        if process_single_txt_file(file_path, output_path):
            success_count += 1
    
    print(f"处理完成！成功处理 {success_count}/{len(txt_files)} 个文件")
    print(f"输出文件保存在当前目录: {os.getcwd()}")

# 执行主程序
if __name__ == "__main__":
    print("=" * 60)
    print("文本后处理工具 (高级格式化版)")
    print("=" * 60)
    print("执行流程:")
    print("1. 扫描当前目录下的.txt文件")
    print("2. 对每个文件执行以下处理:")
    print("   a. 移除包含特殊空白的段落")
    print("   b. 合并重复标点行")
    print("   c. 在特殊符号前添加句号")
    print("   d. 确保段尾有结束标点")
    print("   e. 高级格式化: 非空段落间有且仅有一个空行")
    print("3. 生成 rewrite-xxx.txt 文件")
    print("=" * 60)
    print("特殊空白处理支持以下字符:")
    print(", ".join([f"U+{ord(char):04X}" for char in WHITESPACE_CHARS]))
    print("=" * 60)
    
    process_all_txt_in_directory()
    
    print("\n处理完成！按Enter键退出...")
    input()
