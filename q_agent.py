# q_agent.py
import random
from env import ACTIONS

class QLearningAgent:
    def __init__(self, alpha=0.1, gamma=0.95, epsilon=0.2, seed=None):
        """
        alpha   = learning rate
        gamma   = discount factor
        epsilon = exploration rate (chance to pick random move)
        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = random.Random(seed)

        # Q is a dict: keys are (state, action), values are float
        # state will be (r, c)
        self.Q = {}

    def _q_get(self, state, action):
        """Return Q(s,a), defaulting to 0.0 if unseen."""
        return self.Q.get((state, action), 0.0)

    def act(self, state):
        """
        ε-greedy policy:
        - with prob epsilon: random action
        - otherwise: best known action
        """
        if self.rng.random() < self.epsilon:
            return self.rng.choice(ACTIONS)

        # exploit: choose action with max Q(s,a)
        q_values = [(self._q_get(state, a), a) for a in ACTIONS]
        max_q = max(q_values, key=lambda x: x[0])[0]

        # if multiple actions tie, choose among the best randomly
        best_actions = [a for (q, a) in q_values if q == max_q]
        return self.rng.choice(best_actions)

    def learn(self, state, action, reward, next_state, done):
        """
        Q-learning update:
        Q(s,a) ← Q(s,a) + α [r + γ max_a' Q(s',a') - Q(s,a)]
        if done, the future term is 0.
        """
        old_q = self._q_get(state, action)

        if done:
            target = reward
        else:
            # estimate of optimal future value
            next_best = max(self._q_get(next_state, a) for a in ACTIONS)
            target = reward + self.gamma * next_best

        new_q = old_q + self.alpha * (target - old_q)
        self.Q[(state, action)] = new_q
