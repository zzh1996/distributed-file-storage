from virtual_path import *
from pathlib import Path
import dbm.gnu
import code
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

walk_dir(vp)
"""添加的是一个集合，集合元素是Path"""
# (vp/'.idea').add({adddir})
# (vp/'.git').add({addfile1})
# (vp/'.git').rm()
"""提交更改到数据库"""
# vp.commit()
code.interact(local=locals())
