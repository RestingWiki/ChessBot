"""
Chess Engine Project

This project was inspired by and built following the tutorial series by Eddie Sharick on creating a chess engine in Python.
Tutorial Source: https://www.youtube.com/playlist?list=PLBwF487qi8MGU81nDGaeNE1EnNEPYWKY_

All credit for the foundational knowledge and guidance goes to Eddie Sharick.
Any modifications or extensions are my own.

Author: [RestingKiwi]
Date: [I forgor]
"""


# Import the pygame module and ChessEngine from the Chess package
import pygame as pg
from Chess import ChessEngine
from nguyenpanda.swan import Color

# Initialize pygame
pg.init()

# Set the width and height of the window, and calculate square size
WIDTH = HEIGHT = 512                # Window size, assuming a square window
DIMENSION = 8                       # Dimension of the chessboard (8x8)
SQ_SIZE = WIDTH // DIMENSION        # Size of each square on the chessboard
MAX_FPS = 30
IMG_PATH = "Chess/images/1xR/"
IMAGES = {}                         # Dictionary to hold images of chess pieces

'''
Function to load and scale images of the chess pieces
'''
def loadImages():
    # List of chess pieces by their codes
    pieces = ["wR", "wN", "wB", "wQ", "wK", "wp", "bR", "bN", "bB", "bQ", "bK", "bp"]
    for piece in pieces:
        IMAGES[piece] = pg.transform.smoothscale(pg.image.load( IMG_PATH + piece + ".png"),
                                           (SQ_SIZE, SQ_SIZE))
        #print(piece)  # Optional: print the piece code to confirm loading


# Main function to set up and run the game loop
def main():
    print('PyCharm')
    screen     = pg.display.set_mode((WIDTH, HEIGHT))   # Create the game window
    screen.fill(pg.Color("white"))                  # Set the background color of the window to white
    clock      = pg.time.Clock()                         # Initialize a clock for controlling the game's frame rate
    gs         = ChessEngine.GameState()                    # Initialize the game state

    validMoves = gs.getAllPossibleMoves()
    moveMade   = False
    sqSelected = ()                                 # Keep track of the last click of the user (tuple: (row, col))
    playerClick = []                                  # Keep track of the player's click (two tuples: [(6,4), (4,4)]) )
    loadImages()


    running = True
    while running:  # Main game loop
        for e in pg.event.get():
            # EXIT
            if e.type == pg.QUIT:   # Check for the QUIT event to stop the game
                running = False
            # Mouse handler
            elif e.type == pg.MOUSEBUTTONDOWN:  # Move a piece but clicking on the square
                location = pg.mouse.get_pos()   # (x, y) location of the mouse
                col      = location[0] // SQ_SIZE
                row      = location[1] // SQ_SIZE


                # Choosing a piece
                if sqSelected == (row, col):   # The user clicked the same square twice
                    sqSelected = () # Deselect
                    playerClick  = [] # Clear list
                else:
                    sqSelected = (row, col)
                    playerClick.append(sqSelected)

                # Move the piece
                if len(playerClick) == 2:  # After 2nd click, make the move
                    if gs.board[playerClick[0][0]][playerClick[0][1]] != "--":
                        move = ChessEngine.Move(playerClick[0], playerClick[1], gs.board)

                        # print(Color['r'] +"==========" + Color.reset)
                        # for m in validMoves:
                        #     print(Color['g'] + str(m))
                        # print(Color['r'] +"==========" + Color.reset)
                        if not gs.whiteToMove:
                            print(Color['c'] + "White to move")
                        else:
                            print(Color['p'] + "Black to move")
                        if move in validMoves:
                            print(move.getChessNotation())
                            print(move.moveID)
                            gs.makeMove(move)
                            moveMade = True
                            sqSelected = ()
                            playerClick = []
                        else:
                            playerClick = [sqSelected]

                #  Deselect when making an invalid move
                if len(playerClick) == 1 and gs.board[sqSelected[0]][sqSelected[1]] == "--":
                    sqSelected  = ()
                    playerClick = []
                #  Generate possible moves
            # Key handler
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_z:
                    gs.undoMove()
                    sqSelected = ()
                    playerClick = []
                    moveMade    = True

        if moveMade:
            validMoves = gs.getAllPossibleMoves()
            moveMade   = False
            validMoves     = gs.getAllPossibleMoves()

        drawGameState(screen, gs,playerClick)
        clock.tick(MAX_FPS)
        pg.display.flip()           # Refresh the game screen

    #print(gs.board)

'''
Responsible for all graphics within a current game state.
'''
def drawGameState(screen, gs, playerClick):
    # Order of calling these 2 functions are important.
    drawBoard(screen)
    drawSelectionSquare(screen,playerClick)
    drawPieces(screen,gs.board)

'''
Draw the square on the board
'''
def drawBoard(screen):
    colors = [pg.Color("burlywood4"), pg.Color(124,76,42 ) ]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r+c) % 2]
            pg.draw.rect(screen, color, pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


'''
Draw pieces on top of the squares
'''
def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":       # Not empty square
                screen.blit(IMAGES[piece], pg.Rect(c*SQ_SIZE, r*SQ_SIZE,SQ_SIZE,SQ_SIZE))
    pass


'''
Draw the selection square
'''
def drawSelectionSquare(screen, playerClick: [()]):
    if len(playerClick) == 1:
        square = playerClick[0]
        pg.draw.rect(screen,"brown2",pg.Rect(square[1]*SQ_SIZE, square[0]*SQ_SIZE,SQ_SIZE,SQ_SIZE))


# Ensure this script block runs only if the script is executed directly (not imported)
if __name__ == '__main__':
    main()
