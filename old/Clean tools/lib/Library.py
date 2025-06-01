# -*-已尝试建立新文件夹 coding:utf-8 -*-
from os import *
from shutil import rmtree
import sys
pathpg = path.dirname(path.abspath(sys.argv[0]))  #获取当前程序所在文件夹的绝对路径 #dirname去文件名 #abspath是程序路径
del_path =path.join(pathpg,"logs")                  #修改要删除的路径（就是在后面加/logs）
pathei=(path.exists(del_path))         #检查路径是否存在
def help():
           print("""
                 ----此命令用来显示帮助信息-----------------\n
                 --序号-命令----作用------------------------\n
                 --1----clean---默认清理--------------------\n
                 --2----ver-----显示版本信息----------------\n
                 --3----exit----退出程序--------------------\n
                 --4----dl------删除日志文件----------------\n
                 """)  
            
def ver():         
    print("清理工具---B0.1 (beta 0.1-testversion)")  

def clean():
    print("测试")
    try:  
          clean_file_path_in = input("请输入要清理的文件路径(default为默认清理库):")

          if clean_file_path_in == "default":
             clean_file_path_in = "./lib/cleanlib.txt"
                  # 检查文件路径是否合法
          if not path.exists(clean_file_path_in):
              print("路径无效")
          else:
              with open(clean_file_path_in, "r") as file:
    except ValueError:  
        print("路径无效")


    with open (clean_file_path_in,"r") as file:
        first_line = file.readline() #读取第一行
        if first_line:              #确保每一行不是空的
            first_word = first_line.split(" ")[0] #将每行命令分析，以空格为标识符，这里读取第一个字母
            clean_path = first_line.split(" ")[1]
            ml = first_word
            print(ml)
            print(clean_path)


def test():
      print(pathpg)
      print(del_path)
     #shutil.rmtree(del_path)          #删除文件夹
     #print(pathei)

def dellogs():
        folderyn = pathei                         #检查文件夹状态
        if folderyn == True:                    #文件夹要是存在
              print(del_path)
              rmtree(del_path)                    #删除文件
              print("已尝试删除")  
              mkdir("logs")
              print("已尝试建立新文件夹")
        elif folderyn == False:                 #文件夹要是不存在
              print("文件夹似乎不存在")
              print(del_path)
              mkdir("logs")
              print("已尝试建立新文件夹")
        else:                                     #不知道文件夹到底存不存在
              print("无法获取文件夹状态")
              mkdir("logs")
              print("已尝试建立新文件夹")

def et():
     exit()



