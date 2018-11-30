> 一、idc_ping_monitor

IDC机房测速工具，由3个组件组成：  
smokeping：主要负责采集数据  
prometheus：主要负责存储数据  
grafana：主要负责采集数据  

> 二、使用

>> smokeping

smokeping的家目录：

```
smokeping_home_dir=/usr/local/smokeping
```

创建config文件

```
cd /usr/local/smokeping/etc
curl -O https://github.com/wilsonchai8/idc_ping_monitor/blob/master/smokeping/config
```
