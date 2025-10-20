# visualize.py
import numpy as np
import matplotlib.pyplot as plt
from environment import ACTIONS

ARROWS = {0:'↑', 1:'→', 2:'↓', 3:'←'}

def render_policy(Q, rows, cols):
    """Return grid of best-action arrows given Q (states x actions)."""
    policy = [[' ' for _ in range(cols)] for __ in range(rows)]
    for s in range(Q.shape[0]):
        r = s // cols
        c = s % cols
        best_a = int(np.argmax(Q[s]))
        policy[r][c] = ARROWS.get(best_a, '?')
    return policy

def print_policy(policy, treats=None, traps=None, agent_pos=None):
    rows = len(policy)
    cols = len(policy[0])
    grid = [['.' for _ in range(cols)] for __ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            grid[r][c] = policy[r][c]
    if treats:
        for (tr, tc) in treats:
            grid[tr][tc] = 'T'
    if traps:
        for (xr, xc) in traps:
            grid[xr][xc] = 'X'
    if agent_pos:
        ar, ac = agent_pos
        grid[ar][ac] = 'A'
    print('\n'.join(' '.join(row) for row in grid))

def plot_rewards(reward_history, window=20):
    import numpy as np
    import matplotlib.pyplot as plt
    episodes = list(range(len(reward_history)))
    plt.figure(figsize=(8,4))
    plt.plot(episodes, reward_history, label='episode reward')
    if len(reward_history) >= window:
        smoothed = np.convolve(reward_history, np.ones(window)/window, mode='valid')
        plt.plot(range(window-1, len(reward_history)), smoothed, label=f'smoothed({window})')
    plt.xlabel('episode')
    plt.ylabel('total reward')
    plt.legend()
    plt.tight_layout()
    plt.show()
