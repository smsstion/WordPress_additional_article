import os
import glob
from tqdm import tqdm

def process_novel_files():
    # 获取当前目录下所有txt文件，排除特定文件
    txt_files = glob.glob("*.txt")
    exclude_file = "代码大纲-分段関数.txt"  # 注意文件名可能是日文或中文编码
    files_to_process = [f for f in txt_files if f != exclude_file and not f.startswith("代码大纲-分段")]
    
    print(f"找到 {len(files_to_process)} 个需要处理的文件")
    
    # 处理每个文件
    for file_idx, filename in enumerate(files_to_process, 1):
        print(f"\n处理文件 {file_idx}/{len(files_to_process)}: {filename}")
        
        # 检查是否已存在处理后的文件夹
        output_dir = filename.replace(".txt", "")
        if os.path.exists(output_dir):
            print(f"跳过文件 {filename}，输出目录已存在")
            continue
            
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 读取文件内容
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(filename, 'r', encoding='shift_jis') as f:
                    content = f.read()
            except:
                print(f"无法读取文件 {filename}，请检查编码")
                continue
        
        # 按行拆分内容
        lines = content.splitlines()
        print(f"文件共有 {len(lines)} 行")
        
        # 处理分段
        segments = []
        current_segment = ""
        current_count = 0
        
        # 使用进度条显示处理进度
        for i, line in tqdm(enumerate(lines), total=len(lines), desc="处理行"):
            line_length = len(line)
            
            # 如果当前行加上后会超过4500字符，则保存当前段落并开始新段落
            if current_count + line_length >= 4500:
                if current_segment:  # 确保当前段落不为空
                    segments.append(current_segment)
                    current_segment = line + "\n"  # 开始新段落，包含当前行
                    current_count = line_length
                else:
                    # 如果单行就超过4500字符，直接作为一个段落
                    segments.append(line)
                    current_segment = ""
                    current_count = 0
            else:
                # 添加当前行到段落
                current_segment += line + "\n"
                current_count += line_length
            
            # 每处理100行更新一次进度
            if i % 100 == 0:
                print(f"\n已处理 {i}/{len(lines)} 行，当前段落长度: {current_count} 字符")
        
        # 添加最后一个段落
        if current_segment:
            segments.append(current_segment)
        
        print(f"\n文件分割完成，共 {len(segments)} 个段落")
        
        # 确定序号格式
        total_segments = len(segments)
        if total_segments < 10:
            num_format = "{:01d}"
        elif total_segments < 100:
            num_format = "{:02d}"
        elif total_segments < 1000:
            num_format = "{:03d}"
        else:
            num_format = "{:04d}"
        
        print(f"使用序号格式: {num_format.format(1).zfill(len(str(total_segments)))}")
        
        # 保存分段结果
        for seg_idx, segment in enumerate(tqdm(segments, desc="保存段落"), 1):
            formatted_idx = num_format.format(seg_idx)
            output_filename = f"{filename.replace('.txt', '')}_{formatted_idx}.txt"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(segment)
        
        print(f"\n文件 {filename} 处理完成，保存到 {output_dir} 目录")

if __name__ == "__main__":
    print("日文轻小说分段工具（带智能序号格式化）")
    print("=" * 60)
    process_novel_files()
    print("\n所有文件处理完成！")
