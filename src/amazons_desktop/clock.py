"""Monotonic chess clock. Loading, pause and finished games do not consume time."""
import time

class Clock:
    def __init__(self, limit=900.0, now=time.monotonic):
        self.now = now
        self.limit = limit
        self.used = {1: 0.0, -1: 0.0}
        self.active = None
        self.since = now()
        self.turn_used = 0.0
        self.history = []

    def update(self):
        current = self.now()
        if self.active is not None:
            delta = current - self.since
            self.used[self.active] += delta
            self.turn_used += delta
        self.since = current

    def start(self, side):
        self.update()
        self.active = side

    def pause(self):
        self.start(None)

    def finish_turn(self, next_side):
        self.update()
        self.history.append((dict(self.used), self.turn_used))
        self.turn_used = 0.0
        self.active = next_side

    def undo(self, side, *, resume=True):
        self.pause()
        self.history.pop()
        self.used = dict(self.history[-1][0]) if self.history else {1:0.0, -1:0.0}
        self.turn_used = 0.0
        if resume:
            self.start(side)

    def remaining(self, side):
        return max(0.0, self.limit-self.used[side])

    def expired(self):
        return self.active if self.active is not None and self.limit and self.used[self.active] >= self.limit else None


def display(seconds):
    minutes, seconds = divmod(max(0, int(seconds)), 60)
    return f'{minutes:02}:{seconds:02}'
