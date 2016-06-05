#!/usr/bin/python -O
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, abort
from flask_bootstrap import Bootstrap

import os
import sys
from pathlib import *
from vpath.virtual_path import *
import dbm
import json

db = dbm.open('storage.db', 'c')
VPath.bind_to_db(db)

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

Bootstrap(app)


def vpath_from_full_path(path):
    vp = VPath.get_root()
    for subdir in path.split('/')[1:]:
        if subdir:
            vp = vp / subdir
    return vp


@app.route('/list')
def list_dir():
    if request.args.get('local_path'):
        div = 0
        arg = request.args.get('local_path')
        path = Path(arg)
        filelist = [('..', str(path.parent), 0)]
        for f in path.iterdir():
            if f.is_dir():
                filelist.append((f.name, str(f), 0))
            else:
                filelist.append((f.name, str(f), 1))
    elif request.args.get('remote_path'):
        div = 1
        arg = request.args.get('remote_path')
        path = vpath_from_full_path(arg)
        filelist = [('..', str(path.parent), 0)]
        for f in path.iterdir():
            if f.is_dir():
                filelist.append((f.name, str(f), 0))
            else:
                filelist.append((f.name, str(f), 1))
    else:
        abort(404)
    filelist.sort(key=lambda f: (f[2], f[0]))
    curr_path = str(path)
    if not curr_path.endswith(os.sep):
        curr_path += os.sep
    return render_template(
        'viewfiles.html', curr_path=curr_path, filelist=filelist, div=div)


@app.route('/upload', methods=['POST'])
def upload():
    uploadlist = json.loads(request.form['uploadlist'])
    remotepath = request.form['remotepath']
    print(remotepath, file=sys.stderr)
    print(uploadlist, file=sys.stderr)
    vp = vpath_from_full_path(remotepath)
    vp.add([Path(p) for p in uploadlist])
    return "ok"


@app.route('/delete', methods=['POST'])
def delete():
    deletelist = json.loads(request.form['deletelist'])
    remotepath = request.form['remotepath']
    print(remotepath, file=sys.stderr)
    print(deletelist, file=sys.stderr)
    vp = vpath_from_full_path(remotepath)
    for file in deletelist:
        (vp / file).rm()
    return "ok"


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, port=8000)
