from math import ceil
import queue
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from ..game import Game, encode, decode
from ..engine import Engine
from ..clock import Clock, display
from .board_view import render
from .move_trail import MOVE_COLOR, SHOT_COLOR
from ..record import Record, notation
from .record_dialog import edit_record
from .theme import BG, PANEL, TEXT, MUTED, ACCENT, FONT, configure

class App:
    def __init__(self, root):
        self.root = root
        root.title('AMAZONS · 亚马逊棋')
        scale = root.winfo_fpixels('1i') / 96
        root.geometry(f'{round(1220*scale)}x{round(900*scale)}')
        root.minsize(round(940*scale), round(760*scale))
        root.configure(bg=BG)
        self.events = queue.Queue()
        self.engines = {}
        self.token = 0
        self.paths = {1: '', -1: ''}
        self.engine_directory = Path.home()
        self.labels = {}
        self.clock_labels = {}
        self.time_control = tk.StringVar(value='900')
        self.clock = Clock()
        self.timeout_winner = None
        self.paused = False
        self.started = False
        self.pending = set()
        self.initializing = set()
        self.undo_waiting = set()
        self.undo_turns = 0
        self.error = False
        self.replay = None
        self.replay_index = 0
        self.replay_id = None
        self.playing = False
        self.seeking = False
        configure(root)
        header = tk.Frame(root, bg=BG)
        header.pack(fill='x', padx=32, pady=(25, 10))
        tk.Label(header, text='Amazons', font=('Segoe UI', 24, 'bold'), fg=TEXT, bg=BG).pack(side='left')
        tk.Label(header, text='亚马逊棋 · 本地对弈', font=('Microsoft YaHei UI', 10), fg=MUTED, bg=BG).pack(side='left', padx=20)
        ttk.Button(header, text='对局信息…', command=self.edit_metadata).pack(side='right', padx=8)
        ttk.Button(header, text='新建棋局', command=self.new).pack(side='right')
        self.start_button = ttk.Button(header, text='开始对局', style='Accent.TButton', command=self.start)
        self.start_button.pack(side='right', padx=(0, 8))
        main = tk.Frame(root, bg=BG)
        main.pack(fill='both', expand=True, padx=24, pady=10)
        self.canvas = tk.Canvas(main, bg=BG, highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.draw())
        self.canvas.bind('<Button-1>', self.click)
        side = tk.Frame(main, bg=PANEL, width=round(300*scale), padx=22, pady=22)
        side.pack(side='right', fill='y', padx=(20, 0))
        side.pack_propagate(False)
        self.status = tk.Label(side, bg=PANEL, fg=ACCENT, font=('Microsoft YaHei UI', 19, 'bold'), anchor='w')
        self.status.pack(fill='x')
        self.phase = tk.Label(side, bg=PANEL, fg=TEXT, wraplength=round(232*scale), justify='left', font=('Microsoft YaHei UI', 11), anchor='w')
        self.phase.pack(fill='x', pady=(8, 8))
        self.turn_clock = tk.Label(side, text='本手 00:00', bg=PANEL, fg=MUTED, anchor='w', font=('Microsoft YaHei UI', 10))
        self.turn_clock.pack(fill='x', pady=(0, 16))
        timer_row = tk.Frame(side, bg=PANEL)
        timer_row.pack(fill='x', pady=(0, 16))
        tk.Label(timer_row, text='每方总时限 / 秒', bg=PANEL, fg=MUTED).pack(side='left')
        timer_choice = ttk.Combobox(timer_row, textvariable=self.time_control, values=['100', '300', '750', '900', '不限时'], state='readonly', width=7, font=FONT)
        timer_choice.pack(side='right')
        timer_choice.bind('<<ComboboxSelected>>', lambda e: self.new())
        for color, title in [(1, '●  黑方 · 先手'), (-1, '○  白方 · 后手')]:
            tk.Label(side, text=title, bg=PANEL, fg=TEXT, font=('Microsoft YaHei UI', 12), anchor='w').pack(fill='x')
            timer = tk.Label(side, text='15:00', bg=PANEL, fg=TEXT, anchor='w', font=('Segoe UI', 27, 'bold'))
            timer.pack(fill='x', pady=(3, 0))
            self.clock_labels[color] = timer
            label = tk.Label(side, text='人类玩家', bg=PANEL, fg=MUTED, anchor='w', wraplength=round(230*scale), justify='left')
            label.pack(fill='x', pady=7)
            self.labels[color] = label
            line = tk.Frame(side, bg=PANEL)
            line.pack(fill='x', pady=(0, 18))
            ttk.Button(line, text='加载引擎…', command=lambda c=color: self.load_engine(c)).pack(side='left')
            ttk.Button(line, text='人类', command=lambda c=color: self.human(c)).pack(side='right')
        self.pause_button = ttk.Button(side, text='暂停计时', command=self.toggle_pause)
        self.pause_button.pack(fill='x', pady=(0, 4))
        self.undo_button = ttk.Button(side, text='↶  悔棋', command=self.undo)
        self.undo_button.pack(fill='x', pady=4)
        ttk.Button(side, text='取消选择 / Esc', command=self.cancel).pack(fill='x', pady=4)
        line = tk.Frame(side, bg=PANEL)
        line.pack(fill='x', pady=4)
        ttk.Button(line, text='保存 JSON', command=self.save).pack(side='left')
        ttk.Button(line, text='打开棋谱', command=self.open).pack(side='right')
        ttk.Button(side, text='导出比赛 TXT…', command=self.export_text).pack(fill='x', pady=4)
        tk.Label(side, text='对局记录', bg=PANEL, fg=MUTED, anchor='w').pack(fill='x', pady=(22, 8))
        self.log = tk.Text(side, height=4, bg=BG, fg=TEXT, relief='flat', font=('Consolas', 10), padx=8, pady=8, state='disabled')
        self.log.pack(fill='both', expand=True)
        self.replay_bar = tk.Frame(root, bg=BG)
        for text, action in [('开局', lambda:self.seek(0)), ('上一步', lambda:self.seek(self.replay_index-1))]:
            ttk.Button(self.replay_bar, text=text, command=action).pack(side='left', padx=3)
        self.play_button = ttk.Button(self.replay_bar, text='播放', command=self.play_replay)
        self.play_button.pack(side='left', padx=3)
        for text, action in [('下一步', lambda:self.seek(self.replay_index+1)), ('终局', lambda:self.seek(len(self.replay.moves)))]:
            ttk.Button(self.replay_bar, text=text, command=action).pack(side='left', padx=3)
        self.progress = ttk.Scale(self.replay_bar, from_=0, to=1, command=self.scrub)
        self.progress.pack(side='left', fill='x', expand=True, padx=12)
        self.replay_label = tk.Label(self.replay_bar, bg=BG, fg=TEXT, width=12)
        self.replay_label.pack(side='left')
        ttk.Button(self.replay_bar, text='从此处继续', command=self.continue_game).pack(side='right', padx=3)
        self.feedback = tk.Label(root, bg=BG, fg=MUTED, anchor='w', font=('Microsoft YaHei UI', 10))
        self.feedback.pack(fill='x', padx=34, pady=(0, 18))
        root.bind('<Escape>', lambda e: self.cancel())
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.new()
        root.after(60, self.poll)

    def stop(self):
        self.pause_replay()
        self.started = False
        self.token += 1
        for engine in self.engines.values():
            engine.close()
        self.engines.clear()
        self.pending.clear()
        self.initializing.clear()
        self.undo_waiting.clear()
        self.undo_turns = 0

    def new(self):
        self.stop()
        self.replay = None
        self.replay_bar.pack_forget()
        self.game = Game()
        self.record_info = Record()
        self.source = self.target = None
        self.error = False
        self.clock = Clock(0 if self.time_control.get() == '不限时' else float(self.time_control.get()))
        self.timeout_winner = None
        self.paused = False
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        try:
            for color, path in self.paths.items():
                if path:
                    engine = Engine(path, self.events, self.token, color)
                    self.engines[color] = engine
            self.initializing = set(self.engines)
            if self.engines:
                self.wait_since = time.monotonic()
        except (OSError, ValueError) as exc:
            self.fail(str(exc))
        self.refresh()

    def start(self):
        if self.started or self.replay or self.error or self.initializing or self.game.winner() or self.timeout_winner:
            return
        self.started = True
        try:
            for side in (-1, 1):
                if side in self.engines:
                    self.engines[side].send('new ' + ('black' if side == 1 else 'white'))
            self.clock.start(self.game.turn)
            if self.game.turn in self.engines:
                self.pending.add(self.game.turn)
                self.wait_since = time.monotonic()
        except OSError as exc:
            self.fail(str(exc))
        self.refresh()

    def load_engine(self, color):
        path = filedialog.askopenfilename(title='选择 SAU 协议引擎（将重置棋局）', initialdir=str(self.engine_directory), filetypes=[('Windows 引擎', '*.exe'), ('所有文件', '*')])
        if path:
            self.engine_directory = Path(path).parent
            self.paths[color] = path
            self.labels[color].configure(text=Path(path).parent.name + '\n' + Path(path).name)
            self.new()

    def human(self, color):
        self.paths[color] = ''
        self.labels[color].configure(text='人类玩家')
        self.new()

    def fail(self, text):
        self.error = True
        self.clock.pause()
        self.feedback.configure(text='引擎错误：' + text, fg='#b54730')
        self.write_log('错误：' + text)

    def write_log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def poll(self):
        try:
            while True:
                token, color, kind, text = self.events.get_nowait()
                if token != self.token:
                    continue
                if kind == 'error':
                    self.fail(text)
                elif kind == 'diagnostic':
                    self.write_log(text[:1000])
                elif text.startswith('name '):
                    name = text[5:]
                    self.engines[color].supports_undo = name.endswith(' [undo,go]')
                    self.labels[color].configure(text=name.removesuffix(' [undo,go]'))
                    self.initializing.discard(color)
                    self.refresh()
                elif text == 'ready':
                    if color not in self.undo_waiting:
                        self.fail('引擎返回了未请求的悔棋确认')
                        continue
                    self.undo_waiting.remove(color)
                    self.engines[color].completed_turns = len(self.game.history) - self.undo_turns
                    if not self.undo_waiting and not self.error:
                        self.finish_undo()
                elif text.startswith('move '):
                    if self.error:
                        continue
                    try:
                        if color != self.game.turn or color not in self.pending:
                            raise ValueError('引擎在非本方回合返回走法')
                        self.pending.remove(color)
                        if color in self.engines:
                            self.engines[color].completed_turns += 1
                        self.commit(decode(text[5:]))
                    except (ValueError, OSError) as exc:
                        self.fail(str(exc))
                else:
                    self.fail('无法识别的协议输出：' + text[:120])
        except queue.Empty:
            pass
        if (self.pending or self.initializing or self.undo_waiting) and not self.error and time.monotonic() - self.wait_since > 180:
            self.fail('等待走法超过 180 秒，请检查引擎运行环境后新建棋局')
            self.stop()
        self.tick_clock()
        self.root.after(60, self.poll)

    def commit(self, move):
        self.tick_clock()
        if self.timeout_winner:
            return
        self.game.apply(move)
        self.clock.finish_turn(self.game.turn)
        self.source = self.target = None
        self.write_log(f'{len(self.game.history):03}  {notation(move)}')
        winner = self.game.winner()
        try:
            if winner:
                self.clock.pause()
                for engine in self.engines.values():
                    engine.send('end ' + ('black' if winner == 1 else 'white'))
            elif self.game.turn in self.engines:
                self.engines[self.game.turn].send('move ' + encode(move))
                self.engines[self.game.turn].completed_turns += 1
                self.pending.add(self.game.turn)
                self.wait_since = time.monotonic()
        except OSError as exc:
            self.fail(str(exc))
        self.refresh()

    def click(self, event):
        if not self.started or self.replay or self.paused or self.timeout_winner or self.error or self.initializing or self.undo_waiting or self.game.turn in self.engines or self.game.winner():
            return
        c, r = int((event.x-self.ox)//self.cell), int((event.y-self.oy)//self.cell)
        if not (0 <= r < 10 and 0 <= c < 10):
            self.cancel()
            return
        pos = (r, c)
        if self.target is not None:
            if pos in self.game.arrows(self.source, self.target):
                self.commit((self.source, self.target, pos))
                return
        elif self.game.board[r][c] == self.game.turn:
            self.source = None if self.source == pos else pos
            self.refresh()
            return
        elif self.source is not None and pos in self.game.rays(self.source):
            self.target = pos
            self.refresh()
            return
        if self.target is None:
            self.source = None
            self.refresh()
        self.feedback.configure(text='此位置不合法。请选择提示落点，或按 Esc 取消。', fg='#b54730')

    def cancel(self):
        self.source = self.target = None
        self.refresh()

    def undo_count(self):
        if not self.started or self.replay or self.error or self.pending or self.initializing or self.undo_waiting:
            return 0
        # 引擎在超时后已关闭，重新开始才能恢复协议对局。
        if self.timeout_winner and any(self.paths.values()):
            return 0
        if any(not engine.supports_undo for engine in self.engines.values()):
            return 0
        turns = 2 if self.engines else 1
        return turns if len(self.game.history) >= turns else 0

    def undo(self):
        turns = self.undo_count()
        if not turns:
            return
        self.clock.pause()
        self.source = self.target = None
        self.undo_turns = turns
        remaining = len(self.game.history) - turns
        self.undo_waiting = set(self.engines)
        self.wait_since = time.monotonic()
        try:
            for side in self.undo_waiting:
                self.engines[side].undo(self.engines[side].completed_turns - remaining)
        except OSError as exc:
            self.fail(str(exc))
        if not self.undo_waiting and not self.error:
            self.finish_undo()
        else:
            self.refresh()

    def finish_undo(self):
        turns = self.undo_turns
        for _ in range(turns):
            self.game.undo()
            self.clock.undo(self.game.turn, resume=False)
        self.undo_turns = 0
        self.timeout_winner = None
        self.paused = False
        self.record_info.result = '先(后)手胜'
        self.source = self.target = None
        self.clock.start(self.game.turn)
        self.write_log(f'↶ 撤销 {turns} 手')
        try:
            if self.game.turn in self.engines:
                self.engines[self.game.turn].go()
                self.pending.add(self.game.turn)
                self.wait_since = time.monotonic()
        except OSError as exc:
            self.fail(str(exc))
        self.refresh()

    def refresh(self):
        name = '黑方' if self.game.turn == 1 else '白方'
        winner = self.timeout_winner or self.game.winner()
        self.start_button.configure(state='disabled' if self.started or self.replay or self.error or self.initializing or winner else 'normal')
        self.pause_button.configure(state='disabled' if not self.started or self.replay or self.engines or winner or self.error else 'normal', text='继续对局' if self.paused else '暂停计时')
        self.status.configure(text=('黑方获胜' if winner == 1 else '白方获胜') if winner else name + '回合')
        self.phase.configure(text='正在同步悔棋…' if self.undo_waiting else '对手超时' if self.timeout_winner else '对局已暂停' if self.paused else '对手已无合法走法' if winner else '正在加载引擎…' if self.initializing else '引擎正在思考…' if self.game.turn in self.engines else '03 / 选择射箭位置' if self.target else '02 / 选择移动位置' if self.source else '01 / 选择一枚己方棋子')
        self.undo_button.configure(state='normal' if self.undo_count() else 'disabled')
        if not self.started and not winner and not self.replay:
            self.status.configure(text='准备对局')
            self.phase.configure(text='正在加载引擎…' if self.initializing else '双方就绪后，点击“开始对局”')
        if self.replay:
            self.status.configure(text='棋谱回放')
            self.phase.configure(text=f'第 {self.replay_index} / {len(self.replay.moves)} 手 · ' + ('播放中' if self.playing else '已暂停'))
            self.replay_label.configure(text=f'{self.replay_index} / {len(self.replay.moves)}')
            self.seeking = True
            self.progress.set(self.replay_index)
            self.seeking = False
        if not self.error:
            undo_hint = ''
            if self.engines:
                undo_hint = '  ·  引擎对局悔棋撤销两手，思考结束后可用' if all(e.supports_undo for e in self.engines.values()) else '  ·  当前引擎未声明悔棋能力'
            self.feedback.configure(text=f'第 {len(self.game.history)+1} 手  ·  黑方先行  ·  实心点：移动  /  蓝色圈：射箭' + undo_hint, fg=MUTED)
        if self.replay:
            self.feedback.configure(text='棋谱回放 · 拖动进度条跳转 · 从此处继续将重置双方计时', fg=MUTED)
        elif not self.started and not winner and not self.error:
            self.feedback.configure(text='准备对局 · 设置双方玩家、时限和对局信息 · 点击“开始对局”后开始计时', fg=MUTED)
        self.draw()

    def draw(self):
        if not hasattr(self, 'game'):
            return
        cv = self.canvas
        if cv.winfo_width() < 62 or cv.winfo_height() < 62:
            return
        cv.delete('all')
        self.cell = max(1, min((cv.winfo_width()-52)/10, (cv.winfo_height()-52)/10))
        s = self.cell
        self.ox = (cv.winfo_width()-10*s)/2
        self.oy = (cv.winfo_height()-10*s)/2
        board = self.game.preview(self.source, self.target) if self.target else self.game.board
        hints = self.game.arrows(self.source, self.target) if self.target else self.game.rays(self.source) if self.source else set()
        last = self.game.history[-1] if self.game.history else None
        for i in range(10):
            cv.create_text(self.ox+(i+.5)*s, self.oy-15, text=chr(97+i), fill=MUTED, font=('Segoe UI', 10))
            cv.create_text(self.ox-18, self.oy+(i+.5)*s, text=str(10-i), fill=MUTED, font=('Segoe UI', 10))
        self.board_image = render(board, s, hints, self.target is not None, self.target or self.source, last)
        cv.create_image(self.ox, self.oy, image=self.board_image, anchor='nw')
        if last is not None:
            source, target, arrow = [f'{chr(97+c)}{10-r}' for r, c in last]
            y = self.oy+10*s+16
            x = self.ox
            side = '黑方' if len(self.game.history) % 2 else '白方'
            cv.create_text(x, y, text=f'上手 · {side}', anchor='w', fill=MUTED, font=('Segoe UI', 10))
            x += 94
            cv.create_line(x, y, x+25, y, fill=MOVE_COLOR, width=2, arrow='last')
            cv.create_text(x+33, y, text=f'移动 {source} → {target}', anchor='w', fill=MOVE_COLOR, font=('Segoe UI', 10))
            x += 204
            cv.create_line(x, y, x+25, y, fill=SHOT_COLOR, width=2, dash=(4, 3), arrow='last')
            cv.create_text(x+33, y, text=f'射箭 {arrow}', anchor='w', fill=SHOT_COLOR, font=('Segoe UI', 10))

    def tick_clock(self):
        self.clock.update()
        for side, label in self.clock_labels.items():
            value = ceil(self.clock.remaining(side)) if self.clock.limit else self.clock.used[side]
            label.configure(text=display(value), fg=ACCENT if self.clock.active == side else TEXT)
        self.turn_clock.configure(text=f'本手 {display(self.clock.turn_used)}  ·  累计 {display(sum(self.clock.used.values()))}')
        expired = self.clock.expired() if self.clock.active is not None else None
        if expired and not self.timeout_winner:
            self.timeout_winner = -expired
            self.clock.pause()
            self.stop()
            self.write_log(('黑方' if expired == 1 else '白方') + '超时')
            self.refresh()

    def toggle_pause(self):
        if not self.started or self.replay or self.engines or self.timeout_winner or self.game.winner() or self.error:
            return
        self.paused = not self.paused
        self.clock.start(None if self.paused else self.game.turn)
        self.refresh()

    def current_record(self):
        if self.replay is not None:
            return self.replay
        winner = self.timeout_winner or self.game.winner()
        result = self.record_info.result
        if result not in ('先手胜','后手胜'):
            result = '先手胜' if winner==1 else '后手胜' if winner==-1 else result
        return self.record_info.with_moves(self.game.history, result=result)

    def edit_metadata(self):
        record = edit_record(self.root, self.current_record())
        if record is not None:
            if self.replay is not None:
                self.replay = record
            self.record_info = record.with_moves([])

    def save(self):
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON 棋谱（UTF-8）', '*.json')])
        if path:
            try:
                Path(path).write_bytes(self.current_record().to_json_bytes())
            except (OSError, ValueError) as exc:
                messagebox.showerror('保存失败', str(exc))

    def export_text(self):
        record = edit_record(self.root, self.current_record(), competition=True)
        if record is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('比赛棋谱（GB2312）', '*.txt')])
        if path:
            try:
                Path(path).write_bytes(record.to_bytes())
            except (OSError, ValueError) as exc:
                messagebox.showerror('导出失败', str(exc))
                return
            if self.replay is not None:
                self.replay = record
            self.record_info = record.with_moves([])

    def open(self):
        path = filedialog.askopenfilename(filetypes=[('JSON 棋谱（UTF-8）', '*.json'), ('文本棋谱（GB2312 / GBK）', '*.txt')])
        if not path:
            return
        try:
            raw = Path(path).read_bytes()
            record = Record.from_json_bytes(raw) if Path(path).suffix.lower()=='.json' else Record.from_bytes(raw)
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showerror('无法打开棋谱', str(exc))
            return
        self.stop()
        self.paths = {1:'', -1:''}
        self.labels[1].configure(text=record.black)
        self.labels[-1].configure(text=record.white)
        self.replay = record
        self.record_info = record.with_moves([])
        self.replay_index = 0
        self.clock = Clock(0)
        self.timeout_winner = None
        self.paused = False
        self.error = False
        self.source = self.target = None
        self.progress.configure(to=max(1,len(record.moves)))
        self.replay_bar.pack(fill='x', padx=30, pady=(4,10), before=self.feedback)
        self.write_log('打开棋谱：' + Path(path).name)
        self.seek(0)

    def scrub(self, value):
        if not self.seeking and self.replay:
            self.seek(round(float(value)))

    def pause_replay(self):
        self.playing = False
        if self.replay_id is not None:
            self.root.after_cancel(self.replay_id)
            self.replay_id = None
        if hasattr(self, 'play_button'):
            self.play_button.configure(text='播放')

    def seek(self, index, autoplay=False):
        if self.replay is None:
            return
        if not autoplay:
            self.pause_replay()
        index = min(len(self.replay.moves),max(0,index))
        self.replay_index = index
        self.game = self.replay.game_at(index)
        self.source = self.target = None
        self.refresh()

    def play_replay(self):
        if self.replay is None:
            return
        if self.playing:
            self.pause_replay()
            self.refresh()
            return
        if self.replay_index==len(self.replay.moves):
            self.seek(0)
        self.playing = True
        self.play_button.configure(text='暂停')
        self.advance_replay()

    def advance_replay(self):
        self.replay_id = None
        if not self.playing:
            return
        if self.replay_index>=len(self.replay.moves):
            self.pause_replay()
            self.refresh()
            return
        self.seek(self.replay_index+1, autoplay=True)
        self.replay_id = self.root.after(1000,self.advance_replay)

    def continue_game(self):
        self.record_info = self.record_info.with_moves([], result='先(后)手胜')
        self.pause_replay()
        self.replay = None
        self.replay_bar.pack_forget()
        self.clock = Clock(0 if self.time_control.get()=='不限时' else float(self.time_control.get()))
        self.clock.history = [({1:0.0,-1:0.0},0.0) for _ in self.game.history]
        self.started = False
        self.labels[1].configure(text='人类玩家')
        self.labels[-1].configure(text='人类玩家')
        self.refresh()

    def close(self):
        self.stop()
        self.root.destroy()
