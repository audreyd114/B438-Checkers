from .board import Board
from .piece import Piece

class Game:
    def __init__(self):
        self.board = Board()
        self.turn = "RED"
        self.winner = None

    def reset(self):
        self.board = Board()
        self.turn = "RED"
        self.winner = None

    def in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def get_all_moves(self, color):
        moves = {}
        for r in range(8):
            for c in range(8):
                p = self.board.get(r, c)
                if p and p.color == color:
                    legal = self.get_valid_moves(r, c)
                    if legal:
                        moves[(r, c)] = legal
        return moves

    def get_valid_moves(self, r, c):
        p = self.board.get(r, c)
        if p is None:
            return {}

        simple = {}
        jumps = {}

        if p.king:
            dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        else:
            step = 1 if p.color == "RED" else -1
            dirs = [(step,-1),(step,1)]

        # Simple moves
        for dr,dc in dirs:
            nr,nc = r+dr, c+dc
            if self.in_bounds(nr,nc) and self.board.get(nr,nc) is None:
                simple[(nr,nc)] = []

        # Jump moves (multi-jump)
        def dfs(sr, sc, board_state, captured):
            found = False
            piece = board_state.get(sr, sc)

            if piece.king:
                jdirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
            else:
                step = 1 if piece.color == "RED" else -1
                jdirs = [(step,-1),(step,1)]

            for dr,dc in jdirs:
                mr,mc = sr+dr, sc+dc
                lr,lc = sr+2*dr, sc+2*dc

                if not (self.in_bounds(mr,mc) and self.in_bounds(lr,lc)):
                    continue

                mid = board_state.get(mr,mc)
                land = board_state.get(lr,lc)

                if mid and mid.color != piece.color and land is None:
                    new_board = board_state.clone()
                    new_board.set(lr, lc, new_board.get(sr, sc))
                    new_board.remove(sr, sc)
                    new_board.remove(mr, mc)

                    new_captured = captured + [(mr,mc)]

                    more = dfs(lr, lc, new_board, new_captured)
                    if not more:
                        jumps.setdefault((lr,lc), []).append(new_captured)

                    found = True

            return found

        dfs(r, c, self.board.clone(), [])

        if jumps:
            result = {}
            for dest, seqs in jumps.items():
                best = max(seqs, key=len)
                result[dest] = best
            return result

        return simple

    def move_piece(self, start, end):
        sr,sc = start
        er,ec = end

        p = self.board.get(sr,sc)
        if p is None or p.color != self.turn:
            return False, "Invalid piece"

        valid = self.get_valid_moves(sr,sc)
        if end not in valid:
            return False, "Invalid move"

        captured = valid[end]

        self.board.set(er,ec,p)
        self.board.remove(sr,sc)

        # Remove captured pieces
        for (cr,cc) in captured:
            self.board.remove(cr,cc)

        # Kinging
        if not p.king:
            if p.color == "RED" and er == 7:
                p.make_king()
            if p.color == "BLACK" and er == 0:
                p.make_king()

        # Multi-jump?
        if captured:
            more = self.get_valid_moves(er, ec)
            if any(more.values()):
                # require UI to continue with same piece
                return True, {"continue": True, "pos": (er,ec)}

        self.turn = "BLACK" if self.turn == "RED" else "RED"
        # optional: update winner check here if desired
        return True, {"continue": False}
