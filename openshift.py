# _*_ coding:utf8 _*_

import requests
import json
import sys
import os 
import yaml
import commands
import re
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class OpenShift(object):

    def __init__(self):
        print('Welcome To OpenShift API ! ')
        self.serverurl = 'https://master.example.com:8443'
        self.namespace = sys.argv[1]
        self.dcname = sys.argv[2]
        self.imagename = sys.argv[3]
        self.podcount = sys.argv[4]
        self.servicename = self.dcname
        self.port = sys.argv[5]
        self.tport = sys.argv[6]
        self.token = 'Bearer ' + str(self.GetToken())
        self.headers = {'Authorization': self.token,'Accept':'application/json','Content-Type':'application/json'}

    #获取token
    def GetToken(self):
        #print('Get Token')
        response_type = 'code'
        client_id = 'openshift-browser-client'
        apipath=self.serverurl + '/oauth/authorize?' + 'response_type=' + response_type + '&client_id=' + client_id
        cmd = 'curl -k -X GET ' + "'" + apipath + "'" + ' -u hobot:123456 -I -s'
        #print(cmd)
        status,response = commands.getstatusoutput(cmd)
        #print(response)
    
        if status != 0:
            print('Requests error !')
            return False
        else:
            pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            tokenurl = re.findall(pattern,response)[0]
            response = requests.get(tokenurl,verify=False).text
            #print(response)
            pattern = "<code>(.*?)</code>"
            token = re.findall(pattern,response)[0]
            if token == ' ':
                print('token error!')
                return False
            else:
                print('Get token success!')
            return token

    #获取DC
    def GetDcList(self):
        #print('Get DcList')
        apipath = self.serverurl + '/apis/apps.openshift.io/v1/namespaces/' + self.namespace + '/deploymentconfigs'
        response = requests.get(apipath,headers=self.headers,verify=False)
        #print(response.status_code,response.text)
        dclist = json.loads(response.text)
        dcs = []
        for dc in dclist['items']:
            dcs.append(dc['metadata']['name'])
        #print(dcs)
        if self.dcname in dcs:
            return True
        else:
            return False

    #更改dc配置
    def NewDcConfig(self,dcconfig):
        if self.podcount != '':
           dcconfig['spec']['replicas'] = self.podcount
        else:
            print('Use default pod config --->1')
        dcconfig['spec']['template']['spec']['containers'][0]['image'] = self.imagename
        data = json.dumps(dcconfig)
        return data


    #更改service配置
    def NewServiceConfig(self,serviceconfig):
        if serviceconfig['spec']['ports'][0]['port'] == int(self.port):
            pass
        else:
            serviceconfig['spec']['ports'][0]['port'] = int(self.port)
        if serviceconfig['spec']['ports'][0]['targetPort'] == int(self.tport):
            pass
        else:
            serviceconfig['spec']['ports'][0]['targetPort'] = int(self.tport)
        data = json.dumps(serviceconfig)
        return data

    #创建DC
    def CreateDC(self):
        #print("Create NewDc!")
        apipath = self.serverurl + '/apis/apps.openshift.io/v1/namespaces/' + self.namespace + '/deploymentconfigs/'
        #替换文件内容
        cmd1 = '''sed -i 's#devops#''' + self.namespace + '#g' + "' default.yaml" 
        cmd2 = '''sed -i 's#abcd#''' + self.dcname + '#g' + "' default.yaml"
        os.system(cmd1 + "&&" + cmd2)
        #yaml to dict
        f = open('default.yaml')
        dcconfig = f.read()
        f.close()
        dictconfig = yaml.load(dcconfig)
        #更新镜像
        newconfig = self.NewDcConfig(dictconfig)
        #开始创建
        response = requests.post(apipath,data=newconfig,headers=self.headers,verify=False)
        #print(response.status_code,response.text)
        return int(response.status_code)

    #更新DC
    def UpdateDC(self):
        apipath = self.serverurl + '/apis/apps.openshift.io/v1/namespaces/' + self.namespace + '/deploymentconfigs/' + self.dcname
        #upconfig = self.serverurl + '/apis/apps.openshift.io/v1/namespaces/' + self.namespace + '/deploymentconfigs/' + self.dcname
        dcconfig = json.loads(requests.get(apipath,headers=self.headers,verify=False).text)
        newconfig = self.NewDcConfig(dcconfig)
        response = requests.put(apipath,data=newconfig,headers=self.headers,verify=False)
        return int(response.status_code)

    #创建service
    def CreateService(self):
        #print("Strart create service", self.servicename)
        apipath = self.serverurl + '/api/v1/namespaces/' + self.namespace + '/services/'
        #替换文件内容
        cmd1 = '''sed -i 's#bigdata-stg#''' + self.namespace + '#g' + "' service.yaml" 
        cmd2 = '''sed -i 's#eureka02#''' + self.dcname + '#g' + "' service.yaml"
        os.system(cmd1 + "&&" + cmd2)
        #yaml to dict
        f = open('service.yaml')
        dcconfig = f.read()
        f.close()
        dictconfig = yaml.load(dcconfig)
        #更新镜像
        newconfig = self.NewServiceConfig(dictconfig)
        #开始创建
        response = requests.post(apipath,data=newconfig,headers=self.headers,verify=False)
        #print(response.status_code,response.text)
        return int(response.status_code)

    #更新service
    def UpdataService(self):
        apipath = self.serverurl + '/api/v1/namespaces/' + self.namespace + '/services/' + self.servicename
        serviceconfig = json.loads(requests.get(apipath,headers=self.headers,verify=False).text)
        newconfig = self.NewServiceConfig(serviceconfig)
        response = requests.put(apipath,data=newconfig,headers=self.headers,verify=False)
        return int(response.status_code)

    #DC controler
    def main(self):
        if self.token != False:
            time.sleep(2)
            result = self.GetDcList()
            if result == True:
                print('>>>DC (%s) 已存在' %(self.dcname,))
                print('    准备更新......')
                udcstatus = self.UpdateDC()
                if udcstatus <= 300:
                    print('    DC更新成功')
                else:
                    print('    DC更新失败')
                uservice = self.UpdataService()
                if uservice  <= 300:
                    print('    Service更新成功')
                else:
                    print('    Service更新失败')

            elif result == False:
                print('>>>DC (%s) 不存在' %(self.dcname,))
                print('    准备创建......')
                cdcstatus = self.CreateDC()
                if cdcstatus <= 300:
                    print('    DC创建成功')
                else:  
                    print('    DC创建失败')
                cservice = self.CreateService()
                if cservice  <= 300:
                    print('    Service创建成功')
                else:
                    print('    Service创建失败')
        else:
            print("获取token失败！")


if __name__ == '__main__':
    server = OpenShift()
    #server.main()
    server.main()
 