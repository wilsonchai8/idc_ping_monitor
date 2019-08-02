import pycurl
from lxml import etree
from io import BytesIO
import collections
import json
import IPy
import os
import datetime
from retrying import retry
import multiprocessing
from common import LogHandler


def infoInit():
    province_info = collections.defaultdict()

    province_info["beijing"] = {"name" : "北京" , "abbr" : "beijing" , "url" : "http://ip.yqie.com/cn/beijing/"}
    province_info["tianjin"] = {"name" : "天津" , "abbr" : "tianjin" , "url" : "http://ip.yqie.com/cn/tianjin/"}
    province_info["hebei"] = {"name" : "河北" , "abbr" : "hebei" , "url" : "http://ip.yqie.com/cn/hebei/shijiazhuang/"}
    province_info["neimenggu"] = {"name" : "内蒙古" , "abbr" : "neimenggu" , "url" : "http://ip.yqie.com/cn/neimenggu/huhehaote/"}
    province_info["liaoning"] = {"name" : "辽宁" , "abbr" : "liaoning" , "url" : "http://ip.yqie.com/cn/liaoning/shenyang/"}
    province_info["heilongjiang"] = {"name" : "黑龙江" , "abbr" : "heilongjiang" , "url" : "http://ip.yqie.com/cn/heilongjiang/haerbin/"}
    province_info["jilin"] = {"name" : "吉林" , "abbr" : "jilin" , "url" : "http://ip.yqie.com/cn/jilin/changchun/"}
    province_info["shandong"] = {"name" : "山东" , "abbr" : "shandong" , "url" : "http://ip.yqie.com/cn/shandong/jinan/"}
    province_info["shanxi"] = {"name" : "山西" , "abbr" : "shanxi" , "url" : "http://ip.yqie.com/cn/sanxi/taiyuan/"}
    province_info["shanghai"] = {"name" : "上海" , "abbr" : "shanghai" , "url" : "http://ip.yqie.com/cn/shanghai/"}
    province_info["zhejiang"] = {"name" : "浙江" , "abbr" : "zhejiang" , "url" : "http://ip.yqie.com/cn/zhejiang/hangzhou/"}
    province_info["jiangsu"] = {"name" : "江苏" , "abbr" : "jiangsu" , "url" : "http://ip.yqie.com/cn/jiangsu/nanjing/"}
    province_info["anhui"] = {"name" : "安徽" , "abbr" : "anhui" , "url" : "http://ip.yqie.com/cn/anhui/hefei/"}
    province_info["jiangxi"] = {"name" : "江西" , "abbr" : "jiangxi" , "url" : "http://ip.yqie.com/cn/jiangxi/nanchang/"}
    province_info["fujian"] = {"name" : "福建" , "abbr" : "fujian" , "url" : "http://ip.yqie.com/cn/fujian/fuzhou/"}
    province_info["henan"] = {"name" : "河南" , "abbr" : "henan" , "url" : "http://ip.yqie.com/cn/henan/zhengzhou/"}
    province_info["hubei"] = {"name" : "湖北" , "abbr" : "hubei" , "url" : "http://ip.yqie.com/cn/hubei/wuhan/"}
    province_info["hunan"] = {"name" : "湖南" , "abbr" : "hunan" , "url" : "http://ip.yqie.com/cn/hunan/changsha/"}
    province_info["guangdong"] = {"name" : "广东" , "abbr" : "guangdong" , "url" : "http://ip.yqie.com/cn/guangdong/guangzhou/"}
    province_info["guangxi"] = {"name" : "广西" , "abbr" : "guangxi" , "url" : "http://ip.yqie.com/cn/guangxi/nanning/"}
    province_info["shenzhen"] = {"name" : "深圳" , "abbr" : "shenzhen" , "url" : "http://ip.yqie.com/cn/guangdong/shenzhen/"}
    province_info["hainan"] = {"name" : "海南" , "abbr" : "hainan" , "url" : "http://ip.yqie.com/cn/hainan/haikou/"}
    province_info["sichuan"] = {"name" : "四川" , "abbr" : "sichuan" , "url" : "http://ip.yqie.com/cn/sichuan/chengdu/"}
    province_info["chongqing"] = {"name" : "重庆" , "abbr" : "chongqing" , "url" : "http://ip.yqie.com/cn/chongqing/"}
    province_info["guizhou"] = {"name" : "贵州" , "abbr" : "guizhou" , "url" : "http://ip.yqie.com/cn/guizhou/guiyang/"}
    province_info["yunnan"] = {"name" : "云南" , "abbr" : "yunnan" , "url" : "http://ip.yqie.com/cn/yunnan/kunming/"}
    province_info["xizang"] = {"name" : "西藏" , "abbr" : "xizang" , "url" : "http://ip.yqie.com/cn/xizang/lasa/"}
    province_info["shaanxi"] = {"name" : "陕西" , "abbr" : "shaanxi" , "url" : "http://ip.yqie.com/cn/shanxi/xian/"}
    province_info["ningxia"] = {"name" : "宁夏" , "abbr" : "ningxia" , "url" : "http://ip.yqie.com/cn/ningxia/yinchuan/"}
    province_info["gansu"] = {"name" : "甘肃" , "abbr" : "gansu" , "url" : "http://ip.yqie.com/cn/gansu/lanzhou/"}
    province_info["qinghai"] = {"name" : "青海" , "abbr" : "qinghai" , "url" : "http://ip.yqie.com/cn/qinghai/xining/"}
    province_info["xinjiang"] = {"name" : "新疆" , "abbr" : "xinjiang" , "url" : "http://ip.yqie.com/cn/xinjiang/wulumuqi/"}

    return province_info



