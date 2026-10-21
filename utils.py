#utils
class Connect4:
    
    def __init__(self):
        self.rows = 6
        self.columns = 7
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        
    def drop_piece(self, col: int, player: int):
        for r in range(6): # Start from the bottom row
            if self.board[r][col] == 0:
                self.board[r][col] = player
                return r # Return the row where the piece was dropped
        return None # Column full
    
    def board_reset(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]
    
    def print_board(self):
        for r in range(6):
            for c in range(7):
                print(self.board[r][c], end=' ')
            print()
            
    def get_columns(self, board:list[list[int]]) -> list[int]: #checks if columns are full
        columns = []
        for c in range(7):
            if board[5][c] == 0: # If top row of column is empty, it's a valid move
                columns.append(c)
        return columns

    def check_win(self, player:int, board:list[list[int]]):
        win = player * 4
        p = player
        # Check horizontal, vertical, and diagonal for win
        for r in range(6):
            for c in range(7):
                if c <= 3: # Check right
                    if board[r][c] + board[r][c+1] + board[r][c+2] + board[r][c+3] == win:
                        '''
                        board[r][c] = p * 2 # Highlight winning pieces
                        board[r][c+1] = p * 2
                        board[r][c+2] = p * 2
                        board[r][c+3] = p * 2
                        '''
                        return True
                if r <= 2: # Check down
                    if board[r][c] + board[r+1][c] + board[r+2][c] + board[r+3][c] == win:
                        '''
                        board[r][c] = p * 2
                        board[r+1][c] = p * 2
                        board[r+2][c] = p * 2
                        board[r+3][c] = p * 2
                        '''
                        return True
                if c <= 3 and r <= 2: # Check down-right diagonal
                    if board[r][c] + board[r+1][c+1] + board[r+2][c+2] + board[r+3][c+3] == win:
                        '''
                        board[r][c] = p * 2
                        board[r+1][c+1] = p * 2
                        board[r+2][c+2] = p * 2
                        board[r+3][c+3] = p * 2
                        '''
                        return True
                if c >= 3 and r <= 2: # Check down-left diagonal
                    if board[r][c] + board[r+1][c-1] + board[r+2][c-2] + board[r+3][c-3] == win:
                        '''
                        board[r][c] = p * 2
                        board[r+1][c-1] = p * 2
                        board[r+2][c-2] = p * 2
                        board[r+3][c-3] = p * 2
                        '''
                        return True
        return False
    
    def check_win_optim(self, board: list[list[int]]) -> int | None:
        # Check for draw
        if len(self.get_columns(board)) == 0:
            return 0
        ROWS = 6
        COLS = 7

        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal \
            (1, -1)   # Diagonal /
        ]

        for r in range(ROWS):
            for c in range(COLS):
                player = board[r][c]
                if player == 0:
                    continue

                for dr, dc in directions:
                    count = 1
                    rr, cc = r + dr, c + dc

                    while (
                        0 <= rr < ROWS
                        and 0 <= cc < COLS
                        and board[rr][cc] == player
                    ):
                        count += 1
                        if count == 4:
                            return player
                        rr += dr
                        cc += dc

        

        # No winner yet
        return None
            

        
    def drawboard(self):
        board = self.board
        screen.fill((0, 0, 0)) # Clear screen every frame
        for c in range(7):
            for r in range(6):
                # Calculate position
                x = c * 100 + 50
                y = (5-r) * 100 + 50
                if board[r][c] == 0:
                    pg.draw.circle(screen, (255, 255, 255), (x, y), 40) # Empty slot
                elif board[r][c] == 1 or board[r][c] == 2:
                    pg.draw.circle(screen, (255, 0, 0), (x, y), 40) # Player piece
                elif board[r][c] == -1 or board[r][c] == -2:
                    pg.draw.circle(screen, (255, 255, 0), (x, y), 40) # AI piece
                '''
                elif board[r][c] == 2:
                    pg.draw.circle(screen, (0, 255, 0), (x, y), 40) # Winning piece
                elif board[r][c] == -2:
                    pg.draw.circle(screen, (0, 255, 255), (x, y), 40) # AI winning piece
                '''
                if board[r][c] == 3:
                    pg.draw.circle(screen, (0, 0,0), (x, y), 40) # invisible piece for animation
        pg.display.flip()
    
    def endanimation(self):
        self.drawboard() # Show final board state before animation
        board = self.board
        pg.time.delay(1000) # Pause before animation starts
        rownum = 0
        while rownum < 7:
            for c in range(7):
                if board[5-rownum][c] != 2 and board[5-rownum][c] != -2:
                    # Set row to invisible pieces
                    board[5-rownum][c] = 3
                    
            self.drawboard()
            pg.time.delay(500) # Delay for animation effect
            rownum += 1 
        
    def player_turn(self, num):
        board = self.board
        x, y = pg.mouse.get_pos()
        col = x // 100
        row = self.drop_piece(col, num)
        if row is not None: # Valid move
            #player_peices.append((col, row))
            self.drawboard()
            pg.event.clear() # Clear events to prevent multiple moves
            pg.time.delay(500) 
            if self.check_win(num,board):
                print(f"Player {num} wins!")
                return 0 # End game  
            return -num # Switch to other player
    
    
    def state_to_flat(self,board):
        npboard = np.array(board)
        return npboard.flatten()
    # AI functions
    
    def get_initial_state(self):
        return np.zeros((6,7))
         
    def apply_action(self,gameboard,col,player):
        #board has to be numpy array
        board = [row[:]for row in gameboard]
        for r in range(6): # Start from the bottom row
            if board[r][col] == 0:
                board[r][col] = player
                return board # Return the row where the piece was dropped
        return board
    
    def check_winner(self,board):
        if self.check_win(1,board): return 1
        elif self.check_win(-1,board): return -1
        elif len(self.get_columns(board)) == 0: return 0
        else: return None
        
    def algorithm_move(self,board,rollout=1000):
        from UCB_search import random_fill, ucb_search
        move = ucb_search(board,rollout,-1)
        
        return move
    
    def model_move(self,board,player,runs=1000):
        from AlphaZeroC4 import DEEP_MCTS  # local import avoids circular dependency
        if self.model is not None:
            algorithm = DEEP_MCTS(board,player,runs,self.model)
            return algorithm.best_move(temperature=0)

    def load_model(self,model_weights):
        import torch
        from AlphaZeroC4 import C4CNN  # local import avoids circular dependency
        self.model = C4CNN()
        state_dict = torch.load(model_weights)
        self.model.load_state_dict(state_dict)