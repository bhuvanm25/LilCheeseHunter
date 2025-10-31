# env.py
import random
import gymnasium as gym
import numpy as np

WALL  = '⬛'
EMPTY = '🟥'
AGENT = '🐭'               # jerry
TREAT = '🧀'               # cheese
MOVING_TRAP = '😾'         # tom
# STATIC_TRAP = '🪤'          # mouse trap
# TRAPS!!!#!&!%&^$(!#&^$(@#))
STATIC_TRAP = '💀' # 5 total!!!!

POISON_TRAP = '🍇'         # mouse poison

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
        num_states = size * size    # for now, may change later as game becomes more complex
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

        # Place treat at bottom-right corner (rows-2, cols-2)
        self.treat_pos = (self.rows - 2, self.cols - 2)

        # Place trap at around middle of grid
        self.static_trap1_pos = (2, 1)
        self.static_trap2_pos = (2, 2)
        self.static_trap3_pos = (2, 3)
        self.static_trap4_pos = (2, 4)

        self.static_trap5_pos = (4, 2)
        self.static_trap6_pos = (4, 3)
        self.static_trap7_pos = (4, 4)
        self.static_trap8_pos = (4, 5)

        return self.agent_pos, self.coord_to_state(self.agent_pos)

    def step(self, action):
        
        # Move agent one step if not blocked by a wall (stays put if blocked).
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        # check boundary / wall
        if self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        # at trap or cheese;
        done = (self.agent_pos == self.treat_pos) or (self.agent_pos == self.static_trap1_pos) or (self.agent_pos == self.static_trap2_pos) or (self.agent_pos == self.static_trap3_pos) or (self.agent_pos == self.static_trap4_pos) or (self.agent_pos == self.static_trap5_pos) or (self.agent_pos == self.static_trap6_pos) or (self.agent_pos == self.static_trap7_pos) or (self.agent_pos == self.static_trap8_pos)
        # At trap or cheese
        if done:
            if (self.agent_pos == self.treat_pos):
                dead = False
            elif (self.agent_pos == self.static_trap1_pos) or (self.agent_pos == self.static_trap2_pos) or (self.agent_pos == self.static_trap3_pos) or (self.agent_pos == self.static_trap4_pos) or (self.agent_pos == self.static_trap5_pos) or (self.agent_pos == self.static_trap6_pos) or (self.agent_pos == self.static_trap7_pos) or (self.agent_pos == self.static_trap8_pos):
                dead = True

        #reward
        # +100 if cheese found
        # -1 each step
        # 

        if done:
            if dead:
                reward = -100
            else:
                reward = 100
        else:
            reward = -1

        return self.agent_pos, reward, done

    def render(self):

        for r in range(self.rows):

            line = []

            for c in range(self.cols):

                if (r, c) == self.agent_pos:
                    line.append(AGENT)
                elif (r, c) == getattr(self, 'treat_pos', None):
                    line.append(TREAT)
                elif (r, c) == getattr(self, 'static_trap1_pos', None) or (r, c) == getattr(self, 'static_trap2_pos', None) or (r, c) == getattr(self, 'static_trap3_pos', None) or (r, c) == getattr(self, 'static_trap4_pos', None) or (r, c) == getattr(self, 'static_trap5_pos', None) or (r, c) == getattr(self, 'static_trap6_pos', None) or (r, c) == getattr(self, 'static_trap7_pos', None) or (r, c) == getattr(self, 'static_trap8_pos', None):           # TESTING
                    line.append(STATIC_TRAP)
                else:
                    line.append(self.grid[r][c])

            print(" ".join(line))

    def coord_to_state(self, agent_pos):
        
        r, c = agent_pos

        r -= 1
        c -= 1

        a = (r * (self.cols - 2)) + c

        print(f"State index: {a}")      # TESTING

        return a
    
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

            action_index = np.argmax(q_table[state_index, :])
            best_action = ACTIONS[action_index]

            print(f"Q-value of best action: {q_table[state_index, action_index]}")

            # Goes to section of Q-table where state is relevant, goes through all actions and gives index of action with maximum Q-value
            return best_action, action_index