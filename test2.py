# Making a taxi game that learns how to find customers and drop them off at hotel

import random
import gymnasium as gym
import numpy as np

# Intializes the environment provided by gymnasium
env = gym.make('Taxi-v3')

# Defines parameters for training loop

'''
- Description: Learning rate
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
epsilon_decay = 0.9995      # Will be multipled with epsilon to make it smaller over time 
min_epsilon = 0.01          # Set min epsilon value to leave room for exploration even it value decreases at end

num_episodes = 10000        # Number of times agent plays the game

max_steps = 100             # Max number of steps agent can take per episode (forces it to terminate at certain point)

# Initializes Q-table 
'''
- Q-table is a numpy array filled with 0's
- Has the shape of the environment's observation space
- Has a certain # of observation spaces 
    → how many possible states can game be in
    → how many actions can I take per state
- Contains all the possible states the game can be in, with all possible actions I can take in each state
'''    
# Taxi environment specifics
'''
5x5 grid → 25 positions taxi can be in
5 different coloured squares for customers to be in
4 different locations where hotel can be located
25 * 5 * 4 = 500 different states game can be in
Car can take 4 actions (up, down, left, right) in all these states
'''

'''
For each state, each action will have a Q-value
- Tells you how good this action is
- How much rewards is anticipated by taking this action
When starting, all Q-values start off at 0
'''
# NOTE: this Q-table is not applicable to any other version of the game, is specific to this particular problem on this particular map
q_table = np.zeros((env.observation_space.n, env.action_space.n))

# Chooses action depending on given state
def choose_action(state):

    # Generates random value to see what action to take

    # If random value generated is less than epsilon, take random action
    if (random.uniform(0, 1) < epsilon):

        # Returns any action from the action space
        return env.action_space.sample()
    
    # Otherwise, take best action according to Q-table at the current state
    else :

        # Goes to section of Q-table where state is relevant, goes through all actions and gives index of action with maximum Q-value
        return np.argmax(q_table[state, :])
    

# Training loop
for episode in range(num_episodes):

    # Start with new/empty environment (resets it + gives us random starting point)
    # NOTE: look into how to begin at same starting point
    state, _ = env.reset()

    done = False    # Boolean flag to check if should terminate training

    print('Episode', episode)

    # Loop to max # steps agent can take per episode
    for step in range(max_steps):
        
         # Calls function to choose an action based on the state and store its value
        action = choose_action(state)               

        # Calls function to actually apply/do the action 
        # NOTE: Look into how to include punishment
        # NOTE: Look into how reward system is set up, how it is defined (success of picking up customer, or shortest path to hotel?)
        next_state, reward, done, truncated, info = env.step(action) 

        # Updates Q-table

        old_value = q_table[state, action]               # Gets Q-value of table at the specific state we currently are at and for the specific action we currently took 
        next_max = np.max(q_table[next_state, :])        # Gets max Q-value/best action of next state (after we took the action)

        # Updates Q-table at current state and action by applying formula
        '''
        (1 - alpha) * old_value → keeps part of old info/Q-value
         alpha * (reward + gamma * next_max) → adds part of new info (rewards + discount factor * expected future rewards)
        '''
        q_table[state, action] = (1 - alpha) * old_value + alpha * (reward + gamma * next_max)

        # Updates state
        state = next_state

        # Checks done or truncated conditions
        if (done or truncated):

            print('Finished episode', episode, 'with reward', reward)
            break

    # Updates epsilon value at end of episode
    epsilon = max(min_epsilon, epsilon * epsilon_decay)

print("Training loop finished!")

# Initialize environment again to see what is happening after the running training loop
# Not training, just viewing results in action
env = gym.make('Taxi-v3', render_mode='human')

# Seeing how agent performs across 5 episodes
for episode in range(5):
    state, _ = env.reset()

    done = False

    print('Episode', episode)

    for step in range(max_steps):

        env.render()                                                    # Rendering environment to visualize it

        action = np.argmax(q_table[state, :])                           # Always pick action that results in max Q-value for current state
        next_state, reward, done, truncated, info = env.step(action)    # Actually apply action
        state = next_state                                              # Update state

        if (done or truncated): 
            env.render()
            print('Finished episode', episode, 'with reward', reward)
            break

# Close environment after finishing
env.close()

        
