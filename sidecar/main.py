import csv
import os
import fnmatch
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from ping_ip import ping_ip, ping_ip_command

# 配置参数
PUSHGATEWAY_URL = "10.22.12.178:9091"
MAX_WORKERS = 50
VALID_IPS_DIR = './valid_ips/'
FILE_PREFIX = 'valid_ips*'

def find_csv_files() -> List[str]:
    csv_files = []
    for file in os.listdir(VALID_IPS_DIR):
        if not fnmatch.fnmatch(file, FILE_PREFIX):
            continue
        csv_files.append(file)
    return sorted(csv_files)

def read_ip_addresses(csv_file: str) -> List[Dict[str, str]]:
    ip_info_list = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'valid_ip' in row:
                    ip_info = {
                        'ip': row['valid_ip'],
                        'province': row.get('province', 'unknown'),
                        'city': row.get('city', 'unknown'),
                        'isp': row.get('isp', 'unknown')
                    }
                    ip_info_list.append(ip_info)
        # print(f"从 {csv_file} 读取了 {len(ip_info_list)} 个IP地址")
    except Exception as e:
        print(f"读取文件 {csv_file} 出错: {str(e)}")
    return ip_info_list

def process_ip(ip_info: Dict[str, str]) -> None:
    ret = None
    ip = ip_info['ip']
    try:
        rtt = ping_ip_command(ip)
        # print(ip, rtt)
        if not rtt:
            rtt = 0
            ret = ip_info
        # else:
        #     print(f"{ip} 不可达")
            
        push_to_prometheus(ip_info, rtt)
        return ret
            
    except Exception as e:
        print(f"处理 {ip} 时发生错误: {str(e)}")

def save_to_csv(data_list, output_file):
    if not data_list:
        print("没有数据可保存")
        return
        
    # 写入CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['ip', 'province', 'city', 'isp']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(data_list)
    
    print(f"所有数据已保存到 {output_file}")

def main():
    print("开始IP监控程序...")
    start_time = time.time()
    
    csv_files = find_csv_files()
    if not csv_files:
        print("未找到符合条件的CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件")
    
    all_ip_info = []
    failed_ip_info = []
    for csv_file in csv_files:
        ip_info_list = read_ip_addresses(VALID_IPS_DIR + csv_file)
        all_ip_info.extend(ip_info_list)
    
    print(f"总共需要处理 {len(all_ip_info)} 个IP地址")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_ip, ip_info) for ip_info in all_ip_info]
        
        for future in as_completed(futures):
            try:
                r = future.result()
                if r:
                    failed_ip_info.append(r)
            except Exception as e:
                print(f"任务执行出错: {str(e)}")
    
    end_time = time.time()
    save_to_csv(failed_ip_info, 'ip_to_be_resolved.csv')
    print(f"IP监控程序执行完毕，总耗时: {end_time - start_time:.2f} 秒")

def push_to_prometheus(ip_info, rtt):
    registry = CollectorRegistry()
    g = Gauge('idc_ping_monitor', '', ['instance', 'province', 'city', 'isp'], registry=registry)

    ip = ip_info['ip']
    province = ip_info['province']
    city = ip_info['city']
    isp = ip_info['isp']
    g.labels(instance=ip, province=province, city=city, isp=isp).set(rtt)
    push_to_gateway(PUSHGATEWAY_URL, job='idc_ping_monitor', registry=registry, grouping_key={'city':city, 'isp': isp})


if __name__ == "__main__":
    main()
