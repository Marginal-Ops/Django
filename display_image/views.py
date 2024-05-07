from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.http import HttpResponse, FileResponse, HttpResponseNotFound
from .models import File
import pandas as pd
import shutil
import os
import json
import copy
import yaml


global_df_htmls = None
# global_root_dir = None
# @method_decorator(cache_page(15 * 60), name='dispatch')


class dataframe(View):

    def __init__(self):
        global_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.local/display_config.yaml')
        with open(global_json_path, "r") as f:
            yaml_config = yaml.load(f, Loader=yaml.FullLoader)
            root_dirs = yaml_config.get('root_dir')
        self.target_path = os.path.join('display_image', 'html_files')
        self.root_dirs = root_dirs
        self.root_dir = root_dirs[0]
        if not os.path.exists(self.root_dir):
            raise ValueError(f"path: {self.root_dir} doesn't exists")
        self.gen_df(self.root_dir)
        # global_root_dir = self.root_dir

    def merge_dataframe(self, df0, df1):
        idex_merge = list(set(df0.index) | set(df1.index))
        idex_merge.sort()
        columns_merge = list(df0.columns) + list(df1.columns)
        df_merge0 = pd.DataFrame(index=idex_merge, columns=columns_merge)
        df_merge1 = pd.DataFrame(index=idex_merge, columns=columns_merge)
        df_merge0.loc[df0.index, df0.columns] = df0.values
        df_merge1.loc[df1.index, df1.columns] = df1.values
        # apply htmls to values
        for col in df_merge0.columns:
            if col[0] == '(' and col[-1] == ")":
                plt_type = eval(col)[0]
                df_merge0.loc[:, col] = df_merge0.loc[:, plt_type]
        # cal rank_score to values; 100 is best
        plot_type = 'dist'
        df_merge1.loc[:, plot_type] = (100 * df_merge1[[x for x in df_merge1 if "('%s'," % (plot_type) in x]
                                                       ].rank(method='average', na_option='top', ascending=False, pct=True).min(1))  # .astype(int)
        plot_type = 'nan'
        df_merge1.loc[:, plot_type] = (100 * df_merge1[[x for x in df_merge1 if "('%s'," % (plot_type) in x]
                                                       ].rank(method='average', na_option='top', ascending=False, pct=True).min(1))  # .astype(int)
        plot_type = 'eval'
        df_merge1.loc[:, plot_type] = (100 * df_merge1[[x for x in df_merge1 if "('%s'," % (plot_type) in x]
                                                       ].rank(method='average', na_option='top', ascending=True, pct=True).max(1))  # .astype(int)
        return df_merge0, df_merge1

    def get_dataframe(self, root_dir):
        path_sign = "".join(root_dir.split('/'))
        if os.path.exists('display_image/cachefiles/' + path_sign + '/df_htmls.csv') and os.path.exists('display_image/cachefiles/' + path_sign + '/df_values.csv'):
            df_htmls = pd.read_csv('display_image/cachefiles/' + path_sign + '/df_htmls.csv', index_col=0)
            df_values = pd.read_csv('display_image/cachefiles/' + path_sign + '/df_values.csv', index_col=0)
            return df_htmls, df_values
        df_values = pd.DataFrame()
        df_htmls = pd.DataFrame()
        for plot_type in [x for x in os.listdir(root_dir) if x not in ['corr']]:
            html_dir = os.path.join(root_dir, plot_type, 'html')
            csv_dir = os.path.join(root_dir, plot_type, 'csv')
            # 获取html路径
            if os.path.exists(html_dir):
                for timestamp_str in os.listdir(html_dir):
                    files = [x for x in os.listdir(os.path.join(html_dir, timestamp_str)) if x.endswith('html')]
                    for file in files:
                        column = plot_type
                        index = file.split('.')[0][len(plot_type) + 1:]
                        df_htmls.loc[index, column] = os.path.join(html_dir, timestamp_str, file)
            # 获取统计量
            if os.path.exists(html_dir):
                if os.path.exists(csv_dir):
                    for timestamp_str in os.listdir(html_dir):
                        files = [x for x in os.listdir(os.path.join(csv_dir, timestamp_str)) if x.endswith('csv')]
                        for file in files:
                            temp_df = pd.read_csv(os.path.join(csv_dir, timestamp_str, file), index_col=0)
                            if '5%' in temp_df.index:
                                # dist nan
                                if list(temp_df.columns)[0][1] == 'dist':
                                    # dist
                                    temp_df = temp_df.loc[['5%'], :]
                                else:
                                    # nan
                                    temp_df = temp_df.loc[['max'], :]
                            else:
                                temp_df = pd.DataFrame(temp_df.max() - temp_df.min()).T
                            for x in temp_df.columns:
                                df_values.loc[eval(temp_df.columns[0])[0], str((plot_type, eval(x)[1], eval(x)[2]))] = temp_df[x].values[0]
        df_htmls, df_values = self.merge_dataframe(df_htmls, df_values)
        # 手动排序
        if "('eval', 'label_vol_1d', '0_1_2')" in df_values.columns:
            df_values.sort_values(by="('eval', 'label_vol_1d', '0_1_2')", inplace=True, ascending=False)
        df_htmls = df_htmls.loc[df_values.index, :]
        if not os.path.exists('display_image/cachefiles/'):
            os.mkdir('display_image/cachefiles/')
        if not os.path.exists('display_image/cachefiles/' + path_sign):
            os.mkdir('display_image/cachefiles/' + path_sign)
        df_htmls.to_csv('display_image/cachefiles/' + path_sign + '/df_htmls.csv')
        df_values.to_csv('display_image/cachefiles/' + path_sign + '/df_values.csv')
        return df_htmls, df_values

    def gen_df(self, root_dir):
        self.df_htmls, self.df_values = self.get_dataframe(root_dir=root_dir)
        global global_df_htmls
        global_df_htmls = self.df_htmls
        assert self.df_htmls.index.equals(self.df_values.index)
        if set(self.df_values.columns) > set(self.df_htmls.columns):
            self.df_values = self.df_values[self.df_htmls.columns]
        assert self.df_htmls.columns.equals(self.df_values.columns), print(set(self.df_htmls.columns) -
                                                                           set(self.df_values.columns), set(self.df_values.columns) - set(self.df_htmls.columns), )

    def get(self, request):
        if request.GET.get('root_dir'):
            self.root_dir = request.GET.get('root_dir')
        request.session['root_dir'] = self.root_dir
        self.gen_df(self.root_dir)
        if not (self.df_htmls.index.equals(self.df_values.index) and self.df_htmls.columns.equals(self.df_values.columns)):
            error_mes = '<h1> OOps! please check the data provided by the backend </h1>'
            return render(request, 'display_image/dataframe.html', {'html_table': error_mes})
        # sortby = request.GET.get('sortby')
        # if 'asc' not in request.session:
        #    request.session['asc'] = True
        # if sortby:
        #    self.df_htmls.sort_values(by=sortby, inplace=True, ascending=request.session['asc'])
        #    self.df_values.sort_values(by=sortby, inplace=True,ascending=request.session['asc'])
        #    if request.session['asc']:
        #        request.session['asc'] = False
        #    else:
        #        request.session['asc'] = True
        df_anchored = copy.deepcopy(self.df_values)
        for i in range(len(df_anchored.index)):
            for j in range(len(df_anchored.columns)):
                # row, col = df_anchored.index[i], df_anchored.columns[j]
                val = df_anchored.iloc[i, j]
                path = self.df_htmls.iloc[i, j]
                try:
                    path = os.path.join(self.root_dir, path)
                except:
                    path = ''
                # html_code = f"<input type='submit' class='my-input' name='show_html' value={'{:.5g}'.format(val)} data-path={path} data-val={val} data-row={i}"
                formated_val = '{:.5g}'.format(float(val))
                html_code = f"<input type='submit' class='my-input' name='show_html' value={formated_val} data-path={path} data-val={val} data-row={i}"
                if path:
                    html_code += '>'
                else:
                    # 如果不存在路径，则字体显示为黑色
                    html_code += " style='color: black;' >"
                html_code = html_code.replace("#", '$')
                df_anchored.iloc[i, j] = html_code
        html_table = df_anchored.to_html(index=True, border=0, escape=False)
        self.html_table = html_table
        return render(request, 'display_image/dataframe.html', {'html_table': html_table, 'root_dirs': self.root_dirs, 'root_dir': self.root_dir})

    def post(self, request):
        if 'rootDirDropDown' in request.POST:
            return redirect('' + f"?root_dir={request.POST.get('rootDirDropDown')}")
        else:
            return HttpResponse('not implemented yet')

