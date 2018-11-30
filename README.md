>>####（b）测试脚本

准备一个python文件，每秒往test.log写入hello world

```
root@Bastion:/mnt# more device_test.py
import time
f = open('test.log','a+')
while 1:
    f.write('hello world\n')
    time.sleep(1)
```
