# Full American Checkers (English Draughts) rules implementation.
# 8x8 board, dark squares playable where (r + c) % 2 == 1
# Two players: RED and BLACK. RED starts at top moving "down" (increasing row index)
# Men move diagonally forward 1 square; kings move diagonally forward/back any distance? (American kings move 1 as well)
# Captures are mandatory. When multiple capture sequences are available, this implementation can be configured
# to require the capture that captures the most pieces ("max_capture=True") or accept any capturing move.
# Promotion: a man becomes a king when it lands on the farthest row (opponent's back row) after a move or jump.
# Multiple jumps: after a capture, if further captures are available by the same piece, they must be continued.

from enum import Enum, auto
from copy import deepcopy
from typing import List, Tuple, Optional

BOARD_SIZE = 8


class Player(Enum):
    RED = auto()   # starts at top and moves down (row increasing)
    BLACK = auto()  # starts at bottom and moves up (row decreasing)


class Piece(Enum):
    EMPTY = 0
    RED = 1
    RED_KING = 2
    BLACK = 3
    BLACK_KING = 4


# Utility helpers
def is_dark_square(r: int, c: int) -> bool:
    return (r + c) % 2 == 1


def piece_owner(piece: Piece) -> Optional[Player]:
    if piece in (Piece.RED, Piece.RED_KING):
        return Player.RED
    if piece in (Piece.BLACK, Piece.BLACK_KING):
        return Player.BLACK
    return None


def is_king(piece: Piece) -> bool:
    return piece in (Piece.RED_KING, Piece.BLACK_KING)


def promote(piece: Piece, row: int) -> Piece:
    if piece == Piece.RED and row == 0:
        return Piece.RED_KING
    if piece == Piece.BLACK and row == BOARD_SIZE - 1:
        return Piece.BLACK_KING
    return piece

# Move representation:
# A move is represented as a list of board coordinates (r,c) visited by the moving piece.
# For a single non-capturing move: [(r1,c1), (r2,c2)]
# For captures (including multi-jumps): [(r1,c1), (r2,c2), (r3,c3), ...]
# Where intermediate steps indicate landing squares after each jump.


class Board:
    def __init__(self):
        self.grid = [[Piece.EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.setup_initial()

    def setup_initial(self):
        # Place RED on rows 5-7 on dark squares, BLACK on rows 0-2
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if not is_dark_square(r, c):
                    self.grid[r][c] = Piece.EMPTY
                    continue
                if r <= 2:
                    self.grid[r][c] = Piece.BLACK
                elif r >= 5:
                    self.grid[r][c] = Piece.RED
                else:
                    self.grid[r][c] = Piece.EMPTY

    def clone(self) -> 'Board':
        b = Board.__new__(Board)
        b.grid = deepcopy(self.grid)
        return b

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def get(self, r: int, c: int) -> Piece:
        return self.grid[r][c]

    def set(self, r: int, c: int, val: Piece):
        self.grid[r][c] = val

    def render(self) -> str:
        # simple ASCII rendering (rows 0..7 top to bottom)
        lines = []
        for r in range(BOARD_SIZE):
            row = []
            for c in range(BOARD_SIZE):
                p = self.grid[r][c]
                if p == Piece.EMPTY:
                    char = '.' if is_dark_square(r, c) else ' '
                elif p == Piece.RED:
                    char = 'r'
                elif p == Piece.RED_KING:
                    char = 'R'
                elif p == Piece.BLACK:
                    char = 'b'
                else:
                    char = 'B'
                row.append(char)
            lines.append(' '.join(row))
        return '.join(lines)'


# Public API
def legal_moves(self, player: Player, max_capture: bool = True) -> List[List[Tuple[int, int]]]:
    # Return a list of legal moves for player.
    # If max_capture=True then if any capture moves exist, only return capture sequences that capture the maximum
    # number of opponent pieces (this matches stricter tournament variants). If False, return all capturing sequences
    # (still respecting mandatory capture rule), or all quiet moves if no captures are available.

    captures = []  # list of capture sequences (list of squares)
    quiets = []    # non-capturing single-step moves

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = self.get(r, c)
            if piece_owner(p) != player:
                continue
            # get captures from this piece
            caps = self._find_captures_from(r, c)
            captures.extend(caps)
            if not caps:
                # if no captures from this piece, consider normal moves
                steps = self._find_simple_moves_from(r, c)
                quiets.extend(steps)

    if captures:
        if max_capture:
            # filter to only those with maximal capture length
            maxlen = max(len(m)-1 for m in captures)  # number of jumps equals len-1
            best = [m for m in captures if (len(m)-1) == maxlen]
            return best
        return captures
    return quiets


def apply_move(self, move: List[Tuple[int, int]]):
    # Apply the move to the board. Assumes move is legal. Mutates board.
    # Handles captures and promotion.

    if not move or len(move) < 2:
        raise ValueError("Move must contain at least a source and destination")
    src_r, src_c = move[0]
    piece = self.get(src_r, src_c)
    if piece == Piece.EMPTY:
        raise ValueError("No piece at source")
    self.set(src_r, src_c, Piece.EMPTY)
    # If it's a capturing move, intermediate landings indicate jumps
    for idx in range(1, len(move)):
        dst_r, dst_c = move[idx]
        # if jumped over a piece, remove it
        if abs(dst_r - src_r) == 2 and abs(dst_c - src_c) == 2:
            mid_r = (dst_r + src_r) // 2
            mid_c = (dst_c + src_c) // 2
            self.set(mid_r, mid_c, Piece.EMPTY)
        src_r, src_c = dst_r, dst_c
    # place piece at final location, possibly promoted
    piece = promote(piece, src_r)
    self.set(src_r, src_c, piece)


def is_game_over(self) -> bool:
    # game over when a player has no pieces or no legal moves
    red_exists = any(piece_owner(self.get(r, c)) == Player.RED for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))
    black_exists = any(piece_owner(self.get(r, c)) == Player.BLACK for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))
    if not red_exists or not black_exists:
        return True
    # no legal moves
    if not self.legal_moves(Player.RED) or not self.legal_moves(Player.BLACK):
        return True
    return False


