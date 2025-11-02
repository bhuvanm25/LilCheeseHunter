# main.py
import os
import time
from env import GridWorld
from q_agent import QLearningAgent

# # redirect stdout to a text file
# import sys
# sys.stdout = open("training_log.txt", "w", encoding="utf-8")


def clear():
    # clears the console screen each time its called 
    # this makes the console cleaner
    os.system('cls' if os.name == 'nt' else 'clear')

def run_episode(env, agent, max_steps=50, render=False):
    """
    Runs ONE episode using the agent's current policy.
    Agent both ACTS and LEARNS during this episode.
    Returns total reward for the episode.
    """
    state = env.reset()
    total_reward = 0

    for t in range(max_steps):
        if render:
            print(f"\nStep {t+1}/{max_steps}")
            env.render()
            time.sleep(0.1)
        
        action = agent.act(state)
        next_state, reward, done = env.step(action)

        # learning step
        agent.learn(state, action, reward, next_state, done)

        total_reward += reward
        state = next_state

        if render:
            print(f"Action: {action}")
            print(f"Reward: {reward}")
            print(f"Total: {total_reward}")

        state = next_state

        if done:
            if render:
                print("🧀 Found - Episode Over!")
            break
    
    return total_reward
                  



def main():
    size = 5 #innergrid
    w = size + 2 #add walls

    #makes the grid, the seed value here makes random repeatable GAME
    env = GridWorld(rows=w, cols=w, seed=1)

    #creates agent, the seed value here make random repeatable ACTIONS
    agent = QLearningAgent(
        alpha=0.2, #learning rate
        gamma=0.95, #future discount
        epsilon=0.2, #exploration % (20% random moves)
        seed = 1
    )

    num_episodes = 5
    scores = []

    for ep in range(num_episodes):        
        render_this_one = (ep == 0) # which episode to display
        ep_reward = run_episode(env, agent, max_steps=50, render=True) #render = true -> print all episodes, false -> none
        scores.append(ep_reward)

        # simple progress print
        if (ep + 1) % 20 == 0 or ep == 0:
            avg_recent = sum(scores[-20:]) / len(scores[-20:])
            print(f"Episode {ep+1}/{num_episodes}  Reward={ep_reward}  RecentAvg={avg_recent:.2f}")

    print("\nTraining finished.")
    print(f"Final 20-episode avg reward: {sum(scores[-20:]) / len(scores[-20:]):.2f}")

    # # optional: show agent doing a final greedy run with NO exploration
    # print("\nGreedy showcase run:")
    # old_eps = agent.epsilon
    # agent.epsilon = 0.0  # force best-known actions
    # demo_reward = run_episode(env, agent, max_steps=200, render=True)
    # agent.epsilon = old_eps
    # print(f"Demo total reward: {demo_reward}")

if __name__ == "__main__":
    main()


