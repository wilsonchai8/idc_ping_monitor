import requests
import time
import csv
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from datetime import datetime

# 全局设置
BASE_URL = "https://www.22tool.com/ip-block/china?page={}"
MAX_WORKERS = 10  # 并发线程数
TIMEOUT = 10  # 超时时间(秒)
RETRY_TIMES = 3  # 重试次数
OUTPUT_FILE = "ip_blocks_{}.csv".format(datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S'))  # 输出文件

# 请求头，模拟浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    "Connection": "keep-alive"
}

def create_session():
    """创建带重试机制的请求会话"""
    session = requests.Session()
    retry_strategy = Retry(
        total=RETRY_TIMES,
        backoff_factor=1,  # 重试间隔时间: {backoff_factor} * (2 **({retry_count} - 1))
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def parse_ip_table(html):
    """解析IP地址段表格内容（复用之前的逻辑）"""
    soup = BeautifulSoup(html, 'html.parser')
    ip_data = []
    
    # 查找表格主体
    tbody = soup.find('tbody', class_='fw-semibold text-gray-600')
    if not tbody:
        return ip_data
    
    # 查找所有行
    for row in tbody.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) == 6:
            try:
                start_ip = cells[0].get_text(strip=True)
                end_ip = cells[1].get_text(strip=True)
                ip_count = int(cells[2].get_text(strip=True).replace(',', ''))
                province = cells[3].get_text(strip=True)
                city = cells[4].get_text(strip=True)
                isp = cells[5].get_text(strip=True)
                
                ip_data.append({
                    'start_ip': start_ip,
                    'end_ip': end_ip,
                    'ip_count': ip_count,
                    'province': province,
                    'city': city,
                    'isp': isp
                })
            except Exception as e:
                print(f"解析行数据出错: {e}")
                continue
    
    return ip_data

def crawl_page(session, page):
    """爬取单个页面的数据"""
    try:
        url = BASE_URL.format(page)
        response = session.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()  # 抛出HTTP错误状态码
        
        # 解析页面内容
        data = parse_ip_table(response.text)
        print(f"成功爬取第{page}页，获取{len(data)}条数据")
        return data
        
    except Exception as e:
        print(f"爬取第{page}页失败: {str(e)}")
        return None

def save_to_csv(data_list):
    """将数据保存到CSV文件"""
    if not data_list:
        print("没有数据可保存")
        return
        
    # 写入CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['start_ip', 'end_ip', 'ip_count', 'province', 'city', 'isp']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for data in data_list:
            writer.writerows(data)  # 每个页面的数据是列表，需要展开写入
    
    print(f"所有数据已保存到 {OUTPUT_FILE}")

def main():
    start_time = time.time()
    all_data = []
    session = create_session()
    
    # 使用线程池并发爬取
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        futures = {executor.submit(crawl_page, session, page): page for page in range(1, 213)}
        
        # 处理完成的任务
        for future in as_completed(futures):
            page = futures[future]
            try:
                result = future.result()
                if result:
                    all_data.append(result)
            except Exception as e:
                print(f"处理第{page}页结果时出错: {e}")
    
    # 保存数据
    save_to_csv(all_data)
    
    end_time = time.time()
    print(f"爬取完成，共耗时{end_time - start_time:.2f}秒")

if __name__ == "__main__":
    main()

