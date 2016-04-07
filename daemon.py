import sys
import json
import socket
import struct
import os
import threading
import pdb

OVERWRITE = False
SOCK_TRANSFER_BLOCK = 4096
LEN_PACK_OPT = ("q", 8)


class FileExistError(Exception):
    def __init__(self, file_name):
        self.file_name = file_name
        
    def __str__(self):
        return "File {0} has already existed".format(self.file_name)


def get_progress_bar(current, total, prefix='', suffix='', bar_len=100):
    """
    返回字符串，是进度条，定长
    百分比显示的总宽度,默认是6即精确到小数点后2位(int)
    current     Required:表示当前进度(int or float)
    total       Required:表示总(int or float)
    prefix      Option:显示在进度条前方(str)
    suffix      Option:显示在进度条后面(str)
    barlen      Option:进度条长度(int)

    """
    percents = 100.0*(float(current)/total)
    filled_len = int(round(bar_len*percents/100.0))
    bar = "#" * filled_len + "-" * (bar_len - filled_len)
    return "{0} [{1}] {2:6.2f}% {3}\r".format(prefix, bar, percents, suffix)


def get_json_from_socket(sock):
    """
    返回值是一个从sock中提取的json解析出来的dict
    sock        Required:已建立的连接
    """
    buf = sock.recv(LEN_PACK_OPT[1])
    json_len = struct.unpack(LEN_PACK_OPT[0], buf)[0]
    return json.loads(sock.recv(json_len).decode("utf-8"))


def put_json_to_socket(dict_to_put, sock):
    """
    dict_to_put    Required:用来转换成json,放入sock中的dict
    sock        Required:目标socket
    """
    json_s = json.dumps(dict_to_put)
    sock.send(struct.pack(LEN_PACK_OPT[0], len(json_s))+json_s.encode())


class Daemon(object):
    """
    str self.workdir:工作目录
    

    """
    def __init__(self, workdir):
        if workdir[-1] != "/":
            workdir += "/"
        if os.path.isdir(workdir):
            self.workdir = workdir
        else:
            raise RuntimeError("specified workdir does not exist")

    def run(self, host='', port=6788):
        """
        host        Optional:监听的地址(str)
        port        Optional:监听的端口(int)
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print("Server Started")
        while True:
            c, addr = s.accept()
            print("client({0[0]}:{0[1]}) connected".format(addr))
            t = threading.Thread(target=self.request_handler, name="client{0[0]}".format(addr), args=(c,))
            t.start()
        s.close()

    def request_handler(self, sock):
        while True:
            #pdb.set_trace()
            request = get_json_from_socket(sock)
            print(request)
            try:
                if "method" not in request:
                    raise KeyError("method not exist in request")
                if request["method"] == "exit":
                    print("client({0[0]}:{0[1]}) exited".format(sock.getpeername()))
                    sock.close()
                    break
                elif request["method"] == "upload":
                    self.retrieve_file(request, sock)
            except KeyError as err:
                print("KeyError: {0}".format(err), file=sys.stderr)
                sock.close()
            except struct.error as err:
                print("cache an struct.error {0}".format(err))
                sock.close()
            except FileExistError as err:
                print(err, file=sys.stderr)
            else:
                print("successfully deal with an request")

    def retrieve_file(self, request, sock):
        """
        if not "name" in request:
            raise KeyError("name not exist in request")
        if not "size" in request:
            raise KeyError("size not exist in request")
        """
        """
        如果文件已存在则抛出异常
        """
        path = self.workdir + request["name"]
        file_size = request["size"]
        if os.path.isfile(path):
            respond = dict(method="respond", result="file existed")
            put_json_to_socket(respond, sock)
        else:
            respond = dict(method="respond", result="accepted")
            put_json_to_socket(respond, sock)
            save_file = open(path, "wb")
            data = sock.recv(SOCK_TRANSFER_BLOCK)
            total_recv = len(data)
            save_file.write(data)
            while total_recv < file_size:
                data = sock.recv(SOCK_TRANSFER_BLOCK)
                total_recv += len(data)
                save_file.write(data)
                sys.stdout.write(
                    get_progress_bar(total_recv,
                                     file_size,
                                     "retrieving {0}".format(request["name"]),
                                     "",
                                     100
                                     )
                )
            respond = {
                "method": "respond",
                "result": "OK"
            }
            put_json_to_socket(respond, sock)


class Client(object):
    def __init__(self, remote_host, remote_port):
        """
        remote_host     Required:要连接的地址(str)
        remote_port     Required:要连接的端口(int)
        """
        self.remote_addr = (remote_host, remote_port)
        self.sock = socket.socket()
        try:
            self.sock.connect(self.remote_addr)
        finally:
            print("successfully connected to ({0[0]}:{0[1]})".format(self.remote_addr))

    def upload_file(self, file_path):
        """
        file_path       Required:要上传的文件路径
        """
        try:
            file_size = os.path.getsize(file_path)
            file_dir, file_name = os.path.split(file_path)
            request = dict(method="upload", size=file_size, name=file_name)
            put_json_to_socket(request, self.sock)
            respond = get_json_from_socket(self.sock)
            if respond["result"] == "accepted":
                with open(file_path, "rb") as file_to_send:
                    self.sock.sendfile(file_to_send)
                respond = get_json_from_socket(self.sock)
                if respond["result"] == "OK":
                    print("successfully upload {0}".format(file_path))
                else:
                    print("refused to upload {0}, error is {1}".format(file_path, respond["result"]))
            else:
                print("failed to upload {0}, error is {1}".format(file_path, respond["result"]))
        except OSError as err:
            print(err, file=sys.stderr)
        except KeyError as err:
            print("Invalid respond: {0}".format(err), file=sys.stderr)

    def finish(self):
        request = dict(method="exit")
        put_json_to_socket(request, self.sock)
        self.sock.close()