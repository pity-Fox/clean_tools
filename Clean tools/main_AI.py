import os  
import time  
import sys  
import lib.Library as lib  
pathpg = os.path.dirname(os.path.abspath(sys.argv[0]))  
del_path = os.path.join(pathpg, "logs")  
def main():      
    if os.path.exists(del_path):  
            userin()  
    else:  
            os.makedirs(del_path)  
            userin()  
            print("已经尝试重新建立文件夹")  
      
def userin():  
    while True:  
        user = input("clean$ ")  
        if user == "test":  
            lib.test()  
        elif user == "help":  
            lib.help()  
        elif user == "ver":  
            lib.ver()  
        elif user == "clean":  
            lib.clean()  
        elif user == "dl":  
            lib.dellogs()  
        elif user == "exit":  
            lib.et()  
        else:  
            print("输入的命令有误")  

if __name__ == "__main__":  
    main()