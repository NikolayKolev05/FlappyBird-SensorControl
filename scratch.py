import pygame
from sys import exit
import random
import serial

pygame.init()
clock = pygame.time.Clock()
arduino = serial.Serial('COM5', 9600)
win_height = 720
win_widht = 551

window = pygame.display.set_mode((win_widht, win_height))

bird_images = [pygame.image.load("flappy/bird_down.png"),
               pygame.image.load("flappy/bird_mid.png"),
               pygame.image.load("flappy/bird_up.png"),]
skyline_image = pygame.image.load("flappy/background.png")
ground_image = pygame.image.load("flappy/ground.png")
game_over_image = pygame.image.load("flappy/game_over.png")
pipe_bottom_image = pygame.image.load("flappy/pipe_bottom.png")
pipe_up_image = pygame.image.load("flappy/pipe_top.png")
start_image = pygame.image.load("flappy/start.png")

scroll_speed = 1
bird_start_position = (100, 250)
score = 0
font = pygame.font.SysFont('Segoe', 26)
game_stopped = True
high_score = 0


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = bird_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = bird_start_position
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.alive = True

    def update(self, user_input):
        if self.alive:
            self.image_index += 1
        if self.image_index >= 30:
            self.image_index = 0
        self.image = bird_images[self.image_index // 10]
        if self.alive:
            self.vel += 0.5
            if self.vel > 7:
                self.vel = 7
            if arduino.in_waiting > 0:
                distance = int(arduino.readline().decode().strip())
                if distance < 20:
                    self.rect.y += int(self.vel)
                else:
                    self.rect.y -= int(self.vel)
            if self.vel == 0:
                self.flap = False
            if self.flap:
                self.image = pygame.transform.rotate(self.image, 20)  # Face upward when flapping
            else:
                self.image = pygame.transform.rotate(self.image, -20)  # Face downward when falling
            if user_input[pygame.K_SPACE] and not self.flap and self.rect.y > 0:
                self.flap = True
                self.vel = -7

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, pipe_type):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.enter, self.exit, self.passed = False, False, False
        self.pipe_type = pipe_type

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_widht:
            self.kill()

        global score
        if self.pipe_type == 'bottom':
            if bird_start_position[0] > self.rect.topleft[0] and not self.passed:
                self.enter = True
            if bird_start_position[0] > self.rect.topright[0] and not self.passed:
                self.exit = True
            if self.enter and self.exit and not self.passed:
                self.passed = True
                score += 1

class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = ground_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_widht:
            self.kill()

def quit_game():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

def main():
    global score, scroll_speed, high_score
    level = 1
    scroll_speed = 1
    bird = pygame.sprite.GroupSingle()
    bird.add(Bird())
    pipe_timer = 0
    pipes = pygame.sprite.Group()
    x_pos_ground, y_pos_ground = 0, 520
    ground = pygame.sprite.Group()
    ground.add(Ground(x_pos_ground, y_pos_ground))
    run = True
    while run:
        quit_game()
        window.fill((0, 0, 0))
        user_input = pygame.key.get_pressed()
        window.blit(skyline_image, (0, 0))
        if len(ground) <= 2:
            ground.add(Ground(win_widht, y_pos_ground))
        pipes.draw(window)
        ground.draw(window)
        bird.draw(window)
        score_text = font.render('Score: ' + str(score), True, pygame.Color(255, 255, 255))
        high_score_text = font.render('High Score: ' + str(high_score), True, pygame.Color(255, 255, 255))
        level_text = font.render('Level: ' + str(level), True, pygame.Color(255, 255, 255))
        window.blit(score_text, (20, 20))
        window.blit(high_score_text, (20, 50))
        window.blit(level_text, (20, 80))
        if bird.sprite.alive:
            pipes.update()
            ground.update()
        bird.update(user_input)
        collision_pipes = pygame.sprite.spritecollide(bird.sprites()[0], pipes, False)
        collision_ground = pygame.sprite.spritecollide(bird.sprites()[0], ground, False)
        if collision_pipes or collision_ground:
            bird.sprite.alive = False
            if score > high_score:
                high_score = score
            window.blit(game_over_image, (win_widht // 2 - game_over_image.get_width() // 2,
                                          win_height // 2 - game_over_image.get_height() // 2))
            if user_input[pygame.K_r]:
                score = 0
                scroll_speed = 1
                break
        if pipe_timer <= 0 and bird.sprite.alive:
            x_top, x_bottom = 550, 550
            y_top = random.randint(-600, -480)
            gap_size = random.randint(120, 250)  # Increase the gap range
            y_bottom = y_top + gap_size + pipe_bottom_image.get_height()
            pipes.add(Pipe(x_top, y_top, pipe_up_image, 'top'))
            pipes.add(Pipe(x_bottom, y_bottom, pipe_bottom_image, 'bottom'))
            pipe_timer = int(180 / scroll_speed)
        pipe_timer -= 1
        if score % 2 == 0 and score > 0:
            level = score // 2 + 1
            scroll_speed = 1 + (level - 1)
        clock.tick(60)
        pygame.display.update()
def quit_game():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            arduino.close()
            pygame.quit()
            exit()
def menu():
    global game_stopped
    while game_stopped:
        quit_game()
        window.fill((0, 0, 0))
        window.blit(skyline_image, (0, 0))
        window.blit(ground_image, Ground(0, 520))
        window.blit(bird_images[0], (100, 250))
        window.blit(start_image, (win_widht // 2 - start_image.get_width() // 2,
                                  win_height // 2 - start_image.get_height() // 2))
        user_input = pygame.key.get_pressed()
        if user_input[pygame.K_SPACE]:
            main()
        pygame.display.update()
menu()