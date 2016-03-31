#!/usr/bin/python -O
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, with_statement

from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        data = request.form['upload_file']
        print(data)
        return 'OK!'
    else:
        pass

if __name__ == '__main__':
    app.run(debug=True, port=8000)
    pass

