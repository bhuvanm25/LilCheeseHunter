# env.py
import random

WALL  = '⬛'
EMPTY = '🟥'
AGENT = '🐭' #jerry
TREAT = '🧀' #cheese
MOVINGTRAP = '😾' #tom
TRAP ='🪤'


ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT'] # all the possible movement directions
# how each action changes the coordinates
DELTAS = {
    'UP':    (-1, 0),
    'DOWN':  ( 1, 0),
    'LEFT':  ( 0,-1),
    'RIGHT': ( 0, 1),
}

# a grid environment 
class GridWorld:


    def __init__(self, rows, cols, seed=None):
        assert rows >= 3 and cols >= 3, "Box must be at least 3x3"
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)
        self.grid = self._make_box(rows, cols)
        self.agent_pos = None  # (r, c)

    def _make_box(self, rows, cols):
        # Creates a square grid with walls around the edges and empty cells inside
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

        return self.agent_pos


    def step(self, action):
        # Move agent one step if not blocked by a wall (stays put if blocked).
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        # check boundary / wall
        if self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        # at cheese?
        done = (self.agent_pos == self.treat_pos)

        #reward
        # +100 if cheese found
        # -1 each step
        if done:
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
                else:
                    line.append(self.grid[r][c])
            print(" ".join(line))

