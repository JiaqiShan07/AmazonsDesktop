"""Asynchronous SAU process adapter. Each session owns its process and streams."""
import subprocess
import threading
from pathlib import Path

class Engine:
    def __init__(self, path, events, token, color):
        self.events, self.token, self.color = events, token, color
        self.closed = False
        self.supports_undo = False
        self.completed_turns = 0
        self.process = subprocess.Popen([str(path)], cwd=str(Path(path).parent), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), bufsize=1)
        threading.Thread(target=self.read, args=(self.process.stdout, 'output'), daemon=True).start()
        threading.Thread(target=self.read, args=(self.process.stderr, 'diagnostic'), daemon=True).start()
        self.send('name?')

    def read(self, stream, kind):
        try:
            for line in stream:
                self.events.put((self.token, self.color, kind, line.strip()))
        finally:
            if kind == 'output' and not self.closed:
                self.events.put((self.token, self.color, 'error', '引擎已退出，请查看诊断并重新开始'))
            stream.close()

    def send(self, command):
        if self.closed:
            return
        self.process.stdin.write(command + '\n')
        self.process.stdin.flush()

    def undo(self, turns: int):
        """Undo completed plies on an idle, extension-capable engine; await ready."""
        self.send(f'undo {turns}')

    def go(self):
        """Search the current position after undo."""
        self.send('go')

    def close(self):
        self.closed = True
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        self.process.stdin.close()
