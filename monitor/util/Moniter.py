import abc
import json
import re
import time, os, sys, datetime
import psutil as ps
import pandas as pd
import numpy as np

class Moniter(): #主系统
    def __init__(self,now_name="abstract"):
        self.today_str = time.strftime("%Y%m%d", time.localtime())
        self.name=now_name
        self.describe="demo"
        self.time = '00:00:00.000'
        self.message= 'None'
        self.lock=False
        self.is_warn=True
        self.root_dir = './'
        # self.update()

    def close(self):
        self.lock=True

    def open(self):
        self.lock=False

    def update_msg(self):
        print("update_msg", self.name)

    def update(self):
        print("update", self.name)
        if(self.lock):
            print(self.name+" is Running, wait")
            return False
        else:
            self.close()
        self.update_msg()
        self.open()

    def check_lock(self):
        return self.lock

    def get_msg(self): #返回dataframe格式的数据
        print("get_msg")
        df=pd.DataFrame({"Name":[self.name],"Time":[self.time],"Msg":[self.message],"Warn":[self.is_warn]})
        return df

    def if_warn(self):
        print("if_warn")
        self.is_warn=False

    def get_pid(self): # 获得进程的pid，进行跟踪
        print("get_pid")

    def check_status(self):
        return True

    def check_data(self):
        return True

class CPU(Moniter):
    def __init__(self, now_name):
        super(CPU, self).__init__(now_name)
        self.is_warn=False

    def update_msg(self):
        print("update_msg", self.name)
        self.close()
        now_time = str(time.strftime("%D:%H:%M:%S", time.localtime(time.time())))
        self.time=now_time
        self.message = str(ps.cpu_percent(0))
        self.open()

class Memory(Moniter):
    def __init__(self,now_name):
        super(Memory, self).__init__(now_name)
        self.is_warn=False

    def update_msg(self):
        print("update_msg", self.name)
        self.close()
        now_time = str(time.strftime("%D:%H:%M:%S", time.localtime()))
        self.time = now_time
        self.message=str(ps.virtual_memory().used/ps.virtual_memory().total)
        self.open()


class TradeLog(Moniter):
    def __init__(self,now_name):
        super(TradeLog, self).__init__(now_name)
        self.is_warn=False
        self.message = 'None'
        self.update_msg()

    def update_msg(self):
        myFisherFloatPath ='/mnt/HPC01/home/fisher/Task/FisherFloat/FisherFloat.log'
        if os.path.exists(myFisherFloatPath):
            with  open(myFisherFloatPath, "r") as f:
                lines = f.readlines()
            self.message = lines[-1].replace('\n', '')

        if "Warn" in  self.message:
            self.is_warn=True
        else:
            self.is_warn = False
            

class GetCpuNumber(Moniter):
    def __init__(self,now_name):
        super(GetCpuNumber, self).__init__(now_name)
        self.today_str = time.strftime("%Y%m%d", time.localtime())
        self.name = 'GetCpuNumber'
        self.msg = 'None'
        self.is_warn = True
        self.root_dir = './'
    
    def update_msg(self):
        self.message=self.get_nodes_cpu_num()
        self.update_message(self.message)

    def update_message(self, msg = None):
        now_time = str(time.strftime("%D:%H:%M:%S", time.localtime(time.time())))
        self.time=now_time
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
        # time.sleep(10)
        return free_num_list

class starter():
    def __init__(self):
        self.list=[]
        self.list.append(CPU("cpu"))
        self.list.append(TradeLog("TradeLog"))
        self.list.append(GetCpuNumber("GetCpuNumber"))
        self.data=pd.DataFrame()
        # self.initiaziton()

    def initiaziton(self):
        # for i in self.list:
        #     i.update()
        self.data=pd.concat([i.get_msg() for i in self.list])
        self.data=self.data.reset_index(drop=True)
        return self.data

    def update_all(self):
        for i in range(self.list.__len__()):
            if(self.list[i].check_lock()==False):
                self.list[i].update()
                self.data.iloc[[i]]=self.list[i].get_msg()

    def update(self,i):
        if i < len(self.list):
            if (self.list[i].check_lock() == False):
                self.list[i].update()
                self.data.iloc[[i]] = self.list[i].get_msg()
        else:
            self.update_all()
            
    def get_msg(self):
        self.data=pd.concat([i.get_msg() for i in self.list])
        self.data=self.data.reset_index(drop=True)
        return self.data

    def get_sigle_msg(self,i):
        return self.data[i]
    
    def add_url(self, df, my_url):
        my_str=[]
        myAllIndex = len(df)
        df.loc[myAllIndex, 'Name'] = 'ALL'
        df.loc[myAllIndex, 'Warn'] = False
        for i in range(df.shape[0]):
            my_str.append('<a href=\"/'+my_url+ '?update_idx='+str(i)+'\">Update</a>')
        df.insert(loc=0, column='Update',value=my_str)
        return df


if __name__ == '__main__':
    pass
    # s=starter()
    # print(s.get_msg())
    # print(s.get_msg())
    # s.update_all()
    # print(s.get_msg())
    # print(s.get_msg())
