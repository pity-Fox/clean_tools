# -*- coding:utf-8 -*-  
from os import *  
from shutil import rmtree  
import sys  
import argparse  
  
pathpg = path.dirname(path.abspath(sys.argv[0]))  #获取当前程序所在文件夹的绝对路径  
  
def clean():  
    print("测试")
    clean_file_path = input("清理文件路径(输入default来启用默认清理库):")
    if clean_file_path == "default":
        clean_file_path = "./lib/cleanlib"

    with open (clean_file_path,"r") as file:
        first_line = file.readline() #读取第一行
        if first_line:              #确保每一行不是空的
            first_word = first_line.split(" ")[0] #将每行命令分析，以空格为标识符，这里读取第一个字母
            clean_path = first_line.split(" ")[1]
            ml = first_word
            print(ml)
            print(clean_path)
  
def ver():           
    print("清理工具---B0.1 (beta 0.1-testversion)")    
  
def help():  
    print("""  
         命令行选项：  
          1. clean -- 清理（暂未启动）  
          2. ver -- 显示版本信息  
          3. help -- 显示帮助信息  
          4. exit -- 退出程序  
          """)    
  
def dellogs():  
    try:  
        del_path = path.join(pathpg,"logs")  
        if path.exists(del_path):  # 检查路径是否存在  
            rmtree(del_path)  # 删除文件夹  
            print("已尝试删除")   
            mkdir("logs")  
            print("已尝试建立新文件夹")  
        else:  
            print("文件夹似乎不存在")  
            mkdir("logs")  
            print("已尝试建立新文件夹")  
    except Exception as e:  
        print(f"在删除或创建文件夹时发生错误: {e}")  
          
def et():  
    sys.exit()  
  
if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description='清理工具')  
    parser.add_argument('-c', '--clean', action='store_true', help='执行清理操作（暂未启动）')  
    parser.add_argument('-v', '--ver', action='store_true', help='显示版本信息')  
    parser.add_argument('-e', '--exit', action='store_true', help='退出程序')  
    parser.add_argument('-d', '--dellogs', action='store_true', help='删除日志文件夹')  
    args = parser.parse_args()  
      
    if args.ver:  
        ver()  
    elif args.clean:  
        clean()  
    elif args.exit:  
        et()  
    elif args.dellogs:  
        dellogs()  
    else:  
        help()