# TASHA IS LORD
All hail Tasha!

#Pygame inserting images:

In env.py
In order to get images, can use jpg or png
wall_img_old = pygame.image.load('wall.png').convert_alpha()
To change size
wall_img = pygame.transform.scale(wall_img_old, (20, 20))

Then inside main of env.py, in the while running loop
x = 0
y = 0
        for ii in range(12):
            x = 0
            for i in range(12):
                screen.blit(wall_img, (x,y)) #To put an image
                x += 20
            y += 20











#Notes:
Using this website to help develop the learning curve: https://codesignal.com/learn/courses/game-on-integrating-rl-agents-with-environments/lessons/visualizing-training-statistics-in-reinforcement-learning
Using number of steps, if successful, and reward system to plot. 
Can you the q table anaysis as well, do that after set up this stuff because you'll have to figure out how to get it from the env.py to main.py
