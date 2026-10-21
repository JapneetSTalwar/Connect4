import sys
import os
import pygame as pg
import math,random
import asyncio 

# Setup
pg.init()
size = width, height = 1280,720 
colour = (10, 0, 0) # background colour


screen = pg.display.set_mode(size)
 
clock = pg.time.Clock()

pg.display.set_caption("Connect 4")

# Palette:
BG = (18, 22, 38)     # dark navy 
BOARD, BOARD_SHADE = (40, 72, 163), (27, 50, 120)  # board slab / recessed rings
RED, YELLOW = (231, 76, 60), (247, 201, 72)        # red, gold
GREEN = (96, 190, 140)                             # green
TEXT, MUTED, PANEL = (240, 242, 248), (150, 160, 190), (40, 46, 78)
DARK_TEXT = (24, 28, 46)
WHITE, BLACK, BLUE = (255, 255, 255), (0, 0, 0), (0, 0, 255)  

CELL, HOLE_R = 100, 40         # board geometry (unchanged from before)
BOARD_W, BOARD_H = 700, 600
SHADOW_PAD, SHADOW_DROP = 48, 14   # soft shadow under the board

#Font access
try:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _BASE_DIR = "."
FONT_DIR = os.path.join(_BASE_DIR, "assets", "fonts")

ENGINE_NAMES = ["UCB"]
LEVEL_NAMES = {100: "Easy", 500: "Medium", 1000: "Hard"}

#Done for hover effect
def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
def lighten(c, t=0.2):
    return mix(c, (255, 255, 255), t)
def darken(c, t=0.2):
    return mix(c, (0, 0, 0), t)

#Font stuff
_font_cache = {}
def get_font(size, weight="semibold"):
    """Bundled Poppins if present, otherwise pygame's default font."""
    key = (size, weight)
    if key not in _font_cache:
        fname = "Poppins-SemiBold.ttf" if weight == "semibold" else "Poppins-Medium.ttf"
        try:
            _font_cache[key] = pg.font.Font(os.path.join(FONT_DIR, fname), size)
        except Exception:
            _font_cache[key] = pg.font.Font(None, int(size * 1.2))
    return _font_cache[key]



def draw_text(surf, text, font, colour, center=None, topleft=None, midleft=None, shadow=None):
    img = font.render(text, True, colour)
    rect = img.get_rect()
    if center is not None: rect.center = center
    elif midleft is not None: rect.midleft = midleft
    elif topleft is not None: rect.topleft = topleft
    if shadow is not None: 
        surf.blit(font.render(text, True, shadow), rect.move(2, 4))
    surf.blit(img, rect)
    return rect

def make_bg(dim, colour):
    surf = pg.Surface(dim)
    surf.fill(colour)
    return surf.convert()

def make_disc(radius, base, pad=0, scale=4):
    R = (radius + pad) * scale
    big = pg.Surface((2 * R, 2 * R), pg.SRCALPHA)
    big.fill((*base, 0))                       
    c = (R, R)
    pg.draw.circle(big, (*darken(base, 0.28), 255), c, R)                         #rim
    pg.draw.circle(big, (*base, 255), c, (radius - 4) * scale)                    #face
    out = 2 * (radius + pad)
    return pg.transform.smoothscale(big, (out, out)).convert_alpha()

def make_ring(radius, width, colour, scale=4):
    R = (radius + width) * scale
    big = pg.Surface((2 * R, 2 * R), pg.SRCALPHA)
    big.fill((*colour, 0))
    pg.draw.circle(big, (*colour, 255), (R, R), (radius + width) * scale, width * scale)
    out = 2 * (radius + width)
    return pg.transform.smoothscale(big, (out, out)).convert_alpha()

