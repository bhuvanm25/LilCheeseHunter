# env.py
import random
import gymnasium as gym
import numpy as np
import itertools

WALL  = '⬛'
EMPTY = '🟥'
AGENT = '🐭'               # jerry
TREAT = '🧀'               # cheese
MOVING_TRAP = '😾'         # tom
MOUSE_TRAP = '🪤 '         # mouse trap
POISON_TRAP = '🍇'         # mouse poison
DEATH_TRAP = '☠️'          # mouse death
HOME = '🏠'               # mouse home

# Actions agent can choose to take
ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']

# How each action changes the coordinates
DELTAS = {
    'UP':    (-1, 0),
    'DOWN':  ( 1, 0),
    'LEFT':  ( 0,-1),
    'RIGHT': ( 0, 1),
}

class GridWorld(gym.Env):

    def __init__(self, rows, cols, size, seed=None):

        assert rows >= 3 and cols >= 3, "Box must be at least 3x3"
        self.rows = rows
        self.cols = cols
        self.size = size

        self.rng = random.Random(seed)
        self.grid = self._make_box(rows, cols)

        self.agent_pos = None  # (r, c)

        # MY TESTING WITH GYMNASIUM

        # testing with treats that can disappear once eaten (preparing for multiple treats)
        self.num_treats = 5
        treat_states = 2
        treat_num_pos = 5

        self.treats_bitstring = self.bitGen(self.num_treats)

        self.treat_list = ["treat" + str(i) for i in range(self.num_treats)]

        # self.treat_list = list()
        # for i in range(self.num_treats):
        #     self.treat_list.append("treat" + str(i))
        
        self.treat_dict_status = dict.fromkeys(self.treat_list, 0)                # note, as of python 3.7, dicts are ordered based on insertion

        num_states = (self.size * self.size) * (pow(treat_states, self.num_treats))      # for now, may change later as game becomes more complex
        # num_states = (self.size * self.size)                                                          # number of states for v1
        
        num_actions = 4

        # Define what the agent can observe
        self.observation_space = gym.spaces.Discrete(num_states)

        # Define what actions are available (4 directions)
        self.action_space = gym.spaces.Discrete(num_actions)

        # Defines possible states

        # Possible random positions for treats
        self.treat_rand_pos = [(5, 5), (5, 3), (1, 4), (2, 2), (4, 5)]

        # Dictionary to mapping position of treats to treat (initially off grid)
        self.treat_dict_pos = dict.fromkeys(self.treat_list, (-1, -1))


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

        # Testing random # of cheeses and cheese positions

        # Resets dictionaries
        self.treat_dict_pos.update(dict.fromkeys(self.treat_dict_pos, (-1, -1)))
        self.treat_dict_status.update(dict.fromkeys(self.treat_dict_status, 0))

        # Randomly chooses number of treats to place for episode (between 0 and 5 inclusive)
        self.ep_num_treats = random.randint(0, self.num_treats)
        # self.ep_num_treats = 2

        # Shuffles the array of possible treat positions to randomize which will be used (not sure best method of randomizing)
        random.shuffle(self.treat_rand_pos)         

        for i in range(self.ep_num_treats):

            self.treat_dict_pos["treat" + str(i)] = self.treat_rand_pos[i]          # Sets position of treats that will appear on epsiode
            self.treat_dict_status["treat" + str(i)] = 1                            # Sets status of treats to appear on episode to 1
        
        # Gets initial state of environment
        state = self.get_current_state()

        # Resets treat status to 1
        # for key, value in self.treat_dict_status.items():
        #     self.treat_dict_status[key] = 1

        # Previous fixed treat and trap position

        # Place treat0 at top-right corner (rows-2, cols-2)
        # self.treat0_pos = (1, self.cols - 2)

        # Place treat1 at bottom-right corner (rows-2, cols-2)
        # self.treat1_pos = (self.rows - 2, self.cols - 2)

        # # Place trap at around middle of grid (3,3)
        # self.trap_pos = (3, 3)

        # return self.agent_pos, self.coord_to_state()    # old return statement

        print(f"Game state tuple: {state}")
    
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

        # eat_cheese0 = False
        # eat_cheese1 = False

        eat_cheese = False

        for treat in self.treat_list:

            if (self.treat_dict_status[treat] == 1):

                eat_cheese = eat_cheese or (self.agent_pos == self.treat_dict_pos[treat])

                if self.agent_pos == self.treat_dict_pos[treat]:

                    self.treat_dict_status[treat] = 0           # change status to eaten
                    self.treat_dict_pos[treat] = (-1, -1)       # change position to off grid

        # if (self.treat_dict_status['treat0'] == 1):
            
        #     eat_cheese0 = (self.agent_pos == self.treat0_pos)

        #     if (eat_cheese0):
        #         self.treat_dict_status['treat0'] = 0

        # if (self.treat_dict_status['treat1'] == 1):

        #     eat_cheese1 = (self.agent_pos == self.treat1_pos)

        #     if (eat_cheese1):
        #         self.treat_dict_status['treat1'] = 0

        # eat_cheese = eat_cheese0 
        # eat_cheese = eat_cheese0 or eat_cheese1

        # reach home?
        done = (self.agent_pos == self.home_pos)

        # hit trap?
        hit_trap = (self.agent_pos == self.trap_pos)

        #reward
        # +100 if cheese found
        # +1 if reached home
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

        print(f"Game state tuple: {next_state}")

        # return self.agent_pos, reward, done
        return next_state, reward, done

    def render(self):

        # stores positions of treats in set (not sure this is optimal)
        treat_pos_set = set(self.treat_dict_pos.values())

        for r in range(self.rows):

            line = []

            for c in range(self.cols):

                if (r, c) == getattr(self, 'home_pos', None):
                    line.append(HOME)

                elif (r, c) == self.agent_pos:
                    line.append(AGENT)

                elif (r, c) == getattr(self, 'trap_pos', None):           
                    line.append(MOUSE_TRAP)

                # attempting to place treats
                elif (self.ep_num_treats > 0) and ((r, c) in treat_pos_set):

                    place_treat = False

                    for treat in self.treat_list:

                        if (self.treat_dict_status[treat] == 1) and ((r, c) == self.treat_dict_pos[treat]):

                            place_treat = True
                            line.append(TREAT)

                    if not place_treat:
                        line.append(self.grid[r][c])


                # elif (r, c) == getattr(self, 'treat0_pos', None):
                #     if (self.treat_dict_status['treat0'] == 1):
                #         line.append(TREAT)
                #     else:
                #         line.append(self.grid[r][c])

                # elif (r, c) == getattr(self, 'treat1_pos', None):
                #     if (self.treat_dict_status['treat1'] == 1):
                #         line.append(TREAT)
                #     else:
                #         line.append(self.grid[r][c])

                else:
                    line.append(self.grid[r][c])

            print(" ".join(line))

    # TESTING
    def get_current_state(self):

        treats_status = [self.treat_dict_status[key] for key in self.treat_dict_status]
        treats_status = tuple(treats_status)                                                # convert list to tuple

        treats_pos = [self.treat_dict_pos[key] for key in self.treat_dict_pos]
        treats_pos = tuple(treats_pos)                                                      # convert list to tuple

        # (mouse_pos (r,c), house_pos(r,c), cheese_states (_,_,_,_,_), cheeses_pos ((r0, c0), (r1, c1), (r2, c2), (r3, c3), (r4, c4)), trap_pos)
        return (self.agent_pos, self.home_pos, treats_status, treats_pos, self.trap_pos)

    def bitGen(self, n):
        return list(itertools.product([0, 1], repeat=n))

    def coord_to_state(self):
        
        r, c = self.agent_pos       # gets position of agent

        # adjusts r, c to range from 0 to 4
        r -= 1
        c -= 1

        treats_status = list()      # create list to store status of each treat

        # loop through dictionary values and add to list
        for value in self.treat_dict_status.values():
            treats_status.append(value)

        treats_status = tuple(treats_status)    # convert list to tuple

        treats_status_index = self.treats_bitstring.index(treats_status)      # gets index of current status of treats

        index_adjuster1 = treats_status_index * (self.size * self.size)        # calculates index adjuster, groups range of states by size of grid (currently 5x5)

        # need to adjust state index again to account for random positions cheese can be in

        a = (r * (self.size)) + c       # maps agent position to an index value

        # TESTING
        print(f"State index: {a + index_adjuster1}")      
        print(f"Treats status tuple: {treats_status}")

        return a + index_adjuster1
    
    # Chooses action depending on given state (should move to ENV class)
    def choose_action1(self, agent, state, state_index, q_table, epsilon):

        # Generates random value to see what action to take

        # If random value generated is less than epsilon, take random action
        if (random.uniform(0, 1) < epsilon):

            # gets random action (repeatable sequence of random actions)
            # rand_action = agent.act(state)
            # action_index = ACTIONS.index(rand_action)

            print("Random action")     

            # Using random.sample() function to generate random action
            # action_index = env.action_space.sample()
            # rand_action = ACTIONS[action_index]

            # Using agent seed to randomize actions (repeatable)
            rand_action = agent.act(state)
            action_index = ACTIONS.index(rand_action)

            return rand_action, action_index
        
        # Otherwise, take best action according to Q-table at the current state
        else :

            print("Q-table based action")       

            # Goes to section of Q-table where state is relevant, goes through all actions and gives index of action with maximum Q-value
            action_index = np.argmax(q_table[state_index, :])
            best_action = ACTIONS[action_index]

            print(f"Q-value of best action: {q_table[state_index, action_index]}")

            return best_action, action_index