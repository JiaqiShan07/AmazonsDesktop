"""Metadata editor shared by native records and competition export."""
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import replace
from ..record import Record
from .theme import PANEL, TEXT, MUTED, FONT

class RecordDialog(tk.Toplevel):
    def __init__(self, parent, record: Record, competition: bool):
        super().__init__(parent)
        self.title('导出比赛棋谱' if competition else '对局信息')
        self.transient(parent)
        self.resizable(False,False)
        self.result = None
        self.record = record
        self.competition = competition
        self.fields = {}
        self.configure(bg=PANEL)
        heading = tk.Frame(self, bg=PANEL)
        heading.pack(fill='x', padx=28, pady=(24, 12))
        tk.Label(heading, text=self.title(), bg=PANEL, fg=TEXT,
                 font=('Microsoft YaHei UI', 17, 'bold')).pack(anchor='w')
        tk.Label(heading, text='设置参赛双方与比赛信息', bg=PANEL, fg=MUTED,
                 font=('Microsoft YaHei UI', 10)).pack(anchor='w', pady=(5, 0))
        body = ttk.Frame(self,padding=(28, 0, 28, 24))
        body.pack(fill='both',expand=True)
        labels = [('black','先手参赛队（黑方）'),('white','后手参赛队（白方）'),('result','比赛结果'),('location','比赛时间及地点'),('event','赛事名称')]
        for row,(key,label) in enumerate(labels):
            ttk.Label(body,text=label).grid(row=row,column=0,sticky='w',padx=(0,18),pady=8)
            variable = tk.StringVar(value=getattr(record,key))
            if key=='result':
                widget = ttk.Combobox(body,textvariable=variable,values=['先(后)手胜','先手胜','后手胜'],state='readonly',width=32,font=FONT)
            else:
                widget = ttk.Entry(body,textvariable=variable,width=35,font=FONT)
            widget.grid(row=row,column=1,sticky='ew',pady=8)
            self.fields[key] = variable
        if competition:
            ttk.Label(body,text='GB2312 编码 · 请确认比赛结果及参赛信息',foreground=MUTED).grid(row=5,column=0,columnspan=2,sticky='w',pady=12)
        actions=ttk.Frame(body)
        actions.grid(row=6,column=0,columnspan=2,sticky='e',pady=(12,0))
        ttk.Button(actions,text='取消',command=self.destroy).pack(side='left',padx=(0,8))
        ttk.Button(actions,text='确认导出…' if competition else '保存',style='Accent.TButton',command=self.accept).pack(side='left')
        self.bind('<Escape>',lambda event:self.destroy())
        self.protocol('WM_DELETE_WINDOW',self.destroy)
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f'+{x}+{y}')
        self.grab_set()

    def accept(self):
        fields={key:variable.get().strip() for key,variable in self.fields.items()}
        record=replace(self.record,**fields)
        if self.competition:
            if any(not value for value in fields.values()) or record.result not in ('先手胜','后手胜'):
                messagebox.showerror('信息未完整','请填写参赛信息，并选择先手胜或后手胜。',parent=self)
                return
            try:
                record.to_bytes()
            except (UnicodeError,ValueError) as exc:
                messagebox.showerror('无法导出','内容须符合棋谱格式，且所有字符须能用 GB2312 表示。\n'+str(exc),parent=self)
                return
        self.result=record
        self.destroy()


def edit_record(parent,record,competition=False):
    dialog=RecordDialog(parent,record,competition)
    parent.wait_window(dialog)
    return dialog.result
