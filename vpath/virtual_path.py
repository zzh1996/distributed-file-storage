from protos import dirinfo_pb2
from grpc.beta import implementations
from protos import api_pb2
from pathlib import Path
import hashlib
import os
import time
import sys
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
    host = 'localhost'
    port = 5000
    channel = implementations.insecure_channel(host, port)
    stub = api_pb2.beta_create_FSService_stub(channel)
    _TIMEOUT = 99
    _INDEX_DOWNLOAD_RETRY = 3
    _INDEX_UPLOAD_RETRY = 3
    """:type : api_pb2.BetaFSServiceStub"""

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

    @classmethod
    def from_full_path(cls, path):
        """

        :param str path:
        :return: VPath object
        """
        vp = cls.get_root()
        path = path.lstrip('/')
        return vp.join(path)

    def join(self, *pathstrs):
        """

        :param [str] pathstrs:
        :return: VPath object
        """
        vp = self
        for s in pathstrs:
            if s == '':
                continue
            parts = Path(s).parts
            if parts[0] == '/':
                vp = VPath.get_root()
                parts = parts[1:]
            vp = functools.reduce(VPath.__truediv__, parts, vp)
        return vp

    def __str__(self):
        if self.is_root():
            return '/'
        else:
            return '/'.join([level[1] for level in self.path_stack])

    def __repr__(self):
        return 'VPath(\'{}\')'.format(self.__str__())

    def __hash__(self):
        return hash(self.hash)

    def __eq__(self, other):
        return self.path_stack == other.path_stack

    def __lt__(self, other):
        return len(self.path_stack) < len(other.path_stack)

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
            if dir_hash not in self.db:
                retry = self._INDEX_DOWNLOAD_RETRY
                request = api_pb2.FS_Request(type=api_pb2.INDEX_DOWNLOAD, payload=[dir_hash])
                while retry > 0:
                    respond = self.stub.FSServe(request, self._TIMEOUT)
                    if respond.result == api_pb2.OK:
                        self.db[dir_hash] = respond.payload[0]
                        dirinfo.ParseFromString(respond.payload[0])
                        return dirinfo
                    else:
                        retry -= 1
                        self.dbg("Index Download Failed {}".format(respond.payload))
            else:
                dirinfo.ParseFromString(self.db[dir_hash])
                return dirinfo
        else:
            return dirinfo_pb2.DirInfo()

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
        cls.upload_file_dict.clear()
        cls.upload_file_num = 0
        cls.uploaded_file_num = 0
        cls.uploading_file_name = ''
        cls.upload_index_num = 0
        cls.uploaded_index_num = 0
        cls.uploading_index_name = ''
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
        for new_path in new_path_set:
            if not isinstance(new_path, Path):
                raise NotImplementedError
            elif new_path.exists():
                self.metadata_lock.acquire()
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
                    self.metadata_lock.release()
                elif new_path.is_dir():
                    dir_content = list(new_path.iterdir())
                    if len(dir_content) == 0:
                        print("{} is empty, won't add".format(new_path.name))
                    entry.type = dirinfo_pb2.Entry.DIR
                    entry.hash = str(new_path).encode()
                    entry.size = 0
                    entry.time = 0
                    sub_dir = self / new_path.name
                    buf_record.new_entry.add(new_path.name)
                    self.buf_pool[sub_dir] = mem_buf_record()
                    self.metadata_lock.release()
                    sub_dir.add(set(new_path.iterdir()))
            else:
                print("{} not found, won't add".format(str(new_path)))

    @classmethod
    def recursive_delete_new_dir(cls, dir_vpath):
        if dir_vpath in cls.buf_pool:
            buf_record = cls.buf_pool[dir_vpath]
            for new_item in buf_record.new_entry:
                if buf_record.dirinfo.content[new_item].type == dirinfo_pb2.Entry.DIR:
                    cls.recursive_delete_new_dir(dir_vpath / new_item)
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
        :return: bool True if download success else return false
        """
        localpath.rstrip(os.sep)
        dest = localpath + os.sep + self.name
        if self.is_dir():
            if not os.path.exists(dest):
                os.mkdir(dest)
            for child in self.iterdir():
                child.download(dest)
        elif self.is_file():
            self.dbg("downloading file {} to {}".format(str(self), dest))
            request = api_pb2.FS_Request(type=api_pb2.FILE_DOWNLOAD, payload=[self.hash, dest.encode()])
            response = self.stub.FSServe(request, self._TIMEOUT)
            if response.result == api_pb2.OK:
                self.dbg("File {} download complete".format(str(self)))
                return True
            else:
                self.dbg("Download {} Failed {}".format(str(self), response.payload))
                raise RuntimeError("Download {} Failed {}".format(str(self), response.payload))

    @classmethod
    def get_file_info(cls):
        """
        generate each new_file Entry, in order to index the file in database
        need to use XuQiang's API to upload and get file identifier(such as hash)
        :return: None
        """
        """
        don't need lock because this function only invoked by VPath.commit and it will acquire a lock
        """
        for new_file in list(cls.upload_file_dict.keys()):
            p = Path(new_file)
            entry = cls.upload_file_dict[new_file]
            stat = p.stat()
            entry.time = int(stat.st_mtime)
            entry.size = stat.st_size

            cls.uploading_file_name = new_file
            cls.dbg("uploading file {}".format(new_file))
            request = api_pb2.FS_Request(type=api_pb2.FILE_UPLOAD, payload=[new_file.encode()])
            respond = cls.stub.FSServe(request, cls._TIMEOUT)
            """:type : api_pb2.FS_Response"""
            if respond.result == api_pb2.OK:
                assert respond.payload
                entry.hash = respond.payload[0]
                cls.uploaded_file_num += 1
            else:
                cls.dbg("upload file {} failed".format(new_file))
                del cls.upload_file_dict[new_file]

    @classmethod
    def send_hash(cls, key, value):
        """

        :param bytes key: hash of Dirinfo
        :param bytes value:  the Dirinfo
        :return:
        """
        retry = cls._INDEX_UPLOAD_RETRY
        request = api_pb2.FS_Request(type=api_pb2.INDEX_UPLOAD, payload=[key, value])
        while retry > 0:
            respond = cls.stub.FSServe(request, cls._TIMEOUT)
            if respond.result == api_pb2.OK:
                cls.uploaded_index_num += 1
                return
            else:
                retry -= 1
                cls.dbg("Index Upload Failed {}".format(respond.payload))
        raise RuntimeError("upload index failed")

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
            cls.dbg("uploading index {}".format(cls.uploading_index_name))
            cls.send_hash(dir_hash, serialized)
            cls.db[dir_hash] = serialized

        cls.metadata_lock.release()
        cls.reset_diff()

        # cls.db.sync()

    @classmethod
    def dbg(cls, msg):
        print("[{}] VPath: {}".format(time.ctime(), msg), file=sys.stderr)

    @classmethod
    def clean_up(cls):
        request = api_pb2.FS_Request(type=api_pb2.EXIT)
        try:
            cls.stub.FSServe(request, cls._TIMEOUT)
        except:
            pass


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
