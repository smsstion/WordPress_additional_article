import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def epub_to_txt(epub_path, txt_path):
    book = epub.read_epub(epub_path)
    output_lines = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            
            # 处理所有块级元素（段落/标题/列表等）
            for element in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                # 关键修复1：保留空行结构
                if element.name in ['div', 'section']:
                    output_lines.append('')
                
                # 关键修复2：合并段落内换行
                text = element.get_text()
                text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  # 替换孤立换行符为空格
                text = re.sub(r'\s+', ' ', text).strip()      # 压缩连续空格
                
                # 关键修复3：跳过自动序号
                if not re.match(r'^\d+[\.\s]', text):  # 过滤数字开头的序号
                    output_lines.append(text)
    
    # 写入文件并保留空行
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

# 使用示例
epub_to_txt('input.epub', 'output.txt')
