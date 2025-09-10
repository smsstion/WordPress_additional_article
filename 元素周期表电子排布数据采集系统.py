import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

def fetch_main_table():
    """爬取主页面元素数据"""
    print("\n[进度1/4] 开始获取主页面元素周期表数据...")
    url = "https://www.webelements.com/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        elements_dict = {}
        
        # 查找所有包含元素数据的行
        rows = soup.find_all('tr')
        for row in tqdm(rows, desc="\n[进度] 解析表格行"):
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                at_num_div = cell.find('div', class_='at_num')
                if at_num_div:
                    try:
                        atomic_num = int(at_num_div.text.strip())
                        if 1 <= atomic_num <= 118:
                            e_name_div = cell.find('div', class_='e_name')
                            if e_name_div:
                                element_name = e_name_div.text.strip()
                                elements_dict[atomic_num] = element_name
                    except ValueError:
                        continue
        
        if len(elements_dict) != 118:
            print(f"\n[警告] 只找到{len(elements_dict)}个元素，需要手动检查")
        
        sorted_elements = [elements_dict[i] for i in range(1, 119)]
        return sorted_elements
    
    except Exception as e:
        print(f"\n[错误] 主页面获取失败: {str(e)}")
        return None

def get_electron_config(soup):
    """从元素页面精确提取电子排布信息 - 使用文本分割法"""
    # 找到包含电子排布描述的段落
    p_first = soup.find('p', class_='p_first')
    if not p_first:
        return None
    
    # 获取整个段落的文本
    full_text = p_first.get_text()
    
    # 查找电子排布的开始位置
    config_start = re.search(r'ground state electronic configuration of neutral [\w\s]+ is', full_text, re.IGNORECASE)
    if not config_start:
        return None
    
    # 提取电子排布部分
    config_text = full_text[config_start.end():].strip()
    
    # 查找终止关键词的位置
    term_symbol_pos = config_text.find(' and the term symbol of')
    if term_symbol_pos == -1:
        term_symbol_pos = config_text.find(' and the')
    if term_symbol_pos == -1:
        term_symbol_pos = config_text.find(' (a guess')
    
    # 如果找到终止关键词，截取之前的部分
    if term_symbol_pos != -1:
        config_text = config_text[:term_symbol_pos].strip()
    
    # 清理文本
    config_text = re.sub(r'\[(.*?)\]', r'[\1]', config_text)  # 保留方括号
    config_text = re.sub(r'&nbsp;', ' ', config_text)         # 替换HTML空格
    config_text = re.sub(r'\s+', ' ', config_text).strip()    # 清理多余空格
    
    # 提取核心电子排布模式
    config_match = re.search(r'(\[[A-Za-z]+\]\.?)?([\s\S]*?)(?= and the|\(|$)', config_text)
    if config_match:
        config_str = config_match.group(0).strip()
    else:
        config_str = config_text
    
    # 规范化格式 - 关键改进：修复轨道符号格式
    # 移除轨道符号中的空格（如"5 f" -> "5f"）
    config_str = re.sub(r'(\d)\s*([spdf])', r'\1\2', config_str)
    # 移除轨道符号与上标之间的空格（如"5f ^14" -> "5f^14"）
    config_str = re.sub(r'([spdf])\s*(\^\d+)', r'\1\2', config_str)
    # 确保所有上标都有'^'符号
    config_str = re.sub(r'([spdf])(\d+)', r'\1^\2', config_str)
    # 规范点号格式
    config_str = re.sub(r'\.\s*', '. ', config_str)
    
    # 添加缺失的点号分隔符
    config_str = re.sub(r'([a-z]\d)([A-Z])', r'\1. \2', config_str)
    config_str = re.sub(r'(\])([A-Z])', r'\1. \2', config_str)
    
    # 确保点号后有空格
    config_str = re.sub(r'\.(\S)', r'. \1', config_str)
    
    # 移除可能存在的多余部分
    config_str = re.sub(r'\(.*?\)', '', config_str)  # 移除括号内容
    
    return config_str.strip()

def main():
    elements = fetch_main_table()
    if not elements:
        print("\n[错误] 无法获取元素列表，程序终止")
        return
    
    print("\n[进度2/4] 成功获取118个元素名称列表")
    
    base_url = "https://www.webelements.com/{}/"
    element_urls = [base_url.format(element.lower()) for element in elements]
    
    print("\n[进度3/4] 开始爬取元素详情页面...")
    electron_configs = []
    
    for idx, url in enumerate(tqdm(element_urls, desc="\n[进度] 处理元素页面"), 1):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            config = get_electron_config(soup)
            if config:
                electron_configs.append(config)
            else:
                print(f"\n[警告] 元素 {idx} 未找到电子排布")
                electron_configs.append("N/A")
            
            # 礼貌性延迟
            time.sleep(0.5)
            
        except Exception as e:
            print(f"\n[警告] 元素 {idx} 处理失败: {str(e)}")
            electron_configs.append("N/A")
    
    # 任务4：保存结果到Excel
    print("\n[进度4/4] 生成结果表格...")
    df = pd.DataFrame({
        'Atomic Number': [f"{i:03d}" for i in range(1, 119)],
        'Element Name': elements,
        'Electron Configuration': electron_configs
    })
    
    # 保存文件
    output_file = "periodic_table_electron_config.xlsx"
    df.to_excel(output_file, index=False)
    
    print(f"\n[完成] 结果已保存至: {os.path.abspath(output_file)}")
    print(f"共处理 {len(df)} 个元素，其中 {df['Electron Configuration'].eq('N/A').sum()} 个未找到电子排布")

if __name__ == "__main__":
    main()
