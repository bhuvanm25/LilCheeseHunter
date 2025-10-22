# env.py
import random

WALL  = '⬛'
EMPTY = '🟥'
AGENT = ':cheese~1:' #jerry
TREAT = '🧀' #cheese
MOVINGTRAP = '😾' #tom
TRAP =':cheese~1:'


ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']
DELTAS = {
    'UP':    (-1, 0),
    'DOWN':  ( 1, 0),
    'LEFT':  ( 0,-1),
    'RIGHT': ( 0, 1),
}

class GridWorld:
    def __init__(self, rows=7, cols=7, seed=None):
        assert rows >= 3 and cols >= 3, "Box must be at least 3x3"
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)
        self.grid = self._make_box(rows, cols)
        self.agent_pos = None  # (r, c)

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
        """Place the agent at a random empty cell inside the box."""
        empties = [(r, c)
                   for r in range(1, self.rows - 1)
                   for c in range(1, self.cols - 1)]
        self.agent_pos = self.rng.choice(empties)
        return self.agent_pos

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