def winner(self) -> Optional[Player]:
    # return winner if game over, or None for draw/ongoing
    red_exists = any(piece_owner(self.get(r, c)) == Player.RED for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))
    black_exists = any(piece_owner(self.get(r, c)) == Player.BLACK for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))
    if not red_exists and black_exists:
        return Player.BLACK
    if not black_exists and red_exists:
        return Player.RED
    # If both have pieces but no moves, the player with moves wins; if both have no moves, it's a draw.
    red_moves = bool(self.legal_moves(Player.RED))
    black_moves = bool(self.legal_moves(Player.BLACK))
    if red_moves and not black_moves:
        return Player.RED
    if black_moves and not red_moves:
        return Player.BLACK
    return None


# Internals
def _find_simple_moves_from(self, r: int, c: int) -> List[List[Tuple[int, int]]]:
    piece = self.get(r, c)
    moves = []
    if piece == Piece.EMPTY:
        return moves
    owner = piece_owner(piece)
    # movement directions: for RED men, down (r+1); for BLACK men, up (r-1).
    steps = []
    if is_king(piece):
        steps = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        if owner == Player.RED:
            steps = [(-1, -1), (-1, 1)]
        else:
            steps = [(1, -1), (1, 1)]
    for dr, dc in steps:
        nr, nc = r + dr, c + dc
        if not self.in_bounds(nr, nc):
            continue
        if self.get(nr, nc) == Piece.EMPTY:
            moves.append([(r, c), (nr, nc)])
    return moves


def _find_captures_from(self, r: int, c: int) -> List[List[Tuple[int, int]]]:
    # Find all capture sequences starting from (r,c) for the piece on that square.
    # Returns list of sequences, each sequence is list of positions visited.
    # Uses DFS to explore multi-jump sequences. Does not modify the real board; works on a temporary copy.

    piece = self.get(r, c)
    if piece == Piece.EMPTY:
        return []
    owner = piece_owner(piece)

    results = []

    def dfs(board_snapshot: Board, cur_r: int, cur_c: int, path: List[Tuple[int, int]]):
        moved = False
        p = board_snapshot.get(cur_r, cur_c)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            mid_r = cur_r + dr
            mid_c = cur_c + dc
            land_r = cur_r + 2*dr
            land_c = cur_c + 2*dc
            if not (board_snapshot.in_bounds(mid_r, mid_c) and board_snapshot.in_bounds(land_r, land_c)):
                continue
            mid_piece = board_snapshot.get(mid_r, mid_c)
            land_piece = board_snapshot.get(land_r, land_c)
            if land_piece != Piece.EMPTY:
                continue
            if piece_owner(mid_piece) is None or piece_owner(mid_piece) == owner:
                continue
            # Movement/capture legality for men: men (non-kings) may only capture forward in American checkers.
            if not is_king(p):
                if owner == Player.RED and dr > 0:
                    continue
                if owner == Player.BLACK and dr < 0:
                    continue
            # perform capture on snapshot
            new_snapshot = board_snapshot.clone()
            # remove captured
            new_snapshot.set(mid_r, mid_c, Piece.EMPTY)
            # move piece
            new_snapshot.set(cur_r, cur_c, Piece.EMPTY)
            new_snapshot.set(land_r, land_c, p)
            # promotion only after finishing the entire move in American checkers
            dfs(new_snapshot, land_r, land_c, path + [(land_r, land_c)])
            moved = True
        if not moved:
            # no further captures; path is complete
            if len(path) > 1:
                results.append(path)

    # initial call: path starts with source square
    dfs(self.clone(), r, c, [(r, c)])
    # perform promotion for final landing squares in results
    return results


# Small helper: convert algebraic-style coordinates to tuple and back
def coord_to_pos(s: str) -> Tuple[int, int]:
    col = ord(s[0].lower()) - ord('a')
    row = int(s[1]) - 1
    r = BOARD_SIZE - 1 - row
    c = col
    return (r, c)


def pos_to_coord(pos: Tuple[int, int]) -> str:
    r, c = pos
    row1 = BOARD_SIZE - r
    col = chr(ord('a') + c)
    return f"{col}{row1}"


# Example quick-play demonstration functions (not networked):
if __name__ == '__main__':
    b = Board()
    print("Initial board:")
    print(b.render())
    print('Red legal moves (sample, showing count):', len(b.legal_moves(Player.RED)))
    # Example: make a known opening move for red e.g., move a red piece forward if available
    moves = b.legal_moves(Player.RED)
    if moves:
        print('Example one move sequence (first legal move):', moves[0])
    b.apply_move(moves[0])
    print('Board after applying move:')
    print(b.render())
