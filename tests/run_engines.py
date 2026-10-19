"""Manual real-engine match runner; excluded from unittest discovery."""
import argparse
import ctypes
import json
import sys
import time
import tkinter as tk
from pathlib import Path
from amazons_desktop.ui.app import App


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=330)
    args = parser.parse_args()
    if sys.platform == 'win32':
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    root = tk.Tk()
    app = App(root)
    app.paths = {1: str(args.engine.resolve()), -1: str(args.engine.resolve())}
    app.new()
    started = time.monotonic()
    report = {'engine': str(args.engine), 'moves': []}
    last = 0

    def check():
        nonlocal last
        if not app.started and not app.initializing and not app.error:
            app.start()
        if len(app.game.history) > last:
            last = len(app.game.history)
            elapsed = round(time.monotonic() - started, 3)
            report['moves'].append({'ply': last, 'wall_seconds': elapsed,
                                    'used': dict(app.clock.used)})
            print('ply', last, 'wall', elapsed, flush=True)
        if app.error or app.game.winner() or app.timeout_winner or time.monotonic() - started > args.timeout:
            report.update(error=app.error, winner=app.game.winner(),
                          timeout=app.timeout_winner, plies=last, log=app.log.get('1.0', 'end'))
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            app.close()
        else:
            root.after(100, check)

    root.after(100, check)
    root.mainloop()


if __name__ == '__main__':
    main()
