#!/usr/bin/python -O
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for

import os,sys

app = Flask(__name__)

@app.route('/')
def listfiles():
    path=request.args.get('path', '')
    if not os.path.isdir(path):
        return redirect(url_for('listfiles',path='/'), code=302)
    parentpath=os.path.abspath(os.path.join(path, os.pardir))
    dirlist=[('..',url_for('listfiles',path=parentpath))]
    filelist=[]
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            filelist.append(f)
        else:
            dirlist.append((f,url_for('listfiles',path=os.path.join(path, f))))
    return render_template('index.html',dirlist=dirlist,filelist=filelist,path=path)

if __name__ == '__main__':
    app.run(debug=True, port=8000)

