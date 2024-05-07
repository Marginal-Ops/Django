from django.shortcuts import render
from django.http import HttpResponse
import yaml
import time
import datetime
import os
import pandas as pd
import numpy as np
from django.conf import settings
import matplotlib.pyplot as plt
from django.http import HttpResponseRedirect
import matplotlib.cm as cm
switch_hour = 18


global_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.local/crontab_config.yaml')
with open(global_json_path, "r") as f:
    global_yaml_config = yaml.load(f, Loader=yaml.FullLoader)


def get_map_df(date1=None, date2=None):
    # 解析data
    if date1:
        pass
    else:
        thisHour = int(time.strftime("%H", time.localtime()))
        if thisHour >= switch_hour:
            date1 = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y%m%d')
        else:
            date1 = time.strftime("%Y%m%d", time.localtime())

    theMap = {}
    log_root_dir = global_yaml_config.get("root_dir")
    print(os.path.join(log_root_dir, date1, 'summary.csv'), date1, date2)
    theMap['Crontab_' + date1] = pd.read_csv(os.path.join(log_root_dir, date1, 'summary.csv'))
    return theMap


def if_warn(myMapDf, date1, date2):  # 筛选 warning 的数据
    theMapDf = myMapDf.copy()
    print(theMapDf)
    for thisKey in theMapDf.keys():
        if "Crontab" in thisKey:
            if date1:
                pass
            else:
                print(myMapDf.keys(), thisKey)
                theMapDf[thisKey] = theMapDf[thisKey].loc[theMapDf[thisKey]['Status'] != 'Done', :]
        else:
            if 'Warn' in theMapDf[thisKey].columns:
                myShowCol = list(theMapDf[thisKey].columns)
                if 'Update' in myShowCol:
                    myShowCol.remove('Update')
                theMapDf[thisKey] = theMapDf[thisKey].loc[theMapDf[thisKey].loc[:, 'Warn'] == True, myShowCol]

    return theMapDf


global RAW_DF_MAP
RAW_DF_MAP = {}


def hello(request):  # hello页面
    print('hello 0')
    ip_address0 = request.META.get('REMOTE_ADDR', '')
    ip_address1 = request.META.get('HTTP_X_FORWARDED_FOR')
    ip_address2 = request.META.get('HTTP_CLIENT_IP')
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('HTTP_CLIENT_IP') or request.META.get('REMOTE_ADDR', '')
    global RAW_DF_MAP
    time_str = time.strftime("%H:%M:%S", time.localtime())
    myStr = ""
    myStr += '<img src="/medias/fisher.png" weidth="300" height="150">'
    myStr += "<br/>"
    myStr += "welcome to fisher crontab list!~~~~~~"
    myStr += "<br/>"
    myStr += "Now HOSTNAME: "
    myStr += str(os.environ['HOSTNAME'])
    myStr += "<br/>"
    myStr += "Now IP: "
    myStr += str(ip_address) + " " + str(ip_address0) + " " + str(ip_address1) + " " + str(ip_address2)
    myStr += "<br/>"
    myStr += "Now time: "
    myStr += time_str
    myStr += " switch_hour %s" % (switch_hour)
    myStr += "<br/><br/><br/>"
    myStr += "<form action=\"/search/\" method=\"get\">"
    myStr += " <input type=\"text\" name=\"q1\">"
    myStr += " <input type=\"text\" name=\"q2\">"
    myStr += " <input type=\"submit\" value=\"提交\">"
    myStr += "</form><br/>"

    global_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.local/config.yaml')
    with open(global_json_path, "r") as f:
        yaml_config = yaml.load(f, Loader=yaml.FullLoader)
    ip_dict = yaml_config.get('ips')

    q1 = None
    q2 = None
    password = ''
    if 'q1' in request.GET and (request.GET['q1']):
        q1 = request.GET['q1']
    if 'q2' in request.GET and (request.GET['q2']):
        q2 = request.GET['q2']
    if q1 is None and q2 is not None:
        password = q2
        q2 = None
    if (ip_address not in list(ip_dict.values())) and (password != yaml_config.get('password')):
        return HttpResponse(myStr)

    myMapDf = get_map_df(q1, q2)
    RAW_DF_MAP = myMapDf
    myWarnedMapDf = if_warn(myMapDf, q1, q2)
    print(myMapDf.keys())
    print(myWarnedMapDf.keys())
    for thisKey in myWarnedMapDf.keys():
        myStr += "<form action=\"/detail/\" method=\"get\">"
        myStr += ("<a href=\"/detail ?key=" + thisKey + "\"" + ">" + thisKey + "</a><br/>")
        myStr += "</form><br/>"
        myStr += myWarnedMapDf[thisKey].to_html(escape=False)
        myStr += "<br/><br/><br/>"
    print('done')
    print('hello 1')

    return HttpResponse(myStr)


