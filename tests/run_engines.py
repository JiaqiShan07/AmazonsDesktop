"""Explicit real-engine integration run; not included in unit test discovery."""
import argparse,ctypes,json,time,tkinter as tk
from pathlib import Path
from amazons_desktop.ui.app import App

parser=argparse.ArgumentParser();parser.add_argument('--engine',required=True);parser.add_argument('--report',required=True)
args=parser.parse_args()
ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
r=tk.Tk();a=App(r);a.paths={1:args.engine,-1:args.engine};a.new()
started=time.monotonic();report={'engine':args.engine,'moves':[]};last=0

def check():
    global last
    if len(a.game.history)>last:
        last=len(a.game.history)
        report['moves'].append({'ply':last,'wall_seconds':round(time.monotonic()-started,3),'used':dict(a.clock.used)})
        print('ply',last,'wall',round(time.monotonic()-started,1),flush=True)
    if a.error or a.game.winner() or a.timeout_winner or time.monotonic()-started>330:
        report.update(error=a.error,winner=a.game.winner(),timeout=a.timeout_winner,plies=last,log=a.log.get('1.0','end'))
        Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        a.close()
    else:r.after(100,check)
r.after(100,check);r.mainloop()
