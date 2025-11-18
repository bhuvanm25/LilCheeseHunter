# q_agent.py
import random
from collections import defaultdict
from env import ACTIONS

class QLearningAgent:

    def __init__(self, alpha=0.1, gamma=0.95, epsilon=0.2, seed=None):

        # parameters for training agent    
        """
        alpha 
            - Description: learning rate
            - Range: [0, 1]
            - Purpose: extent which new info overrides old info
            - 1 means new data 100% of time overwrites old info
        gamma   
            - Description: discount factor
            - Range: [0, 1]
            - Purpose: how important future rewards are
            - 1 means long-term focused model
        epsilon 
            - Description: Randomness/exploration rate
            - Range: [0, 1]
            - Purpose: take random action instead of using Q-table accumulated knowledge to find reward previously unaware of
            - 1 means always take random action, 0 means never take random action 
            - High epsilon: important in early stages when agent has limited knowledge and needs to build understanding of environment
            - Low epsilon: important in later stages when agent has gained more knowledge, wants to maximize rewards

        """
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

        self.epsilon_decay = 0.9995        # multiplies with epsilon to decrease it over traning loop 
        self.min_epsilon = 0.01            # sets min epsilon value to leave room for exploration even if value is small at end of training loop
        
        self.rng = random.Random(seed)

        # Q is a dict: keys are states, values are also a dict,  keys are actions, values are float
        self.Q = defaultdict(dict)

    def _q_get(self, state, action):

        """Return Q(s,a), defaulting to 0.0 if unseen."""
        return self.Q[state].get(action, 0.0)

    def act(self, state):

        """
        ε-greedy policy:
        - with prob epsilon: choose random action
        - otherwise: choose best known action
        """

        # exploration: take random action
        if random.uniform(0, 1) < self.epsilon:
            return self.rng.choice(ACTIONS)

        # exploit: choose action with max Q(s,a)
        q_values = [(self._q_get(state, a), a) for a in ACTIONS]
        max_q = max(q_values, key=lambda x: x[0])[0]

        # if multiple actions tie, choose among the best randomly
        best_actions = [a for (q, a) in q_values if q == max_q]
        
        return self.rng.choice(best_actions)
    
    def greedy_act(self, state):

        """
        greedy policy:
        - choose best known action
        """
         
        # exploit: choose action with max Q(s,a)
        q_values = [(self._q_get(state, a), a) for a in ACTIONS]
        max_q = max(q_values, key=lambda x: x[0])[0]

        # if multiple actions tie, choose among the best randomly
        best_actions = [a for (q, a) in q_values if q == max_q]

        best_action = random.choice(best_actions)

        return best_action

    def learn(self, state, action, reward, next_state, done):

        """
        Q-learning update:
        
        (1 - alpha) * old_value → keeps part of old info/Q-value
        alpha * (reward + gamma * next_max) → adds part of new info (rewards + discount factor * expected future rewards)
        
        if done, the future term is 0.
        """
        
        old_q = self._q_get(state, action)

        if done:
            target = reward

        else:
            # estimate of optimal future value
            next_best = max(self._q_get(next_state, a) for a in ACTIONS)
            target = reward + self.gamma * next_best

        new_q = (1 - self.alpha) * old_q + self.alpha * target

        self.Q[state][action] = new_q

    def decay_epsilon(self):

        # Updates epsilon value at end of episode
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
    