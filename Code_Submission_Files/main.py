from flask import Flask, render_template, redirect, flash, request, Response, send_from_directory, jsonify, send_file
from pandas import DataFrame
import pandas
import os, time, random
from forms import *
import re
import pandas_profiling
from pandas_profiling import ProfileReport

from functions import *

app = Flask(__name__)
app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = "jk3k43l"

MAX_UID = 1
DATASETS = [] # Stores DataFrames for multiuser mode
while len(DATASETS) <= MAX_UID:
    DATASETS.append(DataFrame())
uid = 0 


@app.route('/return-file2/')     
def return_file2():
    global uid
    if uid != None:
        print(DATASETS[uid])
        reports = ProfileReport(DATASETS[uid])
        reports.to_file(output_file='report2.html')
        print(reports)
        return send_file('report2.html', attachment_filename='report2.html')
    else:
        return ""

@app.route("/table")
def table():
    global uid
    if uid != None:
        if DATASETS[uid].shape[1] > 0:
            return DATASETS[uid].to_html(classes=['main_table'])
        else:
            return ""
    else:
        return ""
  
@app.route("/")
def index():
    if uid is None:
        redirect("/login")
    return render_template("index.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    global uid, DATASETS
    if uid == None:
        redirect("/login")
    form = CSVForm()
    fnm = ""
    if form.validate_on_submit():
        try:
            fileid = "csv-%s.csv" % (time.time()+random.randint(1,100))
            form.csvf.data.save(fileid)
            if form.rewrite.data == False and DATASETS[uid].shape[0] != 0:
                tmp = pandas.read_csv(fileid, engine='c')
                if form.join_cols.data == False:
                    if len(tmp.columns) == len(DATASETS[uid].columns):
                        DATASETS[uid] = pandas.concat([DATASETS[uid], tmp])
                else:
                        DATASETS[uid] = pandas.concat([DATASETS[uid], tmp], axis=1)
            else:
                DATASETS[uid] = pandas.read_csv(fileid)
            os.remove(fileid)
            fnm = "Uploaded!"
        except Exception as e:
            fnm = "Wrong file content! Error: %s" % str(e)
    return render_template("upload.html", form=form, filename=fnm)
    
@app.route("/sortBy", methods=["GET","POST"])
def sortBy():
    global DATASETS, uid
    if uid == None:
        return redirect("/login")
    form = DELform()
    if form.validate_on_submit():
        if uid != None and form.col.data:
            DATASETS[uid] = DATASETS[uid].sort_values(form.col.data, ascending=True)
            return render_template("sortBy.html", form=form, result="Sorted!")
        return render_template("sortBy.html", form=form, result="Nothing to sort!")
    return render_template("sortBy.html", form=form, result="")

@app.route("/calc", methods=["GET","POST"])
def calc():
    global DATASETS, uid
    if uid == None:
        return redirect("/login")
    form = CSVform()
    result = ""
    if form.validate_on_submit():
        data = form.expr.data
        if data:
            args = re.findall("\w", data)
            cols = DATASETS[uid].columns
            if not all([i in cols for i in args]):
                result = "Missing columns!"
            else:
                method = calculate(args, data)
                result = "Calculated! Using method: %s" % method
    return render_template("calc.html", form=form, result=result)

@app.route("/export.csv")
def export():
    global DATASETS, uid
    if uid != None:
        DATASETS[uid].to_csv(os.path.dirname(os.path.realpath(__file__))+'/static/export.csv')
        return send_from_directory(os.path.dirname(os.path.realpath(__file__))+'/static', 'export.csv')
    else:
        return "Nothing to export!"

@app.route("/delete", methods=['GET','POST'])
def delete():
    global DATASETS, uid
    if uid == None:
        return redirect("/login")
    form = DELform()
    if form.validate_on_submit():
        if uid != None and form.col.data:
            del DATASETS[uid][form.col.data]
            return render_template("delete.html", form=form, result="Deleted!")
        return render_template("delete.html", form=form, result="Nothing to delete!")
    return render_template("delete.html", form=form, result="")

@app.route('/jquery.js', methods=['GET'])
def jq():
     return send_from_directory(os.path.dirname(os.path.realpath(__file__))+'/static', 'jquery.js')


@app.route('/info.json')
def info():
    global uid
    if uid != None:
        data = {'len':DATASETS[uid].shape[0]*DATASETS[uid].shape[1],'cols':DATASETS[uid].shape[1],'rows':DATASETS[uid].shape[0]}
    else:
        data = {'len':0,'cols':0,'rows':0}
    return jsonify(data)
 
# run the app
app.run(debug=True, host="127.0.0.1")

