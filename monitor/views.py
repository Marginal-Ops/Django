from errno import EMULTIHOP
from django.shortcuts import render
from django.http import HttpResponse
switch_hour = 18
import time
import datetime
import os
import yaml
import pandas as pd
import numpy as np
from django.conf import settings
import matplotlib.pyplot as plt
import glob
from monitor.util.Moniter import starter
from django.http import HttpResponseRedirect
import matplotlib.cm as cm
import sys

global_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.local/config.yaml')
with open(global_json_path, "r") as f:
    global_yaml_config = yaml.load(f, Loader=yaml.FullLoader)
for path in global_yaml_config["modules"][::-1]:
    if path not in sys.path:
        print('insert', path)
        sys.path.insert(0, path)
import akshare as ak
tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
market_trade_date_list = tool_trade_date_hist_sina_df["trade_date"].apply(lambda x: x.strftime("%Y%m%d")).values.tolist()

global_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.local/monitor_config.yaml')
with open(global_json_path, "r") as f:
    global_yaml_config = yaml.load(f, Loader=yaml.FullLoader)


class R2Center:
    statistic_list = ['r2_10', 'corr_10', 'std_10', 'tstd_10']

    @staticmethod
    def get_main_columns(cols):
        main_col = {}
        for x in cols:
            if '_' not in x:
                main_col[x] = x
            else:
                # 解析主要
                if np.any(np.array(['Mix' in y for y in cols])):
                    if 'Mix' in x:
                        k = 0
                        k = x.index('_', k)
                        k = x.index('_', k + 1)
                        main_col[x] = x[:k] + '_ret'
                    elif 'CSumPDivideU' in x:
                        k = 0
                        k = x.index('_', k)
                        k = x.index('_', k + 1)
                        main_col[x] = x[:k] + '_vol'
                elif np.any(np.array(['CDiffPDivideU' in y for y in cols])):
                    if 'CDiffPDivideU' in x:
                        k = 0
                        k = x.index('_', k)
                        k = x.index('_', k + 1)
                        main_col[x] = x[:k] + '_ret'
                    elif 'CSumPDivideU' in x:
                        k = 0
                        k = x.index('_', k)
                        k = x.index('_', k + 1)
                        main_col[x] = x[:k] + '_vol'
                elif np.any(np.array(['V0' in y for y in cols])):
                    if 'V0' in x:
                        k = 0
                        k = x.index('_', k)
                        k = x.index('_', k + 1)
                        main_col[x] = x[:k] + '_ret'
        return main_col

    @staticmethod
    def get_df(path_list):
        # 如果输入为单个path, 也转化为list
        if isinstance(path_list, str):
            path_list = [path_list]
        # 获取全量数据
        df_list = []
        # code_list = os.listdir(path)
        for path in path_list:
            code_list = [x for x in os.listdir(path) if len(x.split('_')) == 2]
            for code in code_list:
                code_path = os.path.join(path, code)
                model_list = [x for x in os.listdir(code_path)]
                model_list = [x for x in model_list if 'Linear' in x or 'Gru' in x]
                # print(model_list)
                for model in model_list:
                    this_df_list = []
                    model_path = os.path.join(path, code, model)
                    # 获取文件夹下所有文件的路径，并按照最新修改时间排序
                    files = glob.glob(os.path.join(model_path, '*'))
                    files.sort(key=os.path.getmtime, reverse=True)
                    for result_type in R2Center.statistic_list:
                        this_files = [x for x in files if x.split('/')[-1].startswith(result_type.split('_')[0]) and x.endswith(
                            'csv') and 'mean' not in x and 'median' not in x]
                        if len(this_files) > 0:
                            file = this_files[0]
                            df = pd.read_csv(file)
                            df = df[[x for x in df.columns if result_type.split('_')[0] not in x or ('_10_' in x and '_10_25_' not in x)]]
                            if '2.' in path:
                                main_col = R2Center.get_main_columns(df.columns)
                                df = df[list(main_col.keys())].rename(columns=main_col)
                            this_df_list.append(df)
                        else:
                            # print(files)
                            print('no file', model_path, result_type)
                    if len(this_df_list) > 0:
                        this_df_list = pd.concat(this_df_list, axis=1)
                        this_df_list = this_df_list.loc[:, ~this_df_list.columns.duplicated()]
                        df_list.append(this_df_list)
        df = pd.concat(df_list)
        return df

    @staticmethod
    def plot_df(df, today, crontab_df=None):
        # realtrading daily
        daily_path_from = global_yaml_config["root_dir"]["s2d"] + "/maintain/real_trading_r2.jpg"
        daily_path_to = "./medias/."
        comd = 'cp %s %s' % (daily_path_from, daily_path_to)
        os.system(comd)
        last_day = (datetime.datetime.strptime(today, '%Y%m%d') - datetime.timedelta(days=1)).strftime('%Y%m%d')
        if (crontab_df is None) or (last_day not in market_trade_date_list):
            model_done = np.array([True])
        else:
            deploy_index = list(crontab_df.loc[:, "JobName"].values).index('deploy')
            bool_array = np.array([x == 'Done' for x in crontab_df["Status"].values[:deploy_index]])
            model_done = np.all(bool_array)
        print(crontab_df)
        print(model_done)
        print("np.all(model_done)", np.all(model_done))
        # 画图
        df.loc[:, 'future'] = df['future'].astype(str)
        model_list = list(df['method'].unique())

        save_path = './medias/%s/R2_Stock2Derivative.png' % (today)
        checkpoint_path = './medias/%s/done' % (today)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        if os.path.exists(checkpoint_path):
            print(checkpoint_path, 'exists!')
            return
        else:
            print(checkpoint_path, 'not exists!')
        if True:
            print('all none')
            codes_dir = {}
