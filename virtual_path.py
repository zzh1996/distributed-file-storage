import dirinfo_pb2
import hashlib
import time
import dbm.gnu


class VPath(object):

    db = None

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
        name = self.name
        i = name.rfind('.')
        if 0 < i < len(name)-1:
            return name[i:]
        else:
            return ''

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
        return '/'.join([level[1] for level in self.path_stack])
    def __repr__(self):
        return 'VPath(\'{}\')'.format(self.__str__())

    def iterdir(self):
        dir_entry = self.path_stack[-1][0]
        dir_hash = dir_entry.hash
        try:
            dirinfo = dirinfo_pb2.DirInfo()
            dirinfo.ParseFromString(self.db[dir_hash])
        except:
            raise NotADirectoryError("{} not a directory".format(self.name))
        else:
            for name in dirinfo.content:
                yield self._from_path_stack(self.path_stack+[(dirinfo.content[name], name)])

    def __truediv__(self, name):
        if not isinstance(name, str):
            raise TypeError("argument should be a str")
        elif not self.is_dir():
            raise NotADirectoryError("{} is not a dir".format(self.name))
        else:
            if name == '.':
                return self
            if name == '..':
                return self.parent
            dir_entry = self.path_stack[-1][0]
            dir_hash = dir_entry.hash
            dirinfo = dirinfo_pb2.DirInfo()
            dirinfo.ParseFromString(self.db[dir_hash])
            if name in dirinfo.content.keys():
                return self._from_path_stack(self.path_stack+[(dirinfo.content[name], name)])
            else:
                raise FileNotFoundError("{} not exist".format(self.name + '/' + name))

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
