from .piece import Piece
from copy import deepcopy

class Board:
    ROWS = 8
    COLS = 8

    def __init__(self):
        self.board = self._create_board()

    def _create_board(self):
        b = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]

        # RED pieces (top)
        for r in range(3):
            for c in range(self.COLS):
                if (r + c) % 2 == 1:
                    b[r][c] = Piece("RED")

        # BLACK pieces (bottom)
        for r in range(5, 8):
            for c in range(self.COLS):
                if (r + c) % 2 == 1:
                    b[r][c] = Piece("BLACK")

        return b

    def get(self, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return self.board[r][c]
        return None

    def set(self, r, c, piece):
        if 0 <= r < 8 and 0 <= c < 8:
            self.board[r][c] = piece

    def remove(self, r, c):
        self.set(r, c, None)

    def clone(self):
        new = Board.__new__(Board)
        new.board = deepcopy(self.board)
        return new