# @method_decorator(cache_page(15 * 60), name='dispatch')


class display_html(View):
    def readFile(self, path):
        if path and os.path.exists(path):
            with open(path) as target_file:
                try:
                    html = target_file.read()
                except:
                    raise ValueError("can't read file")
            return html
        else:
            raise ValueError("can't find file")

    def get(self, request):
        path = request.GET.get('path').replace('$', "#")
        val = request.GET.get('val')
        row = int(request.GET.get('row'))
        html = self.readFile(path)
        global global_df_htmls
        path_set = set()
        for each_path in global_df_htmls.iloc[row, ]:
            path_set.add(each_path)
        try:
            return render(request, 'display_image/displayPage.html', {'html': html, 'path': path, 'val': val, 'row': row, 'path_set': path_set})
        except:
            return render(request, 'display_image/404.html')


def downloadCorr(request):
    return HttpResponseNotFound('fetching needed')


def downloadFile(request):
    if 'root_dir' not in request.session:
        return HttpResponseNotFound('fetching needed')
    path_sign = 'display_image/cachefiles/' + ''.join(request.session['root_dir'].split('/')) + '/df_values.csv'
    if request.method == 'GET':
        if os.path.exists(path_sign):
            file = open(path_sign, 'rb')
            response = FileResponse(file)
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment; filename="df_value.csv"'
            return response
        else:
            return HttpResponseNotFound(f'file not exist, path:{path_sign}')
    elif request.method == 'POST':
        if os.path.exists(path_sign):
            try:
                shutil.rmtree('display_image/cachefiles')
                return HttpResponse('200')
            except:
                return HttpResponse("can't not refresh cache")
    else:
        raise NotImplementedError('?')
