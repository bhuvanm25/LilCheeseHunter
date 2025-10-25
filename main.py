# main.py
import os
import time
from env import GridWorld
from agent import RandomAgent

def clear():
    # clears the console screen each time its called 
    # this makes the console cleaner
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    size = 5 #innergrid
    w = size + 2 #add walls

    #makes the grid, the seed value here makes random repeatable GAME
    env = GridWorld(rows=w, cols=w, seed=1)

    #creates agent, the seed value here make random repeatable ACTIONS
    agent = RandomAgent(seed=1)

    state = env.reset() #put agent in grid

    max_steps = 100 #step count
    delay_s = 0.1 #delay for each step so we can see it move

    episode_return = 0.0 #total points this round

    for t in range(max_steps):
        """
        Clear console
        print step count
        draw grid
        make agent pick random action
        move the agent using the random action
        delay

        Repeat 
        """
        #clear()
        print(f"\nStep {t+1}/{max_steps}")
        env.render()

        action = agent.act(state)
        state, reward, done = env.step(action)
        episode_return += reward

        print(f"Action: {action}")
        print(f"Reward: {reward}")
        print(f"Total: {episode_return}")
        if done:
            print("CHEESE FOUND. Round over!")
            print(f"Final Score: {episode_return}")
            break

        time.sleep(delay_s)

    # final frame
    print("\nFinal State:")
    env.render()

if __name__ == "__main__":
    main()


