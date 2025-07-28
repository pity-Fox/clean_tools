import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
from collections import OrderedDict

class QBEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("QB 文件编辑器")
        self.root.geometry("600x500")
        
        self.current_file = None
        self.entries = []
        self.current_index = 0
        
        self.create_menu()
        self.create_widgets()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建", command=self.new_file)
        file_menu.add_command(label="打开", command=self.open_file)
        file_menu.add_command(label="保存", command=self.save_file)
        file_menu.add_command(label="另存为", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        menubar.add_cascade(label="文件", menu=file_menu)
        
        self.root.config(menu=menubar)
    
    def create_widgets(self):
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 导航控制
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.slider = tk.Scale(control_frame, from_=1, to=1, orient=tk.HORIZONTAL, 
                              command=self.on_slider_change)
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        add_btn = tk.Button(control_frame, text="+", command=self.add_entry)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        del_btn = tk.Button(control_frame, text="-", command=self.delete_entry)
        del_btn.pack(side=tk.LEFT)
        
        # 输入区域
        entry_frame = tk.Frame(main_frame)
        entry_frame.pack(fill=tk.BOTH, expand=True)
        
        # Number (自动生成，不可编辑)
        tk.Label(entry_frame, text="Number:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.number_label = tk.Label(entry_frame, text="1")
        self.number_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Name
        tk.Label(entry_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.name_entry = tk.Entry(entry_frame, width=50)
        self.name_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Title
        tk.Label(entry_frame, text="Title:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.title_entry = tk.Entry(entry_frame, width=50)
        self.title_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Choices 框架
        self.choice_frame = tk.Frame(entry_frame)
        self.choice_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Add Choice 按钮
        self.add_choice_btn = tk.Button(entry_frame, text="添加选项", command=self.add_choice)
        self.add_choice_btn.grid(row=4, column=0, sticky=tk.W, pady=5)
        
        # Add 部分
        tk.Label(entry_frame, text="Add:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.add_text = tk.Text(entry_frame, width=50, height=5)
        self.add_text.grid(row=5, column=1, sticky=tk.W, pady=2)
        
        # 初始化一个空条目
        self.add_entry(initial=True)
    
    def add_entry(self, initial=False):
        if not initial:
            # 保存当前条目
            self.save_current_entry()
            
            # 创建新条目
            new_entry = {
                "Number": len(self.entries) + 1,
                "Name": "",
                "Title": "",
                "Choices": [],
                "Add": ""
            }
            self.entries.append(new_entry)
            self.slider.config(to=len(self.entries))
            self.slider.set(len(self.entries))
            self.current_index = len(self.entries) - 1
            self.load_entry(self.current_index)
        else:
            # 初始化第一个条目
            self.entries = [{
                "Number": 1,
                "Name": "",
                "Title": "",
                "Choices": [],
                "Add": ""
            }]
            self.load_entry(0)
    
    def delete_entry(self):
        if len(self.entries) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个条目")
            return
            
        current = self.slider.get() - 1
        del self.entries[current]
        
        # 重新编号
        for i, entry in enumerate(self.entries):
            entry["Number"] = i + 1
        
        if current >= len(self.entries):
            current = len(self.entries) - 1
        
        self.slider.config(to=len(self.entries))
        self.slider.set(current + 1)
        self.current_index = current
        self.load_entry(self.current_index)
    
    def save_current_entry(self):
        if not self.entries:
            return
            
        # 保存当前编辑的内容到当前条目
        current_entry = self.entries[self.current_index]
        current_entry["Name"] = self.name_entry.get()
        current_entry["Title"] = self.title_entry.get()
        current_entry["Add"] = self.add_text.get("1.0", tk.END).strip()
        
        # 保存选项
        choices = []
        for widget in self.choice_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                choice_data = {
                    "letter": widget.letter,
                    "text": widget.text_entry.get(),
                    "probability": widget.prob_entry.get(),
                    "add": widget.add_entry.get()
                }
                choices.append(choice_data)
        
        # 按字母排序
        choices.sort(key=lambda x: x["letter"])
        
        # 更新到条目
        current_entry["Choices"] = choices
    
    def load_entry(self, index):
        if index < 0 or index >= len(self.entries):
            return
            
        self.current_index = index
        entry = self.entries[index]
        
        # 清除当前UI内容
        self.name_entry.delete(0, tk.END)
        self.title_entry.delete(0, tk.END)
        self.add_text.delete("1.0", tk.END)
        
        # 清除所有选项
        for widget in self.choice_frame.winfo_children():
            widget.destroy()
        
        # 加载新内容
        self.number_label.config(text=str(entry["Number"]))
        self.name_entry.insert(0, entry["Name"])
        self.title_entry.insert(0, entry["Title"])
        self.add_text.insert("1.0", entry["Add"])
        
        # 加载选项
        for choice in entry["Choices"]:
            self.add_choice(choice)
    
    def add_choice(self, choice_data=None):
        # 确定新选项的字母
        existing_letters = set()
        for widget in self.choice_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                existing_letters.add(widget.letter)
        
        # 找到第一个未使用的字母
        letter = "A"
        while letter in existing_letters:
            letter = chr(ord(letter) + 1)
        
        # 创建选项框架
        choice_frame = tk.Frame(self.choice_frame)
        choice_frame.pack(fill=tk.X, pady=2)
        choice_frame.letter = letter
        choice_frame.text_entry = None
        choice_frame.prob_entry = None
        choice_frame.add_entry = None
        
        # 字母标签
        tk.Label(choice_frame, text=f"{letter}:").pack(side=tk.LEFT)
        
        # 文本
        tk.Label(choice_frame, text="文本:").pack(side=tk.LEFT, padx=(5,0))
        text_entry = tk.Entry(choice_frame, width=15)
        text_entry.pack(side=tk.LEFT)
        choice_frame.text_entry = text_entry
        
        # 概率
        tk.Label(choice_frame, text="概率:").pack(side=tk.LEFT, padx=(5,0))
        prob_entry = tk.Entry(choice_frame, width=8)
        prob_entry.pack(side=tk.LEFT)
        choice_frame.prob_entry = prob_entry
        
        # 附加内容
        tk.Label(choice_frame, text="附加:").pack(side=tk.LEFT, padx=(5,0))
        add_entry = tk.Entry(choice_frame, width=15)
        add_entry.pack(side=tk.LEFT)
        choice_frame.add_entry = add_entry
        
        # 删除按钮
        del_btn = tk.Button(choice_frame, text="×", command=lambda: choice_frame.destroy())
        del_btn.pack(side=tk.RIGHT, padx=(5,0))
        
        # 如果提供了数据，填充它
        if choice_data:
            text_entry.insert(0, choice_data["text"])
            prob_entry.insert(0, choice_data["probability"])
            add_entry.insert(0, choice_data["add"])
            choice_frame.letter = choice_data["letter"]
    
    def on_slider_change(self, value):
        if not self.entries:
            return
            
        # 保存当前条目
        self.save_current_entry()
        
        # 加载新条目
        new_index = int(value) - 1
        if new_index != self.current_index:
            self.load_entry(new_index)
    
    def new_file(self):
        self.save_current_entry()
        if self.entries and not self.is_empty():
            if not messagebox.askyesno("新建文件", "当前内容未保存，确定要新建文件吗？"):
                return
        
        self.current_file = None
        self.entries = []
        self.add_entry(initial=True)
        self.slider.config(to=1)
        self.slider.set(1)
    
    def open_file(self):
        self.save_current_entry()
        if self.entries and not self.is_empty():
            if not messagebox.askyesno("打开文件", "当前内容未保存，确定要打开新文件吗？"):
                return
        
        file_path = filedialog.askopenfilename(filetypes=[("QB files", "*.qb"), ("All files", "*.*")])
        if not file_path:
            return
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 简单的解析逻辑 - 实际应用中可能需要更复杂的解析器
            # 这里简化处理，假设文件是有效的
            entries = []
            parts = content.split("Number{")[1:]  # 分割每个条目
            
            for part in parts:
                entry = {}
                # 解析Number
                num_end = part.find("}")
                entry["Number"] = int(part[:num_end].strip())
                
                # 解析Name
                name_start = part.find("Name{") + 5
                name_end = part.find("}", name_start)
                entry["Name"] = part[name_start:name_end].strip()
                
                # 解析Title
                title_start = part.find("title{") + 6
                title_end = part.find("}", title_start)
                entry["Title"] = part[title_start:title_end].strip()
                
                # 解析Choices
                choices_start = part.find("choice{") + 7
                choices_end = part.find("}", choices_start)
                choices_str = part[choices_start:choices_end]
                
                choices = []
                # 简单解析每个选项
                for choice_part in choices_str.split("\n"):
                    choice_part = choice_part.strip()
                    if not choice_part or "{" not in choice_part:
                        continue
                    
                    letter = choice_part[0]
                    text_start = choice_part.find("text=") + 5
                    text_end = choice_part.find(",", text_start)
                    text = choice_part[text_start:text_end].strip()
                    
                    prob_start = choice_part.find("Probability=") + 12
                    prob_end = choice_part.find(",", prob_start)
                    probability = choice_part[prob_start:prob_end].strip()
                    
                    add_start = choice_part.find("add=") + 4
                    add_end = choice_part.find("}", add_start)
                    add = choice_part[add_start:add_end].strip().strip('"')
                    
                    choices.append({
                        "letter": letter,
                        "text": text,
                        "probability": probability,
                        "add": add
                    })
                
                entry["Choices"] = choices
                
                # 解析Add
                add_start = part.find("add{") + 4
                add_end = part.find("}", add_start)
                entry["Add"] = part[add_start:add_end].strip()
                
                entries.append(entry)
            
            self.entries = entries
            self.current_file = file_path
            self.slider.config(to=len(self.entries))
            self.slider.set(1)
            self.load_entry(0)
            
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def save_file(self):
        if not self.current_file:
            self.save_as_file()
            return
            
        self.save_to_file(self.current_file)
    
    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".qb",
            filetypes=[("QB files", "*.qb"), ("All files", "*.*")],
            initialfile=self.current_file if self.current_file else "untitled.qb"
        )
        
        if not file_path:
            return
            
        self.save_to_file(file_path)
        self.current_file = file_path
    
    def save_to_file(self, file_path):
        self.save_current_entry()
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in self.entries:
                    # 构建选项字符串
                    choices_str = ""
                    for choice in entry["Choices"]:
                        choices_str += f"{choice['letter']}{{text={choice['text']},Probability={choice['probability']},add=\"{choice['add']}\"}}\n"
                    
                    # 构建条目字符串
                    entry_str = f"""Number{{
{entry['Number']}
}}

Name{{
{entry['Name']}
}}

title{{
{entry['Title']}
}}

choice{{
{choices_str.strip()}
}}
add
{{
{entry['Add']}
}}

"""
                    f.write(entry_str)
            
            messagebox.showinfo("保存成功", f"文件已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件时出错: {str(e)}")
    
    def is_empty(self):
        if not self.entries:
            return True
            
        for entry in self.entries:
            if entry["Name"] or entry["Title"] or entry["Add"] or entry["Choices"]:
                return False
                
        return True

if __name__ == "__main__":
    root = tk.Tk()
    app = QBEditor(root)
    root.mainloop()
