#C4 MCTS
from utils import Connect4
from time import time
import math,random,copy
import UCB_search

class MCTS():
    def __init__(self,orignalstate: list[list[int]], player = -1, runs= 1000):
        self.origin = orignalstate
        self.player = player
        self.runs = runs
    
    def best_move(self):
        origin = MCTSNode(None,self.origin,self.player,self.player)
        for _ in range(self.runs):
            origin.forward()
        
        child_runs = [child.runs for child in origin.children] 
        
        return origin.possibilities[child_runs.index(max(child_runs))]
        
            
        

class MCTSNode():
    def __init__(self,parent,state: list[list[int]],player = -1,origin = -1):
        self.parent = parent
        self.state = state
        self.children = []
        self.game = Connect4()
        
        self.wins = 0
        self.runs = 0
        self.player = player
        self.possibilities = self.game.get_columns(self.state)
        self.result = 0
        self.origin = origin
    
    def explore(self):
        for move in self.possibilities:
            state = copy.deepcopy(self.state)
            state = self.game.apply_action(state,move,self.player)
            self.children.append(MCTSNode(self,state, -self.player,self.origin))
    
    def backward(self,result):
        self.wins += result
        self.runs += 1
        if self.parent is not None:
            self.parent.backward(result)
        
    def simulate(self):
        state = copy.deepcopy(self.state)
        win = UCB_search.random_fill(state,self.player)
        
        if self.origin == win: 
            score = 1
        elif win == -self.origin:
            score = 0
        else: score = 0.5
        self.wins += score
        self.runs += 1

        if self.parent is not None:
            self.parent.backward(score)
        
            
            
            
    
    def forward(self):
        runs = [child.runs for child in self.children]
        win = Connect4().check_winner(self.state)
        if win is not None: # checks for game over
            if win == self.origin: 
                score = 1
            elif win == -self.origin: 
                score = 0
            else: 
                score = 0.5
                
            self.wins += score
            self.runs += 1
            if self.parent is not None:
                self.parent.backward(score)
            return 0
        
        
        if len(self.children) == 0: # not explored
            self.explore()
            random.choice(self.children).simulate()
        elif 0 in runs: # children not fully explored
            matching_indices = [index for index, value in enumerate(runs) if value == 0]
            index = random.choice(matching_indices)
            self.children[index].simulate()
        else: # explored
            #calculate ucb
            ucb_scores = [0  for _ in range(len(self.children)) ]
            for i in range(len(self.children)):
                
                avg = self.children[i].wins / self.children[i].runs
                
                if self.origin != self.player: avg = 1 - avg
                c_param = 1.414  
                ucb_scores[i] = avg + c_param * math.sqrt(math.log(self.runs) / self.children[i].runs)
            
            index = ucb_scores.index(max(ucb_scores))
            self.children[index].forward()

            
            

def main():
    game = Connect4()
    board = game.board
    
    start_time = time() 
    
    alg = MCTS(board,1,10000)
    alg.best_move()
    end_time = time()
    
    elapsed_time = end_time - start_time
    
    print(f"The simulation took {elapsed_time:.6f} seconds to complete.")
    
if __name__ == "__main__":
    main()
    
    