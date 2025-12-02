class Piece:
    """
    Represents a checkers piece.
    color: "RED" or "BLACK"
    king: bool
    """

    def __init__(self, color: str, king: bool = False):
        self.color = color
        self.king = king

    def make_king(self):
        self.king = True

    def __repr__(self):
        return f"{'K' if self.king else 'P'}-{self.color[0]}"