def detail(request):  # 转到详细页面
    # detail 不支持查询历史
    global RAW_DF_MAP
    time_str = time.strftime("%H:%M:%S", time.localtime())
    # myMapDf = get_map_df()
    myMapDf = RAW_DF_MAP
    print(myMapDf)
    myStr = "welcome to fisher crontab detail <br/>"
    myStr += "Now time: "
    myStr += (time_str + "<br/><br/><br/>")
    for thisKey in myMapDf.keys():
        if request.GET['key'] == thisKey:
            thisDate = thisKey.split('_')[-1]
            myStr += "<form action=\"/crontab/detail/\" method=\"get\">"
            myStr += ("<a href=\"/crontab/detail ?key=" + thisKey + "\"" + ">" + thisKey + "</a><br/>")
            # 根据不同的情况，进行配图
            print('insert png')
            if thisKey.startswith('R2_'):
                path = "/medias/real_trading_r2.jpg"
                myStr += path
                myStr += "<br/><br/><br/>"
                myStr += '<img src="%s">' % (path)
                myStr += "<br/><br/><br/>"
                if 'R2_2_2' in thisKey:
                    path = "/medias/%s/R2_Stock2Derivative.2.5.png" % (thisDate)
                else:
                    path = "/medias/%s/R2_Stock2Derivative.png" % (thisDate)
                path = "/medias/%s/R2_Stock2Derivative.png" % (thisDate)
                myStr += path
                myStr += "<br/><br/><br/>"
                myStr += '<img src=%s>' % (path)
                myStr += "<br/><br/><br/>"
            if thisKey.startswith('R2Trading_'):
                path = "/medias/R2Trading_Stock2Derivative.png"
                myStr += path
                myStr += "<br/><br/><br/>"
                myStr += '<img src="%s">' % (path)
                myStr += "<br/><br/><br/>"
                png_list = [x for x in os.listdir('./medias/%s' % (thisDate)) if x.startswith('R2Trading_Stock2Derivative_') and x.endswith('png')]
                for png in png_list:
                    print(png)
                    path = "/medias/%s/%s" % (thisDate, png)
                    myStr += path
                    myStr += "<br/><br/><br/>"
                    myStr += '<img src="%s">' % (path)
                    myStr += "<br/><br/><br/>"
            if thisKey.startswith('R2Client_'):
                png_list = [x for x in os.listdir('./medias') if 'R2Client_Stock2Derivative_' in x and 'png' in x]
                for png in png_list:
                    print(png)
                    path = "/medias/%s" % (png)
                    myStr += path
                    myStr += "<br/><br/><br/>"
                    myStr += '<img src="%s">' % (path)
                    myStr += "<br/><br/><br/>"
            if thisKey.startswith('DataCheck_'):
                png_list = [x for x in os.listdir('./medias/CheckResearch') if x[-3:] == 'png']
                for png in png_list:
                    myStr += '<img src="/medias/CheckResearch/%s">' % (png)
                    myStr += "<br/><br/><br/>"

            print('insert png done')
            myStr += "</form><br/>"
            myStr += myMapDf[thisKey].to_html(escape=False)
            myStr += "<br/><br/><br/>"
            break

    print('done')
    # return HttpResponse("welcome to fisher crontab list! " + time_str  +  "\n \n " + theDf_html + df2.to_html(escape=False))
    return HttpResponse(myStr)
