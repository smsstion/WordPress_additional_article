import re
import requests
import time
from bs4 import BeautifulSoup
from tqdm import tqdm

def clean_html_tags(text):
    """清除HTML标签并保留换行符[[139]][[140]]"""
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'\n{2,}', '\n\n', clean_text)
    return clean_text.strip()

def get_chapter_content(url):
    """获取章节内容[[97]][[102]][[106]]"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取章节组标题
        group_title = ""
        group_tag = soup.find(class_="chapterTitle level1 js-vertical-composition-item")
        if group_tag and group_tag.span:
            group_title = group_tag.span.text + "\n\n"
        
        # 获取章节标题
        chapter_title = ""
        title_tag = soup.find(class_="widget-episodeTitle js-vertical-composition-item")
        if title_tag:
            chapter_title = title_tag.text + "\n\n"
        
        # 获取正文内容
        body_tag = soup.find(class_="widget-episodeBody js-episode-body")
        body_content = clean_html_tags(str(body_tag)) if body_tag else ""
        
        return group_title + chapter_title + body_content
    
    except Exception as e:
        print(f"\n章节解析失败: {url} | 错误: {e}")
        return ""

def main():
    """主爬虫程序"""
    # 01. 获取小说编号[[41]][[46]]
    novel_id = input("请输入小说编号（如1177354054889466403）: ")
    base_url = f"https://kakuyomu.jp/works/{novel_id}"
    
    # 02. 获取第一章节链接[[97]][[102]]
    try:
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        first_chapter_tag = soup.select_one('.Layout_layout__5aFuw.Layout_items-normal__4mOqD.Layout_justify-normal__zqNe7.Layout_direction-row__boh0Z.Layout_wrap-wrap__yY3zM.Layout_gap-2s__xUCm0 a')
        next_url = "https://kakuyomu.jp" + first_chapter_tag['href'] if first_chapter_tag else None
        
        if not next_url:
            print("\n错误：未找到章节链接")
            return
    except Exception as e:
        print(f"\n主页解析失败: {e}")
        return
    
    # 03-05. 爬取所有章节[[97]][[102]][[106]]
    chapters = []
    chapter_count = 0
    progress_bar = tqdm(desc="\n开始爬取", unit="章")
    
    while next_url:
        try:
            # 添加延迟避免封IP[[68]][[72]]
            time.sleep(1.5)  
            
            # 获取章节内容
            content = get_chapter_content(next_url)
            chapters.append(content)
            chapter_count += 1
            
            # 更新进度条[[175]]
            progress_bar.set_description_str(f"\n正在爬取第{chapter_count}章")
            progress_bar.update(1)
            
            # 04. 获取下一章链接
            response = requests.get(next_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            next_tag = soup.select_one('#contentMain-nextEpisode a')
            next_url = "https://kakuyomu.jp" + next_tag['href'] if next_tag else None
            
        except Exception as e:
            print(f"\n爬取中断: {e}")
            break
    
    progress_bar.close()
    
    # 06. 输出文件[[221]][[222]]
    if chapters:
        filename = f"novel_{novel_id}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(chapters))
        print(f"\n完成！共爬取{chapter_count}章，已保存至: {filename}")
    else:
        print("\n未爬取到有效内容")

if __name__ == "__main__":
    main()
