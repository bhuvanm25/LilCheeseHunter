# train.py
import numpy as np
from environment import GridEnv
from agent import QAgent
from visualize import render_policy, print_policy, plot_rewards

def train_and_run(
        rows=5, cols=7, episodes=1000,
        alpha=0.1, gamma=0.99, eps_start=1.0, eps_final=0.05, eps_decay=0.995
    ):
    # simple map: treat at bottom-right, trap bottom-left
    treats = [(rows-1, cols-1)]
    traps = [(rows-1, 0)]
    env = GridEnv(rows=rows, cols=cols, treats=treats, traps=traps, start=(0,0), max_steps=200)
    agent = QAgent(env.n_states, env.n_actions, alpha=alpha, gamma=gamma,
                   eps_start=eps_start, eps_final=eps_final, eps_decay=eps_decay)

    reward_history = []
    for ep in range(episodes):
        s = env.reset()
        total_reward = 0.0
        done = False
        while not done:
            a = agent.choose_action(s)
            s_next, r, done, _ = env.step(a)
            agent.learn(s, a, r, s_next, done)
            s = s_next
            total_reward += r

        agent.decay_epsilon()
        reward_history.append(total_reward)

        # periodic logging
        if (ep+1) % 50 == 0 or ep == 0:
            avg_last50 = np.mean(reward_history[-50:]) if len(reward_history) >= 50 else np.mean(reward_history)
            print(f"Episode {ep+1}/{episodes} | reward: {total_reward:.2f} | eps: {agent.eps:.3f} | avg50: {avg_last50:.3f}")

    # show policy
    policy = render_policy(agent.Q, rows, cols)
    print("\nFinal policy (arrows show best action):")
    print_policy(policy, treats=treats, traps=traps, agent_pos=None)

    # plot reward progression
    plot_rewards(reward_history)

    return env, agent, reward_history

if __name__ == "__main__":
    train_and_run(rows=5, cols=7, episodes=1000)
