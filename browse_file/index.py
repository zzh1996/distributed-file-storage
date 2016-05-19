#!/usr/bin/python -O
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap

import os,sys
import pathlib

app = Flask(__name__)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

Bootstrap(app)

@app.route('/list')
def list_dir():
    if request.args.get('local_path'):
        arg = request.args.get('local_path')
        path = pathlib.Path(arg)
        for f in path.iterdir():
            if f.is_dir():
                pass
            else:
                pass

    elif request.args.get('remote_path'):
        pass
    return ''

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000)

