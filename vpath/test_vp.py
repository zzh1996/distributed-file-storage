from virtual_path import *
from pathlib import Path
import time
import sys
import dbm.gnu
import code
import threading
import resource

db = dbm.gnu.open('storage.db', 'c')
"""绑定一个数据库"""
VPath.bind_to_db(db)
"""得到根目录的VPath对象"""
vp = VPath.get_root()


def walk_dir(vp):
    """
    用来遍历整个文件系统
    :param vp: 作为根目录的VPath对象
    :return:
    """
    for i in vp.iterdir():
        if i.is_file():
            print('File: ' + str(i))
        elif i.is_dir():
            print('Dir:  ' + str(i))
            walk_dir(i)


def print_buf_pool(vp):
    for i in vp.buf_pool:
        print("###{}###".format(i.__repr__()))
        print('new_entry: ' + str(vp.buf_pool[i].new_entry))
        print('dirinfo: ' + str(vp.buf_pool[i].dirinfo))
        print('has_rm: ' + str(vp.buf_pool[i].has_rm))


def update_progress_bar(progress, interval=0.5, prefix='', suffix='', bar_len=60):
    """
    返回字符串，是进度条，定长
    百分比显示的总宽度,默认是6即精确到小数点后2位(int)
    progress    Required:是一个列表，存放了进度信息，格式为[current, total]
        current 表示当前进度(int or float)
        total   表示总(int or float)
    interval    Required:多长时间更新一次进度条
    prefix      Option:显示在进度条前方(str)
    suffix      Option:显示在进度条后面(str)
    barlen      Option:进度条长度(int)

    """
    time.sleep(interval)
    while progress.uploaded_file_num < progress.upload_file_num:
        percents = 100.0 * (float(progress.uploaded_file_num) / progress.upload_file_num)
        filled_len = int(round(bar_len * percents / 100.0))
        bar = "#" * filled_len + "-" * (bar_len - filled_len)
        sys.stdout.write("file  : {0} [{1}] {2:6.2f}% {3}\r".format(prefix, bar, percents, suffix))
        time.sleep(interval)
    while progress.uploaded_index_num < progress.upload_index_num:
        percents = 100.0 * (float(progress.uploaded_index_num) / progress.upload_index_num)
        filled_len = int(round(bar_len * percents / 100.0))
        bar = "#" * filled_len + "-" * (bar_len - filled_len)
        sys.stdout.write("index : {0} [{1}] {2:6.2f}% {3}\r".format(prefix, bar, percents, suffix))
        time.sleep(interval)
    bar = "#" * bar_len
    sys.stdout.write("done  : {0} [{1}] {2:6.2f}% {3}\n".format(prefix, bar, 100.0, suffix))


walk_dir(vp)
"""添加的是一个集合，集合元素是Path"""
# (vp/'.idea').add({adddir})
# (vp/'.git').add({addfile1})
# (vp/'.git').rm()
"""提交更改到数据库"""
vp.add({Path('/home/alkaid/tempfile/lb4g-switch-runtime')})
thread_progress_bar = threading.Thread(
    target=update_progress_bar,
    args=(vp, 0.5, "uploading")
)
thread_progress_bar.start()
vp.commit()
thread_progress_bar.join()
