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

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

db = dbm.open('storage.db', 'c')
VPath.bind_to_db(db)

Bootstrap(app)

DEBUG = os.getenv("FLASK_DEBUG")

# Patch Path Class
Path.is_new = lambda self: False
Path.size = property(lambda self: self.stat().st_size)
Path.time = property(lambda self: int(self.stat().st_mtime))


def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T','P','E','Z']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Y', suffix)

def time_fmt(timestamp):
    if timestamp==0:
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

    else:
        abort(404)

    path = constructor(arg)
    filelist = [('..', escape_backslash(path.parent), 0, False)]
    for f in path.iterdir():
        # (name, fullpath, is_file, is_new, size, mtime)
        if f.is_dir():
            filelist.append((f.name, escape_backslash(f), 0, f.is_new(), sizeof_fmt(f.size), time_fmt(f.time)))
        else:
            filelist.append((f.name, escape_backslash(f), 1, f.is_new(), sizeof_fmt(f.size), time_fmt(f.time)))
    filelist.sort(key=lambda f: (f[2], f[0]))
    curr_path = escape_backslash(path)
    if not curr_path.endswith('/'):
        curr_path += '/'
    return render_template(
        'viewfiles.html', curr_path=curr_path, filelist=filelist, div=div)


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


@app.route('/')
def index():
    return render_template('index.html')


def cleanup():
    #db.sync()
    db.close()
    print('clean up finished')

if __name__ == '__main__':
    atexit.register(cleanup)
    app.run(debug=True, use_reloader=False, port=8000, threaded=True)
