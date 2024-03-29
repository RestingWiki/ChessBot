"""
1. Game state
2. Valid moves
3. Logging (uses chess algebraic notation)
"""
from nguyenpanda.swan import Color
import time

# Maps chess ranks to row indices
ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
               "5": 3, "6": 2, "7": 1, "8": 0}

# Reverse mapping from row indices to chess ranks
rowsToRanks = {v: k for k, v in ranksToRows.items()}

# Maps chess files to column indices
filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
               "e": 4, "f": 5, "g": 6, "h": 7}

# Reverse mapping from column indices to chess files
colsToFiles = {v: k for k, v in filesToCols.items()}

# Piece move direction
diagonalDirection = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Bishop
straightDirection = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Rook
omniDirection = diagonalDirection + straightDirection  # King, Queen
knightDirections = [
    (-2, -1), (-2, 1),  # Up left, Up right
    (-1, -2), (-1, 2),  # Left up, Right up
    (1, -2), (1, 2),  # Left down, Right down
    (2, -1), (2, 1)  # Down left, Down right
]  # Knight

# Mapping from each piece to the direction they can move, Knight, Bishop, Rook, Queen, King
mapDirection = {'N': knightDirections, 'B': diagonalDirection,
                'R': straightDirection, 'Q': omniDirection,
                'K': omniDirection}


def isInBoard(r, c):
    return 0 <= r <= 7 and 0 <= c <= 7

