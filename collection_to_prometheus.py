#coding:utf-8
import requests
import rrdtool
import os
from common import LogHandler


paras = {
    'province_map' : {
        'anhui'         : '安徽' ,
        'beijing'       : '北京' ,
        'chongqing'     : '重庆' ,
        'fujian'        : '福建' ,
        'gansu'         : '甘肃' ,
        'guangdong'     : '广东' ,
        'guangxi'       : '广西' ,
        'guizhou'       : '贵州' ,
        'hainan'        : '海南' ,
        'hebei'         : '河北' ,
        'heilongjiang'  : '黑龙江' ,
        'henan'         : '河南' ,
        'hubei'         : '湖北' ,
        'hunan'         : '湖南' ,
        'jiangsu'       : '江苏' ,
        'jiangxi'       : '江西' ,
        'jilin'         : '吉林' ,
        'liaoning'      : '辽宁' ,
        'neimenggu'     : '内蒙古' ,
        'ningxia'       : '宁夏' ,
        'qinghai'       : '青海' ,
        'shaanxi'       : '陕西' ,
        'shandong'      : '山东' ,
        'shanghai'      : '上海' ,
        'shanxi'        : '山西' ,
        'shenzhen'      : '深圳' ,
        'sichuan'       : '四川' ,
        'tianjin'       : '天津' ,
        'xinjiang'      : '新疆' ,
        'xizang'        : '西藏' ,
        'yunnan'        : '云南' ,
        'zhejiang'      : '浙江'
    } , 
    'prometheus_gateway' : 'http://192.168.56.101:9091' , 
    'data_dir' : '/usr/local/smokeping/data'
}

def pushMetrics(instance , ISP , key , value):
    headers = {'X-Requested-With': 'Python requests', 'Content-type': 'text/xml'}
    pushgateway = '%s/metrics/job/smokeping-collected-%s/instance/%s' % (paras['prometheus_gateway'] , ISP , instance)
    metrics = 'smokeping_%s{instance=\"%s\" , ISP=\"%s\" , IDC=\"%s\" , alias=\"%s\"} %d' % (key , instance , ISP , 'SH' , paras['province_map'].get(instance) , value)
    request_code = requests.post(pushgateway , data='{0}\n'.format(metrics).encode('utf-8') , headers=headers)
    @LogHandler(pushgateway)
    def info():
        return metrics + ' - ' + str(request_code.status_code)

def getMonitorData(rrd_file): 
    rrd_info = rrdtool.info(rrd_file)
    last_update = rrd_info['last_update'] - 60
    args = '-s ' + str(last_update) 
    results = rrdtool.fetch(rrd_file , 'AVERAGE' , args )
    lost_package_num = int(results[2][0][1])
    average_rrt = 0 if not results[2][0][2] else results[2][0][2] * 1000
    return lost_package_num , round(average_rrt , 4)


if __name__ == '__main__':
    ISP_list = ['TELCOM' , 'CMCC' , 'UNICOM' , 'TENCENT']
    for ISP in ISP_list:
        rrd_data_dir = os.path.join(paras['data_dir'] , ISP)
        for filename in os.listdir(rrd_data_dir):
            (instance , postfix) = os.path.splitext(filename)
            if postfix == '.rrd' :
                (lost_package_num , rrt) = getMonitorData(os.path.join(paras['data_dir'] , ISP , filename))
                pushMetrics(instance , ISP , 'rrt' , rrt)
                pushMetrics(instance , ISP , 'lost_package_num' , lost_package_num)
