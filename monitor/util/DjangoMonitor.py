import abc
import time, os, sys, datetime, json

import pandas as pd
import numpy as np
import os, sys, time, re, random
import numpy as np


class GetCpuNumber(abc.ABC):
    def __init__(self):
        self.today_str = time.strftime("%Y%m%d", time.localtime())
        self.root_dir = './'
        self.name = 'GetCpuNumber'
        self.msg = 'None'
        self.is_warn = True
        self.update_msg()
        
    def run(self):
        self.msg = self.get_nodes_cpu_num()
        self.update_msg(self.msg)
        pass
    
    def update_msg(self, msg = None):
        myDir = os.path.join(self.root_dir, self.today_str)
        os.path.isdir(myDir) or os.makedirs(myDir)
        myFile = os.path.join(self.root_dir , self.today_str, self.name)
        if msg:
            # 储存
            with open(myFile, "w") as f:
                f.write(json.dumps(msg))
        else:
            # 读取
            try:
                with open(myFile) as f:
                    msg = json.load(f)
            except Exception:
                return
        # 是否需要显示
        self.is_warn = False
        #
        myMinNum = msg[-1][0]
        if myMinNum < 0:
            self.is_warn = True
        if self.is_warn:
            self.msg = json.dumps(msg)
        else:
            self.msg = json.dumps(msg[:3])
        pass
    
    def get_os_return(self, aSent):
        print(aSent)
        theReturn = os.popen(aSent)
        theReturn = theReturn.read()
        return theReturn

    def get_nodes_cpu_num(self):
        nodes_info = self.get_os_return('ssh login0 "scontrol show nodes"')
        # 正则表达式提取cpu使用情况
        pattern = re.compile("NodeName=(SB8U1-N[0-9]+|GPU[0-9]+).*\s+CPUAlloc=([0-9]+) CPUTot=([0-9]+)")
        pattern = re.compile("NodeName=(SB8U1-N[0-9]+|GPU[0-9]+).*\s+CPUAlloc=([0-9]+) CPUTot=([0-9]+)")
        cpu_num_list = pattern.findall(nodes_info)
        free_num_list = []
        for info in cpu_num_list:
            print('node_name:%08s free:%03s/%s' % tuple(info))
            this_node_name = info[0]
            this_cpu_num = -1
            try:
                this_cpu_num = int(info[2]) -int(info[1])
            except:
                pass
            free_num_list.append((this_cpu_num, this_node_name))
        free_num_list.sort()
        free_num_list = free_num_list[::-1]
        time.sleep(10)
        return free_num_list

if __name__ == '__main__':
    x = GetCpuNumber()
    print(x.msg)
    print(x.is_warn)
    x.run()
    print(x.msg)
    print(x.is_warn)