#             codes_dir['option'] = [x[6:] for x in df[df['stock'].isin(['399006SZ', '399330SZ', '000688SH'])].dropna(how='all', axis=1).columns if (x.startswith('r2_10_'))]
#             codes_dir['future'] = [x[6:] for x in df[df['stock'].isin(['50SH', '300SZ', '500SZ', '1000SZ', '300SH', '500SH', '1000SH'])].dropna(how='all', axis=1).columns if (x.startswith('r2_10_'))]
#             codes_dir['volatility'] = [x[6:] for x in df.columns if x[:5] == 'r2_10' and (x.endswith('vol'))]
            codes_dir['option'] = list(set(df[df['stock'].isin(['399006SZ', '399330SZ', '000688SH'])]['stock'].values)), 'ret'
            codes_dir['future'] = list(set(df[df['stock'].isin(['50SH', '300SZ', '500SZ', '1000SZ', '300SH', '500SH', '1000SH'])]['stock'].values)), 'ret'
            codes_dir['volatility'] = list(set(df[df['stock'].isin(['399006SZ', '399330SZ', '000688SH'])]['stock'].values)), 'vol'

            fig, axes = plt.subplots(nrows=len(R2Center.statistic_list), ncols=len(codes_dir.keys()))
            for m, statistic in enumerate(R2Center.statistic_list):
                for n, dev_type in enumerate(codes_dir.keys()):
                    code_list, plot_statistic = codes_dir[dev_type]
                    this_columns = [x for x in df.columns if x.startswith(statistic) and x.endswith(plot_statistic)]
                    for k, model_type in enumerate(model_list):
                        marker = ['o', 'x', 's', '+', '<', '>']
                        marker = marker[k]
                        df_plot_all = pd.DataFrame()
                        for col in this_columns:
                            for code in code_list:
                                df_plot = df[['date', 'state', 'method', 'stock', col]].copy()
                                df_plot = df_plot[df_plot['state'].isin(['test'])]
                                df_plot = df_plot[df_plot['method'].isin([model_type])]
                                df_plot = df_plot[df_plot['stock'].isin([code])]
                                df_plot['date'] = df_plot['date'].astype(str)
                                df_plot = df_plot.dropna(subset=[col])
                                if len(df_plot) == 0:
                                    continue
                                missing_date_list = [x for x in market_trade_date_list if x > df_plot['date'].max() and x < today]
                                for date in missing_date_list:
                                    temp_df = df_plot.iloc[-1:, :].copy()
                                    temp_df.loc[:, 'date'] = date
                                    temp_df.iloc[:, 4:] = np.nan
                                    df_plot = pd.concat([df_plot, temp_df], axis=0)
                                df_plot.set_index('date', inplace=True)
                                for r2 in this_columns:
                                    new_columns = "%s_%s_%s" % (model_type, df_plot['stock'].values[0], r2)
                                    if r2 in df_plot.columns:
                                        df_plot.loc[:, new_columns] = df_plot[r2]
                                        # 新增index
                                        bool_added = False
                                        for x in df_plot.index:
                                            if x not in df_plot_all.index:
                                                bool_added = True
                                                df_plot_all.loc[x, :] = np.nan
                                        if bool_added:
                                            df_plot_all = df_plot_all.sort_index()
                                        df_plot_all.loc[df_plot.index, new_columns] = df_plot[new_columns].clip(0, np.inf).fillna(0)
                        print(statistic, dev_type, model_type, df_plot_all.shape)
                        if len(df_plot_all) > 0:
                            ax = df_plot_all.plot(grid=True, rot=15, title=dev_type, linestyle='-', marker=marker, ax=axes[m, n], figsize=(20, 20))
                            leg = ax.legend()
                            leg.get_frame().set_alpha(0.25)
        else:
            future_list = [x for x in df['future'].unique() if x[-2:] == 'V0']
            option_list = [x for x in df['future'].unique() if x[-2:] != 'V0']
            fig, axes = plt.subplots(nrows=len(R2Center.statistic_list), ncols=2)
            for m, statistic in enumerate(R2Center.statistic_list):
                for n, dev_type in enumerate(['future', 'option']):
                    r2_list = ['%s_V0' % (statistic)] if dev_type == 'future' else ['%s_C0' % (statistic),
                                                                                    '%s_P0' % (statistic), ]
                    code_list = future_list if dev_type == 'future' else option_list
                    df_plot_all = pd.DataFrame()
                    for model_type in model_list:
                        for code in code_list:
                            df_plot = df.copy()
                            df_plot = df_plot[df_plot['future'] == code]
                            df_plot = df_plot[df_plot['state'].isin(['test'])]
                            df_plot = df_plot[df_plot['method'].isin([model_type])]
                            df_plot['date'] = df_plot['date'].astype(str)
                            if len(df_plot) > 0:
                                missing_date_list = [x for x in market_trade_date_list if
                                                     x > df_plot['date'].max() and x < today]
                                for date in missing_date_list:
                                    temp_df = df_plot.iloc[-1:, :].copy()
                                    temp_df.loc[:, 'date'] = date
                                    temp_df.iloc[:, 5:] = np.nan
                                    df_plot = pd.concat([df_plot, temp_df], axis=0)
                                df_plot.set_index('date', inplace=True)
                                for r2 in r2_list:
                                    new_columns = "%s_%s_%s" % (code, model_type, r2)
                                    if r2 in df_plot.columns:
                                        df_plot.loc[:, new_columns] = df_plot[r2]
                                        # 新增index
                                        bool_added = False
                                        for x in df_plot.index:
                                            if x not in df_plot_all.index:
                                                bool_added = True
                                                df_plot_all.loc[x, :] = np.nan
                                        if bool_added:
                                            # 似乎排序功能没有正常发挥作用！ 还需要debug
                                            df_plot_all = df_plot_all.sort_index()
                                        df_plot_all.loc[:, new_columns] = df_plot[new_columns].clip(0, np.inf).fillna(0)
                    ax = df_plot_all.plot(grid=True, rot=15, title=dev_type, linestyle='-', marker='*', ax=axes[m, n], figsize=(15, 15))
                    leg = ax.legend()
                    leg.get_frame().set_alpha(0.25)
        plt.tight_layout()
        plt.savefig(save_path)
        if np.all(model_done):
            print("touch %s" % checkpoint_path)
            os.system("touch %s" % checkpoint_path)
        else:
            print('last_day = ', last_day, 'model_done = ', model_done)
        return

    @staticmethod
    def get_df_wran(df):
        # 生成is_wran
        df.loc[:, 'future'] = df['future'].astype(str)
        date_list = [df['date'].max()]
        df_wran = df.copy()
        df_wran = df_wran[[x for x in df_wran.columns if '_' not in x or ('r2_10_ret' in x) or (x.startswith('r2_10_') and x.endswith('0'))]]
        df_wran = df_wran[df_wran['date'].isin(date_list)]
        df_wran = df_wran[df_wran['state'].isin(['test'])]
        return df_wran


