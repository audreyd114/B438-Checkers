import tkinter as tk
from tkinter import messagebox
from game.game_logic import Game

CELL = 70
LIGHT = "#F0D9B5"
DARK = "#B58863"
RED_COLOR = "#C62828"
BLACK_COLOR = "#222222"
HIGHLIGHT_FILL = "#8BC34A"   # green for legal dest marker
HIGHLIGHT_BORDER = "#FFD54F" # outline for selected

class CheckersUI:
    def __init__(self, root):
        self.root = root
        root.title("Checkers (UI & Logic)")

        self.game = Game()
        self.selected = None            # selected piece (r,c)
        self.must_continue = False      # whether a multi-capture continuation is required
        self.continue_pos = None

        # main canvas
        self.canvas = tk.Canvas(root, width=8*CELL, height=8*CELL)
        self.canvas.pack(side=tk.LEFT)
        self.canvas.bind("<Button-1>", self.on_click)

        # right-side controls
        control = tk.Frame(root)
        control.pack(side=tk.RIGHT, fill=tk.Y, padx=8, pady=8)

        self.turn_label = tk.Label(control, text=f"Turn: {self.game.turn}", font=("Arial", 14))
        self.turn_label.pack(pady=(4,8))

        tk.Button(control, text="Restart", command=self.restart).pack(pady=6, fill=tk.X)

        # Move history listbox
        history_frame = tk.LabelFrame(control, text="Move History", padx=6, pady=6)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(8,0))
        self.move_listbox = tk.Listbox(history_frame, width=28, height=20)
        self.move_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.move_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.move_listbox.config(yscrollcommand=sb.set)

        self.status = tk.Label(control, text="", font=("Arial", 11), fg="red")
        self.status.pack(pady=(8,0))

        self.draw_board()

    # --- Networking hook ---
    def on_move_attempt(self, start, end):
        """
        NETWORK HOOK 
        - Currently this applies the move immediately (local logic).
        -cna/should be replaced to:
            1) send the move to server
            2) wait server validation/confirmation
            3) apply the confirmed move (or show error)
    keep it on_move_attempt(start:(r,c), end:(r,c))
        """
        # Default local behavior: apply immediately
        success, info = self.game.move_piece(start, end)
        return success, info

    # --- Actions ---
    def restart(self):
        self.game.reset()
        self.selected = None
        self.must_continue = False
        self.continue_pos = None
        self.move_listbox.delete(0, tk.END)
        self.turn_label.config(text=f"Turn: {self.game.turn}")
        self.status.config(text="")
        self.draw_board()

    def on_click(self, event):
        col = event.x // CELL
        row = event.y // CELL

        if row < 0 or row > 7 or col < 0 or col > 7:
            return

        # enforce multi-capture continuation
        if self.must_continue and (row, col) != self.continue_pos:
            self.status.config(text="You must continue capturing with the same piece.")
            return

        piece = self.game.board.get(row, col)

        # selecting own piece
        if piece is not None and piece.color == self.game.turn:
            self.selected = (row, col)
            self.status.config(text="")
            self.draw_board()
            return

        # attempting a move when a piece is selected
        if self.selected:
            start = self.selected
            end = (row, col)

            # If end is not one of valid moves, show error
            valid = self.game.get_valid_moves(start[0], start[1])
            if end not in valid:
                self.status.config(text="Invalid move.")
                return

            # Call network hook (you can replace this)
            success, info = self.on_move_attempt(start, end)
            if not success:
                self.status.config(text=f"Move rejected: {info}")
                return

            # If successful locally (or after server confirmation), finalize UI changes:
            # ( game.move_piece already applied the move in default on_move_attempt)
            # Add to move history
            self.append_move_history(start, end, captured=valid[end])

            # Multi-capture required?
            if isinstance(info, dict) and info.get("continue"):
                self.must_continue = True
                self.continue_pos = info.get("pos")
                self.selected = self.continue_pos
                self.status.config(text="Continue capturing with same piece.")
            else:
                self.must_continue = False
                self.continue_pos = None
                self.selected = None
                self.status.config(text="")
                self.turn_label.config(text=f"Turn: {self.game.turn}")

            self.draw_board()

            # winner check (simple)
            if self.game.winner:
                messagebox.showinfo("Game Over", f"{self.game.winner} wins!")
                self.turn_label.config(text=f"Winner: {self.game.winner}")

    # --- UI helpers ---
    def append_move_history(self, start, end, captured):
        # Human-friendly move text: "RED: (r,c) -> (r,c) [captures: ...]"
        player = self.game.turn  # note: turn was switched inside move_piece when applicable
        # Actually, player label should be the player who made the move determine from captured or prior state:
        # We can imagine last player as opposite of current turn if turn switched but safer: determine color from dest
        dest_piece = self.game.board.get(end[0], end[1])
        made_by = dest_piece.color if dest_piece else player
        cap_text = ""
        if captured:
            cap_text = f" captures {len(captured)}"
        txt = f"{made_by}: {start} -> {end}{cap_text}"
        self.move_listbox.insert(tk.END, txt)
        # auto-scroll
        self.move_listbox.yview_moveto(1.0)

    def draw_board(self):
        self.canvas.delete("all")

        # draw squares
        for r in range(8):
            for c in range(8):
                color = LIGHT if (r + c) % 2 == 0 else DARK
                x1, y1 = c*CELL, r*CELL
                x2, y2 = x1 + CELL, y1 + CELL
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        # draw pieces
        for r in range(8):
            for c in range(8):
                piece = self.game.board.get(r, c)
                if piece:
                    self.draw_piece(r, c, piece)

        # selected piece outline
        if self.selected:
            sr, sc = self.selected
            x1 = sc*CELL + 4
            y1 = sr*CELL + 4
            x2 = x1 + CELL - 8
            y2 = y1 + CELL - 8
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=HIGHLIGHT_BORDER, width=3)

            # show valid moves for selected piece (green markers)
            moves = self.game.get_valid_moves(sr, sc)
            for (mr, mc), captured in moves.items():
                cx = mc*CELL + CELL//2
                cy = mr*CELL + CELL//2
                rsize = CELL//6
                self.canvas.create_oval(cx - rsize, cy - rsize, cx + rsize, cy + rsize,
                                        fill=HIGHLIGHT_FILL, outline="")

    def draw_piece(self, r, c, piece):
        x = c*CELL + CELL//2
        y = r*CELL + CELL//2
        radius = CELL//2 - 12
        color = RED_COLOR if piece.color == "RED" else BLACK_COLOR
        self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill=color, outline="black")
        if piece.king:
            self.canvas.create_text(x, y, text="K", fill="#FFD54F", font=("Arial", 18, "bold"))

def main():
    root = tk.Tk()
    ui = CheckersUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
