#AlphaZeroC4
import torch,random,copy,math,time
from torch.utils.data import Dataset, DataLoader
from time import time
from pathlib import Path
from torch import nn
from utils import Connect4
import tqdm
global game 
game = Connect4()

class C4CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.network = nn.Sequential(
            #Block 1
            nn.Conv2d(4,64,4),
            nn.ReLU(),
            nn.BatchNorm2d(64),
            #Block 2
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            #Block 3
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            
            nn.Flatten()
        )
        self.policy_head = nn.Linear(768,7)  
        self.value_head = nn.Linear(768,1)
        
    def forward(self,x):
        z = self.network(x)
        p = self.policy_head(z)
        
        v = self.value_head(z)
        v = torch.tanh(v)
        return p,v

def list_to_input(state:list[list[int]],turn):
    # 4 features 1- empty, 2-p1 3-p2 4-next_move
    #f1[row][column]
    f1 = torch.tensor([[1 if cell == 0 else 0 for cell in row] for row in state],dtype= torch.float32)
    f2 =  torch.tensor([[1 if cell == 1 else 0 for cell in row] for row in state],dtype= torch.float32)
    f3 =  torch.tensor([[1 if cell == -1 else 0 for cell in row] for row in state],dtype= torch.float32)
    f4 = torch.tensor( [[1 if turn == 1 else -1 for _ in row] for row in state],dtype= torch.float32)
    
    tensor = torch.stack([f1,f2,f3,f4])
    tensor = tensor.unsqueeze(0)
    
    return tensor   
    
class DEEP_MCTS():
    def __init__(self,board: list[list[int]], player = -1, runs= 1000,model = None):
        self.original_state = [row[:] for row in board]
        self.player = player
        self.runs = runs
        self.model = model if model is not None else C4CNN()
        self.origin = DEEP_Node(self.model,None,self.original_state,self.player,self.player)
    
    def best_move(self,return_runs=False, temperature = 1.0):
        self.model.eval()
        
        for _ in range(self.runs):
            self.origin.forward()
        child_runs = [child.runs for child in self.origin.children] 
        
        if temperature == 0:
            move = self.origin.possibilities[child_runs.index(max(child_runs))]
        else:
            weights = [run ** (1 / temperature) for run in child_runs]
            probs = [w / sum(weights) for w in weights]
            move = random.choices(self.origin.possibilities, weights=probs, k=1)[0]
        
        #return runs to include all possible moves including illegal moves
        if len(self.origin.possibilities) != 7:
            runs = []
            child_index = 0
            for i in range(7):
                if i in self.origin.possibilities:
                    runs.append(self.origin.children[child_index].runs)
                    child_index += 1  
                else: 
                    runs.append(0)
        else: runs = child_runs
            
        
        self.update_origin(self.original_state,move)#upd origin
        if return_runs:
            return move,runs
        else: return move
    
    def update_origin(self, board: list[list[int]], move: int):
            moves = self.origin.possibilities
            player = self.origin.player  

            if len(self.origin.children) > 0:
                for i in range(len(moves)):
                    if moves[i] == move:
                        break
                self.origin = self.origin.children[i]
                self.origin.parent = None
            else:
                self.origin = DEEP_Node(self.model,None,game.apply_action(board, move, player),-player,self.player)
                         
class DEEP_Node():
    def __init__(self,model,parent,state: list[list[int]],player = -1,origin = -1,):
        self.parent = parent
        self.state = state
        self.children = []
        self.game = game
        
        self.wins = 0
        self.runs = 0
        self.player = player
        self.possibilities = self.game.get_columns(self.state)
        self.result = 0
        self.origin = origin
        
        self.model = model
        self.policy, self.values = None,None

    def explore(self):
        for move in self.possibilities:
            state = [row[:] for row in self.state] # copy state
            state = self.game.apply_action(state,move,self.player)
            self.children.append(DEEP_Node(self.model,self,state, -self.player,self.origin))
    
    def backward(self, result):
        result = -result
        self.wins += result
        self.runs += 1
        if self.parent is not None:
            self.parent.backward(result)
        
    def simulate(self):
        score = self.values  # already relative to self.player, in [-1, 1]
        self.wins += score
        self.runs += 1
        if self.parent is not None:
            self.parent.backward(score)

    
    def forward(self):
        win = game.check_win_optim(self.state)
        if win is not None: # checks for game over
            if win == self.player: 
                score = 1
            elif win == -self.player: 
                score = -1
            else: 
                score = 0
                
            self.wins += score
            self.runs += 1
            if self.parent is not None:
                self.parent.backward(score)
            return 0
                #state to tensor + 1 dimention for batch dimention for CNN
        if self.policy is None:
            state_tensor = list_to_input(self.state,self.player)
            with torch.inference_mode(): #save compute
                
                self.policy, self.values = self.model(state_tensor) 
                self.policy = self.policy.squeeze(0)
                self.values = self.values.item()
                self.policy = torch.softmax(self.policy,0)
            
            if self.parent is None:  # root node 
                epsilon = 0.25
                alpha = 0.5  # concentration parameter — worth tuning for 7 actions
                gamma_samples = [random.gammavariate(alpha, 1) for _ in range(len(self.policy))]
                dirichlet_sample = torch.tensor([g / sum(gamma_samples) for g in gamma_samples])
                self.policy = (1 - epsilon) * self.policy + epsilon * dirichlet_sample


        
        if len(self.children) == 0: # not explored
            self.explore()
            self.simulate()
            return
            
        else: # explored
            #calculate pucb
            ucb_scores = [0  for _ in range(len(self.children)) ]
            

                    
            for i in range(len(self.children)):
                
                avg = (self.children[i].wins / self.children[i].runs) if self.children[i].runs != 0 else 0
                avg = -avg

                c_param = 1.414  
                ucb_scores[i] = avg + c_param * self.policy[self.possibilities[i]] * ( math.sqrt(self.runs)/ (1+self.children[i].runs)) 
            
            index = ucb_scores.index(max(ucb_scores))
            self.children[index].forward()
        

