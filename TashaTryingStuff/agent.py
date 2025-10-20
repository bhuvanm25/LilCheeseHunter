# agent.py
import numpy as np
from typing import Tuple

class QAgent:
    def __init__(self, n_states: int, n_actions: int,
                 alpha=0.1, gamma=0.99, eps_start=1.0, eps_final=0.05, eps_decay=0.995):
        self.n_states = n_states
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma

        self.eps = eps_start
        self.eps_final = eps_final
        self.eps_decay = eps_decay

        # Q-table as 2D numpy array (states x actions)
        self.Q = np.zeros((n_states, n_actions))

    def choose_action(self, state: int) -> int:
        # epsilon-greedy
        if np.random.rand() < self.eps:
            return np.random.randint(self.n_actions)
        else:
            # break ties deterministically by argmax
            return int(np.argmax(self.Q[state]))

    def learn(self, s: int, a: int, r: float, s_next: int, done: bool):
        q = self.Q[s, a]
        if done:
            target = r
        else:
            target = r + self.gamma * np.max(self.Q[s_next])
        self.Q[s, a] = q + self.alpha * (target - q)

    def decay_epsilon(self):
        if self.eps > self.eps_final:
            self.eps *= self.eps_decay
            if self.eps < self.eps_final:
                self.eps = self.eps_final
