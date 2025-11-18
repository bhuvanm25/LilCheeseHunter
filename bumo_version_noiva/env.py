# env.py
import random

WALL  = '⬛'
EMPTY = '🟥'
AGENT = '🐭'               # jerry
TREAT = '🧀'               # cheese
MOVING_TRAP = '😾'         # tom
MOUSE_TRAP = '🪤 '         # mouse trap
POISON_TRAP = '🍇'         # mouse poison
DEATH_TRAP = '☠️'          # mouse death
HOME = '🏠'                # mouse home

# Actions agent can choose to take
ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']

# How each action changes the coordinates
DELTAS = {
    'UP':    (-1, 0),
    'DOWN':  ( 1, 0),
    'LEFT':  ( 0,-1),
    'RIGHT': ( 0, 1),
}

class GridWorld():

    def __init__(self, rows, cols, size, seed=None):

        assert rows >= 3 and cols >= 3, "Box must be at least 3x3"
        self.rows = rows
        self.cols = cols
        self.size = size

        self.rng = random.Random(seed)
        self.grid = self._make_box(rows, cols)

        self.agent_pos = None  # (r, c)

        self.num_treats = 5
        self.treat_list = ["treat" + str(i) for i in range(self.num_treats)]
        self.treat_dict_status = dict.fromkeys(self.treat_list, 0)             
                                                            
        self.treat_rand_pos = [(5, 5), (5, 3), (1, 4), (2, 2), (4, 5)]      # list of possible random positions of treats
        self.treat_dict_pos = dict.fromkeys(self.treat_list, (-1, -1))      # dict mapping position of treats to treat (initially off grid)


    def _make_box(self, rows, cols):

        grid = []
        for r in range(rows):
            row = []
            for c in range(cols):
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    row.append(WALL)
                else:
                    row.append(EMPTY)
            grid.append(row)

        return grid

    def reset(self):

        # Force the agent to spawn at top-left corner (1,1)
        self.agent_pos = (1, 1)

        # Place home in bottom-left corner (self,rows - 2, 1)
        self.home_pos = (5, 1)

        # Place trap 
        self.trap_pos = (3, 3)

        # Resets dictionaries
        self.treat_dict_pos.update(dict.fromkeys(self.treat_dict_pos, (-1, -1)))
        self.treat_dict_status.update(dict.fromkeys(self.treat_dict_status, 0))

        # Randomly chooses number of treats to place for episode (between 0 and 5 inclusive)
        self.ep_num_treats = random.randint(0, self.num_treats)

        # Shuffles the array of possible treat positions to randomize which will be used (not sure best method of randomizing)
        random.shuffle(self.treat_rand_pos)         

        for i in range(self.ep_num_treats):

            self.treat_dict_pos["treat" + str(i)] = self.treat_rand_pos[i]          # Sets position of treats that will appear on epsiode
            self.treat_dict_status["treat" + str(i)] = 1                            # Sets status of treats to appear on episode to 1
        
        # Gets initial state of environment
        state = self.get_current_state()

        # print(f"Game state tuple: {state}")
    
        return state

    def step(self, action):
        
        # Move agent one step if not blocked by a wall (stays put if blocked).
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        # check boundary / wall
        if self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)       # updates agent's position

        # get cheese?
        eat_cheese = False

        for treat in self.treat_list:

            if (self.treat_dict_status[treat] == 1):

                eat_cheese = eat_cheese or (self.agent_pos == self.treat_dict_pos[treat])

                if self.agent_pos == self.treat_dict_pos[treat]:

                    self.treat_dict_status[treat] = 0           # change status to eaten
                    self.treat_dict_pos[treat] = (-1, -1)       # change position to off grid

        # reach home?
        done = (self.agent_pos == self.home_pos)

        # hit trap?
        hit_trap = (self.agent_pos == self.trap_pos)

        #reward
        # +100 if cheese found
        # 0 if reached home
        # -1 each step
        # -25 for hitting trap

        if eat_cheese:
            reward = 100
        elif done:
            reward = 0
        elif hit_trap:          
            reward = -25
        else:
            reward = -1

        next_state = self.get_current_state()

        # print(f"Game state tuple: {next_state}")

        return next_state, reward, done

    def render(self):

        for r in range(self.rows):

            line = []

            for c in range(self.cols):

                # place house
                if (r, c) == getattr(self, 'home_pos', None):
                    line.append(HOME)

                # place agent
                elif (r, c) == self.agent_pos:
                    line.append(AGENT)

                # place trap
                elif (r, c) == getattr(self, 'trap_pos', None):           
                    line.append(MOUSE_TRAP)

                # place treats
                elif (self.ep_num_treats > 0) and ((r, c) in self.treat_dict_pos.values()):

                    place_treat = False

                    for treat in self.treat_list:

                        if (self.treat_dict_status[treat] == 1) and ((r, c) == self.treat_dict_pos[treat]):

                            place_treat = True
                            line.append(TREAT)

                    if not place_treat:
                        line.append(self.grid[r][c])

                # place wall/floor
                else:
                    line.append(self.grid[r][c])

            print(" ".join(line))

    def get_current_state(self):

        treats_status = [self.treat_dict_status[key] for key in self.treat_dict_status]
        treats_status = tuple(treats_status)                                                # convert list to tuple

        treats_pos = [self.treat_dict_pos[key] for key in self.treat_dict_pos]
        treats_pos = tuple(treats_pos)                                                      # convert list to tuple

        # (mouse_pos (r,c), house_pos(r,c), cheese_states (_,_,_,_,_), cheeses_pos ((r0, c0), (r1, c1), (r2, c2), (r3, c3), (r4, c4)), trap_pos)
        return (self.agent_pos, self.home_pos, treats_status, treats_pos, self.trap_pos)