import pygame
from pygame import *
import win32gui, win32con

import os, sys
from threading import Thread

class DummyThread:
	def __init__(self):
		pass

	def join(self):
		pass

class Slideshow:
	def __init__(self, width, height, fullscreen=True, zoom=0.9, bgc=1, fc=4, fs=3, pc=3):
		self.index = 0

		self.width = width
		self.height = height
		self.fullscreen = fullscreen

		self.zoom = zoom
		self.background_color = bgc
		self.frame_color = fc
		self.frame_size = fs
		self.preload_count = pc

		self.framerate = 30
		self.running = False

	def load(self, path, caption=None):
		self.path = path
		self.caption = caption

		if not caption:
			self.caption = os.path.rsplit(path, 1)

		print "Loading gallery '%s' from path '%s'"%(caption, path)

		self.filenames = [f for f in os.listdir(path) if f[-4:].upper() == ".JPG"]
		self.file_count = len(self.filenames)

		print "This gallery contains %i images"%(self.file_count)
		
		self.images = {}
		self.scaled_images = {}
		self.threads = {}

		for filename in self.filenames:
			self.images[filename] = None
			self.scaled_images[filename] = None
			self.threads[filename] = None

		self.preload()

	def preload(self):
		for i in range(1, self.preload_count+1, 1):
			self.threads[self.filenames[(self.index + i)%self.file_count]] = Thread(target = self.preload_img, args = ((self.index + i)%self.file_count,))
			self.threads[self.filenames[(self.index + i)%self.file_count]].start()
			self.threads[self.filenames[(self.index - i)%self.file_count]] = Thread(target = self.preload_img, args = ((self.index - i)%self.file_count,))
			self.threads[self.filenames[(self.index - i)%self.file_count]].start()

		self.preload_img(self.index)
		self.threads[self.filenames[self.index]] = DummyThread()

	def preload_img(self, index, scale=True):
		filename = self.filenames[index]

		img = pygame.image.load(os.path.join(self.path, filename))
		if scale:
			scaled_img = self.fit_img_to_zoom(img)

		if abs(index-self.index) <= self.preload_count or abs(index-self.index) >= self.file_count-self.preload_count:
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

		while self.running:
			for e in pygame.event.get():
				if e.type is QUIT: 
					self.running = False
				elif e.type is KEYDOWN:
					if e.key == K_ESCAPE: 
						self.running = False
					elif (e.key == K_f and (e.mod & (KMOD_LALT|KMOD_RALT)) != 0):
						self.toggle_fullscreen()

					elif e.key == K_k:
						self.background_color -= 1
						if self.background_color < 0:
							self.background_color = len(BACKGROUND_COLORS)-1
						self.update_screen()
					elif e.key == K_l:
						self.background_color += 1
						if self.background_color >= len(BACKGROUND_COLORS):
							self.background_color = 0
						self.update_screen()

					elif e.key == K_i:
						self.frame_color -= 1
						if self.frame_color < 0:
							self.frame_color = len(FRAME_COLORS)-1
						self.update_screen()
					elif e.key == K_o:
						self.frame_color += 1
						if self.frame_color >= len(FRAME_COLORS):
							self.frame_color = 0
						self.update_screen()

					elif e.key in [K_PLUS, K_KP_PLUS, 93]: # 93 is '+' on UX31A
						self.frame_size += 1
						self.update_screen()
					elif e.key in [K_MINUS, K_KP_MINUS, 47]: # 47 is '-' on UX31A
						if self.frame_size > 0:
							self.frame_size -= 1
							self.update_screen()

					elif e.key == K_LEFT:
						# free up memory
						self.images[self.filenames[(self.index+self.preload_count)%self.file_count]] = None
						self.scaled_images[self.filenames[(self.index+self.preload_count)%self.file_count]] = None
						self.threads[self.filenames[(self.index+self.preload_count)%self.file_count]] = None

						self.index -= 1
						if self.index < 0:
							self.index = self.file_count - 1

						# wait for image to be loaded from seperate Thread
						self.threads[self.filenames[self.index]].join()

						# preload image further to the left
						self.threads[self.filenames[(self.index - self.preload_count)%self.file_count]] = Thread(target = self.preload_img, args = ((self.index - self.preload_count)%self.file_count,))
						self.threads[self.filenames[(self.index - self.preload_count)%self.file_count]].start()

						self.update_screen()

					elif e.key == K_RIGHT:
						# free up memory
						self.images[self.filenames[(self.index-self.preload_count)%self.file_count]] = None
						self.scaled_images[self.filenames[(self.index-self.preload_count)%self.file_count]] = None
						self.threads[self.filenames[(self.index-self.preload_count)%self.file_count]] = None

						self.index += 1
						if self.index >= self.file_count:
							self.index = 0

						# wait for image to be loaded from seperate Thread
						self.threads[self.filenames[self.index]].join()

						# preload image further to the right
						self.threads[self.filenames[(self.index + self.preload_count)%self.file_count]] = Thread(target = self.preload_img, args = ((self.index + self.preload_count)%self.file_count,))
						self.threads[self.filenames[(self.index + self.preload_count)%self.file_count]].start()

						self.update_screen()

			self.clock.tick(self.framerate)

		self.cleanup()

	def setup_pygame(self):
		pygame.init()
		pygame.display.init()

		pygame.display.set_caption(self.caption)

		resolution = pygame.display.Info()
		w = resolution.current_w
		h = resolution.current_h

		if w != self.width or h != self.height:
			print "Slideshow is not running in optimal resolution!"
			print "current settings: (%i, %i)"%(self.width, self.height)
			print "optimal settings: (%i, %i)\n"%(w, h)

		if self.fullscreen:
			self.screen = pygame.display.set_mode((self.width, self.height), HWSURFACE|DOUBLEBUF|FULLSCREEN)
		else:
			self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)

			hwnd = win32gui.GetForegroundWindow()
			win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

		# Other pygame functions
		self.clock = pygame.time.Clock()
		pygame.key.set_repeat(400)


	def toggle_fullscreen(self):
		tmp = self.screen.convert()

		#flags = self.screen.get_flags()
		#bits = self.screen.get_bitsize()

		pygame.display.quit()
		pygame.display.init()

		pygame.display.set_caption(self.caption)
		
		if not self.fullscreen:
			self.screen = pygame.display.set_mode((self.width, self.height), HWSURFACE|DOUBLEBUF|FULLSCREEN)
			self.fullscreen = True
		else:
			self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)

			hwnd = win32gui.GetForegroundWindow()
			win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

			self.fullscreen = False

		self.screen.blit(tmp, (0,0))
		pygame.display.flip()
	 
		#pygame.key.set_mods(0) #HACK: work-a-round for a SDL bug??
		#pygame.mouse.set_cursor(*cursor)  # Duoas 16-04-2007


	def update_screen(self):
		img = self.scaled_images[self.filenames[self.index]]

		w, h = img.get_size()
		img_x = (self.width-w)/2
		img_y = (self.height-h)/2

		self.screen.fill(BACKGROUND_COLORS[self.background_color])
		pygame.draw.rect(self.screen, FRAME_COLORS[self.frame_color], (img_x-self.frame_size, img_y-self.frame_size, w + 2*self.frame_size, h + 2*self.frame_size))

		self.screen.blit(img, (img_x, img_y))
		pygame.display.flip()


	def cleanup(self):
		pygame.display.quit()
		pygame.quit()

		sys.exit(0)


BACKGROUND_COLORS = [(0, 0, 0), (60, 60, 60), (120, 120, 120), (200, 200, 200), (255, 255, 255)]
FRAME_COLORS = [(0, 0, 0), (60, 60, 60), (120, 120, 120), (200, 200, 200), (255, 255, 255)]

if __name__ == "__main__":
	print "Slideshow - created by Leo Gaube - 2016\n"

	slideshow = Slideshow(1920, 1080)
	slideshow.load(r"C:\Users\Leo\Pictures\Skye", caption=r"Skye")
	slideshow.setup_pygame()
	slideshow.run()
