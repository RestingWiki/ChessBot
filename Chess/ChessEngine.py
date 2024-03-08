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
whitePawnDirection = [(1, -1), (1, 1)]
blackPawnDirection = [(-1, -1), (-1, 1)]

# Mapping from each piece to the direction they can move, Knight, Bishop, Rook, Queen, King
mapDirection = {'N': knightDirections, 'B': diagonalDirection,
                'R': straightDirection, 'Q': omniDirection,
                'K': omniDirection}


def isInBoard(r, c):
    return 0 <= r <= 7 and 0 <= c <= 7


class GameState:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
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

    '''
    All moves considering check
    '''

    def getValidMoves(self):
        # 1.) Generate all possible move
        moves = self.getAllPossibleMoves()

        if self.whiteToMove:
            print(Color['r'] + "White generating moves" + Color.reset)
        else:
            print(Color['r'] + "Black generating moves" + Color.reset)

        # 2.) For each move, make the move
        for i in range(len(moves) - 1, -1, -1):  # traverse backward
            self.makeMove(moves[i])
            # 3.) Generate all opponents move
            # 4.) For of the opponent's move see if they attack the king
            self.whiteToMove = not self.whiteToMove
            t0 = time.time()
            if self.__inCheckAnhKhoa():
                print("Removed move:" + str(moves[i]))
                moves.remove(moves[i])
            t1 = time.time()
            if (t1 - t0) > 0:
                print(str(t1-t0))
            self.whiteToMove = not self.whiteToMove
            self.undoMove()
        # 5.) If they do attack the king, remove it

        if self.whiteToMove:
            print(Color['r'] + "White move count" + str(len(moves)) + Color.reset)
        else:
            print(Color['r'] + "Black move count" + str(len(moves)) + Color.reset)

        # Checking Checkmate/Stalemate
        if len(moves) == 0:
            if self.__inCheck():
                self.checkMate = True
            else:
                self.checkMate = False

        else:  # Just for undo-ing moves
            self.checkMate = False
            self.staleMate = False
        return moves

    # Determine if the current player is in check
    def __inCheck(self):
        if self.whiteToMove:
            return self.__squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.__squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])

    def __inCheckAnhKhoa(self):
        # check from the white King position
        # 1. Knights attack
        # 2. Check Pawn attack
        # 3. Rook/Bishop/Queen attack

        if self.whiteToMove:
            return self.__checkWhiteKing()
        else:
            return self.__checkBlackKing()

    def __checkWhiteKing(self):
        Kr, Kc = self.whiteKingLocation
        Er, Ec = (0, 0)  # Enemy row, column
        for d in knightDirections:
            Er = Kr + d[0]
            Ec = Kc + d[1]
            if isInBoard(Er, Ec) and self.board[Er][Ec] == "bN":
                return True

        for d in whitePawnDirection:
            Er = Kr + d[0]
            Ec = Kc + d[1]
            if isInBoard(Er, Ec) and self.board[Er][Ec] == "bp":
                return True

        for d in diagonalDirection:
            for i in range(1, 8):
                Er = Kr + d[0] * i
                Ec = Kc + d[1] * i

                if isInBoard(Er, Ec) and self.board[Er][Ec][0] == 'w':
                    break

                if isInBoard(Er, Ec) and (self.board[Er][Ec] == "bB" or
                                          self.board[Er][Ec] == "bQ"):
                    return True

        for d in straightDirection:
            for i in range(1, 8):
                Er = Kr + d[0] * i
                Ec = Kc + d[1] * i

                if isInBoard(Er, Ec) and self.board[Er][Ec][0] == 'w':
                    break

                if isInBoard(Er, Ec) and (self.board[Er][Ec] == "bB" or
                                          self.board[Er][Ec] == "bQ"):
                    return True

        return False

    def __checkBlackKing(self):
        Kr, Kc = self.blackKingLocation
        Er, Ec = (0, 0)  # Enemy row, column
        for d in knightDirections:
            Er = Kr + d[0]
            Ec = Kc + d[1]
            if isInBoard(Er, Ec) and self.board[Er][Ec] == "wN":
                return True

        for d in whitePawnDirection:
            Er = Kr + d[0]
            Ec = Kc + d[1]
            if isInBoard(Er, Ec) and self.board[Er][Ec] == "wp":
                return True

        for d in diagonalDirection:
            for i in range(1, 8):
                Er = Kr + d[0] * i
                Ec = Kc + d[1] * i

                if isInBoard(Er, Ec) and self.board[Er][Ec][0] == 'b':
                    break

                if isInBoard(Er, Ec) and (self.board[Er][Ec] == "wB" or
                                          self.board[Er][Ec] == "wQ"):
                    return True

        for d in straightDirection:
            for i in range(1, 8):
                Er = Kr + d[0] * i
                Ec = Kc + d[1] * i

                if isInBoard(Er, Ec) and self.board[Er][Ec][0] == 'b':
                    break

                if isInBoard(Er, Ec) and (self.board[Er][Ec] == "wB" or
                                          self.board[Er][Ec] == "wQ"):
                    return True

        return False

    # Determine if the enemy can attack the square
    # This does not modify the current player's turn
    def __squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove  # Switch to opponent turn
        oppoMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove  # Switch the turn back

        for move in oppoMoves:
            if move.endRow == r and move.endCol == c:
                return True

        return False

    def __getPawnMoves(self, r: int, c: int, moves):

        # White pawn to move
        if self.whiteToMove:
            if r == 0:
                return

            if self.board[r - 1][c] == "--":  # 1 square pawn advance
                moves.append(Move((r, c), (r - 1, c), self.board))
                if r == 6 and self.board[r - 2][c] == "--":  # 2 square pawn move advance
                    moves.append(Move((r, c), (r - 2, c), self.board))

            # Capture to the left
            if c - 1 >= 0:
                if self.board[r - 1][c - 1][0] == "b":  # Enemy piece
                    moves.append(Move((r, c), (r - 1, c - 1), self.board))

            # Capture to the right
            if c + 1 <= 7:
                if self.board[r - 1][c + 1][0] == "b":  # Enemy piece
                    moves.append(Move((r, c), (r - 1, c + 1), self.board))

        # Black pawn to move
        if not self.whiteToMove:
            if r == 7:
                return
            if self.board[r + 1][c] == "--":  # 1 square pawn advance
                moves.append(Move((r, c), (r + 1, c), self.board))
                if r == 1 and self.board[r + 2][c] == "--":
                    moves.append(Move((r, c), (r + 2, c), self.board))

            # Capture to the left
            if c - 1 >= 0:
                if self.board[r + 1][c - 1][0] == "w":  # Enemy piece
                    moves.append(Move((r, c), (r + 1, c - 1), self.board))

            # Capture to the right
            if c + 1 <= 7:
                if self.board[r + 1][c + 1][0] == "w":  # Enemy piece
                    moves.append(Move((r, c), (r + 1, c + 1), self.board))
        pass

    def __getRookMoves(self, r: int, c: int, moves):
        self.__getSiegeMoves(r, c, moves, 8)

    def __getBishopMoves(self, r: int, c: int, moves):
        self.__getSiegeMoves(r, c, moves, 8)

    def __getKnightMoves(self, r: int, c: int, moves):
        self.__getSiegeMoves(r, c, moves, 2)

    def __getQueenMoves(self, r: int, c: int, moves):
        self.__getSiegeMoves(r, c, moves, 8)

    def __getKingMoves(self, r: int, c: int, moves):
        self.__getSiegeMoves(r, c, moves, 2)

        pass

    def __getSiegeMoves(self, r: int, c: int, moves, maxLength: int):
        piece = self.board[r][c]
        enemy = 'b' if self.whiteToMove else 'w'

        if (self.whiteToMove and piece[0] == 'w') or (not self.whiteToMove and piece[0] == 'b'):
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
