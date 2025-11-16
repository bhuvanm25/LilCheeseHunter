# main.py
import os
import time
import random
from env import GridWorld
from agent import RandomAgent
from env import ACTIONS
from collections import defaultdict

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

    num_episodes = 15000   # number of episodes to run training loop
    max_steps = 100        # max step count
    delay_s = 0.01         # delay for each step sp we can see it move

    episode_return = 0 # total points this round/episode

    # parameters for training agent

    '''- Description: Learning rate
    - Range: [0, 1]
    - Purpose: extent which new info overrides old info)
    - 1 means new data 100% of time overwrites old info
    '''
    alpha = 0.85

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
    epsilon_decay = 0.9995        # Will be multipled with epsilon to make it smaller over time 
    min_epsilon = 0.01          # Set min epsilon value to leave room for exploration even it value decreases at end

    # creates q_table to track agent's learning progress
    # q_table = np.zeros((env.observation_space.n, env.action_space.n))

    # TESTING NEW Q-TABLE  (each new state key automatically gets an empty dictionary as its value)
    q_table_dict = defaultdict(dict)

    def get_q_value(state, action):

        """Return Q(s,a), defaulting to 0.0 if unseen."""
        return q_table_dict[state].get(action, 0.0)

    # TESTING
    def choose_action2(agent, state, q_table, epsilon):

        # Generates random value to see what action to take

        # If random value generated is less than epsilon, take random action
        if (random.uniform(0, 1) < epsilon):

            print("Random action")     

            # Using agent seed to randomize actions (repeatable sequence of random actions)
            rand_action = agent.act(state)

            return rand_action
        
        # Otherwise, take best action according to Q-table at the current state
        else :

            print("Q-table based action")       

            # Goes to section of Q-table where state is relevant, goes through all actions and gives index of action with maximum Q-value
            q_values = [(get_q_value(state, a), a) for a in ACTIONS]
            
            max_q = max(q_values, key=lambda x: x[0])[0]

            # if multiple actions tie, choose among the best randomly
            best_actions = [a for (q, a) in q_values if q == max_q]

            best_action = random.choice(best_actions)

            print(f"Q-value of best action: {get_q_value(state, best_action)}")

            return best_action
        
    def choose_best_action(state):

        print("Q-table based action")       

        # Goes to section of Q-table where state is relevant, goes through all actions and gives index of action with maximum Q-value
        q_values = [(get_q_value(state, a), a) for a in ACTIONS]
            
        max_q = max(q_values, key=lambda x: x[0])[0]

        # if multiple actions tie, choose among the best randomly
        best_actions = [a for (q, a) in q_values if q == max_q]

        best_action = random.choice(best_actions)

        print(f"Q-value of best action: {get_q_value(state, best_action)}")

        return best_action

    # training loop
    for episode in range(num_episodes):

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
            # clear()
            print('\nEpisode', (episode + 1))
            print(f"\nStep {step+1}/{max_steps}")
            # env.render()

            # choose action 
            # action, action_index = env.choose_action1(agent, state, state_index, q_table, epsilon)
            action = choose_action2(agent, state, q_table_dict, epsilon)

            # applies action 
            next_state, reward, done = env.step(action)

            # get next state index
            # next_state_index = env.coord_to_state()

            # updates q-table

            old_value = get_q_value(state, action)
            next_max = max(get_q_value(next_state, a) for a in ACTIONS)

            # old_value = q_table[state_index, action_index]               # Gets Q-value of table at the specific state we currently are at and for the specific action we currently took 
            # next_max = np.max(q_table[next_state_index, :])              # Gets max Q-value/best action of next state (after we took the action)

            # updates q-table at current state and action by applying formula
            '''
            (1 - alpha) * old_value → keeps part of old info/Q-value
            alpha * (reward + gamma * next_max) → adds part of new info (rewards + discount factor * expected future rewards)
            '''
            # q_table[state_index, action_index] = (1 - alpha) * old_value + alpha * (reward + gamma * next_max)
            q_table_dict[state][action] = (1 - alpha) * old_value + alpha * (reward + gamma * next_max)

            # Updates state
            state = next_state
            # state_index = next_state_index
            
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
        epsilon = max(min_epsilon, epsilon * epsilon_decay)

    # final frame
    # clear()
    print("\nFinal State:")
    env.render()

    print("\nTraining Loop Over:")

    # rendering loop
    for episode in range(10):

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
            # action, action_index = env.choose_action1(agent, state, state_index, q_table, epsilon)
            action = choose_best_action(state)

            # applies action 
            next_state, reward, done = env.step(action)

            # get next state index
            # next_state_index = env.coord_to_state()

            # updates q-table

            old_value = get_q_value(state, action)
            next_max = max(get_q_value(next_state, a) for a in ACTIONS)

            # Updates state
            state = next_state
            # state_index = next_state_index
            
            episode_return += reward

            print(f"Episode # of cheese: {env.ep_num_treats}")

            print(f"Action: {action}")
            print(f"Reward: {reward}")
            print(f"Total: {episode_return}")

            if done:
                print("🧀 HOME REACHED. Round over!")
                print(f"Final Score: {episode_return}")
                break

            time.sleep(0.3)

    # final frame
    # clear()
    print("\nFinal State:")
    env.render()

if __name__ == "__main__":
    main()