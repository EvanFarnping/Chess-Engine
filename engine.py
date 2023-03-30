import numpy as np 
import copy

# NOTE's
"""
# TODO: use numpy, iterable, and comprehension for better speed

# NOTE: There is a bug in which checkmate is detected. The engine thinks that
        the spaces around the king are also consider check, but also not really
        as you can still move another piece as long as the king itself is in check.
        The engine is making a weird decision in what it considers to be a check.
        It may have something to do with king_move, in_check, or square_under_attack.
"""

class GameState():
    def __init__(self):
        """
        8x8 np 2D array: 
        b = black, w = white, and second character is the type of piece.
        "__" = represents the board's empty spots.
        """
        self.board = np.array([
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"], # row 0
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["__", "__", "__", "__", "__", "__", "__", "__"],
            ["__", "__", "__", "__", "__", "__", "__", "__"],
            ["__", "__", "__", "__", "__", "__", "__", "__"],
            ["__", "__", "__", "__", "__", "__", "__", "__"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"], # row 7
            ])

        """
        Later python version has match case which is better, also
        this would not be necessary if pieces were all classes with
        a generate_moves method, w/ colors & other info (Probably make a Ver.2)
        """
        self.move_functions = {
            "P": self.get_pawn_moves, 
            "N": self.get_knight_moves, 
            "B": self.get_bishop_moves, 
            "R": self.get_rook_moves, 
            "Q": self.get_queen_moves,
            "K": self.get_king_moves
            } 
        
        self.white_turn = True
        self.move_log = []
        self.white_king_loc = (7,4)
        self.black_king_loc = (0,4)
        self.check_mate = False
        self.stale_mate = False
        self.get_castling_rights = CastlingRights(True, True, True, True)
        self.castling_rights_log = [CastlingRights(self.get_castling_rights.wK_side, 
                                                   self.get_castling_rights.wQ_side,
                                                   self.get_castling_rights.bK_side,
                                                   self.get_castling_rights.bQ_side)]
        self.en_passant_coords = () # coords for squares where en passant is valid
        
    def make_move(self, move):
        """
        Takes the "Move" class (move) as a parameter and executes it.
        """
        self.board[move.start_row][move.start_col] = "__"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move) 
        self.white_turn = not self.white_turn
        if move.piece_moved == "wK":
            self.white_king_loc = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_loc = (move.end_row, move.end_col)

        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        #En passant move
        if move.is_en_passant_valid:
            self.board[move.start_row][move.end_col] = "__" #Pawn captured
        
        #Update en_passant_coords variable, only on 2 square pawn advances
        if move.piece_moved[1] == "P" and abs(move.start_row - move.end_row) == 2:
            self.en_passant_coords = ((move.start_row + move.end_row)//2, move.start_col)
        else:
            self.en_passant_coords = ()

        #Castle move
        if move.is_castling_valid:
            if move.end_col - move.start_col == 2: #king side castle
                #moves the rook (copy)
                self.board[move.end_row][move.end_col-1] = self.board[move.end_row][move.end_col+1]
                self.board[move.end_row][move.end_col+1] = "__" #Remove old rook
            else: #Queen side castle
                self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-2]
                self.board[move.end_row][move.end_col-2] = "__" #Remove old rook

        #Updating CastlingRights if rook or king moves, or something prevents it
        self.update_castling_rights(move)
        self.castling_rights_log.append(CastlingRights(self.get_castling_rights.wK_side, 
                                                   self.get_castling_rights.wQ_side,
                                                   self.get_castling_rights.bK_side,
                                                   self.get_castling_rights.bQ_side))

    def undo_last_move(self):
        """
        Undo the last move made. 
        To do this, 
            get the length of the move_log and pop off the most recent element.
        """
        if len(self.move_log) != 0:
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_turn = not self.white_turn
            if move.piece_moved == "wK":
                self.white_king_loc = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_loc = (move.start_row, move.start_col)

            if move.is_en_passant_valid:
                self.board[move.end_row][move.end_col] = "__" #leave landing sq blank
                self.board[move.start_row][move.end_col] = move.piece_captured
                #Allow to redo en passant after undoing
                self.en_passant_coords = (move.end_row, move.end_col)
            #Undo a two sq pawn push
            if move.piece_moved[1] == "P" and abs(move.start_row - move.end_row) == 2:
                self.en_passant_coords = ()

            #Undoing CastlingRights
            #Get rid of the new castle rights from the move we are undoing
            self.castling_rights_log.pop()
            #Set the current castle rights to the last one in the list
            self.get_castling_rights = self.castling_rights_log[-1]
            #Undo Castle move
            if move.is_castling_valid:
                if move.end_col - move.start_col == 2: #king side
                    self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-1]
                    self.board[move.end_row][move.end_col-1] = "__"
                else: #queen side
                    self.board[move.end_row][move.end_col-2] = self.board[move.end_row][move.end_col+1]
                    self.board[move.end_row][move.end_col+1] = "__"

    def update_castling_rights(self, move):
        """
        Update the castling rights given the move.
        """
        if move.piece_moved == "wK":
            self.get_castling_rights.wK_side = False
            self.get_castling_rights.wQ_side = False
        elif move.piece_moved == "bK":
            self.get_castling_rights.bK_side = False
            self.get_castling_rights.bQ_side = False
        elif move.piece_moved == "wR":
            if move.start_row == 7:
                if move.start_col == 0:
                    self.get_castling_rights.wQ_side = False
                elif move.start_col == 7:
                    self.get_castling_rights.wK_side = False
        elif move.piece_moved == "bR":
            if move.start_row == 0:
                if move.start_col == 0:
                    self.get_castling_rights.bQ_side = False
                elif move.start_col == 7:
                    self.get_castling_rights.bK_side = False

    def get_valid_moves(self):
        """
        Get only the valid moves of that game_state instance:
        Checks, pins, double attacks, discovered attacks, etc.
        NOTE, yes- a bit inefficient, but easy to implement and understand.
        """
        temp_en_passant_valid = self.en_passant_coords
        temp_castling_rights = CastlingRights(self.get_castling_rights.wK_side, 
                                                   self.get_castling_rights.wQ_side,
                                                   self.get_castling_rights.bK_side,
                                                   self.get_castling_rights.bQ_side)
        moves = self.get_all_possible_moves()
        if self.white_turn:
            self.get_castle_moves(self.white_king_loc[0], self.white_king_loc[1], moves)
            print("test")
        else:
            self.get_castle_moves(self.black_king_loc[0], self.black_king_loc[1], moves)

        for i in range(len(moves)-1, -1, -1):
            self.make_move(moves[i])
            if self.in_check():
                moves.remove(moves[i])
            self.undo_last_move()
        if len(moves) == 0:
            if self.in_check():
                print("Checkmate")
                self.check_mate = True
            else:
                print("Stalemate")
                self.stale_mate = True
        else:
            self.stale_mate = False
            self.check_mate = False
        
        self.en_passant_coords = temp_en_passant_valid
        self.get_castling_rights = temp_castling_rights
        return moves
    
    def in_check(self):
        """
        Checks if the King's location is under attack (in check).
        """
        if not self.white_turn:
            return self.square_under_attacK(self.white_king_loc[0], 
                                            self.white_king_loc[1])
        else:
            return self.square_under_attacK(self.black_king_loc[0], 
                                            self.black_king_loc[1])
        
    def square_under_attacK(self, row, col):
        """
        Get all of the possible moves that the opponent can make.
        If those moves cross over the square in question 
            (location of row and col), return True, else, False.
        """
        opponent_moves = self.get_all_possible_moves()
        for move in opponent_moves:
            if move.end_row == row and move.end_col == col:
                return True
        return False

    def get_all_possible_moves(self):
        """
        Get both black and white's moves possible moves
        """
        moves = []
        for row in range(len(self.board)): 
            for col in range(len(self.board[row])): 
                turn = self.board[row][col][0]
                if ((turn == "w" and self.white_turn) or 
                    (turn == "b" and not self.white_turn)):
                    piece = self.board[row][col][1]
                    self.move_functions[piece](row, col, moves)
        return moves

    def get_pawn_moves(self, row, col, moves):
        """
        Get all of the possible pawn moves for both black and white.
        Each pawn has the option to move forward, capture left or right.
            To do this, the pawn must check if the space in front is "__".
        If the pawn is on the starting space, it can move forward two spaces.
        It also checks that the pawn cannot capture off the board "col" check.
        If the en_passant spot is valid, then "is_en_passant_valid" becomes true.
        """
        if self.white_turn:
            if self.board[row-1][col] == "__":
                moves.append(Move((row,col), (row-1,col), self.board))
                if row == 6 and self.board[row-2][col] == "__":
                    moves.append(Move((row,col), (row-2,col), self.board))
            if col-1 >= 0: 
                if self.board[row-1][col-1][0] == "b":
                    moves.append(Move((row,col), (row-1,col-1), self.board))
                elif (row-1,col-1) == self.en_passant_coords:
                    moves.append(Move((row,col), (row-1,col-1), self.board, 
                                      is_en_passant_valid=True))
            if col+1 <= 7: 
                if self.board[row-1][col+1][0] == "b":
                    moves.append(Move((row,col), (row-1,col+1), self.board))
                elif (row-1,col+1) == self.en_passant_coords:
                    moves.append(Move((row,col), (row-1,col+1), self.board, 
                                      is_en_passant_valid=True))
        else: 
            if self.board[row+1][col] == "__":
                moves.append(Move((row, col), (row+1, col), self.board))
                if row == 1 and self.board[row+2][col] == "__":
                    moves.append(Move((row,col), (row+2,col), self.board))
            if col-1 >= 0: 
                if self.board[row+1][col-1][0] == "w":
                    moves.append(Move((row,col), (row+1,col-1), self.board))
                elif (row+1,col-1) == self.en_passant_coords:
                    moves.append(Move((row,col), (row+1,col-1), self.board, 
                                      is_en_passant_valid=True))
            if col+1 <= 7: 
                if self.board[row+1][col+1][0] == "w":
                    moves.append(Move((row,col), (row+1,col+1), self.board))
                elif (row+1,col+1) == self.en_passant_coords:
                    moves.append(Move((row,col), (row+1,col+1), self.board, 
                                      is_en_passant_valid=True))

    def get_knight_moves(self, row, col, moves):
        """
        
        """
        knight_moves = ((2,1), (2,-1), (1,2), (1,-2), 
                        (-1,2), (-1,-2), (-2,1), (-2,-1))
        ally_color = "w" if self.white_turn else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((row,col), (end_row,end_col), self.board)) 
                    
    def get_bishop_moves(self, row, col, moves):
        """
        
        """
        directions = ((1,-1), (1,1), (-1,-1), (-1,1)) #r-u,r-d,l-u,l-d
        enemy_color = "b" if self.white_turn else "w"
        for d in directions:
            for i in range(1,8): 
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "__":
                        moves.append(Move((row,col), (end_row,end_col), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((row,col), (end_row,end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_rook_moves(self, row, col, moves):
        """
        
        """
        directions = ((-1,0), (1,0), (0,-1), (0,1)) #up,down,left,right
        enemy_color = "b" if self.white_turn else "w"
        for d in directions:
            for i in range(1,8): 
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "__":
                        moves.append(Move((row,col), (end_row,end_col), self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((row,col), (end_row,end_col), self.board))
                        break
                    else:
                        break
                else:
                    break

    def get_queen_moves(self, row, col, moves):
        """
        Re-using the functions 
        "get_rook_moves" and "get_bishop_moves" b/c when combined
        create the move set for where the Queen can move. 
        """
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    def get_king_moves(self, row, col, moves):
        """
        
        """
        king_moves = ((-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)) 
        ally_color = "w" if self.white_turn else "b"
        for i in range(8): # maybe make this similar to knight moves for better performance?
            end_row = row + king_moves[i][0]
            end_col = col + king_moves[i][1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    moves.append(Move((row,col), (end_row, end_col), self.board)) 

    def get_castle_moves(self, row, col, moves):
        if self.square_under_attacK(row, col):
            return #Can't castle if in check 
        if ((self.white_turn and self.get_castling_rights.wK_side) or 
            (not self.white_turn and self.get_castling_rights.bK_side)):
            self.get_king_side_castle_moves(row, col, moves)
        if ((self.white_turn and self.get_castling_rights.wQ_side) or 
            (not self.white_turn and self.get_castling_rights.bQ_side)):
            self.get_queen_side_castle_moves(row, col, moves)
    
    def get_king_side_castle_moves(self, row, col, moves):
        """
        NOTE, Adding a check to this is unnecessary as once the king loses castling rights, 
        this will never be called, so the king will always be in the appropriate space and
        its location does not need to be checked such that it falls off the board.  
        """
        if self.board[row][col+1] == "__" and self.board[row][col+2] == "__":
            if (not self.square_under_attacK(row, col+1) and 
                not self.square_under_attacK(row, col+2)):
                moves.append(Move((row, col)), (row, col+2), 
                             self.board, is_castling_valid=True)

    def get_queen_side_castle_moves(self, row, col, moves):
        if (self.board[row][col-1] == "__" and 
            self.board[row][col-2] == "__" and 
            self.board[row][col-3] == "__"):
            if (not self.square_under_attacK(row, col-1) and 
                not self.square_under_attacK(row, col-2)):
                moves.append(Move((row, col)), (row, col-2), 
                             self.board, is_castling_valid=True)

class CastlingRights():
    def __init__(self, wK_side, wQ_side, bK_side, bQ_side) -> bool:
        self.wK_side = wK_side
        self.wQ_side = wQ_side
        self.bK_side = bK_side
        self.bQ_side = bQ_side

class Move():
    ranks_to_row = {"1":7, "2":6, "3":5, "4":4, "5":3, "6":2, "7":1, "8":0}
    rows_to_ranks = {chess_notation: python_notation for python_notation, 
                     chess_notation in ranks_to_row.items()}
    
    files_to_col = {"h":7, "g":6, "f":5, "e":4, "d":3, "c":2, "b":1, "a":0}
    cols_to_files = {chess_notation: python_notation for python_notation, 
                     chess_notation in files_to_col.items()}

    def __init__(self, start_square, end_square, board, 
                 is_en_passant_valid=False, is_castling_valid=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]

        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        #en passant
        self.is_en_passant_valid = is_en_passant_valid
        if self.is_en_passant_valid:
            self.piece_captured = "wP" if self.piece_moved == "bP" else "bP"

        #Castle move
        self.is_castling_valid = is_castling_valid

        #promotions
        self.is_pawn_promotion = ((self.piece_moved == "wP" and self.end_row == 0) or 
                                  (self.piece_moved == "bP" and self.end_row == 7))
            

        self.move_id = (self.start_row * 256 + 
                        self.start_col * 64 + 
                        self.end_row * 8 + self.end_col)

    def __eq__(self, other: object) -> bool:
        """
        
        """
        if isinstance(other, Move):
            return self.move_id == other.move_id
        return False

    def get_chess_notations(self):
        """
        
        """
        return (self.get_rank_file(self.start_row, self.start_col) + 
                self.get_rank_file(self.end_row, self.end_col))
    
    def get_rank_file(self, row, col):
        """
        
        """
        return self.cols_to_files[col] + self.rows_to_ranks[row]