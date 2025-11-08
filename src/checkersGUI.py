import tkinter as tk
from checkersEngine import Board, Player

CELL_SIZE = 80
BOARD_SIZE = 8


class CheckersGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Checkers - Local Play")

        self.board = Board()
        self.current_player = Player.RED
        self.selected = None
        self.legal_moves = []

        self.canvas = tk.Canvas(root, width=CELL_SIZE*BOARD_SIZE, height=CELL_SIZE*BOARD_SIZE)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        self.draw_board()
        self.draw_pieces()

    def draw_board(self):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = '#B58863' if (r+c)%2 else '#F0D9B5'
                self.canvas.create_rectangle(c*CELL_SIZE, r*CELL_SIZE,
                                             (c+1)*CELL_SIZE, (r+1)*CELL_SIZE,
                                             fill=color, outline='')

    def draw_pieces(self):
        self.canvas.delete("piece")
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board.board[r][c]
                if p.value != 0:
                    color = 'red' if p.value in (1,2) else 'black'
                    x = c*CELL_SIZE + CELL_SIZE//2
                    y = r*CELL_SIZE + CELL_SIZE//2
                    self.canvas.create_oval(x-30, y-30, x+30, y+30, fill=color, tags="piece")
                    if p.value in (2,4):
                        self.canvas.create_text(x, y, text='K', fill='white', font=('Arial', 20, 'bold'), tags="piece")

    def on_click(self, event):
        r = event.y // CELL_SIZE
        c = event.x // CELL_SIZE

        if self.selected is None:
            # Select piece if it belongs to player
            piece_moves = self.board.legal_moves(self.current_player, max_capture=True)
            moves_from = [m[0] for m in piece_moves]
            if (r, c) in moves_from:
                self.selected = (r, c)
                self.legal_moves = [m for m in piece_moves if m[0] == (r, c)]
                self.highlight_moves()
        else:
            # Attempt move
            for move in self.legal_moves:
                if move[-1] == (r, c):
                    self.board.apply_move(move)
                    self.selected = None
                    self.legal_moves = []
                    self.switch_player()
                    self.draw_board()
                    self.draw_pieces()
                    return
            # If invalid move, reset selection
            self.selected = None
            self.legal_moves = []
            self.draw_board()
            self.draw_pieces()

    def highlight_moves(self):
        self.draw_board()
        self.draw_pieces()
        for m in self.legal_moves:
            r, c = m[-1]
            self.canvas.create_rectangle(c*CELL_SIZE, r*CELL_SIZE,
                                         (c+1)*CELL_SIZE, (r+1)*CELL_SIZE,
                                         outline='yellow', width=3)

    def switch_player(self):
        self.current_player = Player.BLACK if self.current_player == Player.RED else Player.RED
        if self.board.is_game_over():
            winner = self.board.winner()
            msg = f"Winner: {winner.name if winner else 'Draw'}"
            tk.messagebox.showinfo("Game Over", msg)


if __name__ == '__main__':
    root = tk.Tk()
    app = CheckersGUI(root)
    root.mainloop()
