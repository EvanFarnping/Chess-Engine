# Handle game state, user input, and displaying said game state
from engine import *
import pygame as p
import numpy as np 

# TODO 
# Put things in comprehension forms for better optimization...
# use numpy when applicable
# Organize func from engine.py into different files for better organization

p.init()
WIDTH = HEIGHT = 512 # Maybe less for better efficiency?
DIMENSIONS = 8 # chessboard dimensions
SQUARE_SIZE = HEIGHT // DIMENSIONS
MAX_FPS = 10 # Lower probably, like 10-20
IMAGES = {}

def load_images():
    """
    Initialize a global dictionary of images. This is only called once.
    """
    pieces = np.array(["wK", "wQ", "wR", "wB", "wN", "wP",
                       "bK", "bQ", "bR", "bB", "bN", "bP"])
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), 
                                          (SQUARE_SIZE, SQUARE_SIZE))

def main():
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white")) # I don't think I need this...
    game_state = GameState()
    valid_moves = game_state.get_valid_moves()
    move_made = False # flag var for when move is made
    load_images()
    running = True
    square_selected = () # tuple: row,col --> keeps track of last click
    player_clicks = [] # keep track of player clicks [tuple:(row, col)]
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                loc = p.mouse.get_pos() # x,y
                col = loc[0]//SQUARE_SIZE
                row = loc[1]//SQUARE_SIZE
                if square_selected == (row, col): # user clicks same sq twice
                    square_selected = ()
                    player_clicks = []
                else:
                    square_selected = (row, col)
                    player_clicks.append(square_selected)
                if len(player_clicks) == 2: # after 2nd click
                    move = Move(player_clicks[0], player_clicks[1], game_state.board)
                    for i in range(len(valid_moves)):
                        if move == valid_moves[i]:
                            print(move.get_chess_notations())
                            game_state.make_move(valid_moves[i])
                            move_made = True
                            square_selected = ()
                            player_clicks = []
                    if not move_made:
                        player_clicks = [square_selected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_BACKSPACE:
                    game_state.undo_last_move()
                    move_made = True

        if move_made:
            valid_moves = game_state.get_valid_moves()
            move_made = False

        draw_game_state(screen, game_state)
        clock.tick(MAX_FPS)
        p.display.flip()

def draw_game_state(screen, game_state):
    create_board(screen, game_state.board)

def create_board(screen, board):
    colors = np.array([p.Color(192, 192, 192), p.Color(51, 51, 51)])
    for row in range(DIMENSIONS):
        for col in range(DIMENSIONS):
            color = colors[(row+col) % 2]
            p.draw.rect(screen, color, p.Rect(col*SQUARE_SIZE, 
                                              row*SQUARE_SIZE, 
                                              SQUARE_SIZE, 
                                              SQUARE_SIZE))
            piece = board[row][col]
            if piece != "__":
                screen.blit(IMAGES[piece], p.Rect(col*SQUARE_SIZE, 
                                              row*SQUARE_SIZE, 
                                              SQUARE_SIZE, 
                                              SQUARE_SIZE))

if __name__ == "__main__":
    main()