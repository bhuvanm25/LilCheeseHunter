# main.py
import os
import time
from env import GridWorld
from q_agent import QLearningAgent

def clear():
    # clears the console screen each time its called 
    # this makes the console cleaner
    os.system('cls' if os.name == 'nt' else 'clear')

def main():

    size = 5        # inner grid
    w = size + 2    # add walls
    
    # makes the grid, the seed value here makes random repeatable GAME 
    env = GridWorld(rows=w, cols=w, size=size, seed=42)
    
    # creates agent, the seed value here make random repeatable ACTIONS
    agent = QLearningAgent(0.85, 0.95, 1, seed=1)

    num_ep_train = 15000   # number of episodes to run training loop
    num_ep_render = 10     # number of episodes to render results of traning
    max_steps = 100              # max step count
    
    delay_s = 0.3          # delay for each step sp we can see it move

    episode_return = 0 # total points this round/episode

    # training loop (epsilon-greedy policy - exploratation with exploration)
    for episode in range(num_ep_train):

        done = False
        episode_return = 0

        print('\nEpisode', (episode + 1))

        # state, state_index = env.reset() # put agent in grid
        state = env.reset()

        for step in range(max_steps):

            """
            Clear console
            print step count
            draw grid
            make agent pick random action
            move the agent using the random action
            delay

            Repeat 
            """
            # clear()
            # print('\nEpisode', (episode + 1))
            # print(f"\nStep {step+1}/{max_steps}")
            # env.render()

            # choose action 
            action = agent.act(state)

            # applies action 
            next_state, reward, done = env.step(action)

            # updates agent's knowledge on q-table
            agent.learn(state, action, reward, next_state, done)

            # Updates state
            state = next_state
            
            episode_return += reward

            # print(f"Episode # of cheese: {env.ep_num_treats}")

            # print(f"Action: {action}")
            # print(f"Reward: {reward}")
            # print(f"Total: {episode_return}")

            if done:
                print("🧀 HOME REACHED. Round over!")
                print(f"Final Score: {episode_return}")
                break

            # time.sleep(delay_s)

        # Updates epsilon value at end of episode
        agent.decay_epsilon()

    # final frame
    # clear()
    print("\nFinal State:")
    env.render()

    print("\nTraining Loop Over:")

    # rendering loop (pure greedy run - only exploitation)
    for episode in range(num_ep_render):

        done = False
        episode_return = 0

        # state, state_index = env.reset() # put agent in grid
        state = env.reset()

        for step in range(max_steps):

            """
            Clear console
            print step count
            draw grid
            make agent pick random action
            move the agent using the random action
            delay

            Repeat 
            """
            clear()
            print('Episode', (episode + 1))
            print(f"\nStep {step+1}/{max_steps}")
            env.render()

            # choose action 
            action = agent.greedy_act(state)

            # applies action 
            next_state, reward, done = env.step(action)

            # Updates state
            state = next_state
            
            episode_return += reward

            print(f"Episode # of cheese: {env.ep_num_treats}")

            print(f"Action: {action}")
            print(f"Reward: {reward}")
            print(f"Total: {episode_return}")

            if done:
                print("🧀 HOME REACHED. Round over!")
                print(f"Final Score: {episode_return}")
                break

            time.sleep(delay_s)

    # final frame
    # clear()
    print("\nFinal State:")
    env.render()

if __name__ == "__main__":
    main()