class R2Client:
    root_dir = global_yaml_config["root_dir"]["realtime"]
    machine_list = global_yaml_config["machines"]["client"]

    @staticmethod
    def get_df(date):
        return pd.DataFrame([date], columns=['date'])

    @staticmethod
    def plot_df(df):
        date = df['date'].values[0]
        for machine, project in R2Client.machine_list:
            print("R2Client", machine, project)
            path = os.path.join(R2Client.root_dir, machine, project, date)
            path_cp = './medias/R2Client_Stock2Derivative_%s.png' % (machine)
            if os.path.exists(path):
                png_list = [x for x in os.listdir(path) if x.endswith('png')]
                for file in png_list:
                    os.system('cp %s %s' % (os.path.join(path, file), path_cp))
            else:
                os.system('rm %s' % (path_cp))
        return

    @staticmethod
    def get_df_wran(df):
        return df


class R2Trading:
    root_dir = global_yaml_config["root_dir"]["realtime"]
    machine_list = global_yaml_config["machines"]["trade"]
    statistic_list = ["R2", "Corr", "Std"]

    @staticmethod
    def get_df(date):
        # 获取全量数据
        df_list = []
        error_project_list = []
        for machine, project in R2Trading.machine_list:
            print("R2Trading", machine, project)
            path = os.path.join(R2Trading.root_dir, machine, project, date)
            if os.path.exists(path):
                csv_list = [x for x in os.listdir(path) if x[-4:] == '.csv']
                if len(csv_list) > 0:
                    for csv in csv_list:
                        csv_path = os.path.join(path, csv)
                        df = pd.read_csv(csv_path)
                        df = df[[x for x in df.columns if 'r2_' not in x or len(x) == 8]]
                        df.insert(0, 'Project', project)
                        df_list.append(df)
                else:
                    print(path, project)
                    error_project_list.append(project)
            else:
                print(path, project)
                error_project_list.append(project)
        df = pd.concat(df_list)
        print(error_project_list)
        for error_project in error_project_list:
            df = df.append({"Project": error_project, "ModelName": "None"}, ignore_index=True)
        df.loc[:, "TradeDate"] = date
        return df

    @staticmethod
    def plot_df(df):
        m_subplot = 2  # * len(R2Trading.machine_list)
        n_subplot = len(R2Trading.statistic_list)
        plt.figure(figsize=(15, 20))
        viridis_spectral = cm.get_cmap('Spectral', 256)
        # 根据当前时间，调整画图的freq
        if df['EndTime'].dropna().max() <= "09:36:00.000":
            freq = '1min'
        elif df['EndTime'].dropna().max() <= "10:15:00.000":
            freq = '5min'
        else:
            freq = '30min'
        df_rename = df.copy()
        for index, (machine, project) in enumerate(R2Trading.machine_list):
            df_rename.loc[df_rename.loc[:, "Project"] == project, "ModelName"] = [str(int(index)) + "_" + x for x in
                                                                                  df_rename.loc[df_rename.loc[:, "Project"] == project, "ModelName"]]
        model_list = [x for x in list(df_rename['ModelName'].unique()) if 'V0' in x or len(x.split('_')[1]) <= 6]
        for s, statistic in enumerate(R2Trading.statistic_list):
            plt.subplot(n_subplot, m_subplot, s * m_subplot + 1)
            if s == 0:
                plt.ylabel(project)
            colors = viridis_spectral(np.arange(len(model_list)) / len(model_list))
            for m, model in enumerate(model_list):
                df_plot = df_rename.loc[(df_rename.loc[:, "Freq"] == freq) & (df_rename.loc[:, "ModelName"] == model),
                                        :].copy()
                df_plot.set_index('EndTime', inplace=True)
                name_plot = "%s" % (model)
                df_plot.loc[:, name_plot] = df_plot.loc[:, statistic]
                ax = df_plot[name_plot].clip(0, np.inf).fillna(0).plot(grid=True, legend=True, rot=15, title=statistic,
                                                                       color=[colors[m]],
                                                                       # linestyle='-', marker='*'
                                                                       )
            leg = ax.legend(bbox_to_anchor=(1.0, 0.7))
            leg.get_frame().set_alpha(0.25)

        model_list = list(set(list(df_rename['ModelName'].unique())) - set(model_list))
        for s, statistic in enumerate(R2Trading.statistic_list):
            plt.subplot(n_subplot, m_subplot, s * m_subplot + 2)
            if s == 0:
                plt.ylabel(project)
            viridis = cm.get_cmap('Spectral', 256)
            colors = viridis_spectral(np.arange(len(model_list)) / len(model_list))
            for m, model in enumerate(model_list):
                df_plot = df_rename.loc[(df_rename.loc[:, "Freq"] == freq) & (df_rename.loc[:, "ModelName"] == model),
                                        :].copy()
                df_plot.set_index('EndTime', inplace=True)
                name_plot = "%s" % (model)
                df_plot.loc[:, name_plot] = df_plot.loc[:, statistic]
                ax = df_plot[name_plot].clip(0, np.inf).fillna(0).plot(grid=True, legend=True, rot=15, title=statistic,
                                                                       color=[colors[m]],
                                                                       # linestyle='-', marker='*'
                                                                       )
            leg = ax.legend(bbox_to_anchor=(1.0, 0.7))
            leg.get_frame().set_alpha(0.25)
        plt.tight_layout()
        print('save to', './medias/R2Trading_Stock2Derivative.png')
        plt.savefig('./medias/R2Trading_Stock2Derivative.png')

        # 还有一些图片 直接复制回来
        print(df)
        date = df['TradeDate'].values[0]
        os.makedirs("./medias/%s" % (date), exist_ok=True)
        for machine, project in R2Trading.machine_list:
            path = os.path.join(R2Trading.root_dir, machine, project, date)
            if os.path.exists(path):
                png_list = [x for x in os.listdir(path) if x.endswith('png')]
                for file in png_list:
                    path_cp = './medias/%s/R2Trading_Stock2Derivative_%s_%s' % (date, machine, file)
                    comd = 'cp %s %s' % (os.path.join(path, file), path_cp)
                    os.system(comd)
            else:
                pass
                # os.system('rm -rf ./medias/R2Trading_Stock2Derivative_%s_*'%(machine))
        return df

    @staticmethod
    def get_df_wran(df):
        if len(df) == 0:
            return df
        else:
            df_wran = df.groupby(['Project', 'ModelName']).apply(lambda x: x.iloc[0, :]).reset_index(drop=True)
            return df_wran


