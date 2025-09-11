import os
import re

# 全局标点符号定义
PUNCTUATIONS = r'[！？。，、；：“”‘’（）【】《》〈〉「」『』〔〕…—～・．·＊※!?,.;:"\'()\[\]{}<>…\-~*#\s\u3000]'
FULL_WIDTH_PUNCTUATIONS = "！？。，、；：“”‘’（）【】《》〈〉「」『』〔〕…—～・．·＊※"
ENDING_PUNCTUATIONS = "！？。.!?…"  # 用于检测结尾标点
CLOSING_SYMBOLS = "」』）】]〉》」'\"~"  # 所有需要特殊处理的结尾符号

def clean_japanese_content(input_path, output_path):
    """处理中日混合文本，根据日文字符存在性筛选中文段落"""
    try:
        # 扩展日文字符正则表达式（平假名+片假名+日文汉字+日文符号）
        japanese_pattern = re.compile(
            r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF\u3000-\u303F]|'  # 平假名+片假名+汉字+日文符号
            r'[々〆〤ヶ]'  # 特殊日文字符
        )
        
        # 读取文件并逐行处理
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        chinese_paragraphs = []
        skipped_empty = 0
        for line in lines:
            stripped_line = line.strip()
            # 跳过空行检测
            if not stripped_line:
                skipped_empty += 1
                continue
            # 日文字符检测逻辑 - 更严格地排除日文行
            if japanese_pattern.search(line) and has_japanese_content(line):
                continue
            chinese_paragraphs.append(line)
        
        # 后处理：合并重复标点行、添加句号、格式化输出
        processed_lines = post_process_content(chinese_paragraphs)
        
        # 写入处理结果（添加段落间空行）
        with open(output_path, 'w', encoding='utf-8') as f:
            # 添加段落间空行
            formatted_output = format_with_blank_lines(processed_lines)
            f.write(formatted_output)
        
        # 统计信息输出
        processed_lines_count = len(lines) - skipped_empty
        final_lines_count = len(processed_lines)
        print(f"SUCCESS: 共处理 {processed_lines_count} 行，清洗后保留 {len(chinese_paragraphs)} 行，后处理后保留 {final_lines_count} 行")
        print(f"输出文件路径：{os.path.abspath(output_path)}")
    except FileNotFoundError:
        print(f"ERROR: 输入文件 {input_path} 不存在")
    except Exception as e:
        print(f"ERROR: 处理失败 - {str(e)}")

def has_japanese_content(line):
    """更精确地检测日文内容（排除纯中文标点行）"""
    # 排除纯标点行
    stripped = re.sub(r'[^\w\s]', '', line)  # 移除非字母数字字符
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF]', stripped))  # 检查平假名/片假名

def post_process_content(lines):
    """后处理内容：1. 合并重复标点行 2. 添加句号 3. 段尾标点处理"""
    # 第一步：合并重复标点行
    merged_lines = merge_repeated_punctuation_lines(lines)
    
    # 第二步：在特殊符号前添加句号
    step1_lines = []
    for line in merged_lines:
        processed_line = add_period_before_closing_symbols(line)
        step1_lines.append(processed_line)
    
    # 第三步：确保段尾有标点
    processed_lines = []
    for line in step1_lines:
        processed_line = add_period_at_end(line)
        processed_lines.append(processed_line)
    
    return processed_lines

def merge_repeated_punctuation_lines(lines):
    """合并连续的重复标点行（如多个「……」）"""
    if not lines:
        return []
    
    # 检测是否为纯标点行（允许包含空格）
    def is_punctuation_only(line):
        cleaned = re.sub(r'\s', '', line)  # 移除所有空白字符
        if not cleaned:
            return False
        # 检查是否只包含标点符号
        return all(char in PUNCTUATIONS or char in FULL_WIDTH_PUNCTUATIONS for char in cleaned)
    
    result = []
    i = 0
    n = len(lines)
    
    while i < n:
        current_line = lines[i].strip()
        
        # 检查当前行是否为纯标点行
        if is_punctuation_only(current_line):
            # 查找连续相同的标点行
            j = i + 1
            while j < n and lines[j].strip() == current_line:
                j += 1
            
            # 对于连续重复的标点行，每两行保留一行
            repeat_count = j - i
            num_to_keep = (repeat_count + 1) // 2  # 向上取整
            
            # 保留计算出的行数
            for _ in range(num_to_keep):
                result.append(lines[i])
            i = j  # 跳过已处理的行
        else:
            # 非标点行直接保留
            result.append(lines[i])
            i += 1
    
    return result

def add_period_before_closing_symbols(line):
    """在特殊符号前添加句号（如果前面没有结束标点）"""
    # 检查是否包含特殊符号
    if not any(sym in line for sym in CLOSING_SYMBOLS):
        return line
    
    # 处理行内多个特殊符号
    processed_line = line
    last_index = -1
    
    # 从后向前处理，避免索引位置变化
    for symbol in CLOSING_SYMBOLS:
        if symbol not in processed_line:
            continue
            
        last_index = -1
        while symbol in processed_line[last_index + 1:]:
            # 查找下一个特殊符号
            symbol_index = processed_line.index(symbol, last_index + 1)
            last_index = symbol_index
            
            # 检查符号前是否有结束标点
            if symbol_index > 0:
                # 向前查找第一个非空白字符
                prev_index = symbol_index - 1
                while prev_index >= 0 and processed_line[prev_index] in [' ', '\t', '\u3000']:
                    prev_index -= 1
                
                if prev_index >= 0:
                    prev_char = processed_line[prev_index]
                    # 如果前一个字符不是结束标点，需要添加句号
                    if prev_char not in ENDING_PUNCTUATIONS:
                        # 在非空白字符后、符号前添加句号
                        insert_position = prev_index + 1
                        processed_line = (
                            processed_line[:insert_position] + 
                            '。' + 
                            processed_line[insert_position:]
                        )
                        last_index += 1  # 插入后符号位置后移
    
    return processed_line

def add_period_at_end(line):
    """确保段尾有结束标点（处理标题和普通段落）"""
    stripped_line = line.rstrip()  # 移除尾部空白
    if not stripped_line:
        return line
    
    # 检查最后一个非空白字符
    last_char = stripped_line[-1]
    
    # 如果已经是结束标点或特殊符号，不需要处理
    if last_char in ENDING_PUNCTUATIONS or last_char in CLOSING_SYMBOLS:
        return line
    
    # 特殊处理：以"~"结尾的情况
    if last_char == '~':
        return stripped_line + '。' + line[len(stripped_line):]
    
    # 添加句号并保留原格式
    return stripped_line + '。' + line[len(stripped_line):]

def format_with_blank_lines(lines):
    """在段落间添加空行并保留原格式"""
    formatted = []
    for i, line in enumerate(lines):
        stripped_line = line.rstrip()
        if not stripped_line:  # 空行保留
            formatted.append("\n")
        else:
            # 添加段落和空行（最后一行不加空行）
            formatted.append(stripped_line)
            if i < len(lines) - 1:
                formatted.append("\n\n")
    
    # 最后一行处理
    if formatted and formatted[-1] == "\n\n":
        formatted[-1] = "\n"
    
    return "".join(formatted)

# 使用示例
clean_japanese_content('input.txt', 'output_chinese.txt')