def make_board_overlay(scale=3):
    """Blue slab with see-through holes. Pieces are drawn *behind* it, so they
    appear to sit inside the board."""
    S = scale
    big = pg.Surface((BOARD_W * S, BOARD_H * S), pg.SRCALPHA)
    big.fill((*BOARD, 0))
    pg.draw.rect(big, (*BOARD, 255), big.get_rect(), border_radius=28 * S)
    lip = big.get_rect().inflate(-12 * S, -12 * S)
    pg.draw.rect(big, (*lighten(BOARD, 0.10), 255), lip, width=2 * S, border_radius=22 * S)
    for c in range(7):
        for r in range(6):
            centre = ((c * CELL + CELL // 2) * S, (r * CELL + CELL // 2) * S)
            pg.draw.circle(big, (*BOARD_SHADE, 255), centre, (HOLE_R + 6) * S)   # recessed socket
            pg.draw.circle(big, (*BOARD_SHADE, 0), centre, HOLE_R * S)           # the hole itself
    return pg.transform.smoothscale(big, (BOARD_W, BOARD_H)).convert_alpha()

def make_soft_shadow(strength=130, k=8):
    pad = SHADOW_PAD
    w, h = BOARD_W + 2 * pad, BOARD_H + 2 * pad
    small = pg.Surface((w // k, h // k), pg.SRCALPHA)
    pg.draw.rect(small, (0, 0, 0, strength),
                 pg.Rect(pad // k, pad // k, BOARD_W // k, BOARD_H // k), border_radius=4)
    shadow = pg.transform.smoothscale(small, (w, h)).convert_alpha()
    pg.draw.rect(shadow, (0, 0, 0, 0), pg.Rect(pad, pad - SHADOW_DROP, BOARD_W, BOARD_H), border_radius=28)
    return shadow

BACKGROUND = make_bg(size, BG)
BOARD_OVERLAY = make_board_overlay()
BOARD_SHADOW = make_soft_shadow()
DISCS = {1: make_disc(HOLE_R, RED, pad=3), -1: make_disc(HOLE_R, YELLOW, pad=3)}
GHOSTS = {1: make_disc(28, RED), -1: make_disc(28, YELLOW)}
for _g in GHOSTS.values():
    _g.set_alpha(205)
WIN_RING = make_ring(HOLE_R + 2, 4, (255, 255, 255))
ICONS = {1: make_disc(16, RED), -1: make_disc(16, YELLOW)}
HOVER_BAND = pg.Surface((CELL, BOARD_H), pg.SRCALPHA)
HOVER_BAND.fill((255, 255, 255, 16))

def draw_card(surf, rect):
    pg.draw.rect(surf, PANEL, rect, border_radius=18)
    pg.draw.rect(surf, lighten(PANEL, 0.08), rect, width=1, border_radius=18)

def draw_banner(surf, text, colour):
    font = get_font(30)
    w = font.size(text)[0] + 64
    rect = pg.Rect(0, 0, w, 44)
    rect.center = (width // 2, 30)
    pg.draw.rect(surf, PANEL, rect, border_radius=22)
    pg.draw.rect(surf, colour, rect, width=2, border_radius=22)
    draw_text(surf, text, font, colour, center=rect.center)

def winner_of(board):
    for row in board:
        for v in row:
            if abs(v) == 2:
                return 1 if v > 0 else -1
    return 0 

def draw_scene(screen, game, offset, turn, interactive=True):
    mode, info = game.hud if game.hud is not None else (1, [])
    ox, oy = int(offset.x), int(offset.y)
    screen.blit(BACKGROUND, (0, 0))
    screen.blit(BOARD_SHADOW, (ox - SHADOW_PAD, oy - SHADOW_PAD + SHADOW_DROP))

    hover_col = None
    if interactive and (turn == 1 or (mode == 2 and turn == -1)):
        mx, my = pg.mouse.get_pos()
        if pg.Rect(ox, oy, BOARD_W, BOARD_H).collidepoint(mx, my):
            hover_col = (mx - ox) // CELL
            ghost = GHOSTS[turn]
            screen.blit(ghost, ghost.get_rect(center=(ox + hover_col * CELL + CELL // 2, oy - 32)))

    game.drawboard()
    screen.blit(game.screen, offset)
    if hover_col is not None:
        screen.blit(HOVER_BAND, (ox + hover_col * CELL, oy))

class Connect4:
    
    def __init__(self,screen):
        self.rows = 6
        self.columns = 7
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.screen = screen
        self.model = None
        self.hud = None  # (mode, [(label, value), ...]) shown in the side cards
        
    def drop_piece(self, col: int, player: int):
        for r in range(6): # Start from the bottom row
            if self.board[r][col] == 0:
                self.board[r][col] = player
                return r # Return the row where the piece was dropped
        return None # Column full
            
    def get_columns(self, board:list[list[int]]) -> list[int]: #checks if columns are full
        columns = []
        for c in range(7):
            if board[5][c] == 0: # If top row of column is empty, it's a valid move
                columns.append(c)
        return columns

    def check_win(self, player:int, board:list[list[int]], show = False):
        win = player * 4
        p = player
        # Check horizontal, vertical, and diagonal for win
        for r in range(6):
            for c in range(7):
                if c <= 3: # Check right
                    if board[r][c] + board[r][c+1] + board[r][c+2] + board[r][c+3] == win:
                        
                        board[r][c] = p * 2 # Highlight winning pieces
                        board[r][c+1] = p * 2
                        board[r][c+2] = p * 2
                        board[r][c+3] = p * 2
                        
                        if show:
                            return True,[(r,c),(r,c+1),(r,c+2),(r,c+3)]
                        return True
                        
                if r <= 2: # Check down
                    if board[r][c] + board[r+1][c] + board[r+2][c] + board[r+3][c] == win:
                    
                        board[r][c] = p * 2
                        board[r+1][c] = p * 2
                        board[r+2][c] = p * 2
                        board[r+3][c] = p * 2
                        
                        if show:
                            return True,[(r,c),(r+1,c),(r+2,c),(r+3,c)]
                        
                        return True
                if c <= 3 and r <= 2: # Check down-right diagonal
                    if board[r][c] + board[r+1][c+1] + board[r+2][c+2] + board[r+3][c+3] == win:
                        
                        board[r][c] = p * 2
                        board[r+1][c+1] = p * 2
                        board[r+2][c+2] = p * 2
                        board[r+3][c+3] = p * 2
                        
                        if show:
                            return True,[(r,c),(r+1,c+1),(r+2,c+2),(r+3,c+3)]
                        return True
                if c >= 3 and r <= 2: # Check down-left diagonal
                    if board[r][c] + board[r+1][c-1] + board[r+2][c-2] + board[r+3][c-3] == win:
                        
                        board[r][c] = p * 2
                        board[r+1][c-1] = p * 2
                        board[r+2][c-2] = p * 2
                        board[r+3][c-3] = p * 2
                        
                        if show:
                            return True,[(r,c),(r+1,c-1),(r+2,c-2),(r+3,c-3)]
                        return True
        return False
   
    def drawboard(self):
        board = self.board
        screen = self.screen
        screen.fill((0, 0, 0, 0))        # transparent: the backdrop shows through the holes
        wins = []
        # layer 1: pieces (value 3 = cleared by the end animation, so nothing is drawn)
        for c in range(7):
            for r in range(6):
                v = board[r][c]
                if v == 0 or v == 3:
                    continue
                player = 1 if v > 0 else -1
                disc = DISCS[player]
                x = c * CELL + CELL // 2
                y = (5 - r) * CELL + CELL // 2
                screen.blit(disc, disc.get_rect(center=(x, y)))
                if abs(v) == 2:
                    wins.append((x, y))
        # layer 2: the board slab, with real holes, on top of the pieces
        screen.blit(BOARD_OVERLAY, (0, 0))
        # layer 3: ring around the winning pieces
        for x, y in wins:
            screen.blit(WIN_RING, WIN_RING.get_rect(center=(x, y)))

    def showline(self,offset):
        x,y = tuple(a - b for a, b in zip(pg.mouse.get_pos(), offset)) #subract tuple
        col = int(x // 100)
        translucent_surface = pg.Surface((100, 600), pg.SRCALPHA)
        translucent_surface.fill((255, 255, 255, 16))
        self.screen.blit(translucent_surface,(100*col,0))
    
    async def endanimation(self,screen,offset,labels=("Player 1 wins!", "Player 2 wins!")):
        won = winner_of(self.board)      # read before the animation overwrites cells
        if won == 0:
            text, colour = "It's a draw!", TEXT
        else:
            text, colour = labels[0 if won == 1 else 1], (RED if won == 1 else YELLOW)

        def show():
            draw_scene(screen, self, offset, 0, interactive=False)
            draw_banner(screen, text, colour)
            pg.display.flip()

        board = self.board
        show() # Show final board state before animation
        await asyncio.sleep(1) # Pause before animation starts
        rownum = 0
        while rownum < 7:
            for c in range(7):
                if board[5-rownum][c] != 2 and board[5-rownum][c] != -2:
                    # Set row to invisible pieces
                    board[5-rownum][c] = 3
            show()
            await asyncio.sleep(0.5) # Delay for animation effect
            rownum += 1 
        await asyncio.sleep(1)

    def player_turn(self, num:int,mouse_pos: tuple):
        board = self.board
        x,y = mouse_pos
        col = int(x // 100)
        row = self.drop_piece(col, num)
        if row is not None: # Valid move
            pg.event.clear() # Clear events to prevent multiple moves

            self.drawboard()
            if self.check_win(num,board):
                print(f"Player {num} wins!")
                return 0 # End game  
            return -num # Switch to other player
        return num # Invalid move
    
    def board_reset(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]
    
    def apply_action(self,gameboard,col,player):
        #board has to be numpy array
        board = gameboard.copy()
        for r in range(6): # Start from the bottom row
            if board[r][col] == 0:
                board[r][col] = player
                return board # Return the row where the piece was dropped
        return board
            
    def algorithm_move(self,board,rollout=1000):
        return ucb_search(board,rollout,-1)

    def check_win_optim(self, board: list[list[int]], col: int, player: int) -> bool:
        r = 5
        while r >= 0 and board[r][col] == 0:   # find the topmost piece in the column
            r -= 1
        if r < 0 or board[r][col] != player:
            return False
        return wins_at(board, r, col, player)

    def check_winner(self, board: list[list[int]]):
        for column in range(7):
            if self.check_win_optim(board, column, 1): return 1
            if self.check_win_optim(board, column, -1): return -1
        if len(self.get_columns(board)) == 0: return 0
        return None
        
class Button(pg.sprite.Sprite):
    def __init__(self, x:int, y:int, width:int, height:int, text:str | None,colour = YELLOW,alpha = 255):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.x =x
        self.y = y
        self.colour = colour
        self.alpha = alpha

    def draw(self, screen, font_size=26):
        if self.is_hovered():
            pg.draw.rect(screen, self.colour, self.rect, border_radius=14)
            text_col = DARK_TEXT
        else:
            pg.draw.rect(screen, PANEL, self.rect, border_radius=14)
            pg.draw.rect(screen, self.colour, self.rect, width=2, border_radius=14)
            text_col = TEXT
        draw_text(screen, self.text, get_font(font_size), text_col, center=self.rect.center)

    
    def is_clicked(self):
        mouse_x, mouse_y = pg.mouse.get_pos()
        return self.rect.collidepoint(mouse_x, mouse_y) and pg.mouse.get_pressed()[0]
    def is_hovered(self):
        return self.rect.collidepoint(pg.mouse.get_pos())
    
    def change_text(self,text):
        self.text = text

class Checkbox(Button):
    # one-of-three selector: selected = filled accent, unselected = muted
    def __init__(self,x,y,width,height,label= None,text_offset=(0,0), text_colour=None,text_size=22):
        super().__init__(x,y,width,height,label)
        self.state = 0
        self.label = label
        self.offset = pg.Vector2(text_offset)
        self.text_col = text_colour
        self.text_size = text_size
        
    def draw(self, screen):
        if self.state == 1:
            fill, text_col = YELLOW, DARK_TEXT
        else:
            fill = lighten(PANEL, 0.08) if self.is_hovered() else PANEL
            text_col = TEXT if self.is_hovered() else MUTED
        pg.draw.rect(screen, fill, self.rect, border_radius=12)
        if self.state == 0:
            pg.draw.rect(screen, lighten(PANEL, 0.12), self.rect, width=1, border_radius=12)
        if self.label is not None:
            if self.text_col is not None: text_col = self.text_col
            draw_text(screen, self.text, get_font(self.text_size), text_col,
                      center=self.rect.move(self.offset).center)
        
    def is_clicked(self):
        if super().is_clicked():
            if self.state == 0:
                self.state = 1
                return True
            elif self.state == 1:
                self.state = 0
        else: 
            return False

async def mainmenu(computer):
    pg.display.set_caption("Connect 4 - Main Menu")
    cx = width // 2

    # difficulty buttons (clicking one starts a game, as before)
    easy = Button(cx - 279, 330, 170, 60,"Easy",GREEN)
    medium = Button(cx - 85, 330, 170, 60,"Medium",YELLOW)
    hard = Button(cx + 109, 330, 170, 60,"Hard",RED)


    pvp_button = Button(cx - 160, 450, 320, 56,"Player vs Player",lighten(PANEL, 0.35))
    #exit_button = Button(cx - 160, 550, 320, 56,"Exit",lighten(PANEL, 0.35))

    title_font = get_font(96)
    title = title_font.render("Connect 4", True, TEXT)
    title_shadow = title_font.render("Connect 4", True, (8, 10, 20))
    title_rect = title.get_rect(center=(cx, 160))
    
    
    buttons = [pvp_button,easy, medium, hard]

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                sys.exit()
                
        screen.blit(BACKGROUND, (0, 0))
        
        screen.blit(title_shadow, title_rect.move(2, 5))
        screen.blit(title, title_rect)
        for player, side in ((1, -1), (-1, 1)):
            disc = DISCS[player]
            screen.blit(disc, disc.get_rect(center=(cx + side * (title_rect.width // 2 + 70), 160)))
            
        for button in buttons:
            button.draw(screen)
        
        if easy.is_clicked():
            if pg.mouse.get_pressed()[0]: # Left click
                return 1,100 # Start game
        if medium.is_clicked():
            if pg.mouse.get_pressed()[0]: # Left click
                return 1,500 # Start game
        if hard.is_clicked():
            if pg.mouse.get_pressed()[0]: # Left click
                return 1,1000# Start game
        if pvp_button.is_clicked():
            if pg.mouse.get_pressed()[0]: # Left click
                return 2,0# Start player vs player game
                
        pg.display.flip()
        clock.tick(60)

        await asyncio.sleep(0) 


#UCB algorithm

DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))
FORCED_MOVES = True  

def wins_at(board: list[list[int]], row: int, col: int, player: int) -> bool:
    for dr, dc in DIRECTIONS:
        count = 1
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= 4:
            return True
    return False

def random_fill(board: list[list[int]], turn: int) -> int:
    board = [row[:] for row in board]
    open_cols = [c for c in range(7) if board[5][c] == 0]
    player = turn
    while open_cols:
        col = random.choice(open_cols)
        r = 0
        while board[r][col] != 0:
            r += 1
        board[r][col] = player
        if wins_at(board, r, col, player):
            return player     
        if r == 5:
            open_cols.remove(col)   
        player = -player
    return 0

def ucb_search(board:list[list[int]], rollouts: int, turn: int ,stats = False) -> int | tuple:
    moves = [c for c in range(7) if board[5][c] == 0]
    length = len(moves)

    children = []
    for col in moves:
        child = [row[:] for row in board]
        r = 0
        while child[r][col] != 0:
            r += 1
        child[r][col] = turn
        children.append((child, wins_at(child, r, col, turn)))

    if FORCED_MOVES:
        for col, (child, won) in zip(moves, children):   # win now
            if won:
                return (col, rollouts) if stats else col
        for col in moves:                                # block the opponent's win
            r = 0
            while board[r][col] != 0:
                r += 1
            probe = [row[:] for row in board]
            probe[r][col] = -turn
            if wins_at(probe, r, col, -turn):
                return (col, rollouts) if stats else col

    def playout(i: int) -> int:
        child, won = children[i]
        if won:
            return 1                                     # this move wins 
        return random_fill(child, -turn) * turn

    win_scores = [playout(i) for i in range(length)]
    run_amount = [1] * length
    ucb_scores: list[float] = [0.0] * length

    # UCB algorithm
    for i in range(rollouts):
        log_term = 2 * math.log(i + length)
        for j in range(length):
            ucb_scores[j] = win_scores[j] / run_amount[j] + math.sqrt(log_term / run_amount[j])

        next_move = ucb_scores.index(max(ucb_scores))
        run_amount[next_move] += 1
        win_scores[next_move] += playout(next_move)

    best_move = run_amount.index(max(run_amount))

    if stats:
        return moves[best_move], rollouts
    else:
        return moves[best_move]

async def main():
    # Setup
    game = Connect4(pg.Surface((700,600), pg.SRCALPHA))
    gamestate = 0 
    computer = 0 #used to save model between games
    while True:
        while gamestate == 0: # Main menu
            gamestate,difficulty = await mainmenu(computer)
            turn = 1 
            game.board_reset()
            board = game.board

            game.screen = pg.Surface((700,600), pg.SRCALPHA)

            hud = [("MODE", "Player vs AI" if gamestate == 1 else "Two players")]
            if gamestate == 1:
                hud += [("ENGINE", "UCB"), ("LEVEL", LEVEL_NAMES.get(difficulty, str(difficulty)))]
            game.hud = (gamestate, hud)

        screen.fill(BLACK) # clear screen after main menu
        
        #PvC game loop
        gameboard_offset = pg.math.Vector2(width//2 - 350,height//2-300)
        while gamestate == 1: # PVC
            pg.display.set_caption("Connect 4 - Player vs AI")
            for event in pg.event.get():
                if event.type == pg.QUIT: sys.exit() # end game if window closed
                    
                if turn == 1: # Player
                        mx, my = pg.mouse.get_pos()
                        mouse_pos = (int(mx - gameboard_offset.x), int(my - gameboard_offset.y))

                        if event.type == pg.MOUSEBUTTONDOWN and game.screen.get_rect(topleft=gameboard_offset).collidepoint(pg.mouse.get_pos()):
                            turn = game.player_turn(1,mouse_pos) 
                            
                            if turn == 0: # Player won
                                gamestate = 0
                                break
                            elif turn == -1:
                                turn = -0.5
                                
            if turn == -1: # AI
                    if len(game.get_columns(game.board)) > 0:
                        action = game.algorithm_move(board,difficulty)
                        game.drop_piece(col=action,player=-1)
                        board = game.board
                        turn = 1
                    else:
                        print("draw")
                        gamestate = 0

                    if game.check_win(-1,board):
                        print("AI wins!")
                        gamestate = 0
                
                    pg.event.clear()
                    await asyncio.sleep(0.5)

            if len(game.get_columns(game.board)) == 0:
                print("It's a draw!")
                gamestate = 0
            if turn == -0.5:
                turn = -1

            clock.tick(60) 
            draw_scene(screen, game, gameboard_offset, turn)
            pg.display.flip()
            await asyncio.sleep(0)
            if gamestate == 0:  
                await game.endanimation(screen,gameboard_offset,labels=("You win!", "AI wins!")) 

        while gamestate == 2: # PVP
            pg.display.set_caption("Connect 4 - Player vs Player")
            
            for event in pg.event.get():
                if event.type == pg.QUIT: sys.exit() 
                
                if event.type == pg.MOUSEBUTTONDOWN and game.screen.get_rect(topleft=gameboard_offset).collidepoint(pg.mouse.get_pos()):
                    mx, my = pg.mouse.get_pos()
                    mouse_pos = (int(mx - gameboard_offset.x), int(my - gameboard_offset.y))
                    if turn == 1: 
                            turn = game.player_turn(1,mouse_pos) 
                    elif turn == -1: 
                            turn = game.player_turn(-1,mouse_pos) 
                    
            if turn == 0: # Player won
                await game.endanimation(screen,gameboard_offset)
                gamestate = 0
                break
            
            clock.tick(60) 
            draw_scene(screen, game, gameboard_offset, turn) 
            pg.display.flip()
            await asyncio.sleep(0)

asyncio.run(main())