class CheckResearch:
    root_dir = global_yaml_config["root_dir"]["data_check"]

    @staticmethod
    def get_df(date):
        # 获取全量数据
        csv_dir = os.path.join(CheckResearch.root_dir, date, 'csv')
        if os.path.exists(csv_dir):
            files = [x for x in os.listdir(csv_dir) if x[-4:] == '.csv']
            df_list = []
            for file in files:
                df = pd.read_csv(os.path.join(CheckResearch.root_dir, date, 'csv', file))
                df_list.append(df)
            df = pd.concat(df_list, axis=0)
            df.insert(0, 'Date', date)
        else:
            df = pd.DataFrame({'Date': [date], 'CodeNum': [0]})
        return df

    @staticmethod
    def plot_df(df):
        date = df['Date'].values[0]
        png_dir = os.path.join(CheckResearch.root_dir, date, 'png', '*')
        medias_dir = './medias/CheckResearch/.'
        print('mkdir ./medias/CheckResearch')
        print('cp -rf %s %s' % (png_dir, medias_dir))
        os.system('mkdir ./medias/CheckResearch')
        os.system('rm -rf ./medias/CheckResearch/*')
        os.system('cp -rf %s %s' % (png_dir, medias_dir))
        return df

    @staticmethod
    def get_df_wran(df):
        df_wran = df.loc[df.loc[:, 'CodeNum'] > 0, :]
        return df_wran


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
    print('get data check')
    theMap['DataCheck_' + date1] = CheckResearch.get_df(date1)
    CheckResearch.plot_df(theMap['DataCheck_' + date1])

    print('get crontab')
    theMap['Crontab_' + date1] = pd.read_csv(os.path.join(global_yaml_config["root_dir"]["crontab"], date1, 'summary.csv'))

    print('get R2_2', date1, date2)
    theMap['R2_2_' + date1] = R2Center.get_df([
        global_yaml_config["root_dir"]["s2d"] + "/r2_result",
    ])
    R2Center.plot_df(theMap['R2_2_' + date1], date1, theMap['Crontab_' + date1])

    print('get model_check')
    csv_path_list = [
        global_yaml_config["root_dir"]["s2d"] + '/model_check.csv',
        global_yaml_config["root_dir"]["s2d"] + '/model_date.csv',]
    df = pd.DataFrame()
    for csv_path in csv_path_list:
        if os.path.exists(csv_path):
            temp_df = pd.read_csv(csv_path, index_col=0)
            if df is None:
                df = temp_df.copy()
            else:
                df = pd.concat([df, temp_df])
    theMap['ModelCheck_' + date1] = df

    print('get R2Trading')
    try:
        theMap['R2Trading_' + date1] = R2Trading.get_df(date1)
        R2Trading.plot_df(theMap['R2Trading_' + date1])
    except Exception as e:
        print(e)
        print('no file', date1)

    try:
        theMap['R2Client_' + date1] = R2Client.get_df(date1)
        R2Client.plot_df(theMap['R2Client_' + date1])
    except Exception as e:
        print(e)
        print('no file', date1)

    print('get monitor')
    my_url = 'hello'
    df = pd.DataFrame(myMonitorStarter.get_msg()).copy()
    df = myMonitorStarter.add_url(df, my_url)
    theMap['Monitor_' + date1] = df
    print('new', theMap.keys())
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
        elif "R2_" in thisKey:
            theMapDf[thisKey] = R2Center.get_df_wran(theMapDf[thisKey])
        elif "R2Trading_" in thisKey:
            theMapDf[thisKey] = R2Trading.get_df_wran(theMapDf[thisKey])
        elif "DataCheck_" in thisKey:
            theMapDf[thisKey] = CheckResearch.get_df_wran(theMapDf[thisKey])
        else:
            if 'Warn' in theMapDf[thisKey].columns:
                myShowCol = list(theMapDf[thisKey].columns)
                if 'Update' in myShowCol:
                    myShowCol.remove('Update')
                theMapDf[thisKey] = theMapDf[thisKey].loc[theMapDf[thisKey].loc[:, 'Warn'] == True, myShowCol]

    return theMapDf