class ALpha_Zero_Dataset(Dataset):
    def __init__(self,memory,max_size = 10000):
        self.memory = memory
        self.max_size = max_size
    
    def __len__(self): #length
        return len(self.memory)
    
    def __getitem__(self, index):
        state, turn, target_policy, game_result = self.memory[index]
        
        #totensor
        tensor = list_to_input(state,turn).squeeze(0)
        target_policy = torch.tensor(target_policy, dtype=torch.float32)
        target_value = torch.tensor([game_result], dtype=torch.float32)
        
        return tensor, target_policy, target_value
    
    def add_game_data(self,gamehistory: list[tuple]):
        self.memory.extend(gamehistory)
        
        #save case
        if len(self.memory) > self.max_size:
            self.memory = self.memory[-self.max_size:]


def train_DEEP_MCTS(epochs=500,batch_size=10,mlmodel= None):    
    model = C4CNN() if mlmodel is None else mlmodel
    optimiser = torch.optim.Adam(model.parameters(),lr=0.0001)
    
    value_loss_fn = nn.MSELoss()
    policy_loss_fn = nn.CrossEntropyLoss()
    
    data = ALpha_Zero_Dataset([])
    
    try:
        for epoch in tqdm.tqdm(range(epochs)):
            #play a game
            game.board_reset()
            model.eval()
            game_data = []
            win = None
            p1 = DEEP_MCTS(game.board,1,model=model,runs=500)
            p2 = DEEP_MCTS(game.board,-1,model=model,runs=500)
            moves = 0
            
            
            while win is None:
                #player 1 move
                
                temp = 1.0 if moves < 10 else 0 #random first few moves of the game
                
                p1_move,runs = p1.best_move(return_runs=True,temperature=temp)
                runs = [runs[i]/sum(runs) for i in range(len(runs))]
                game_data.append(([row[:]for row in game.board],1,runs))
                p2.update_origin(game.board, p1_move)   
                game.drop_piece(p1_move,1)
                moves += 1
                
                win = game.check_win_optim(game.board)
                if win is not None:
                    break
                
                #player 2 move
                p2_move,runs = p2.best_move(return_runs=True,temperature=temp)
                runs = [runs[i]/sum(runs) for i in range(len(runs))]
                game_data.append(([row[:]for row in game.board],-1,runs))
                p1.update_origin(game.board, p2_move)   
                game.drop_piece(p2_move,-1)
                moves += 1
                
                win = game.check_win_optim(game.board)
                
            
            game_data = [(state, player, policy, 1 if player == win else (0 if win == 0 else -1)) for state, player, policy in game_data]
            data.add_game_data(game_data)
            
            #Training every 10 games
            if len(data) >= 64 and epoch % batch_size == 0:
                model.train()
                train_data = DataLoader(dataset=data,batch_size=64,shuffle=True)
                inner_epochs = 2
                for inner_epoch in range(inner_epochs):    
                    total_value_loss = 0
                    total_policy_loss = 0
                    num_batches = 0
                    max_batches = 1024
                    for i, (state,policy,value) in enumerate(train_data):
                        if i >= max_batches:
                            break
                        p_pred, v_pred = model(state)
                        
                        value_loss = value_loss_fn(v_pred,value)
                        policy_loss = policy_loss_fn(p_pred,policy)
                        
                        loss = value_loss + policy_loss
                        
                        optimiser.zero_grad()
                        
                        loss.backward()
                        
                        optimiser.step()
                        
                        total_value_loss += value_loss.item()
                        total_policy_loss += policy_loss.item()
                        num_batches += 1
                
                print(f"Epoch {epoch}: value_loss={total_value_loss/num_batches:.4f}, policy_loss={total_policy_loss/num_batches:.4f}, datasize ={len(data)}")
    except KeyboardInterrupt:
        print("\nTraining interrupted — saving current model state...")
        MODEL_PATH = Path("models")
        MODEL_PATH.mkdir(parents=True,exist_ok=True)
        
        MODEL_NAME = "DMCTSL3-3"
        MODEL_SAVE_PATH = MODEL_PATH / MODEL_NAME 
        torch.save(obj=model.state_dict(), f=MODEL_SAVE_PATH)
        
    # saving
    MODEL_PATH = Path("models")
    MODEL_PATH.mkdir(parents=True,exist_ok=True)
    
    MODEL_NAME = "DMCTSL3-3"
    MODEL_SAVE_PATH = MODEL_PATH / MODEL_NAME 
    torch.save(obj=model.state_dict(), f=MODEL_SAVE_PATH)

    return model

def main():
    model = C4CNN()
    
    state_dict = torch.load("models/DMCTSl3-2")
    model.load_state_dict(state_dict)
    
    model = train_DEEP_MCTS(epochs=500,mlmodel=model)

    
if __name__ == "__main__":
    main()
    