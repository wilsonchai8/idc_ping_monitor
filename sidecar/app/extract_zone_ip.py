import sys
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from ping_ip import ping_ip_command
from pypinyin import lazy_pinyin

VALID_IPS_DIR = '/data/valid_ips/'

province_info = {
    "beijing": {
        "name": "北京",
        "abbr": "beijing",
        "file": "valid_ips_beijing.csv"
    },
    "tianjin": {
        "name": "天津",
        "abbr": "tianjin",
        "file": "valid_ips_tianjin.csv"
    },
    "hebei": {
        "name": "河北",
        "abbr": "hebei",
        "file": "valid_ips_hebei.csv"
    },
    "neimenggu": {
        "name": "内蒙古",
        "abbr": "neimenggu",
        "file": "valid_ips_neimenggu.csv"
    },
    "liaoning": {
        "name": "辽宁",
        "abbr": "liaoning",
        "file": "valid_ips_liaoning.csv"
    },
    "heilongjiang": {
        "name": "黑龙江",
        "abbr": "heilongjiang",
        "file": "valid_ips_heilongjiang.csv"
    },
    "jilin": {
        "name": "吉林",
        "abbr": "jilin",
        "file": "valid_ips_jilin.csv"
    },
    "shandong": {
        "name": "山东",
        "abbr": "shandong",
        "file": "valid_ips_shandong.csv"
    },
    "shanxi": {
        "name": "山西",
        "abbr": "shanxi",
        "file": "valid_ips_shanxi.csv"
    },
    "shanghai": {
        "name": "上海",
        "abbr": "shanghai",
        "file": "valid_ips_shanghai.csv"
    },
    "zhejiang": {
        "name": "浙江",
        "abbr": "zhejiang",
        "file": "valid_ips_zhejiang.csv"
    },
    "jiangsu": {
        "name": "江苏",
        "abbr": "jiangsu",
        "file": "valid_ips_jiangsu.csv"
    },
    "anhui": {
        "name": "安徽",
        "abbr": "anhui",
        "file": "valid_ips_anhui.csv"
    },
    "jiangxi": {
        "name": "江西",
        "abbr": "jiangxi",
        "file": "valid_ips_jiangxi.csv"
    },
    "fujian": {
        "name": "福建",
        "abbr": "fujian",
        "file": "valid_ips_fujian.csv"
    },
    "henan": {
        "name": "河南",
        "abbr": "henan",
        "file": "valid_ips_henan.csv"
    },
    "hubei": {
        "name": "湖北",
        "abbr": "hubei",
        "file": "valid_ips_hubei.csv"
    },
    "hunan": {
        "name": "湖南",
        "abbr": "hunan",
        "file": "valid_ips_hunan.csv"
    },
    "guangdong": {
        "name": "广东",
        "abbr": "guangdong",
        "file": "valid_ips_guangdong.csv"
    },
    "guangxi": {
        "name": "广西",
        "abbr": "guangxi",
        "file": "valid_ips_guangxi.csv"
    },
    "hainan": {
        "name": "海南",
        "abbr": "hainan",
        "file": "valid_ips_hainan.csv"
    },
    "sichuan": {
        "name": "四川",
        "abbr": "sichuan",
        "file": "valid_ips_sichuan.csv"
    },
    "chongqing": {
        "name": "重庆",
        "abbr": "chongqing",
        "file": "valid_ips_chongqing.csv"
    },
    "guizhou": {
        "name": "贵州",
        "abbr": "guizhou",
        "file": "valid_ips_guizhou.csv"
    },
    "yunnan": {
        "name": "云南",
        "abbr": "yunnan",
        "file": "valid_ips_yunnan.csv"
    },
    "xizang": {
        "name": "西藏",
        "abbr": "xizang",
        "file": "valid_ips_xizang.csv"
    },
    "shaanxi": {
        "name": "陕西",
        "abbr": "shaanxi",
        "file": "valid_ips_shaanxi.csv"
    },
    "ningxia": {
        "name": "宁夏",
        "abbr": "ningxia",
        "file": "valid_ips_ningxia.csv"
    },
    "gansu": {
        "name": "甘肃",
        "abbr": "gansu",
        "file": "valid_ips_gansu.csv"
    },
    "qinghai": {
        "name": "青海",
        "abbr": "qinghai",
        "file": "valid_ips_qinghai.csv"
    },
    "xinjiang": {
        "name": "新疆",
        "abbr": "xinjiang",
        "file": "valid_ips_xinjiang.csv"
    }
}

def get_province_abbr(name):
    for k, v in province_info.items():
        if v['name'] == name:
            return k

