from pathlib import Path, PosixPath
import dirinfo_pb2
import hashlib
import code
import sys
import dbm.gnu

db = dbm.gnu.open('storage.db', 'c')
p = Path(sys.argv[1])


def get_hash(f):
    h = hashlib.sha256()
    if isinstance(f, str):
        h.update(f.encode())
    elif isinstance(f, Path):
        h.update(f.name.encode())
    return h.digest()


def dir_info(p):
    """
    p is pathlib.Path object
    """
    if not p.is_dir():
        print("{} is not a dir, quit", file=sys.stderr)
    total_size = 0
    info = dirinfo_pb2.DirInfo()
    entry = dirinfo_pb2.Entry()
    last_mtime = 0
    for i in p.iterdir():
        # if i.name == '.git' or i.name == '.':
        #     continue
        if i.is_file():
            stat = i.stat()
            entry.time = int(stat.st_mtime)
            entry.size = stat.st_size
            entry.type = entry.FILE
            # get_hash(i) here just hash the file name, need xuqiang's API
            entry.hash = get_hash(i)
            total_size += stat.st_size
            last_mtime = max(last_mtime, int(stat.st_mtime))
        elif i.is_dir():
            subdir = dir_info(i)
            entry.time = subdir['time']
            entry.size = subdir['size']
            entry.type = entry.DIR
            entry.hash = subdir['hash']
        info.content[i.name].CopyFrom(entry)
    # print('####' + str(p))
    # print(info.content)
    serialized = info.SerializeToString()
    dir_hash = get_hash(str(info))
    db[dir_hash] = serialized
    # print('&&& ' + str(serialized))
    return {'size': total_size, 'hash': dir_hash, 'time': last_mtime}


dir_info = dir_info(p)
print(dir_info)
root_entry = dirinfo_pb2.Entry()
root_entry.time = dir_info['time']
root_entry.size = dir_info['size']
root_entry.hash = dir_info['hash']
root_entry.type = root_entry.DIR
root_hash = get_hash(str(root_entry))
db[root_hash] = root_entry.SerializeToString()
db[b'root'] = root_hash
db.close()
