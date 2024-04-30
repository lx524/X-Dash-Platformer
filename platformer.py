import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()  # initialize the pygame module

# A caption for display (at the top of the window)
pygame.display.set_caption("X-Dash Platformer")

# Define a few global variables
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 10  # Player velocity

# Set up pygame window
window = pygame.display.set_mode((WIDTH, HEIGHT))


# Function that flips the image (of character's status) or is called 'sprite'.
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


# Function that loads the sprite sheets for the character.
# Within the character, we can pick what sheet we want to use, what animations we want to loop through.
# Notice: with dir1 and dir2, we can load other images that aren't just the characters and this will be
#  very dynamic.
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)  # path to the images we're going to be loading
    images = [f for f in listdir(path) if isfile(join(path, f))]  # loads every file inside the dir

    all_sprites = {}  # key = animation style, value = all the images in that animation

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        # convert.alpha() loads a transparent background image

        # Get all the sprites in the image
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            # draw an animation frame from image onto the surface of exact size
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)  # 32 is the depth
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)  # 'blit' means 'draw'
            sprites.append(pygame.transform.scale2x(surface))  # double size: 64 by 64

            # Want a multi-directional animation, add two keys to our dictionary 'sprites'
            #  for every one of the animations
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


# Function that gets our blocks
def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)  # (96, 0) is the coordinate of top left corner of block
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


# Character Selection Interface
def character_selection():
    selected_character = None
    font = pygame.font.SysFont(None, 50)    # Define font for text
    text = font.render("Select Your Character", True, (0, 0, 0))  # Render text
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))   # Calculate text position

    # Create character buttons
    character_buttons = []
    characters = ["MaskDude", "NinjaFrog", "PinkMan", "VirtualGuy"]
    button_width = 200
    button_height = 100
    button_gap = 50
    total_width = (button_width + button_gap) * len(characters) # Total width of all character buttons
        
    # Create Rect objects for each character button
    for i, char in enumerate(characters):
        x = (WIDTH - total_width) // 2 + i * (button_width + button_gap) + 25
        y = HEIGHT // 2
        button_rect = pygame.Rect(x, y, button_width, button_height)
        character_buttons.append((button_rect, char))   # Add button Rect and character name to list
    
    # Main loop for character selection
    while not selected_character:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                for button in character_buttons:
                    if button[0].collidepoint(event.pos):
                        selected_character = button[1]

        # Clear screen
        window.fill((173, 216, 230))

        # Display text
        window.blit(text, text_rect)

        # Draw character buttons
        for button in character_buttons:
            pygame.draw.rect(window, (255, 0, 0), button[0])
            char_text = font.render(button[1], True, (255, 255, 255))
            char_text_rect = char_text.get_rect(center=button[0].center)
            window.blit(char_text, char_text_rect)

        pygame.display.update()

    return selected_character


# Inheriting from this pygame class for our Player
class Player(pygame.sprite.Sprite):
    COLOUR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", character_selection(), 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.sprite = None
        self.rect = pygame.Rect(x, y, width, height)  # on rectangle to make it easier to move and collide
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0  # tell us how long the character has been in the air for...
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel):
        self.x_vel = - vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    # loop is called once every frame (1 iteration of the while loop)
    # This is going to move our character in the correct direction and handle things like updating
    #   the animation and all the stuff that we constantly need to do for our character
    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        # For every frame in the loop, we increase y_vel by our gravity
        #  (varies on how long the character has been falling for)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    # update our sprite every single frame
    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:  # means moving up
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.x_vel != 0:
            sprite_sheet = "run"
        elif self.y_vel > self.GRAVITY * 2:  # not > 0 because y_vel is always > 0 due to gravity
            sprite_sheet = "fall"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)  # make sprite dynamic
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))

    # Constantly update the rectangle that bounds our character based on the sprite that we're showing
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # A mask is a mapping of all the pixels that exist in the sprite
        #  This mask allows us to perform pixel perfect collision because we can overlap it with another
        #  mask and make sure that  we only say two objects collide if pixels (not the rectangular box)
        #  are colliding.
        self.mask = pygame.mask.from_surface(self.sprite)

    # Character lands on an object: character stops...
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0  # comment this later..........

    # Character hits head (collide with bottom of an object)
    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -0.8

    # Character jumps
    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0  # reset to remove any gravity accumulated

    # Character get hit (ex. by fire...)
    def make_hit(self):
        self.hit = True


# Class for all the objects, inherit from this class for specific objects
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()  # Initialize the superclass
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)  # pygame.SRCALPHA supports transparent images
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


# Class for blocks
class Block(Object):
    def __init__(self, x, y, size):  # A block is a square, just need one dimension
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


# Class for fire (trap)
class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop_fire(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):  # so that animation_count doesn't get too large
            self.animation_count = 0


# Returns a list that contains all the background tiles aht we need to draw
def get_background(name):  # name = colour of background
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()  # don't care about '_' values??
    tiles = []

    # Loop through how many tiles that need to be created in the x and y direction
    for i in range(WIDTH // width + 1):
        for j in range (HEIGHT // height + 1):
            pos = (i * width, j * height)  # position of the top left corner of the current
                                           #   tile that I'm adding to the tiles list in pygame
            tiles.append(pos)

    return tiles, image


# Draw function
def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:  # looping through every tile and then draw bg_image at that position
        window.blit(bg_image, tile)  #   which will fill the entire screen with bg_image

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


# Function that handles vertical collision
def handle_vertical_collision(player, objects, dy):  # dy = displacement in y
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:  # if character moves down, colliding with the top of the obj
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


#  Function that handles horizontal collision
def collide(player, objects, dx):
    player.move(dx, 0)  # move the character
    player.update()  # update the mask
    collided_obj = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):  # check collide if moving in that direction
            collided_obj = obj
            break

    player.move(-dx, 0)  # move the character back after the check for collision
    player.update()  # update the mask again
    return collided_obj


# Inside this function, check for keys being pressed on the keyboard to
#   move the character (and check for collision)
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0  # ensure that character only moves to certain direction when we hold the certain key
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)  # move the character to the left by its velocity
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()


# Main function (start the game)
def main():
    clock = pygame.time.Clock()
    background, bg_image = get_background("Yellow.png")

    block_size = 96

    selected_character = character_selection()
    player = Player(100, 100, 50, 50)


    # Blocks filling not just the current screen (will implement scrolling background):
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 5) // block_size)]

    tile1 = [Block(i * block_size, HEIGHT - block_size * 4, block_size)
             for i in range(5, (WIDTH * 2) // block_size)]

    fire = Fire(100, HEIGHT - block_size - 64, 16, 32)
    fire.on()
    objects = [* floor, * tile1, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size), fire]

    # For scrolling background
    offset_x = 0
    scroll_area_width = 300

    run = True
    while run:
        clock.tick(FPS)  # ensure running no more than 60 fps

        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # if the user quits the game, stop the event loop and exit
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:  # allows double jumping
                    player.jump()

        player.loop(FPS)  # before handle_move because loop is what actually moves the player
        fire.loop_fire()
        handle_move(player, objects)  # before calling draw function
        draw(window, background, bg_image, player, objects, offset_x)

        # Scrolling bg: simply offset things we draw on the screen by a certain amount
        # - start scrolling if it gets to 200 pixels to the left or to the right
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or \
                ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


# Only call the main function if we run this file directly
if __name__ == "__main__":
    main()