class GameState:
    def __init__(self):
        self.board = [
            ["bR", "--", "--", "--", "bK", "--", "--", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.whiteToMove = True
        self.moveLog = []
        self.moveFunctions = {'p': self.__getPawnMoves, 'R': self.__getRookMoves,
                              'N': self.__getKnightMoves, 'B': self.__getBishopMoves,
                              'Q': self.__getQueenMoves, 'K': self.__getKingMoves}

        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.isInCheck = False
        self.pins = []
        self.checks = []
        self.checkMate = False
        self.staleMate = False

    '''
    Take a Move s a parameter and  execute it( this will not work for castling, en-passant, promotion)
    '''

    def makeMove(self, move):
        if move.pieceMoved != "--":
            self.board[move.startRow][move.startCol] = "--"
            self.board[move.endRow][move.endCol] = move.pieceMoved
            self.moveLog.append(move)

            # Update the king location
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.endRow, move.endCol)
            elif move.pieceMoved == "bK":
                self.blackKingLocation = (move.endRow, move.endCol)

            # Switch turn
            self.whiteToMove = not self.whiteToMove
        else:
            pass

    def undoMove(self):
        if len(self.moveLog) != 0:
            lastMove = self.moveLog.pop()
            self.board[lastMove.startRow][lastMove.startCol] = lastMove.pieceMoved
            self.board[lastMove.endRow][lastMove.endCol] = lastMove.pieceCaptured
            self.whiteToMove = not self.whiteToMove

            if lastMove.pieceMoved == "wK":
                self.whiteKingLocation = (lastMove.startRow, lastMove.startCol)
            elif lastMove.pieceMoved == "bK":
                self.blackKingLocation = (lastMove.startRow, lastMove.startCol)

    def getValidMoves(self):
        moves = []
        self.isInCheck, self.pins, self.checks = self.__inCheckAnhKhoa()
        t0 = time.time()
        if self.whiteToMove:
            Kr, Kc = self.whiteKingLocation
        else:
            Kr, Kc = self.blackKingLocation
        if self.isInCheck:
            if len(self.checks) == 1:  # Only 1 check, block or move the king
                moves = self.getAllPossibleMoves()
                # Move a square between the checking enemy and the king
                check = self.checks[0]
                checkRow, checkCol, _, _ = check
                pieceChecking = self.board[checkRow][checkCol]

                validSquares = []  # Square that the piece can move to
                # If knight, must capture the knight or move the king
                if pieceChecking[1] == 'N':
                    validSquares = [(checkRow, checkCol)]
                # If not then try to block
                else:
                    for i in range(1, 8):
                        validSquare = (Kr + check[2] * i, Kc + check[3] * i)
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol:
                            break

                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].pieceMoved[1] != 'K':  # If this move doesn't move the king, it has to stop the check
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else:  # Double check -> King is forced to move
                self.__getKingMoves(Kr, Kc, moves)
        else:
            moves = self.getAllPossibleMoves()
        t1 = time.time()
        print(t1 - t0)
        print("length of moves:" + str(len(moves)))
        if len(moves) == 0:
            if self.isInCheck:
                self.checkMate = True
                print("Checkmate!")
            else:
                self.StaleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        return moves

    """
    # Determine if the current player is in check, unused cuz inefficient
    """

    def __inCheck(self):
        if self.whiteToMove:
            return self.__squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.__squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    """
    # Determine if the enemy can attack the square
    # This does not modify the current player's turn
    """

    def __squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove  # Switch to opponent turn
        oppoMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove  # Switch the turn back

        for move in oppoMoves:
            if move.endRow == r and move.endCol == c:
                return True

        return False

    """
    # Return all possible pins and check 
    # Actually came up with this one myself (minus the pins), fined tuned by Eddie Sharick
    """

    def __inCheckAnhKhoa(self):
        # check from the white King position
        # 1. Knights attack
        # 2. Check Pawn attack
        # 3. Rook/Bishop/Queen attack
        isInCheck = False
        pins = []
        checks = []

        if self.whiteToMove:
            allyColor = 'w'
            enemyColor = 'b'
            Kr, Kc = self.whiteKingLocation
        else:
            allyColor = 'b'
            enemyColor = 'w'
            Kr, Kc = self.blackKingLocation

        # Track enemy's Pawn, Bishop, Rook, Queen, King
        for i in range(0, 8):  # Index based retrieval allows for checking diagonal/horizontal moves separately
            d = omniDirection[i]
            possiblePin = ()
            for j in range(1, 8):
                endRow = Kr + j * d[0]
                endCol = Kc + j * d[1]

                if isInBoard(endRow, endCol):
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != 'K':
                        if possiblePin == ():
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else:  # 2nd ally piece, no longer possible to be pinned/check in this direction
                            break

                    elif endPiece[0] == enemyColor:
                        pieceType = endPiece[1]
                        # If there's an enemy piece in this direction, check if the enemy can give a check
                        # There are 5 cases, I think...
                        # 1.) Bishop - diagonal
                        # 2.) Rook   - horizontal
                        # 3.) Pawn
                        #   3.a Black Pawn  (-1,-1) or (-1,-1)
                        #   3.a White Pawn  (1,-1) or (1,1)
                        # 4.) King  - There's another king adjacent or j = 1
                        # 5.) Queen - If the King can see the queen then it can be checked from that direction
                        if (0 <= i <= 3 and pieceType == 'B') or \
                                (4 <= i <= 7 and pieceType == 'R') or \
                                (j == 1 and pieceType == 'p' and enemyColor == 'b' and 2 <= i <= 3) or \
                                (j == 1 and pieceType == 'p' and enemyColor == 'w' and 0 <= i <= 1) or \
                                (pieceType == 'K' and j == 1) or \
                                (pieceType == 'Q'):

                            if possiblePin == ():  # No blocking piece
                                isInCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else:
                                pins.append(possiblePin)
                                break
                        else:  # Enemy cannot check the king
                            break
                else:  # out of the board
                    break

        # Track the enemy's Knight
        for d in knightDirections:
            endRow = Kr + d[0]
            endCol = Kc + d[1]
            if isInBoard(endRow, endCol):
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == 'N':
                    isInCheck = True
                    checks.append((endRow, endCol, d[0], d[1]))

        return isInCheck, pins, checks

    """
    # Generate all the possible moves for the Pawns
    # White pawns can capture to the direction that it is being pinned
    # Or advance forward/ away from a vertical pin
    # 
    """

    def __getPawnMoves(self, r: int, c: int, moves):
        piecePined = False
        pinDirection = ()

        # Looks for pin information
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePined = True
                pinDirection = self.pins[i][2:3]
                self.pins.remove(self.pins[i])
                break

        # White pawn to move
        if self.whiteToMove:
            if r == 0:
                return

            if self.board[r - 1][c] == "--":  # 1 square pawn advance
                if not piecePined or pinDirection == (-1, 0) or pinDirection == (1, 0):
                    moves.append(Move((r, c), (r - 1, c), self.board))
                    if r == 6 and self.board[r - 2][c] == "--":  # 2 square pawn move advance
                        moves.append(Move((r, c), (r - 2, c), self.board))

            # Capture to the left
            if c - 1 >= 0:
                if self.board[r - 1][c - 1][0] == "b":  # Enemy piece
                    if not piecePined or pinDirection == (-1, -1):
                        moves.append(Move((r, c), (r - 1, c - 1), self.board))

            # Capture to the right
            if c + 1 <= 7:
                if self.board[r - 1][c + 1][0] == "b":  # Enemy piece
                    if not piecePined or pinDirection == (-1, 1):
                        moves.append(Move((r, c), (r - 1, c + 1), self.board))

        # Black pawn to move
        if not self.whiteToMove:
            if r == 7:
                return

            if self.board[r + 1][c] == "--":  # 1 square pawn advance
                if not piecePined or pinDirection == (1, 0) or pinDirection == (-1, 0):
                    moves.append(Move((r, c), (r + 1, c), self.board))
                    if r == 1 and self.board[r + 2][c] == "--":
                        moves.append(Move((r, c), (r + 2, c), self.board))

            # Capture to the left
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == "w":  # Enemy piece
                    if not piecePined or pinDirection == (1, -1):
                        moves.append(Move((r, c), (r + 1, c - 1), self.board))

            # Capture to the right
            if c + 1 <= 7:
                if self.board[r + 1][c + 1][0] == "w":  # Enemy piece
                    if not piecePined or pinDirection == (1, 1):
                        moves.append(Move((r, c), (r + 1, c + 1), self.board))
        pass

    """
    # Generate all the possible moves for the Rooks
    # Rooks can travel horizontally or vertically until it is blocked by an ally or an enemy piece
    # Can travels along the horizontal/vertical line that it's being pinned
    # 
    """

    def __getRookMoves(self, r: int, c: int, moves):
        piecePined = False
        pinDirection = ()
        # Looks for pin information
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePined = True
                pinDirection = self.pins[i][2:3]
                if self.board[r][c][1] != 'Q':  # Can't remove queen pin from rook moves, only remove it on bisohp moves
                    self.pins.remove(self.pins[i])
                break

        enemy = 'b' if self.whiteToMove else 'w'
        for d in straightDirection:
            for i in range(1, 8):
                # Find the end location
                endRow = r + i * d[0]
                endCol = c + i * d[1]

                if isInBoard(endRow, endCol):
                    if not piecePined or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":  # Empty square
                            moves.append(Move((r, c), (endRow, endCol), self.board))

                        elif endPiece[0] == enemy:  # Enemy square, stop moving in that direction
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:  # Allies square
                            break
                else:
                    break

    """
    # Generate all the possible moves for the Bishops
    # Bishops can travel diagonally until it is blocked by an ally or an enemy piece
    # Can travels along the diagonal line that it's being pinned
    # 
    """

    def __getBishopMoves(self, r: int, c: int, moves):
        piecePined = False
        pinDirection = ()
        # Looks for pin information
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePined = True
                pinDirection = self.pins[i][2:3]
                self.pins.remove(self.pins[i])
                break

        enemy = 'b' if self.whiteToMove else 'w'
        for d in diagonalDirection:
            for i in range(1, 8):
                # Find the end location
                endRow = r + i * d[0]
                endCol = c + i * d[1]

                if isInBoard(endRow, endCol):
                    if not piecePined or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--":  # Empty square
                            moves.append(Move((r, c), (endRow, endCol), self.board))

                        elif endPiece[0] == enemy:  # Enemy square, stop moving in that direction
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else:  # Allies square
                            break
                else:
                    break

    """
    # Generate all the possible moves for the Queens
    # Pretty much a combination of rook and bishop
    """

    def __getQueenMoves(self, r: int, c: int, moves):
        self.__getRookMoves(r, c, moves)
        self.__getBishopMoves(r, c, moves)

    """
    # Generate all the possible moves for the Knights
    # The knights only care if it can jump to an empty space or onto an enemy piece
    # If the knight isn't pinned nothing can stop it
    """

    def __getKnightMoves(self, r: int, c: int, moves):
        piecePined = False

        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePined = True
                self.pins.remove(self.pins[i])
                break

        allyColor = 'w' if self.whiteToMove else 'b'
        for d in knightDirections:
            endRow = r + d[0]
            endCol = c + d[1]
            if isInBoard(endRow, endCol):
                if not piecePined:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))

    def __getKingMoves(self, r: int, c: int, moves):
        allyColor = "w" if self.whiteToMove else "b"
        for d in omniDirection:
            endRow = r + d[0]
            endCol = c + d[1]
            print("Current Ally " + allyColor)
            if isInBoard(endRow, endCol):
                endPiece = self.board[endRow][endCol]
                # Try to move the king to the new location and check for checks

                if endPiece[0] != allyColor:
                    print(endPiece)
                    if self.whiteToMove:
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)

                    inCheck, _, _ = self.__inCheckAnhKhoa()
                    if not inCheck:
                        print(str(Move((r, c), (endRow, endCol), self.board)))
                        moves.append(Move((r, c), (endRow, endCol), self.board))

                    # Revert the king move testing
                    if allyColor == 'w':
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)

    pass

    """
    # Deprecated - I'll just leave this function in for future testing
    # Generalize the generation of the moves of each piece type (Knight, King,...)
    # r: int - The piece's row
    # c: int - The piece's column
    # moves: A list for storing all possible move of all pieces of the same color
    # maxLength: A multiplier the for the direction that a piece can move in
    #            E.g : A queen can moves 7 square at a time -> multiplier is 7
    """

    def __getSiegeMoves(self, r: int, c: int, moves, maxLength: int):
        piece = self.board[r][c]
        enemy = 'b' if self.whiteToMove else 'w'
        for d in mapDirection[piece[1]]:
            for i in range(1, maxLength):
                # Find the end location
                endRow = r + i * d[0]
                endCol = c + i * d[1]

                if (0 <= endRow < 8) and (0 <= endCol < 8):

                    if self.board[endRow][endCol] == "--":  # Empty square
                        moves.append(Move((r, c), (endRow, endCol), self.board))

                    elif self.board[endRow][endCol][0] == enemy:  # Enemy square, stop moving in that direction
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else:  # Allies square
                        break
                else:
                    break

    '''
    All moves without considering check
    '''

    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]

                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)

        return moves


"""
# Store the start and end coordinates of the move.
# Along with the current state of the board just before the move is made
"""


class Move:
    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return colsToFiles[c] + rowsToRanks[r]

    def __eq__(self, other):
        return self.moveID == other.moveID

    def __str__(self):
        return str(self.moveID)
