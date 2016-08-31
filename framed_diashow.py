import pygame
from pygame import *
import os, sys
from threading import Thread

def preload_img(filename, p):
	global INDEX
	global CURRENT_IMG, CURRENT_SCALED_IMG
	global NEXT_IMG, NEXT_SCALED_IMG
	global PREVIOUS_IMG, PREVIOUS_SCALED_IMG

	old_index = int(INDEX)

	img = pygame.image.load(os.path.join(PATH, filename))
	scaled_img = fit_img(img, 0.05)

	if p == -1:
		if INDEX-old_index <= 0:
			PREVIOUS_IMG = img
			PREVIOUS_SCALED_IMG = scaled_img
	elif p == 0:
		CURRENT_IMG = img
		CURRENT_SCALED_IMG = scaled_img
	elif p == 1:
		if INDEX-old_index >= 0:
			NEXT_IMG = img
			NEXT_SCALED_IMG = scaled_img

def setup():
	global WIDTH, HEIGHT

	pygame.init()
	pygame.display.init()

	resolution = pygame.display.Info()
	WIDTH = resolution.current_w
	HEIGHT = resolution.current_h

	screen = pygame.display.set_mode((WIDTH, HEIGHT), FULLSCREEN)
	pygame.display.set_caption(CAPTION)

def toggle_fullscreen():
    screen = pygame.display.get_surface()
    tmp = screen.convert()
    caption = pygame.display.get_caption()
    cursor = pygame.mouse.get_cursor()  # Duoas 16-04-2007 
    
    w, h = screen.get_width(), screen.get_height()
    flags = screen.get_flags()
    bits = screen.get_bitsize()
    
    pygame.display.quit()
    pygame.display.init()
    
    screen = pygame.display.set_mode((w,h), flags^FULLSCREEN, bits)
    screen.blit(tmp,(0,0))
    pygame.display.set_caption(*caption)
 
    pygame.key.set_mods(0) #HACK: work-a-round for a SDL bug??
 
    pygame.mouse.set_cursor(*cursor)  # Duoas 16-04-2007
    
    return screen

def fit_img(img, border_percent):
	width, height = img.get_size()

	if width/(WIDTH*(1.-border_percent)) > height/(HEIGHT*(1.-border_percent)):
		scaled_width = WIDTH*(1.-border_percent)
		scaled_height = height*scaled_width/width
	else:
		scaled_height = HEIGHT*(1.-border_percent)
		scaled_width = width*scaled_height/height

	return pygame.transform.scale(img, (int(scaled_width), int(scaled_height)))


def update_screen():
	screen = pygame.display.get_surface()

	w, h = CURRENT_SCALED_IMG.get_size()
	img_x = (WIDTH-w)/2
	img_y = (HEIGHT-h)/2

	if LIGHTS == True:
		screen.fill((255, 255, 255))
		pygame.draw.rect(screen, (0, 0, 0), (img_x-FRAME_WIDTH, img_y-FRAME_WIDTH, w + 2*FRAME_WIDTH, h + 2*FRAME_WIDTH))
	else:
		screen.fill((0, 0, 0))
		pygame.draw.rect(screen, (255, 255, 255), (img_x-FRAME_WIDTH, img_y-FRAME_WIDTH, w + 2*FRAME_WIDTH, h + 2*FRAME_WIDTH))

	screen.blit(CURRENT_SCALED_IMG, (img_x, img_y))
	pygame.display.flip()


def main():
	global INDEX
	global LIGHTS
	global FRAME_WIDTH

	global CURRENT_IMG, CURRENT_SCALED_IMG
	global NEXT_IMG, NEXT_SCALED_IMG
	global PREVIOUS_IMG, PREVIOUS_SCALED_IMG

	running = True

	filenames = os.listdir(PATH)

	NEXT_THREAD = Thread(target = preload_img, args = (filenames[INDEX+1], 1))
	NEXT_THREAD.start()
	PREVIOUS_THREAD = Thread(target = preload_img, args = (filenames[INDEX-1], -1))
	PREVIOUS_THREAD.start()

	preload_img(filenames[INDEX], 0)

	#NEXT_THREAD.join()
	#PREVIOUS_THREAD.join()

	update_screen()


	while running:
		for e in pygame.event.get():
			if e.type is QUIT: 
				running = False
			elif e.type is KEYDOWN:
				if e.key == K_ESCAPE: 
					running = False
				elif (e.key == K_f and (e.mod & (KMOD_LALT|KMOD_RALT)) != 0):
					screen = toggle_fullscreen()
				elif e.key == K_l:
					if LIGHTS:
						LIGHTS = False
					else:
						LIGHTS = True
					update_screen()
				elif e.key == 93:
					FRAME_WIDTH += 1
					update_screen()
				elif e.key == 47:
					FRAME_WIDTH -= 1
					FRAME_WIDTH = max(0, FRAME_WIDTH)
					update_screen()
				elif e.key == K_LEFT:
					PREVIOUS_THREAD.join()

					INDEX -= 1
					if INDEX < 0:
						INDEX = len(filenames) - 1


					#NEXTThread needs to be killed!!!

					NEXT_IMG = CURRENT_IMG
					NEXT_SCALED_IMG = CURRENT_SCALED_IMG
					CURRENT_IMG = PREVIOUS_IMG
					CURRENT_SCALED_IMG = PREVIOUS_SCALED_IMG
					PREVIOUS_IMG = None
					PREVIOUS_SCALED_IMG = None
					
					PREVIOUS_THREAD = Thread(target = preload_img, args = (filenames[(INDEX-1)%len(filenames)], -1))
					PREVIOUS_THREAD.start()
					
					update_screen()
				elif e.key == K_RIGHT:
					NEXT_THREAD.join()

					INDEX += 1
					if INDEX >= len(filenames):
						INDEX = 0

					#PreviousThread needs to be killed!!!

					PREVIOUS_IMG = CURRENT_IMG
					PREVIOUS_SCALED_IMG = CURRENT_SCALED_IMG
					CURRENT_IMG = NEXT_IMG
					CURRENT_SCALED_IMG = NEXT_SCALED_IMG
					NEXT_IMG = None
					NEXT_SCALED_IMG = None
					
					NEXT_THREAD = Thread(target = preload_img, args = (filenames[(INDEX+1)%len(filenames)], 1))
					NEXT_THREAD.start()
					
					update_screen()
				else:
					print e.key
	cleanup()


def cleanup():
	pygame.display.quit()
	pygame.quit()

	sys.exit(0)

CAPTION = "Skye"
#PATH = r"E:\images\best"
PATH = r"C:\Users\Leo\Pictures\Skye"

INDEX = 0

LIGHTS = False
FRAME_WIDTH = 2

WIDTH = 0
HEIGHT = 0

CURRENT_IMG = None
CURRENT_SCALED_IMG = None
PREVIOUS_IMG = None
PREVIOUS_SCALED_IMG = None
NEXT_IMG = None
NEXT_SCALED_IMG = None

NEXT_THREAD = None
PREVIOUS_THREAD = None

if __name__ == "__main__":
	setup()
	main()
