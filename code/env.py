import json
import random

# Emoji used when printing the grid to console
WALL = '⬛'
EMPTY = '🟥'
AGENT = '🐭'
TREAT = '🧀'
TRAP = '🪤'

# Discrete actions and their row/col deltas
ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT']
DELTAS = {
    'UP': (-1, 0),
    'DOWN': (1, 0),
    'LEFT': (0, -1),
    'RIGHT': (0, 1),
}


class GridWorld:
    # Internal tile codes for local observations
    TILE_EMPTY = 0
    TILE_WALL = 1
    TILE_TRAP = 2
    TILE_CHEESE = 3
    TILE_HOME = 4

    def __init__(self, rows, cols, seed: int = 0):
        # Core grid layout + RNG
        assert rows >= 3 and cols >= 3, "Grid must be at least 3x3"
        self.rows = rows
        self.cols = cols
        self.rng = random.Random(seed)

        # Grid stores WALL/EMPTY emojis for visualization
        self.grid: list[list[str]] = [[EMPTY for _ in range(cols)] for _ in range(rows)]

        # Dynamic state
        self.agent_pos: tuple[int, int] | None = None
        self._homes: list[tuple[int, int]] = []
        self._cheeses: list[tuple[int, int]] = []
        self._traps: set[tuple[int, int]] = set()
        self.home_pos: tuple[int, int] | None = None

        # Bitmask of which cheeses are still available
        self.cheese_mask: int = 0

    @classmethod
    def from_json(cls, path, seed=0):
        # Build an environment from a JSON map (cleaned/editor format)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        grid_codes = data["grid"]
        rows = len(grid_codes)
        cols = len(grid_codes[0])
        env = cls(rows, cols, seed)

        homes: list[tuple[int, int]] = []
        traps: set[tuple[int, int]] = set()
        cheeses: list[tuple[int, int]] = []  # currently unused (no cheese code in map)

        for r in range(rows):
            for c in range(cols):
                code = grid_codes[r][c]

                # 1 = wall, everything else = floor
                if code == 1:
                    env.grid[r][c] = WALL
                else:
                    env.grid[r][c] = EMPTY

                # 3 = trap, 4 = home
                if code == 3:
                    traps.add((r, c))
                elif code == 4:
                    homes.append((r, c))

        env._homes = homes
        env._cheeses = cheeses
        env._traps = traps

        # Home is first home tile if present, otherwise None
        env.home_pos = homes[0] if homes else None

        # Compute bitmask from cheese list (0 when no cheeses)
        env.cheese_mask = env._full_cheese_mask()

        return env

    def set_home(self, idx):
        # Choose which home tile is the “main” home
        self.home_pos = self._homes[idx]

    def _full_cheese_mask(self):
        # 1-bits for all cheese indices (e.g., 3 cheeses → 0b111)
        return (1 << len(self._cheeses)) - 1

    def _tile_code_at(self, r, c):
        # Convert a grid position to a local tile code (for observations)
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return self.TILE_WALL

        pos = (r, c)
        if self.grid[r][c] == WALL:
            return self.TILE_WALL
        if pos in self._traps:
            return self.TILE_TRAP

        # Check if a still-active cheese lives here
        for idx, cz in enumerate(self._cheeses):
            if pos == cz and (self.cheese_mask & (1 << idx)):
                return self.TILE_CHEESE

        if pos == self.home_pos:
            return self.TILE_HOME

        return self.TILE_EMPTY

    def local_tile_codes_4(self):
        # Codes for tiles in each cardinal direction around the agent
        r, c = self.agent_pos
        return (
            self._tile_code_at(r - 1, c),
            self._tile_code_at(r + 1, c),
            self._tile_code_at(r, c - 1),
            self._tile_code_at(r, c + 1),
        )

    def reset(self):
        # Reset agent to home and restore all cheeses
        self.agent_pos = self.home_pos
        self.cheese_mask = self._full_cheese_mask()
        return self.agent_pos

    def step(self, action):
        # Generic step function used by older code paths (not RL goals)
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        # Block movement into walls / outside map
        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        pos = self.agent_pos
        reward = -1
        done = False

        # Stepping on a trap ends the episode with a big penalty
        if pos in self._traps:
            return pos, -100, True

        # Collect cheese if present and still active in the mask
        for idx, cz in enumerate(self._cheeses):
            if pos == cz and (self.cheese_mask & (1 << idx)):
                self.cheese_mask &= ~(1 << idx)
                reward += 100
                break

        # Hitting home ends the episode; reward depends on cheese status
        if pos == self.home_pos:
            if self.cheese_mask == 0:
                reward += 200
            else:
                reward -= 50
            done = True

        return pos, reward, done

    def render(self):
        # Print an emoji view of the grid to the console (for debugging)
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
        # Step with reward shaped around a single “goal_pos” tile
        dr, dc = DELTAS[action]
        r, c = self.agent_pos
        nr, nc = r + dr, c + dc

        old_pos = self.agent_pos

        # Same movement constraints: can't walk through walls
        if 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nr][nc] != WALL:
            self.agent_pos = (nr, nc)

        pos = self.agent_pos

        # Penalize bumping into walls (no movement)
        if pos == old_pos:
            return pos, -5, False

        # Trap = big negative, episode ends
        if pos in self._traps:
            return pos, -100, True

        # Hitting the target tile ends episode with a big positive reward
        if pos == goal_pos:
            return pos, 100, True

        # Otherwise small step cost
        return pos, -1, False
