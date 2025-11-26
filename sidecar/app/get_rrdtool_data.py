import rrdtool
import sys

THRESHOLD = 10

def main(rrd_file):
    ret = rrdtool.fetch(
        rrd_file,
        "AVERAGE",
        "--start", "-30m",
        "--end", "now"
    )
    print(ret)



if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)
