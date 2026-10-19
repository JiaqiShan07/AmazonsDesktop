"""UI-independent Amazons rules; positions are (row, column), top-left is (0, 0)."""
from dataclasses import dataclass

Position = tuple[int, int]
Move = tuple[Position, Position, Position]
DIRECTIONS = [(r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c]

@dataclass
class Game:
    def __init__(self):
        self.board = [[0] * 10 for _ in range(10)]
        for r, c in [(3, 0), (0, 3), (0, 6), (3, 9)]:
            self.board[r][c] = -1
        for r, c in [(6, 0), (9, 3), (9, 6), (6, 9)]:
            self.board[r][c] = 1
        self.turn = 1
        self.history: list[Move] = []

    def rays(self, source: Position) -> set[Position]:
        result = set()
        for dr, dc in DIRECTIONS:
            r, c = source
            r, c = r + dr, c + dc
            while 0 <= r < 10 and 0 <= c < 10 and self.board[r][c] == 0:
                result.add((r, c))
                r, c = r + dr, c + dc
        return result

    def preview(self, source: Position, target: Position):
        board = [row[:] for row in self.board]
        board[source[0]][source[1]] = 0
        board[target[0]][target[1]] = self.turn
        return board

    def arrows(self, source: Position, target: Position) -> set[Position]:
        preview = Game()
        preview.board = self.preview(source, target)
        return preview.rays(target)

    def apply(self, move: Move):
        source, target, arrow = move
        if any(not (0 <= r < 10 and 0 <= c < 10) for r, c in move):
            raise ValueError('坐标超出棋盘')
        if self.board[source[0]][source[1]] != self.turn or target not in self.rays(source):
            raise ValueError('棋子移动不合法')
        if arrow not in self.arrows(source, target):
            raise ValueError('射箭不合法')
        self.board = self.preview(source, target)
        self.board[arrow[0]][arrow[1]] = 2
        self.history.append(move)
        self.turn = -self.turn

    def winner(self):
        if any(self.rays((r, c)) for r in range(10) for c in range(10) if self.board[r][c] == self.turn):
            return None
        return -self.turn

    def undo(self):
        source, target, arrow = self.history.pop()
        self.turn = -self.turn
        self.board[arrow[0]][arrow[1]] = 0
        self.board[target[0]][target[1]] = 0
        self.board[source[0]][source[1]] = self.turn


def encode(move: Move) -> str:
    return ''.join(chr(65 + v) for r, c in move for v in (c, r))


def decode(text: str) -> Move:
    if len(text) != 6 or any(c < 'A' or c > 'J' for c in text):
        raise ValueError('引擎走法必须为 A–J 的六个坐标字符')
    return tuple((ord(text[i+1])-65, ord(text[i])-65) for i in (0, 2, 4))
