# checkersGUINetworked.py
# Tkinter GUI with embedded 1-to-1 TCP networking (uses networkTCP.py).
# Run this directly: python checkersGUINetworked.py
#
# Requirements: checkersEngine.py, networkTCP.py in same directory.

import tkinter as tk
from tkinter import simpledialog, messagebox
from checkersEngine import Board, Player, pos_to_coord, coord_to_pos
import networkTCP
from typing import List, Tuple, Optional

CELL = 70
BOARD_SIZE = 8


# helper: convert board pos tuple -> algebraic e.g. (r,c) -> 'a1'
def pos_to_alg(pos):
    return pos_to_coord(pos)


def alg_to_pos(s):
    return coord_to_pos(s)


class NetworkedCheckersApp:
    def __init__(self, root):
        self.root = root
        root.title("Networked Checkers (TCP)")

        self.board = Board()
        self.canvas = tk.Canvas(root, width=CELL*BOARD_SIZE, height=CELL*BOARD_SIZE, bg='white')
        self.canvas.pack(side=tk.LEFT)
        control = tk.Frame(root)
        control.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        # network controls
        tk.Label(control, text="Networking (TCP 1↔1)").pack()
        tk.Button(control, text="Host (RED, listen)", command=self.host).pack(fill=tk.X)
        tk.Button(control, text="Connect (BLACK)", command=self.connect).pack(fill=tk.X)
        tk.Label(control, text="Port:").pack()
        self.port_var = tk.StringVar(value="5000")
        tk.Entry(control, textvariable=self.port_var).pack()
        tk.Label(control, text="Host IP (for Connect):").pack()
        self.host_var = tk.StringVar(value="localhost")
        tk.Entry(control, textvariable=self.host_var).pack()

        # game controls
        self.turn_label = tk.Label(control, text="Turn: RED")
        self.turn_label.pack(pady=8)
        tk.Button(control, text="Reset Board", command=self.reset_board).pack(fill=tk.X)

        # internals
        self.current_player = Player.RED  # RED on top by convention; host will be RED
        self.local_side: Optional[Player] = None  # which color this instance controls (set after host/connect)
        self.conn = None  # networkTCP.TCPServer or TCPClient
        self.tcp_conn_interface = None  # wrapper for sending (has send method)
        self.selected: Optional[Tuple[int,int]] = None
        self.valid_moves_cache: List[List[Tuple[int,int]]] = []
        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()

        # message queue from networking; processed on main thread via after
        self._network_msg_queue = []
        self.root.after(100, self._pump_network_messages)

    def reset_board(self):
        self.board = Board()
        self.current_player = Player.RED
        self.turn_label.config(text="Turn: RED")
        self.selected = None
        self.valid_moves_cache = []
        self.draw_board()

    def host(self):
        # start server; hosting instance becomes RED (local player RED)
        port = int(self.port_var.get())

        def on_msg(msg):
            # network callback (background thread) -> queue
            self._network_msg_queue.append(msg)

        def on_client_connected():
            self._append_status("Client connected.")
        self.server = networkTCP.TCPServer(port, on_msg, on_client_connected)
        self.tcp_conn_interface = self.server
        self.local_side = Player.RED
        messagebox.showinfo("Hosting", f"Listening on port {port}. You are RED (bottom) and start first.")
        self._append_status("Hosting; waiting for client...")

    def connect(self):
        host = self.host_var.get()
        port = int(self.port_var.get())

        def on_msg(msg):
            self._network_msg_queue.append(msg)

        def on_connect():
            self._append_status("Connected to host.")
        self.client = networkTCP.TCPClient(host, port, on_msg, on_connect)
        self.tcp_conn_interface = self.client
        self.local_side = Player.BLACK
        messagebox.showinfo("Connect", f"Attempting to connect to {host}:{port}. You are BLACK (top).")

    def _append_status(self, text):
        print("[STATUS]", text)

    def _pump_network_messages(self):
        # called on main thread periodically
        while self._network_msg_queue:
            msg = self._network_msg_queue.pop(0)
            try:
                self._handle_network_msg(msg)
            except Exception as e:
                print("Error handling net msg:", e)
        self.root.after(100, self._pump_network_messages)

    def _handle_network_msg(self, raw: str):
        # expects lines like: MOVE a3-b4-c5
        if raw.startswith("MOVE "):
            seq = raw[5:].strip()
            coords = seq.split('-')
            positions = [alg_to_pos(s) for s in coords]
            # apply remote move (must be legal)
            self.board.apply_move(positions)
            # flip turn
            self.current_player = Player.RED if self.current_player == Player.BLACK else Player.BLACK
            self.turn_label.config(text=f"Turn: {self.current_player.name}")
            self.selected = None
            self.valid_moves_cache = []
            self.draw_board()
        elif raw.startswith("MSG "):
            self._append_status("MSG from peer: " + raw[4:])
        else:
            self._append_status("Unknown protocol message: " + raw)

    def send_move_over_network(self, move_positions: List[Tuple[int,int]]):
        if not self.tcp_conn_interface:
            return
        seq = '-'.join(pos_to_alg(p) for p in move_positions)
        self.tcp_conn_interface.send(f"MOVE {seq}")

    # GUI interactions ------------------------------------------------
    def on_click(self, event):
        col = event.x // CELL
        row = event.y // CELL
        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        # convert to internal representation where (0,0) is top-left as in Board
        pos = (row, col)
        # if it's not this player's network (local_side set), restrict moves
        if self.local_side is not None and self.local_side != self.current_player:
            # not our turn
            self._append_status("Not your turn.")
            return
        piece = self.board.get(row, col)
        owner = None
        if piece:
            from checkersEngine import piece_owner
            owner = piece_owner(piece)
        # if something is selected, check if this click corresponds to a legal move target
        if self.selected:
            # find a move in valid_moves_cache that starts with selected and lands on clicked pos
            for m in self.valid_moves_cache:
                if m[0] == self.selected and m[-1] == pos:
                    # apply move
                    self.board.apply_move(m)
                    self.send_move_over_network(m)
                    # promotion handled by core.apply_move
                    # update turn
                    self.current_player = Player.RED if self.current_player == Player.BLACK else Player.BLACK
                    self.turn_label.config(text=f"Turn: {self.current_player.name}")
                    self.selected = None
                    self.valid_moves_cache = []
                    self.draw_board()
                    return
            # if click on another of our pieces, change selection
            if owner == self.current_player:
                self.select_square(pos)
            else:
                # invalid target, deselect
                self.selected = None
                self.valid_moves_cache = []
                self.draw_board()
        else:
            # no selection; if clicked on our piece, select and show valid moves
            if owner == self.current_player:
                self.select_square(pos)

    def select_square(self, pos):
        r, c = pos
        self.selected = pos
        # gather legal moves for current player and filter those starting from selected
        all_moves = self.board.legal_moves(self.current_player)
        self.valid_moves_cache = [m for m in all_moves if m[0] == pos]
        if not self.valid_moves_cache:
            self._append_status("No legal moves from that piece.")
            self.selected = None
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")
        # draw squares
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x0 = c * CELL
                y0 = r * CELL
                x1 = x0 + CELL
                y1 = y0 + CELL
                if (r + c) % 2 == 0:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill="#EEE", outline="")
                else:
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill="#6B8E23", outline="")
        # highlight valid destinations
        for m in self.valid_moves_cache:
            dest = m[-1]
            r, c = dest
            x0 = c*CELL; y0 = r*CELL; x1 = x0+CELL; y1 = y0+CELL
            self.canvas.create_rectangle(x0+4, y0+4, x1-4, y1-4, outline="yellow", width=3)

        # highlight selected
        if self.selected:
            r, c = self.selected
            x0 = c*CELL; y0 = r*CELL; x1 = x0+CELL; y1 = y0+CELL
            self.canvas.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline="cyan", width=3)

        # draw pieces
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                p = self.board.get(r, c)
                if p == None:
                    continue
                if p.name.startswith("RED"):
                    fill = "red"
                elif p.name.startswith("BLACK"):
                    fill = "black"
                else:
                    continue
                cx = c*CELL + CELL//2
                cy = r*CELL + CELL//2
                rad = CELL//2 - 8
                self.canvas.create_oval(cx-rad, cy-rad, cx+rad, cy+rad, fill=fill)
                if p.name.endswith("KING"):
                    self.canvas.create_text(cx, cy, text="K", fill="white", font=("Helvetica", 16, "bold"))


if __name__ == '__main__':
    root = tk.Tk()
    app = NetworkedCheckersApp(root)
    root.mainloop()
