import struct
import random
import socket
import os
import time
import platform
import re
import subprocess
from typing import Optional


PING_COUNT = 2  # 每个IP的ping次数
TIMEOUT_SECONDS = 1  # 超时时间(秒)
ICMP_ECHO_REQUEST = 8  # ICMP请求类型
ICMP_ECHO_REPLY = 0    # ICMP响应类型

def checksum(source_data: bytes) -> int:
    sum_val = 0
    count_to = (len(source_data) // 2) * 2
    count = 0
    
    while count < count_to:
        this_val = (source_data[count + 1] << 8) + source_data[count]
        sum_val += this_val
        sum_val &= 0xffffffff
        count += 2
        
    if count_to < len(source_data):
        sum_val += source_data[len(source_data) - 1]
        sum_val &= 0xffffffff
        
    sum_val = (sum_val >> 16) + (sum_val & 0xffff)
    sum_val += sum_val >> 16
    answer = ~sum_val
    answer &= 0xffff
    
    answer = answer >> 8 | (answer << 8 & 0xff00)
    
    return answer

def create_icmp_packet(seq: int, pid: int) -> bytes:
    """创建ICMP Echo Request数据包"""
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, 0, pid, seq)
    data = bytes([random.randint(0, 255) for _ in range(48)])
    check_sum = checksum(header + data)
    header = struct.pack('!BBHHH', ICMP_ECHO_REQUEST, 0, check_sum, pid, seq)
    return header + data

def ping_ip(ip: str) -> Optional[float]:
    """使用原生ICMP协议对指定IP执行ping操作"""
    pid = os.getpid() & 0xFFFF
    rtt_list = []
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as sock:
            sock.settimeout(TIMEOUT_SECONDS)
            
            for seq in range(1, PING_COUNT + 1):
                packet = create_icmp_packet(seq, pid)
                send_time = time.time()
                sock.sendto(packet, (ip, 1))
                
                try:
                    response, addr = sock.recvfrom(1024)
                    recv_time = time.time()
                    rtt = (recv_time - send_time) * 1000
                    rtt_list.append(rtt)
                    
                    ip_header = response[:20]
                    _, _, _, _, _, _, ip_protocol, _, _, _ = struct.unpack('!BBHHHBBHII', ip_header)
                    
                    if ip_protocol != socket.IPPROTO_ICMP:
                        continue
                        
                    icmp_header = response[20:28]
                    icmp_type, _, _, icmp_pid, icmp_seq = struct.unpack('!BBHHH', icmp_header)
                    
                    if icmp_type == ICMP_ECHO_REPLY and icmp_pid == pid and icmp_seq == seq:
                        continue
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"处理 {ip} (seq {seq}) 响应时出错: {str(e)}")
                    continue
    
    except PermissionError:
        print(f"没有足够权限执行ping操作，请以管理员/root权限运行程序")
        return None
    except Exception as e:
        print(f"ping {ip} 时发生错误: {str(e)}")
        return None
    
    if rtt_list:
        return sum(rtt_list) / len(rtt_list)
    else:
        # print(f"ping {ip} 失败，没有收到任何响应")
        return None

def ping_ip_command(ip: str) -> Optional[float]:
    """
    对指定IP执行ping操作并返回平均往返时间(ms)
    返回None表示ping失败
    """
    # 根据操作系统设置ping命令参数
    command = ['ping', '-c', str(PING_COUNT), '-W', str(TIMEOUT_SECONDS), ip]
    
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        
        # match = re.search(r'round-trip min/avg/max = [\d.]+/([\d.]+)/[\d.]+ ms', output)
        match = re.search(r'rtt min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms', output)
            
        if match:
            return float(match.group(1))
        else:
            print(f"无法解析 {ip} 的ping结果")
            return None
            
    except subprocess.CalledProcessError:
        # print(f"ping {ip} 失败")
        return None
    except Exception as e:
        print(f"ping {ip} 时发生错误: {str(e)}")
        return None
