from . import dirinfo_pb2
from pathlib import Path
import hashlib
import os
import time
from threading import Lock
import functools


@functools.total_ordering
class VPath(object):

    db = None
    buf_pool = {}  # type: dict [VPath,mem_buf_record]
    upload_file_dict = {}
    upload_file_num = 0
    uploaded_file_num = 0
    uploading_file_name = ''
    upload_index_num = 0
    uploaded_index_num = 0
    uploading_index_name = ''
    metadata_lock = Lock()

    def __init__(self, path_stack):
        """

        :param path_stack: list of tuple(protobuf message Entry:root entry, str:root name)
        #path_stack = [(db['root'], '')]
        """
        if self.db is None:
            raise PermissionError("haven't binded to a db, use bind_to_db")

        self.path_stack = path_stack

    @classmethod
    def bind_to_db(cls, db):
        """

        :param db: dbm.gnu, need read permission
        :return: None
        """
        cls.db = db

    @classmethod
    def get_root(cls):
        """

        :return: VPath: the root directory of entire filesystem
        """
        root_entry = dirinfo_pb2.Entry()
        try:
            root_entry.ParseFromString(cls.db[cls.db[b'root']])
        except KeyError:
            root_entry.type = root_entry.DIR
            print("Empty filesystem")
        return cls([(root_entry, '')])

    @property
    def name(self):
        """The final path component, if any."""
        return self.path_stack[-1][1]

    @property
    def size(self):
        return self.path_stack[-1][0].size

    @property
    def time(self):
        return self.path_stack[-1][0].time

    @property
    def hash(self):
        return self.path_stack[-1][0].hash

    @property
    def suffix(self):
        return os.path.splitext(self.name)[1]

    @property
    def parent(self):
        if len(self.path_stack) > 1:
            return self._from_path_stack(self.path_stack[:-1])
        else:
            return self

    @classmethod
    def _from_path_stack(cls, path_stack):
        """

        :param path_stack: base path stack
        :return: a new instance
        """
        self = cls(path_stack)
        return self

    def __str__(self):
        if self.is_root():
            return os.sep
        else:
            return os.sep.join([level[1] for level in self.path_stack])

    def __repr__(self):
        return 'VPath(\'{}\')'.format(self.__str__())

    def __hash__(self):
        return hash(self.hash)

    def __eq__(self, other):
        return self.path_stack == other.path_stack

    def __lt__(self, other):
        return len(self.path_stack) < len(other.path_stack)

    @staticmethod
    def get_hash(data):
        h = hashlib.sha256()
        if isinstance(data, str):
            h.update(data.encode())
        elif isinstance(data, Path):
            h.update(data.name.encode())
        else:
            raise NotImplementedError
        return h.digest()

    @staticmethod
    def get_path_hash(p):
        h = hashlib.sha256()
        h.update(p.name.encode())
        return h.digest()

    @staticmethod
    def get_dirinfo_hash(dirinfo):
        h = hashlib.sha256()
        h.update(str(dirinfo).encode())
        return h.digest()

    def get_dirinfo(self):
        dir_entry = self.path_stack[-1][0]
        dir_hash = dir_entry.hash
        dirinfo = dirinfo_pb2.DirInfo()
        if len(dir_hash) > 0:
            dirinfo.ParseFromString(self.db[dir_hash])
        return dirinfo

    def iterdir(self):
        if not self.is_dir():
            raise NotADirectoryError("{} not a directory".format(self.name))
        if self in self.buf_pool:
            dirinfo = self.buf_pool[self].dirinfo
        else:
            try:
                dirinfo = self.get_dirinfo()
            except:
                raise FileNotFoundError("index of {} not found".format(self.name))
        for name in dirinfo.content:
            yield self._from_path_stack(self.path_stack + [(dirinfo.content[name], name)])

    def __truediv__(self, other):
        if not isinstance(other, str):
            raise TypeError("argument should be a str")
        elif not self.is_dir():
            raise NotADirectoryError("{} is not a dir".format(self.name))
        else:
            if other == '.':
                return self
            if other == '..':
                return self.parent
            if self in self.buf_pool:
                dirinfo = self.buf_pool[self].dirinfo
            else:
                dirinfo = self.get_dirinfo()
            if other in dirinfo.content.keys():
                return self._from_path_stack(self.path_stack + [(dirinfo.content[other], other)])
            else:
                raise FileNotFoundError("{} not exist".format(self.name + '/' + other))

    def is_file(self):
        dir_entry = self.path_stack[-1][0]
        if dir_entry.type is dir_entry.FILE:
            return True
        else:
            return False

    def is_dir(self):
        dir_entry = self.path_stack[-1][0]
        if dir_entry.type is dir_entry.DIR:
            return True
        else:
            return False

    def is_root(self):
        return len(self.path_stack) == 1

    def is_new(self):
        """
        新添加未commit的目录的特点是，在buf_pool中
        新添加未commit的文件的特点是，time，size == 0
        :return: bool
        """
        if self.is_dir():
            return self in self.buf_pool
        elif self.is_file():
            return self.time == 0
        else:
            return False

    @classmethod
    def reset_diff(cls):
        cls.metadata_lock.acquire()
        cls.buf_pool.clear()
        cls.metadata_lock.release()

    def add(self, new_path_set):
        """
        add a set of new file/dir into this VPath, buffered until commit
        :param set of Path new_path_set: file to add
        will overwrite if there is a same name file/dir existing
        :return:
        """
        if not self.is_dir():
            raise NotADirectoryError
        self.metadata_lock.acquire()
        for new_path in new_path_set:
            if not isinstance(new_path, Path):
                raise NotImplementedError
            elif new_path.exists():
                if self not in self.buf_pool:
                    self.buf_pool[self] = mem_buf_record(self)

                buf_record = self.buf_pool[self]
                entry = buf_record.dirinfo.content[new_path.name]
                if new_path.is_file():
                    entry.type = dirinfo_pb2.Entry.FILE
                    entry.hash = str(new_path).encode()
                    entry.size = new_path.stat().st_size
                    entry.time = 0
                    buf_record.new_entry.add(new_path.name)
                    self.upload_file_dict[str(new_path)] = dirinfo_pb2.Entry()
                elif new_path.is_dir():
                    dir_content = list(new_path.iterdir())
                    if len(dir_content) == 0:
                        print("{} is empty, won't add".format(new_path.name))
                    entry.type = dirinfo_pb2.Entry.DIR
                    entry.hash = str(new_path).encode()
                    entry.size = 0
                    entry.time = 0
                    sub_dir = self/new_path.name
                    buf_record.new_entry.add(new_path.name)
                    self.buf_pool[sub_dir] = mem_buf_record()
                    sub_dir.add(set(new_path.iterdir()))
            else:
                print("{} not found, won't add".format(str(new_path)))
        self.metadata_lock.release()

    @classmethod
    def recursive_delete_new_dir(cls, dir_vpath):
        if dir_vpath in cls.buf_pool:
            buf_record = cls.buf_pool[dir_vpath]
            for new_item in buf_record.new_entry:
                if buf_record.dirinfo.content[new_item].type == dirinfo_pb2.Entry.DIR:
                    cls.recursive_delete_new_dir(dir_vpath/new_item)
            del cls.buf_pool[dir_vpath]

    def rm(self):
        self.metadata_lock.acquire()
        if not self.is_root():
            print("rm {}".format(str(self)))
            parent = self.parent
            """if it's parent haven't been modified, add the parent in buf_pool"""
            if parent not in self.buf_pool:
                self.buf_pool[parent] = mem_buf_record(self.parent)
            parent_buf_record = self.buf_pool[parent]
            parent_new_entry = parent_buf_record.new_entry

            """if remove a file added, remove it's record in upload_file_dict and buf_pool"""
            if self.name in parent_new_entry:
                parent_new_entry.remove(self.name)
                # 不递归删除空目录了，下面的代码被注释掉
                # if len(parent_new_entry) == 0 and not parent_buf_record.has_rm:
                #     self.parent.rm()
                real_path = self.buf_pool[parent].dirinfo.content[self.name].hash.decode()
                """real_path :str"""
                if real_path in self.upload_file_dict:
                    del self.upload_file_dict[real_path]

            else:
                self.buf_pool[parent].has_rm = True
            del parent_buf_record.dirinfo.content[self.name]

        if self.is_dir():
            self.recursive_delete_new_dir(self)
        self.metadata_lock.release()

    def download(self, localpath):
        """
        下载此文件/夹到一个本地目录(localpath)
        :param str localpath:
        :return:
        """
        if self.is_dir():
            for child in self.iterdir():
                child.download(localpath)
        elif self.is_file():
            print("download file {} to {}".format(str(self), localpath+os.sep+self.name))

    @classmethod
    def get_file_info(cls):
        """
        generate each new_file Entry, in order to index the file in database
        need to use XuQiang's API to upload and get file identifier(such as hash)
        :return: None
        """
        for new_file in cls.upload_file_dict:
            p = Path(new_file)
            entry = cls.upload_file_dict[new_file]
            stat = p.stat()
            entry.time = int(stat.st_mtime)
            entry.size = stat.st_size
            """here, may change hash source someday"""
            entry.hash = cls.get_path_hash(p)
            cls.uploaded_file_num += 1
            cls.uploading_file_name = new_file
            time.sleep(0.01)

    @classmethod
    def send_hash(cls, key, value):
        """

        :param bytes key: hash of Dirinfo
        :param bytes value:  the Dirinfo
        :return:
        """
        cls.uploaded_index_num += 1
        time.sleep(0.2)
        """need use XuQiang's API to upload hash"""

    @classmethod
    def commit(cls):
        cls.metadata_lock.acquire()
        for dir_vpath in list(cls.buf_pool.keys()):
            while dir_vpath.parent not in cls.buf_pool:
                cls.buf_pool[dir_vpath.parent] = mem_buf_record(dir_vpath.parent)
                dir_vpath = dir_vpath.parent

        cls.upload_file_num = len(cls.upload_file_dict)
        cls.uploaded_file_num = 0
        cls.uploading_file_name = ''
        cls.get_file_info()
        cls.upload_index_num = len(cls.buf_pool)
        cls.uploaded_index_num = 0
        cls.uploading_index_name = ''

        for dir_vpath in sorted(cls.buf_pool, reverse=True):
            buf_record = cls.buf_pool[dir_vpath]
            total_size = 0
            last_mtime = 0
            for new_item in buf_record.new_entry:
                new_item_entry = buf_record.dirinfo.content[new_item]
                if new_item_entry.type == dirinfo_pb2.Entry.FILE:
                    buf_record.dirinfo.content[new_item].CopyFrom(cls.upload_file_dict[new_item_entry.hash.decode()])
            for item in buf_record.dirinfo.content:
                total_size += buf_record.dirinfo.content[item].size
                last_mtime = max(last_mtime, buf_record.dirinfo.content[item].time)
            dir_hash = cls.get_dirinfo_hash(buf_record.dirinfo)
            if dir_vpath.is_root():
                entry_record = dirinfo_pb2.Entry()
                entry_record.type = entry_record.DIR
            else:
                entry_record = cls.buf_pool[dir_vpath.parent].dirinfo.content[dir_vpath.name]
            entry_record.time = last_mtime
            entry_record.size = total_size
            entry_record.hash = dir_hash
            if dir_vpath.is_root():
                root_hash = cls.get_hash(str(entry_record))
                cls.db[root_hash] = entry_record.SerializeToString()
                cls.db[b'root'] = root_hash
            else:
                if dir_vpath.name in cls.buf_pool[dir_vpath.parent].new_entry:
                    cls.buf_pool[dir_vpath.parent].new_entry.remove(dir_vpath.name)
            serialized = buf_record.dirinfo.SerializeToString()
            cls.uploading_index_name = str(dir_vpath)
            cls.send_hash(dir_hash, serialized)
            cls.db[dir_hash] = serialized

        cls.buf_pool.clear()
        cls.upload_file_dict.clear()
        cls.metadata_lock.release()

        cls.db.sync()

    @classmethod
    def clean_up(cls):
        cls.db.close()


class mem_buf_record(object):

    def __init__(self, vpath=None):
        """

        :param VPath vpath: if is None, generate a empty dirinfo; or copy from dirinfo of vpath
        """
        self.new_entry = set()
        self.dirinfo = dirinfo_pb2.DirInfo()
        self.has_rm = False
        if vpath is not None:
            self.dirinfo = vpath.get_dirinfo()
