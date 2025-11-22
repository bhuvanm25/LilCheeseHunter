import random
import pickle
from env import ACTIONS


class QLearningAgent:
    def __init__(self, alpha, gamma, epsilon, seed):
        # Learning rate, discount, and exploration rate
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

        # RNG and Q-table
        self.rng = random.Random(seed)
        self.Q = {}

    def _q_get(self, state, action):
        # Return Q(s,a) if it exists, otherwise 0
        return self.Q.get((state, action), 0.0)

    def act(self, state):
        # ε-greedy action selection over ACTIONS
        if self.rng.random() < self.epsilon:
            return self.rng.choice(ACTIONS)

        # Exploit: pick any action with maximal Q-value
        q_values = [(self._q_get(state, a), a) for a in ACTIONS]
        max_q = max(q_values, key=lambda x: x[0])[0]
        best_actions = [a for (q, a) in q_values if q == max_q]
        return self.rng.choice(best_actions)

    def learn(self, state, action, reward, next_state, done):
        # Standard Q-learning update
        old_q = self._q_get(state, action)

        if done:
            target = reward
        else:
            next_best = max(self._q_get(next_state, a) for a in ACTIONS)
            target = reward + self.gamma * next_best

        new_q = old_q + self.alpha * (target - old_q)
        self.Q[(state, action)] = new_q

    def save(self, path):
        # Persist Q-table and hyperparameters to disk
        payload = {
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "Q": self.Q,
        }
        with open(path, "wb") as f:
            pickle.dump(payload, f)

    @classmethod
    def load(cls, path):
        # Load agent from a saved pickle
        with open(path, "rb") as f:
            payload = pickle.load(f)

        agent = cls(
            alpha=payload["alpha"],
            gamma=payload["gamma"],
            epsilon=payload["epsilon"],
            seed=0,  # seed doesn't matter once Q-table is fixed
        )
        agent.Q = payload["Q"]
        return agent

    def set_greedy(self):
        # Switch to fully greedy policy (no exploration)
        self.epsilon = 0.0
