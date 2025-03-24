import pygame 
import pymunk

pygame.init()
disp = pygame.display.set_mode((800, 800))
clock = pygame.time.Clock()
FPS = 60
space = pymunk.Space()


def game_loop():
    while True: 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        disp.fill((255, 255, 255))
        pygame.display.update()
        clock.tick(FPS)

game_loop()
pygame.quit()