def get_available_ips(start_ip, end_ip):
    def ip_to_int(ip):
        """将IP地址转换为整数"""
        octets = list(map(int, ip.split('.')))
        return (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
    
    def int_to_ip(ip_int):
        """将整数转换为IP地址"""
        return f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
    start_int = ip_to_int(start_ip)
    end_int = ip_to_int(end_ip)
    
    # 验证IP段有效性
    if start_int > end_int:
        raise ValueError("起始IP不能大于终止IP")
    
    # 生成所有IP，跳过网络地址和广播地址
    for ip_int in range(start_int, end_int + 1):
        # 网络地址（主机位全为0）：最后一段为0
        if ip_int & 0xFF == 0:
            continue
        # 广播地址（主机位全为1）：最后一段为255
        if ip_int & 0xFF == 0xFF:
            continue
        # 返回可用IP
        yield int_to_ip(ip_int)

def find_pingable_ips(start_ip, end_ip, max_workers=100):
    ip_iterator = get_available_ips(start_ip, end_ip)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有IP的ping任务
        future_to_ip = {executor.submit(ping_ip_command, ip): ip for ip in ip_iterator}
        first_success = None
        
        # 逐个获取结果
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                # 检查是否ping通
                if future.result():
                    first_success = ip
                    break  # 找到第一个成功的就退出循环
            except Exception:
                continue
        
        # 如果找到第一个成功的IP，取消所有未完成的任务
        if first_success is not None:
            for future in future_to_ip:
                if not future.done():
                    future.cancel()
        
        return first_success

def read_ip_csv(file_path, encoding="utf-8"):
    ip_data = []
    try:
        with open(file_path, "r", newline="", encoding=encoding) as f:
            # 读取CSV并指定表头为键
            reader = csv.DictReader(f)
            
            # 验证表头是否正确（避免文件格式错误）
            required_headers = ["start_ip", "end_ip", "ip_count", "province", "city", "isp"]
            if not all(header in reader.fieldnames for header in required_headers):
                raise ValueError(f"CSV表头缺失，需包含：{required_headers}")
            
            # 逐行解析数据（可添加数据清洗逻辑）
            for row_num, row in enumerate(reader, start=2):  # row_num从2开始（跳过表头行）
                try:
                    # 数据类型转换（如ip_count从字符串转为整数，去除逗号）
                    cleaned_row = {
                        "start_ip": row["start_ip"].strip(),
                        "end_ip": row["end_ip"].strip(),
                        "ip_count": int(row["ip_count"].replace(",", "").strip()),  # 处理带逗号的数字（如"2,048"）
                        "province": row["province"].strip(),
                        "city": row["city"].strip(),
                        "isp": row["isp"].strip()
                    }
                    ip_data.append(cleaned_row)
                
                except ValueError as e:
                    print(f"第{row_num}行数据格式错误（跳过）：{e} → 原始数据：{row}")
                except KeyError as e:
                    print(f"第{row_num}行缺失关键字段（跳过）：{e} → 原始数据：{row}")
        
        print(f"成功读取 {file_path}，共获取 {len(ip_data)} 条IP段数据")
        return ip_data
    
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 不存在，请检查路径是否正确")
        return []
    except Exception as e:
        print(f"读取文件时发生未知错误：{e}")
        return []

def check_exists(data, piece):
    for d in data:
        if piece['province'] == d['province'] and piece['city'] == d['city'] and piece['isp'] == d['isp']:
            return True
    return False

def sub_save_to_csv(ip_info, province_abbr):
    new_ip = ip_info['valid_ip']
    target_city = ip_info['city']
    target_city_chinese = ip_info['city_chinese']
    target_isp = ip_info['isp']
    target_province = province_info[province_abbr]['name']
    file_path = f"/opt/ips/{province_abbr}"

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False

    is_target_isp = False
    is_target_city = False
    
    for i in range(len(lines)):
        line = lines[i]
        
        if line.strip() == f"++ {target_isp}":
            is_target_isp = True
            continue
        if is_target_isp and line.strip().startswith("++ ") and not line.strip().startswith("+++"):
            is_target_isp = False
            continue
            
        if is_target_isp and line.strip() == f"+++ {target_city}":
            is_target_city = True
            continue
        if is_target_city and line.strip().startswith("+++ "):
            is_target_city = False
            continue
            
        if is_target_city:
            if line.strip().startswith(f"title = {target_city_chinese}"):
                lines[i] = f"title = {target_city_chinese}\n"
                modified = True
            if line.strip().startswith("host ="):
                lines[i] = f"host = {new_ip}\n"
                modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"已成功将{target_city}{target_isp}的IP地址修改为: {new_ip}")
    else:
        print(f"未找到需要修改的{target_city}{target_isp}IP地址部分")

