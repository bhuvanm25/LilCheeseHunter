import json
import random

WALL = '⬛'
EMPTY = '🟥'
AGENT = '🐭'
TREAT = '🧀'
TRAP = '🪤'

ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']
DELTAS = {
    'UP': (-1, 0),
    'DOWN': (1, 0),
    'LEFT': (0, -1),
    'RIGHT': (0, 1),
}


class GridWorld:
    TILE_EMPTY = 0
    TILE_WALL = 1
    TILE_TRAP = 2
    TILE_CHEESE = 3
    TILE_HOME = 4

    def __init__(self, rows, cols, seed: int = 0):
        assert rows >= 3 and cols >= 3, "Grid must be at least 3x3"
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)
        self.grid: list[list[str]] = [[EMPTY for _ in range(cols)] for _ in range(rows)]
        self.agent_pos: tuple[int, int] | None = None
        self._homes: list[tuple[int, int]] = []
        self._cheeses: list[tuple[int, int]] = []
        self._traps: set[tuple[int, int]] = set()
        self.home_pos: tuple[int, int] | None = None
        self.cheese_mask: int = 0

    @classmethod
    def from_json(cls, path, seed=0):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        grid_codes = data["grid"]
        rows = len(grid_codes)
        cols = len(grid_codes[0])
        env = cls(rows, cols, seed)

        homes = []
        cheeses = []
        traps = set()

        for r in range(rows):
            for c in range(cols):
                code = grid_codes[r][c]

                if code in (0, 1):
                    env.grid[r][c] = WALL
                elif code == 2:
                    env.grid[r][c] = EMPTY
                elif code == 3:
                    env.grid[r][c] = EMPTY
                    traps.add((r, c))
                elif code == 4:
                    env.grid[r][c] = EMPTY
                    cheeses.append((r, c))
                elif code == 5:
                    env.grid[r][c] = EMPTY
                    homes.append((r, c))

        env._homes = homes
        env._cheeses = cheeses
        env._traps = traps

        env.home_pos = homes[0]
        env.cheese_mask = env._full_cheese_mask()

        return env

    def set_home(self, idx):
        self.home_pos = self._homes[idx]

    def _full_cheese_mask(self):
        return (1 << len(self._cheeses)) - 1

    def _tile_code_at(self, r, c):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return self.TILE_WALL

        pos = (r, c)
        if self.grid[r][c] == WALL:
            return self.TILE_WALL
        if pos in self._traps:
            return self.TILE_TRAP

        for idx, cz in enumerate(self._cheeses):
            if pos == cz and (self.cheese_mask & (1 << idx)):
                return self.TILE_CHEESE

        if pos == self.home_pos:
            return self.TILE_HOME

        return self.TILE_EMPTY

    def local_tile_codes_4(self):
        r, c = self.agent_pos
        return (
            self._tile_code_at(r - 1, c),
            self._tile_code_at(r + 1, c),
            self._tile_code_at(r, c - 1),
            self._tile_code_at(r, c + 1),
        )

    def reset(self):
        self.agent_pos = self.home_pos
        self.cheese_mask = self._full_cheese_mask()
        return self.agent_pos

    def step(self, action):
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        pos = self.agent_pos
        reward = -1
        done = False

        if pos in self._traps:
            return pos, -100, True

        for idx, cz in enumerate(self._cheeses):
            if pos == cz and (self.cheese_mask & (1 << idx)):
                self.cheese_mask &= ~(1 << idx)
                reward += 100
                break

        if pos == self.home_pos:
            if self.cheese_mask == 0:
                reward += 200
            else:
                reward -= 50
            done = True

        return pos, reward, done

    def render(self):
        active = {pos for i, pos in enumerate(self._cheeses)
                  if (self.cheese_mask & (1 << i))}

        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                pos = (r, c)
                if pos == self.agent_pos:
                    row.append(AGENT)
                elif pos in self._traps:
                    row.append(TRAP)
                elif pos in active:
                    row.append(TREAT)
                else:
                    row.append(self.grid[r][c])
            print(" ".join(row))

    def step_to_goal(self, action: str, goal_pos: tuple[int, int]):
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        old_pos = self.agent_pos

        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        pos = self.agent_pos

        if pos == old_pos:
            return pos, -5, False

        if pos in self._traps:
            return pos, -100, True

        if pos == goal_pos:
            return pos, 100, True

        return pos, -1, False