class GetInfo(object):
    
    def __init__(self):
        pass

    @retry(stop_max_attempt_number=3)
    def getHtml(self , province , url , province_info_shared):
        ####
        @LogHandler('getHtml()')
        def info():
            return '[info] get ' + url
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEDATA, buffer)
        try:
            c.perform()
        except Exception as e :
            @LogHandler('getHtml()')
            def error():
                return 'retry ' + url + e
            raise e
        c.close()
        body = buffer.getvalue()
        if province in ('shaanxi' , 'qinghai') :
            body = body[:-2]
            
        html = etree.HTML(body.decode('utf-8'))
        piece_list = html.xpath('//table[@id="GridViewOrder"]/tr')
        
        results = self.parse(piece_list)
        province_info_temp = province_info_shared[province]
        province_info_temp.update({"cmcc" : results.get('cmcc')[0]})
        province_info_temp.update({"telcom" : results.get('telcom')[0]})
        province_info_temp.update({"unicom" : results.get('unicom')[0]})
        province_info_shared[province] = province_info_temp
        
    def parse(self , piece_list):
        results = collections.defaultdict()
        results['cmcc'] = []
        results['telcom'] = []
        results['unicom'] = []
    
        ip_addr = None
        location = None
    
        for piece in  piece_list:
            ip_start = piece.xpath('./*')[1].text
            ip_end = piece.xpath('./*')[2].text
            location = piece.xpath('./*')[3].text
    
            if results['cmcc'] and results['telcom'] and results['unicom']:
                break
    
            if not results['cmcc'] and '移动' in location :
                (exit_code , ip_addr) = self.pingCheck(ip_start , ip_end)
                if exit_code :
                    results['cmcc'].append(ip_addr)
                    results['cmcc'].append(location)
                    continue
            if not results['telcom'] and '电信' in location :
                (exit_code , ip_addr) = self.pingCheck(ip_start , ip_end)
                if exit_code :
                    results['telcom'].append(ip_addr)
                    results['telcom'].append(location)
                    continue
            if not results['unicom'] and '联通' in location :
                (exit_code , ip_addr) = self.pingCheck(ip_start , ip_end)
                if exit_code :
                    results['unicom'].append(ip_addr)
                    results['unicom'].append(location)
                    continue
            
        return results

    def pingCheck(self , ip_start , ip_end):
        ip_start_int = IPy.IP(ip_start).int()
        ip_end_int = IPy.IP(ip_end).int()
        for_count = 0
        ip_addr = None
        if ip_end_int - ip_start_int > 10 :
            for_count = 10
        else :
            for_count = ip_end_int - ip_start_int + 1
        for count in range(for_count):
            ip_addr = IPy.IP(ip_start_int + count).strNormal(0)
            os_code = not os.system("ping -c 1 -w 1 "+ ip_addr +" > /dev/null") if True else False
            if os_code :
                break
        return (os_code , ip_addr)
        
    
    def getIP(self , province_info):
        pool = multiprocessing.Pool(processes = 4)
        province_info_shared = multiprocessing.Manager().dict()
        province_info_shared.update(province_info)

        for province in province_info_shared:
            pool.apply_async(self.getHtml , (province , province_info_shared.get(province).get("url") , province_info_shared), error_callback=self.throw_error) 
        pool.close()
        pool.join()  

        return province_info_shared

    def throw_error(self , e):
        raise e


def syncToSmokingFile(province_info):
    data = collections.defaultdict()
    data['cmcc'] = "+ CMCC \n" \
                   "menu = 移动 \n" \
                   "title = 移动 \n" \
                   "\n"
    data['unicom'] = "+ UNICOM \n" \
                   "menu = 联通 \n" \
                   "title = 联通 \n" \
                   "\n"
    data['telcom'] = "+ TELCOM \n" \
                   "menu = 电信 \n" \
                   "title = 电信 \n" \
                   "\n"

    for province in province_info:
        if province_info[province].get('cmcc'):
            record = "++ " + province_info[province].get('abbr') + "\n" \
                     "menu = " + province_info[province].get('name') + "\n" \
                     "title = " + province_info[province].get('cmcc') + "\n" \
                     "host = " + province_info[province].get('cmcc') + "\n" \
                     "\n"
            data['cmcc'] += record
        if province_info[province].get('unicom'):
            record = "++ " + province_info[province].get('abbr') + "\n" \
                     "menu = " + province_info[province].get('name') + "\n" \
                     "title = " + province_info[province].get('unicom') + "\n" \
                     "host = " + province_info[province].get('unicom') + "\n" \
                     "\n"
            data['unicom'] += record
        if province_info[province].get('telcom'):
            record = "++ " + province_info[province].get('abbr') + "\n" \
                     "menu = " + province_info[province].get('name') + "\n" \
                     "title = " + province_info[province].get('telcom') + "\n" \
                     "host = " + province_info[province].get('telcom') + "\n" \
                     "\n"
            data['telcom'] += record

    for isp in data:
        with open("smokeping/location/"+isp , "w") as f:
            f.writelines(data[isp])

def getDate():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(getDate() , 'begin...')
    getinfo = GetInfo()
    province_info = getinfo.getIP(infoInit())
    syncToSmokingFile(province_info)
    print(getDate() , 'end...')
