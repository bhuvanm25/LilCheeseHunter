# environment.py
import numpy as np
from typing import Tuple, List

# Actions: 0=up,1=right,2=down,3=left
ACTIONS = [( -1, 0 ), (0, 1), (1, 0), (0, -1)]

class GridEnv:
    def __init__(self, rows=5, cols=7, treats=None, traps=None, start=(0,0), max_steps=200):
        self.rows = rows
        self.cols = cols
        self.start = start
        self.max_steps = max_steps

        # place treats and traps as lists of (r,c)
        self.treats = treats if treats is not None else [(rows-1, cols-1)]
        self.traps = traps if traps is not None else [(rows-1, 0)]
        self.reset()

    def reset(self):
        self.agent_pos = tuple(self.start)
        self.steps = 0
        self.done = False
        return self._state()

    def _state(self):
        # encode state as single integer: r * cols + c
        r, c = self.agent_pos
        return r * self.cols + c

    def _in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def step(self, action: int) -> Tuple[int, float, bool, dict]:
        if self.done:
            raise RuntimeError("Env step called after done==True. Call reset().")
        dr, dc = ACTIONS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc
        if not self._in_bounds(nr, nc):
            nr, nc = r, c  # bump into wall -> stay put

        self.agent_pos = (nr, nc)
        self.steps += 1

        reward = 0.0
        if self.agent_pos in self.treats:
            reward = 1.0
            self.done = True   # episode ends on treat found
        elif self.agent_pos in self.traps:
            reward = -1.0
            self.done = True   # episode ends on trap
        elif self.steps >= self.max_steps:
            self.done = True

        return self._state(), reward, self.done, {}

    @property
    def n_states(self):
        return self.rows * self.cols

    @property
    def n_actions(self):
        return len(ACTIONS)

    def render_text(self):
        grid = [['.' for _ in range(self.cols)] for __ in range(self.rows)]
        for (tr, tc) in self.treats:
            grid[tr][tc] = 'T'
        for (xr, xc) in self.traps:
            grid[xr][xc] = 'X'
        ar, ac = self.agent_pos
        grid[ar][ac] = 'A'
        print('\n'.join(' '.join(row) for row in grid))
