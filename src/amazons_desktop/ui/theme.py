"""Shared palette and ttk styles for the board window and record dialogs."""
from tkinter import ttk

BG = '#f6f7f9'
PANEL = '#ffffff'
TEXT = '#202630'
MUTED = '#67717f'
ACCENT = '#385fe0'
BORDER = '#dce2eb'
FONT = ('Microsoft YaHei UI', 10)


def configure(root):
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=FONT, foreground=TEXT)
    style.configure('TFrame', background=PANEL)
    style.configure('TLabel', background=PANEL)
    style.configure('TButton', padding=8, background='#edf0f5', borderwidth=0)
    style.map('TButton', background=[('active', '#dfe6f4')], foreground=[('disabled', MUTED)])
    style.configure('Accent.TButton', background=ACCENT, foreground=PANEL)
    style.map('Accent.TButton', background=[('disabled', '#edf0f5'), ('active', '#2f51cc')], foreground=[('disabled', MUTED)])

    style.configure('TEntry', padding=(10, 8), fieldbackground=PANEL, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, insertcolor=ACCENT,
                    selectbackground='#e8efff', selectforeground=TEXT, borderwidth=1)
    style.map('TEntry', bordercolor=[('focus', ACCENT)], lightcolor=[('focus', ACCENT)],
              darkcolor=[('focus', ACCENT)], fieldbackground=[('disabled', BG)])
    style.configure('TCombobox', padding=(10, 7), background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, arrowcolor=MUTED, arrowsize=12, borderwidth=1,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    selectbackground=PANEL, selectforeground=TEXT)
    style.map('TCombobox', background=[('active', '#f2f5fb')],
              fieldbackground=[('disabled', BG), ('readonly', PANEL)],
              foreground=[('disabled', MUTED), ('readonly', TEXT)],
              selectbackground=[('readonly', PANEL)], selectforeground=[('readonly', TEXT)],
              bordercolor=[('focus', ACCENT)], lightcolor=[('focus', ACCENT)],
              darkcolor=[('focus', ACCENT)], arrowcolor=[('active', ACCENT)])
    # The combobox popup is a Tk Listbox, outside ttk's style hierarchy.
    for option, value in {'background': PANEL, 'foreground': TEXT, 'selectBackground': '#e8efff',
                          'selectForeground': ACCENT, 'font': FONT, 'relief': 'flat',
                          'borderWidth': 0, 'highlightThickness': 0}.items():
        root.option_add('*TCombobox*Listbox.' + option, value)
    style.configure('TScale', background='#c7d2e6', troughcolor='#edf0f5', borderwidth=0,
                    lightcolor='#c7d2e6', darkcolor='#c7d2e6')
    style.map('TScale', background=[('active', ACCENT)])
