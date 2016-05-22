from virtual_path import *
import dbm.gnu
import code
import resource

db = dbm.gnu.open('storage.db', 'r')

VPath.bind_to_db(db)
root_entry = dirinfo_pb2.Entry()
root_entry.ParseFromString(db[db[b'root']])
vp = VPath([(root_entry, '')])

def walk_dir(vp):
    for i in vp.iterdir():
        if i.is_file():
            print('File: ' + str(i))
        elif i.is_dir():
            print('Dir:  ' + str(i))
            walk_dir(i)
walk_dir(vp)
# print(resource.getrusage(resource.RUSAGE_SELF))
code.interact(local=locals())
