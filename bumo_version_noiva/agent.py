# agent.py
import random
from env import ACTIONS

class RandomAgent:

    def __init__(self, seed=None):

        self.rng = random.Random(seed)

    def act(self, state):
        
        """Ignore state and pick a random action."""
        return self.rng.choice(ACTIONS)