global RAW_DF_MAP
RAW_DF_MAP = {}
global myMonitorStarter
myMonitorStarter = starter()


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

    if 'update_idx' in request.GET and (request.GET['update_idx']):
        update_i = int(request.GET['update_idx'])
        myMonitorStarter.update(update_i)
        print('HttpResponseRedirect')
        return HttpResponseRedirect("/")

    myMapDf = get_map_df(q1, q2)
    RAW_DF_MAP = myMapDf
    myWarnedMapDf = if_warn(myMapDf, q1, q2)
    print(myMapDf.keys())
    print(myWarnedMapDf.keys())
    for thisKey in myWarnedMapDf.keys():
        myStr += "<form action=\"/monitor/detail/\" method=\"get\">"
        myStr += ("<a href=\"/monitor/detail ?key=" + thisKey + "\"" + ">" + thisKey + "</a><br/>")
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
    myStr += "this key: "
    myStr += (request.GET['key'] + "<br/><br/><br/>")
    for thisKey in myMapDf.keys():
        if request.GET['key'] == thisKey:
            thisDate = thisKey.split('_')[-1]
            myStr += "<form action=\"/detail/\" method=\"get\">"
            myStr += ("<a href=\"/detail ?key=" + thisKey + "\"" + ">" + thisKey + "</a><br/>")
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