def save_to_csv(data, prov_abbr):
    """
    将包含多个IP信息的数据转换为指定格式的文本并写入文件
    
    参数:
    data: 包含IP信息的字典列表
    output_file: 输出文件路径
    """
    if not data:
        print("数据为空，无法转换")
        return

    content = []
    classified_by_isp = {}

    for info in data:
        isp = info['isp']
        if isp not in classified_by_isp:
            classified_by_isp[isp] = []
        classified_by_isp[isp].append(info)

    province_name = province_info[prov_abbr]['name']
    content.append(f"+ {prov_abbr}")
    content.append("")
    content.append(f"menu = {province_name}")
    content.append(f"title = {province_name}")
    content.append("")

    for isp, isp_info in classified_by_isp.items():
        isp_abbr = ''.join(lazy_pinyin(isp))
        content.append(f"++ {isp_abbr}")
        content.append("")
        content.append(f"menu = {isp}")
        content.append(f"title = {isp}")
        content.append("")
        for piece in isp_info:
            city = piece['city']
            city_abbr = ''.join(lazy_pinyin(city))
            valid_ip = piece['valid_ip']
            content.append(f"+++ {city_abbr}")
            content.append("")
            content.append(f"menu = {city}")
            content.append(f"title = {city}")
            content.append(f"host = {valid_ip}")
            content.append("")
    
    # 将内容写入文件
    output_file = prov_abbr
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))
    
    print(f"已成功将数据转换并写入到 {output_file}")


def find_all_ip(ip_data, prov_abbr, ci=None):
    data = []
    target_province = province_info[prov_abbr]['name']
    for ip_info in ip_data:
        province = ip_info['province']
        start_ip = ip_info['start_ip']
        end_ip = ip_info['end_ip']
        city = ip_info['city']
        isp = ip_info['isp']
        if target_province != province:
            continue
        if ci and ci != city:
            continue
        if city == '未知':
            continue
        if check_exists(data, ip_info):
            continue
        if not isp in ['电信', '移动', '联通']:
            continue
        valid_ip = find_pingable_ips(start_ip, end_ip)
        if not valid_ip:
            continue
        data.append({
            'valid_ip': valid_ip,
            'province': province,
            'city': city,
            'isp': isp
        })
    # output_file = "valid_ips_{}.csv".format(prov_abbr)
    save_to_csv(data, prov_abbr)

def find_sub(ip_data):
    f = open('/data/invalid_ips.txt')
    ret = f.readlines()
    data = list()
    to_be_resolved_ip_info_list = list()
    for piece in ret:
        result = piece.split('/')
        province = result[2]
        isp = result[3]
        city = os.path.splitext(result[4])[0]
        to_be_resolved_ip_info_list.append(
            {
                'province': province,
                'isp': isp,
                'city': city,
            }
        )

    def find_ip_internal(to_be_resolved_ip_info):
        print(to_be_resolved_ip_info)
        for ip_info in ip_data:
            province = ''.join(lazy_pinyin(ip_info['province'])) if not ip_info['province'] == '陕西' else 'shaanxi'
            city = ''.join(lazy_pinyin(ip_info['city']))
            isp = ''.join(lazy_pinyin(ip_info['isp']))
            # city_abbr = ''.join(lazy_pinyin(city))

            if to_be_resolved_ip_info['province'] == province and \
                    to_be_resolved_ip_info['city'] == city and \
                    to_be_resolved_ip_info['isp'] == isp:
                if check_exists(data, ip_info):
                    continue
                start_ip = ip_info['start_ip']
                end_ip = ip_info['end_ip']
                valid_ip = find_pingable_ips(start_ip, end_ip)
                if valid_ip:
                    return {
                        'valid_ip': valid_ip,
                        'province': province,
                        'city': city,
                        'city_chinese': ip_info['city'],
                        'isp': isp
                    }

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(find_ip_internal, ip_info) for ip_info in to_be_resolved_ip_info_list]
        
        for future in as_completed(futures):
            try:
                r = future.result()
                if r:
                    data.append(r)
            except Exception as e:
                print(f"任务执行出错: {str(e)}")
    # data = [{'province':'guizhou', 'valid_ip': '58.42.184.1', 'city': 'bijie', 'isp':'dianxin'}]
    for piece in data :
        abbr = piece['province']
        sub_save_to_csv(piece, abbr)


def main(*args, **kwargs):
    file = args[0]
    prov_abbr = args[1]
    ip_data = read_ip_csv(file)
    if prov_abbr == 'sub':
        find_sub(ip_data)
    else:
        find_all_ip(ip_data, prov_abbr)

if __name__ == "__main__":
    file = sys.argv[1]
    province = sys.argv[2] if len(sys.argv) >2 else None
    main(file, province)

