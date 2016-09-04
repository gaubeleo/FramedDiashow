import pygame
from pygame import *
import win32gui, win32con

import os, sys
from threading import Thread

class Slideshow:
	def __init__(self, width, height, zoom=0.9, bgc=2, fc=4, preload_count=2):
		self.index = 0

		self.width = width
		self.height = height

		self.zoom = zoom
		self.background_color = bgc
		self.frame_color = fc
		self.preload_count = 5

		self.running = False

	def load(self, path, caption=None):
		self.path = path
		self.caption = caption

		if not caption:
			self.caption = os.path.rsplit(path, 1)

		print "Loading gallery '%s' from path '%s'"%(caption, path)

		self.filenames = [f for f in os.listdir(path) if f[-4:].upper() == ".JPG"]
		self.filecount = len(self.filenames)

		print "This gallery contains %i images"%(self.filecount)
		
		self.images = {}
		self.scaled_images = {}

		for filename in self.filenames:
			self.images[filename] = None
			self.scaled_images[filename] = None

		self.preload()

	def preload(self):
		for i in range(-self.preload_count, self.preload_count+1, 1):
			Thread(target = self.preload_img, args = ((self.index + i)%self.filecount,))

	def preload_img(self, index, scale=True):
		filename = self.filenames[index]

		img = pygame.image.load(os.path.join(PATH, filename))
		if scale:
			scaled_img = fit_img(filename)

		if abs(index-self.index) <= preload_count:
			self.images[filename] = img
			if scale:
				self.scaled_images[filename] = scaled_img

	def fit_img_to_zoom(self, img):
		width, height = img.get_size()

		if width/(self.width*self.zoom) >= height/(self.height*self.zoom):
			scaled_width = self.width*self.zoom
			scaled_height = height*scaled_width/width
		else:
			scaled_height = self.height*self.zoom
			scaled_width = width*scaled_height/height

		return pygame.transform.scale(img, (int(scaled_width), int(scaled_height)))


	def run(self):
		self.running = True

		self.update_screen()

		while running:
			for e in pygame.event.get():
				if e.type is QUIT: 
					self.running = False
				elif e.type is KEYDOWN:
					if e.key == K_ESCAPE: 
						self.running = False
					elif (e.key == K_f and (e.mod & (KMOD_LALT|KMOD_RALT)) != 0):
						self.screen = self.toggle_fullscreen()
					elif e.key == K_l:
						self.background_color += 1
						if self.background_color >= len(BACKGROUND_COLORS):
							self.background_color = 0
						self.update_screen()
					elif e.key == K_f:
						self.frame_color += 1
						if self.frame_color >= len(FRAME_COLORS):
							self.frame_color = 0
						self.update_screen()

					elif e.key == 93: # '+' on UX31A
						FRAME_WIDTH += 1
						self.update_screen()
					elif e.key == 47: # '-' on UX31A
						if FRAME_WIDTH > 0:
							FRAME_WIDTH -= 1
							self.update_screen()

					elif e.key == K_LEFT:
						# free up memory
						self.images[self.filenames[(self.index+self.preload_count)%self.filecount]]

						self.index -= 1
						if self.index < 0:
							self.index = len(filenames) - 1

						# wait for image to be loaded from seperate Thread
						self.threads[self.filenames[self.index]].join()

						# preload image further to the left
						self.preload_img(self.index-self.preload_count)

						self.update_screen()

					elif e.key == K_RIGHT:
						# free up memory
						self.images[self.filenames[(self.index-self.preload_count)%self.filecount]]

						self.index += 1
						if self.index >= len(filenames):
							self.index = 0

						# wait for image to be loaded from seperate Thread
						self.threads[self.filenames[self.index]].join()

						# preload image further to the left
						self.preload_img(self.index-self.preload_count)

						self.update_screen()

		cleanup()




def setup_pygame(width, height, caption, fullscreen=False):
	pygame.init()
	pygame.display.init()

	pygame.display.set_caption(cation)

	resolution = pygame.display.Info()
	w = resolution.current_w
	h = resolution.current_h

	if w != width or h != height:
		print "Slideshow is not running in optimal resolution!"
		print "current settings: (%i, %i)"%(width, height)
		print "optimal settings: (%i, %i)\n"%(w, h)

	if fullscreen:
		screen = pygame.display.set_mode((width, height), HWSURFACE|DOUBLEBUF|FULLSCREEN)
	else:
		screen = pygame.display.set_mode((width, height)) #, RESIZABLE

		hwnd = win32gui.GetForegroundWindow()
		win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)


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


def update_screen():
	screen = pygame.display.get_surface()

	w, h = CURRENT_SCALED_IMG.get_size()
	img_x = (WIDTH-w)/2
	img_y = (HEIGHT-h)/2

	screen.fill(background_color)
	pygame.draw.rect(screen, frame_color, (img_x-FRAME_WIDTH, img_y-FRAME_WIDTH, w + 2*FRAME_WIDTH, h + 2*FRAME_WIDTH))

	screen.blit(CURRENT_SCALED_IMG, (img_x, img_y))
	pygame.display.flip()


def cleanup():
	pygame.display.quit()
	pygame.quit()

	sys.exit(0)


BACKGROUND_COLORS = [(0, 0, 0), (60, 60, 60), (120, 120, 120), (200, 200, 200), (255, 255, 255)]
FRAME_COLORS = [(0, 0, 0), (60, 60, 60), (120, 120, 120), (200, 200, 200), (255, 255, 255)]

if __name__ == "__main__":
	print "Slideshow - created by Leo Gaube - 2016\n"

	slideshow = Slideshow(1920, 1080)
	slideshow.load(r"C:\Users\Leo\Pictures\Skye", caption=r"Skye")
	slideshow.run()
