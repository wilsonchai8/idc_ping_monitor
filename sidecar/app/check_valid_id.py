import rrdtool
import os

THRESHOLD = 10

def check_rrd_data(rrd_file):
    ret = rrdtool.fetch(
        rrd_file,
        "AVERAGE",
        "--start", "-30m",
        "--end", "now"
    )
    count = 0
    for piece in ret[2]:
        if not piece[2]:
            count += 1
        if count == THRESHOLD:
            return False
    return True

def write_file(data):
    with open('/data/invalid_ips.txt', 'w', encoding='utf-8') as f:
        for path in data:
            f.write(path + '\n')

def main():
    unvalid_ips = list()
    for root, _, files in os.walk('/data'):
        for file in files:
            if file.lower().endswith('.rrd'):
                rrd_file = os.path.join(root, file)
                if not check_rrd_data(rrd_file):
                    unvalid_ips.append(rrd_file)
    write_file(unvalid_ips)

if __name__ == '__main__':
    main()
