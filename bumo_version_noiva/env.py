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
        num_treats = 2
        treat_states = 2

        self.treats_bitstring = self.bitGen(num_treats)

        self.treat_list = list()

        for i in range(num_treats):
            self.treat_list.append("treat" + str(i))
        
        # self.treat_list_status = [1] * num_treats                               # not sure which one I want to use
        self.treat_dict_status = dict.fromkeys(self.treat_list, 1)       # note, as of python 3.7, dicts are ordered based on insertion

        # may want to create dictionary to map position of treats to treat to make code shorter later

        num_states = (self.size * self.size) * (pow(treat_states, num_treats))        # for now, may change later as game becomes more complex
        # num_states = (self.size * self.size)                                                  # number of states for v1
        num_actions = 4

        # dictionary that maps each state to an action
        # self.P = {
        #     state: {action: [] for action in range(num_actions)}
        #     for state in range(num_states)
        # }

        # Define what the agent can observe
        self.observation_space = gym.spaces.Discrete(num_states)

        # Define what actions are available (4 directions)
        self.action_space = gym.spaces.Discrete(num_actions)

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
        self.home_pos = (self.rows - 2, 1)

        # Place treat0 at top-right corner (rows-2, cols-2)
        self.treat0_pos = (1, self.cols - 2)

        # Place treat1 at bottom-right corner (rows-2, cols-2)
        self.treat1_pos = (self.rows - 2, self.cols - 2)

        # Place trap at around middle of grid (3,3)
        self.trap_pos = (3, 3)

        # Reset treat status to 1
        for key, value in self.treat_dict_status.items():
            self.treat_dict_status[key] = 1

        return self.agent_pos, self.coord_to_state()

    def step(self, action):
        
        # Move agent one step if not blocked by a wall (stays put if blocked).
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        # check boundary / wall
        if self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)       # updates agent's position

        # get cheese?
        # done = (self.agent_pos == self.treat_pos)
        eat_cheese0 = False
        if (self.treat_dict_status['treat0'] == 1):
            eat_cheese0 = (self.agent_pos == self.treat0_pos)

        eat_cheese1 = False
        if (self.treat_dict_status['treat1'] == 1):
            eat_cheese1 = (self.agent_pos == self.treat1_pos)

        # reach home?
        done = (self.agent_pos == self.home_pos)

        # hit trap?
        hit_trap = (self.agent_pos == self.trap_pos)

        #reward
        # +100 if cheese found
        # +1 if reached home
        # -1 each step
        # -25 for hitting trap

        if eat_cheese0:
            self.treat_dict_status['treat0'] = 0
            reward = 100
        elif eat_cheese1:      # simplify this later
            self.treat_dict_status['treat1'] = 0
            reward = 100
        elif done:
            reward = 1
        elif hit_trap:          
            reward = -25
        else:
            reward = -1

        return self.agent_pos, reward, done

    def render(self):

        for r in range(self.rows):

            line = []

            for c in range(self.cols):

                if (r, c) == self.agent_pos:
                    line.append(AGENT)

                elif (r, c) == getattr(self, 'treat0_pos', None):
                    if (self.treat_dict_status['treat0'] == 1):
                        line.append(TREAT)
                    else:
                        line.append(self.grid[r][c])

                elif (r, c) == getattr(self, 'treat1_pos', None):
                    if (self.treat_dict_status['treat1'] == 1):
                        line.append(TREAT)
                    else:
                        line.append(self.grid[r][c])

                elif (r, c) == getattr(self, 'trap_pos', None):           
                    line.append(MOUSE_TRAP)

                elif (r, c) == getattr(self, 'home_pos', None):
                    line.append(HOME)

                else:
                    line.append(self.grid[r][c])

            print(" ".join(line))

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

        index_adjuster = treats_status_index * (self.size * self.size)        # calculates index adjuster, groups range of states by size of grid (currently 5x5)

        a = (r * (self.size)) + c

        # TESTING
        print(f"State index: {a + index_adjuster}")      
        print(f"Treats status tuple: {treats_status}")

        return a + index_adjuster
    
    # Chooses action depending on given state (should move to ENV class)
    def choose_action(self, agent, state, state_index, q_table, epsilon):

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