#UCB
import math,random,copy
from time import time

from utils import Connect4

def random_fill(board: list[list[int]], turn: int): 
    game = Connect4()
    game.board = copy.deepcopy(board) 
    
    possibilities = game.get_columns(game.board)
    player = turn
    winner = None
    
    # Also add a safety check so a pre-existing draw doesn't cause an infinite loop/crash
    while winner is None and len(possibilities) > 0:
        move = random.choice(possibilities)
        game.drop_piece(move, player)
        winner = game.check_winner(game.board)
        
        player = -player
        possibilities = game.get_columns(game.board)
        
    return winner if winner is not None else 0

def ucb_search(board:list[list[int]], rollouts: int, turn: int ,stats = False) -> int | tuple:
    #Game inits
    game = Connect4()
    game.board = board
    possible_moves = game.get_columns(game.board)
    length = len(possible_moves)
    
    #UCB inits
    win_scores = possible_moves.copy()
    run_amount = [1 for i in range(length)]
    ucb_scores: list[float] = [0 for i in range(length)]
    
    for i in range(length):
        new_board = copy.deepcopy(game.board)
        new_board = game.apply_action(new_board,possible_moves[i],turn)
        
        rollout = random_fill(new_board,-turn)
        if rollout == turn:
            win_scores[i] = 1
        elif rollout == -turn:
            win_scores[i] =-1
        else:
            win_scores[i] = 0
    
    # UCB algorithm
    for i in range(rollouts):
        #choose best move via updating ucb_scores
        for j in range(length):
            #ucb_scores[j] = avg + math.sqrt( (2 * math.log(i+length))/run_amount[j] )
            
            # average win rate
            avg = win_scores[j] / run_amount[j]
            
            ucb_scores[j] = avg + math.sqrt((2 * math.log(i+length)) / run_amount[j])
            
        next_move = ucb_scores.index(max(ucb_scores))
        run_amount[next_move] += 1
        
        new_board = copy.deepcopy(game.board)
        new_board = game.apply_action(new_board,possible_moves[next_move],turn)
        
        rollout = random_fill(new_board,-turn)
        if rollout == turn:
            win_scores[next_move] += 1
        elif rollout == -turn:
            win_scores[next_move] -=1
    
    best_move = run_amount.index(max(run_amount))
    
    if stats:
        return possible_moves[best_move], rollouts
    else:
        return possible_moves[best_move]

def main():
    game = Connect4()
    board = game.board
    
    start_time = time() 
    
    random_fill(board,1)
    
    end_time = time()
    
    elapsed_time = end_time - start_time
    
    print(f"The simulation took {elapsed_time:.6f} seconds to complete.")
    
if __name__ == "__main__":
    main()
    