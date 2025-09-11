import os
import re
from bs4 import BeautifulSoup
from tqdm import tqdm
import glob

def get_all_folders():
    """获取当前目录下所有文件夹"""
    return [f for f in os.listdir('.') if os.path.isdir(f)]

def process_folder(folder_path):
    """处理单个文件夹中的所有HTML文件"""
    # 获取所有HTML文件
    html_files = glob.glob(os.path.join(folder_path, "*.html"))
    if not html_files:
        print(f"\n文件夹 '{folder_path}' 中没有找到HTML文件，跳过处理。")
        return
    
    print(f"\n开始处理文件夹: {folder_path}")
    print(f"\n找到 {len(html_files)} 个HTML文件")
    
    # 存储文件信息和内容
    file_data = []
    
    # 首先收集所有文件信息和序列号
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 获取源文件名
            meta_tag = soup.find('meta', {'name': 'filename'})
            if not meta_tag:
                print(f"\n警告: 文件 {html_file} 中没有找到 <meta name='filename'> 标签，跳过此文件。")
                continue
                
            source_filename = meta_tag.get('content', '')
            if not source_filename:
                print(f"\n警告: 文件 {html_file} 中的源文件名为空，跳过此文件。")
                continue
            
            # 提取序列号
            match = re.search(r'(\d+)\.txt$', source_filename)
            if not match:
                print(f"\n警告: 无法从源文件名 '{source_filename}' 中提取序列号，跳过此文件。")
                continue
                
            seq_num = int(match.group(1))
            
            file_data.append({
                'file_path': html_file,
                'source_filename': source_filename,
                'seq_num': seq_num,
                'soup': soup
            })
            
        except Exception as e:
            print(f"\n处理文件 {html_file} 时出错: {str(e)}")
            continue
    
    if not file_data:
        print(f"\n文件夹 '{folder_path}' 中没有有效的HTML文件，跳过处理。")
        return
    
    # 按序列号排序
    file_data.sort(key=lambda x: x['seq_num'])
    
    # 确定序列号位数
    total_files = len(file_data)
    seq_digits = len(str(total_files))
    
    # 检查序列号是否连续
    expected_seq = list(range(1, total_files + 1))
    actual_seq = [item['seq_num'] for item in file_data]
    
    if expected_seq != actual_seq:
        missing = set(expected_seq) - set(actual_seq)
        print(f"\n错误: 序列号不连续! 缺失的文件: {sorted(missing)}")
        return
    
    print(f"\n序列号检查通过，共有 {total_files} 个文件，序列号位数为 {seq_digits}")
    
    # 提取共同的文件名前缀
    base_name = re.sub(r'_\d+\.txt$', '', file_data[0]['source_filename'])
    
    # 处理每个文件并提取内容
    extracted_contents = []
    
    print(f"\n开始提取内容:")
    for item in tqdm(file_data, desc=f"\n处理 {folder_path}"):
        try:
            # 提取body内容
            body = item['soup'].find('body')
            if not body:
                print(f"\n警告: 文件 {item['file_path']} 中没有找到<body>标签")
                continue
                
            # 提取所有段落文本
            paragraphs = []
            for p in body.find_all('p'):
                text = p.get_text().strip()
                if text:  # 只添加非空段落
                    paragraphs.append(text)
            
            # 在段落之间添加空行
            content = '\n\n'.join(paragraphs)
            extracted_contents.append(content)
            
        except Exception as e:
            print(f"\n提取文件 {item['file_path']} 内容时出错: {str(e)}")
            continue
    
    if not extracted_contents:
        print(f"\n没有成功提取任何内容，跳过写入文件。")
        return
    
    # 合并所有内容
    merged_content = '\n\n'.join(extracted_contents)
    
    # 生成输出文件名
    output_filename = f"Solution_{base_name}.txt"
    output_path = os.path.join(folder_path, output_filename)
    
    # 写入文件
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(merged_content)
        print(f"\n成功生成文件: {output_path}")
    except Exception as e:
        print(f"\n写入输出文件时出错: {str(e)}")

def main():
    """主函数"""
    print("HTML小说文件合并及提取工具")
    print("=" * 50)
    
    # 获取所有文件夹
    folders = get_all_folders()
    if not folders:
        print("当前目录下没有找到任何文件夹。")
        return
    
    print(f"\n找到 {len(folders)} 个文件夹: {', '.join(folders)}")
    
    # 处理每个文件夹
    for folder in folders:
        process_folder(folder)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()
