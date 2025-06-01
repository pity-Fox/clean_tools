# -*- coding:utf-8 -*-
from sys import argv                         #调用库
from time import sleep                       
import lib.Library as library
from os import mkdir, path
pathpg = path.dirname(path.abspath(argv[0]))  #获取当前程序所在文件夹的绝对路径 #dirname去文件名 #abspath是程序路径
del_path =path.join(pathpg,"logs")                  #修改要删除的路径（就是在后面加/logs）
pathei=(path.exists(del_path))         #检查路径是否存在
print(pathpg)
def userin():
    while True:
        user=input ("clean$")
        if user == "test":
            library.test()              ##文件位于./lib/library.py

        elif user == "help":
            library.help()

        elif user == "version":
            library.ver()

        elif user == "clean":
            library.clean()

        elif user =="dl":
            library.dellogs()

        elif user =="exit":
            library.et()

        else:
            print("输入的命令有误")
if pathei == True:
    userin()
elif pathei == False:
    print("未检测到日志文件夹")
    print(pathei)
    print("已经尝试重新建立文件夹")
    userin()
else:
    print("未检测到日志文件夹,5秒后退出")
    sleep(5)