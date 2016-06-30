#!/usr/bin/python3 -O
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, abort
from flask_bootstrap import Bootstrap

import os
import sys
from pathlib import Path
from vpath.virtual_path import VPath
import dbm
import json
import threading
import atexit
import datetime
import gpg_wrapper
import gpgconfig
import subprocess

subprocess.Popen(["bash", "-c", "java -cp build/classes:config:lib/* cn.edu.ustc.center.Center"], cwd='../REOpenChord')

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

db = dbm.open('storage.db', 'c')
VPath.bind_to_db(db)
gpg_path = None
gpg_key = None
gpg_object = None
gpg_config = gpgconfig.gpg_config()

Bootstrap(app)

DEBUG = os.getenv("FLASK_DEBUG")

# Patch Path Class
Path.is_new = lambda self: False
Path.size = property(lambda self: self.stat().st_size)
Path.time = property(lambda self: int(self.stat().st_mtime))


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)


def time_fmt(timestamp):
    if timestamp == 0:
        return 'Not synchronized'
    else:
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def escape_backslash(s):
    return str(s).replace('\\', '/')


@app.route('/list')
def list_dir():
    if request.args.get('local_path'):
        div = 0
        arg = request.args.get('local_path')
        constructor = Path

    elif request.args.get('remote_path'):
        div = 1
        arg = request.args.get('remote_path')
        constructor = VPath.from_full_path

    elif request.args.get('gpg_path'):
        div = 2
        arg = request.args.get('gpg_path')
        constructor = Path

    else:
        abort(404)

    path = constructor(os.path.expanduser(arg))
    filelist = [('..', escape_backslash(path.parent), 0, False)]
    for f in path.iterdir():
        # (name, fullpath, is_file, is_new, size, mtime)
        if f.is_dir():
            filelist.append((f.name, escape_backslash(f), 0, f.is_new(), sizeof_fmt(f.size), time_fmt(f.time)))
        elif f.is_file():
            filelist.append((f.name, escape_backslash(f), 1, f.is_new(), sizeof_fmt(f.size), time_fmt(f.time)))
    filelist.sort(key=lambda f: (f[2], f[0]))
    curr_path = escape_backslash(path)
    if not curr_path.endswith('/'):
        curr_path += '/'
    height = 60 if div == 2 else 80
    return render_template(
        'viewfiles.html', curr_path=curr_path, filelist=filelist, div=div, height=height)


@app.route('/upload', methods=['POST'])
def upload():
    uploadlist = json.loads(request.form['uploadlist'])
    remotepath = request.form['remotepath']
    if DEBUG:
        print(remotepath, file=sys.stderr)
        print(uploadlist, file=sys.stderr)
    vp = VPath.from_full_path(remotepath)
    try:
        vp.add(Path(p) for p in uploadlist)
    except Exception as e:
        return str(e)
    return 'Upload succeeded!'


@app.route('/download', methods=['POST'])
def download():
    download_list = json.loads(request.form['downloadlist'])
    local_root = request.form['localpath']
    if DEBUG:
        print(download_list)
        print(local_root)
    vdir = VPath.from_full_path(os.path.dirname(download_list[0]))
    try:
        for f in map(os.path.basename, download_list):
            vdir.join(f).download(local_root)
    except Exception as e:
        return str(e)
    return 'Download succeeded!'


@app.route('/delete', methods=['POST'])
def delete():
    deletelist = json.loads(request.form['deletelist'])
    remotepath = request.form['remotepath']
    if DEBUG:
        print(remotepath, file=sys.stderr)
        print(deletelist, file=sys.stderr)
    vdir = VPath.from_full_path(remotepath)
    try:
        for f in deletelist:
            vdir.join(f).rm()
    except Exception as e:
        return str(e)
    return 'Delete succeeded!'


def commit():
    print('start commit')
    VPath.commit()
    print('commit finished')


@app.route('/sync', methods=['POST'])
def sync():
    t = threading.Thread(target=commit)
    t.start()
    return 'Syncing'


@app.route('/status')
def status():
    return json.dumps({
        "uploaded_file_num": VPath.uploaded_file_num,
        "upload_file_num": VPath.upload_file_num,
        "uploaded_index_num": VPath.uploaded_index_num,
        "upload_index_num": VPath.upload_index_num,
        "uploading_file_name": VPath.uploading_file_name,
        "uploading_index_name": VPath.uploading_index_name})


def set_gpg_path(path):
    global gpg_path
    global gpg_key
    gpg_key = gpg_wrapper.gpg_key(path)
    gpg_path = path
    print('GPG folder: ', path, file=sys.stderr)


def set_gpg_email(email):
    global gpg_object
    global gpg_key
    gpg_object = gpg_wrapper.gpg_object(gpg_key.homedir, email, key_passphrase=None)
    print('GPG email: ', email, file=sys.stderr)


@app.route('/selectgpg', methods=['POST'])
def select_gpg():
    set_gpg_path(request.form['gpgpath'])
    return ''


@app.route('/listkeys')
def list_keys():
    global gpg_key
    if gpg_key:
        emails = gpg_key.list_email()
    else:
        emails = list()
    # emails = ['abc@mail.ustc.edu.cn', 'xyz@mail.ustc.edu.cn', 'someone@163.com']
    return render_template('listkeys.html', emails=emails)


@app.route('/selectkey', methods=['POST'])
def select_key():
    set_gpg_email(request.form['gpgemail'])
    gpg_config.set(gpg_path, request.form['gpgemail'])
    return ''


@app.route('/initgpg', methods=['POST'])
def init_gpg():
    if gpg_config.exist():
        path, email = gpg_config.get()
        set_gpg_path(path)
        set_gpg_email(email)
        return '0'
    else:
        return '1'


@app.route('/')
def index():
    return render_template('index.html')


def cleanup():
    # db.sync()
    db.close()
    VPath.clean_up()
    print('clean up finished')


if __name__ == '__main__':
    atexit.register(cleanup)
    app.run(debug=True, use_reloader=False, port=8000, threaded=True)
