import os
import rrdtool
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import time
from datetime import datetime

PUSHGATEWAY_URL = None
FILE_PREFIX = 'valid_ips*'

def push_to_prometheus(ip_info, rtt):
    registry = CollectorRegistry()
    g = Gauge('idc_ping_monitor', '', ['instance', 'province', 'city', 'isp', 'ip'], registry=registry)

    ip = ip_info['ip']
    province = ip_info['province']
    city = ip_info['city']
    isp = ip_info['isp']
    instance = f'{province}-{city}-{isp}'
    g.labels(instance=instance, province=province, city=city, isp=isp, ip=ip).set(rtt)
    push_to_gateway(PUSHGATEWAY_URL, job='idc_ping_monitor', registry=registry, grouping_key={'city':city, 'isp': isp}, timeout=5)

def get_ip_info(file_path, full_path):
    hierarchy = []
    root = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('+'):
                level = line.count('+')
                node_name = line.split('+')[-1].strip()
                new_node = {'title': None, 'children': {}}
                
                hierarchy = hierarchy[:level-1]
                
                if hierarchy:
                    parent = hierarchy[-1]
                    parent['children'][node_name] = new_node
                else:
                    root[node_name] = new_node
                
                hierarchy.append(new_node)
            
            elif line.startswith('title = '):
                if hierarchy:
                    title_value = line.split('=', 1)[1].strip()
                    hierarchy[-1]['title'] = title_value
            elif line.startswith('host = '):
                if hierarchy:
                    host_value = line.split('=', 1)[1].strip()
                    hierarchy[-1]['host'] = host_value
    
    path_parts = [p for p in full_path.strip('/').split('/') if p]
    
    if 'data' not in path_parts:
        return {}
    
    data_index = path_parts.index('data')
    valid_parts = path_parts[data_index+1:]
    file_name = valid_parts[-1] if valid_parts else ''
    file_prefix = file_name.split('.')[0]
    
    query_parts = valid_parts[:-1] + [file_prefix] if valid_parts else []
    
    result = {}
    current_node = root

    key_name_dict = {0: 'province', 1: 'isp', 2: 'city'}
    for i in range(len(query_parts)):
        part = query_parts[i]
        if part not in current_node:
            break
        result[key_name_dict[i]] = current_node[part]['title']
        if i == 2:
            result['ip'] = current_node[part]['host']
        current_node = current_node[part]['children']
    
    return result

def main():
    for root, _, files in os.walk('/data'):
        for file in files:
            if file.lower().endswith('.rrd'):
                rrd_file = os.path.join(root, file)
                ip_file = '/opt/ips/{}'.format(rrd_file.split('/')[2])
                ip_info = get_ip_info(ip_file, rrd_file)
                ret = rrdtool.fetch(
                    rrd_file,
                    "AVERAGE",
                    "--start", "-30m",
                    "--end", "now"
                )
                f = lambda var: var * 1000 if isinstance(var, float) else 0
                rrt = f(ret[2][0][2])
                push_to_prometheus(ip_info, rrt)

if __name__ == "__main__":
    PUSHGATEWAY_URL = os.environ.get('PUSHGATEWAY_URL')
    if PUSHGATEWAY_URL:
        start_time = time.time()
        main()
        end_time = time.time()
        print('{} 上报到prometheus-pushgateway共花费 {} s'.format(datetime.strftime(datetime.now(), '%Y%m%d-%H%M%S'), end_time-start_time))
