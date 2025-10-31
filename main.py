# main.py
import os
import time
from env import GridWorld
from agent import RandomAgent

import numpy as np

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
    agent = RandomAgent(seed=1)

    num_episodes = 100    # number of episodes to run training loop
    max_steps = 100       # max step count
    delay_s = 0.1         # delay for each step sp we can see it move

    episode_return = 0 # total points this round/episode

    # parameters for training agent

    '''- Description: Learning rate
    - Range: [0, 1]
    - Purpose: extent which new info overrides old info)
    - 1 means new data 100% of time overwrites old info
    '''
    alpha = 0.9

    '''
    - Description: Discount factor
    - Range: [0, 1]
    - Purpose: how important future rewards are
    - 1 means long-term focused model
    '''
    gamma = 0.95    

    '''
    - Description: Randomness/exploration rate
    - Range: [0, 1]
    - Purpose: take random action instead of using Q-table accumulated knowledge, may find reward not previously aware of
    - 1 means always take random action (good for when have lots of info), 0 means never take random action (good for starting off new)
    '''
    epsilon = 1 
    epsilon_decay = 0.95        # Will be multipled with epsilon to make it smaller over time 
    min_epsilon = 0.01          # Set min epsilon value to leave room for exploration even it value decreases at end

    # creates q_table to track agent's learning progress
    q_table = np.zeros((env.observation_space.n, env.action_space.n))

    # training loop
    for episode in range(num_episodes):

        done = False
        episode_return = 0

        state, state_index = env.reset() # put agent in grid

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

            # action = agent.act(state)

            # choose action (testing with q_table)
            action, action_index = env.choose_action(agent, state, state_index, q_table, epsilon)

            # applies action (testing with q-table)
            next_state, reward, done = env.step(action)

            # get next state index
            next_state_index = env.coord_to_state(next_state)

            # updates q-table (testing)
            old_value = q_table[state_index, action_index]               # Gets Q-value of table at the specific state we currently are at and for the specific action we currently took 
            next_max = np.max(q_table[next_state_index, :])              # Gets max Q-value/best action of next state (after we took the action)

            # updates q-table at current state and action by applying formula
            '''
            (1 - alpha) * old_value → keeps part of old info/Q-value
            alpha * (reward + gamma * next_max) → adds part of new info (rewards + discount factor * expected future rewards)
            '''
            q_table[state_index, action_index] = (1 - alpha) * old_value + alpha * (reward + gamma * next_max)

            # Updates state
            state = next_state
            state_index = next_state_index
            
            episode_return += reward

            print(f"Action: {action}")
            print(f"Reward: {reward}")
            print(f"Total: {episode_return}")

            if done:
                if (reward == -100):
                    print ("Mouse died 😵☠️💀⚰️🪦")
                    break
                elif (reward == 100):
                    print("CHEESE FOUND. Round over!")
                    print(f"Final Score: {episode_return}")
                    break

            time.sleep(delay_s)

        # Updates epsilon value at end of episode
        epsilon = max(min_epsilon, epsilon * epsilon_decay)

    # final frame
    # clear()
    print("\nFinal State:")
    env.render()

if __name__ == "__main__":
    main()
