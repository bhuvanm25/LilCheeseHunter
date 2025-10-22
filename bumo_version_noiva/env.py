# env.py
import random
import gymnasium as gym
import numpy as np

WALL  = '⬛'
EMPTY = '🟥'
AGENT = '🐭'               # jerry
TREAT = '🧀'               # cheese
MOVING_TRAP = '😾'         # tom
STATIC_TRAP ='🪤'          # mouse trap

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

        num_states = size * size
        num_actions = 4

        self.P = {
            state: {action: [] for action in range(num_actions)}
            for state in range(num_states)
        }

        # Define what the agent can observe
        self.observation_space = gym.spaces.Discrete(num_states)

        # Define what actions are available (4 directions)
        self.action_space = gym.spaces.Discrete(num_actions)

        # Initialize positions - will be set randomly in reset()
        # Using -1,-1 as "uninitialized" state
        # self._agent_location = np.array([-1, -1], dtype=np.int32)
        # self._target_location = np.array([-1, -1], dtype=np.int32)

        # Map action numbers to actual movements on the grid
        # This makes the code more readable than using raw numbers
        # self._action_to_direction = {
        #     0: np.array([1, 0]),   # Move right (positive x)
        #     1: np.array([0, 1]),   # Move up (positive y)
        #     2: np.array([-1, 0]),  # Move left (negative x)
        #     3: np.array([0, -1]),  # Move down (negative y)
        # }

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

    # NEED TO COMPLETE THIS IMPLEMENTATION
    def reset(self):

        """Place the agent at a random empty cell inside the box."""
        empties = [(r, c)
                   for r in range(1, self.rows - 1)
                   for c in range(1, self.cols - 1)]
        self.agent_pos = self.rng.choice(empties)

        return self.agent_pos

    # NEED TO COMPLETE THIS IMPLEMENTATION
    def step(self, action):

        """Move agent one step if not blocked by a wall (stays put if blocked)."""
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        # check boundary / wall
        if self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        # for now, no rewards/termination; return next state
        return self.agent_pos

    def render(self):
        """Print grid with agent overlaid."""
        for r in range(self.rows):
            line = []
            for c in range(self.cols):
                if (r, c) == self.agent_pos:
                    line.append(AGENT)
                else:
                    line.append(self.grid[r][c])
            print(" ".join(line))