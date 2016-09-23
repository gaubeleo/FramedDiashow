import pygame
from pygame.constants import *
import win32gui, win32con

import os, sys, time
from math import sqrt
from threading import Thread, Timer

SLOW = 0.35
FAST = 0.1

class DummyThread:
	def __init__(self):
		pass

	def join(self):
		pass


class Slideshow:
	def __init__(self, width=1920, height=1080, fullscreen=False, dur=3, zoom=0.9, bgc=1, fc=4, fs=3, pc=3):
		self.index = 0

		self.width = width
		self.height = height
		self.fullscreen = fullscreen
		self.play = False
		self.duration = dur

		self.zoom = zoom
		self.alpha = 255
		self.background_color = bgc
		self.frame_color = fc
		self.frame_size = fs
		self.preload_count = pc

		self.framerate = 30
		self.running = False
		self.play_thread = None

	def load(self, path, caption=None):
		self.path = path
		self.caption = caption

		if not caption:
			self.caption = os.path.rsplit(path, 1)

		print "Loading gallery '%s' from path '%s'"%(caption, path)

		self.filenames = [f for f in os.listdir(path) if f[-4:].upper() == ".JPG"]
		self.file_count = len(self.filenames)

		print "This gallery contains %i images\n"%(self.file_count)
		
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
			self.threads[self.filenames[(self.index + i)%self.file_count]] = Thread(target=self.preload_img, args=((self.index + i)%self.file_count,))
			self.threads[self.filenames[(self.index + i)%self.file_count]].start()
			self.threads[self.filenames[(self.index - i)%self.file_count]] = Thread(target=self.preload_img, args=((self.index - i)%self.file_count,))
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

		self.create_new_frame()
		self.draw()
		self.update_screen()

		while self.running:
			for e in pygame.event.get():
				if e.type is QUIT: 
					self.running = False
				elif e.type == FORCE_NEXT:
					self.next_img(dur=SLOW)
				elif e.type is KEYDOWN:
					if e.key == K_ESCAPE: 
						self.running = False
					elif (e.key == K_f and (e.mod & (KMOD_LALT|KMOD_RALT)) != 0):
						if not self.fullscreen:
							self.set_fullscreen()
						else:
							if self.play:
								self.play = False
								self.play_thread.cancel()
							self.set_windowed()

					elif e.key == K_SPACE:
						if not self.play:
							self.play = True
							if not self.fullscreen:
								self.set_fullscreen()
							self.play_thread = Timer(self.duration, self.force_next_img, args=())
							self.play_thread.start()
						else:
							self.play = False
							self.play_thread.cancel()

					elif e.key == K_a:
						if self.play:
							self.play_thread.cancel()

						self.smooth_zoom()
						self.draw()
						self.update_screen()

						if self.play:
							self.play_thread = Timer(self.duration, self.force_next_img, args=())
							self.play_thread.start()

					elif e.key == K_k:
						self.background_color -= 1
						if self.background_color < 0:
							self.background_color = len(BACKGROUND_COLORS)-1
						self.draw()
						self.update_background()
					elif e.key == K_l:
						self.background_color += 1
						if self.background_color >= len(BACKGROUND_COLORS):
							self.background_color = 0
						self.draw()
						self.update_background()

					elif e.key == K_i:
						self.frame_color -= 1
						if self.frame_color < 0:
							self.frame_color = len(FRAME_COLORS)-1
						self.create_new_frame()
						self.draw()
						self.update_framed_background()
					elif e.key == K_o:
						self.frame_color += 1
						if self.frame_color >= len(FRAME_COLORS):
							self.frame_color = 0
						self.create_new_frame()
						self.draw()
						self.update_framed_background()

					elif e.key in [K_PLUS, K_KP_PLUS, 93]: # 93 is '+' on UX31A
						self.frame_size += 1
						self.create_new_frame()
						self.draw()
						self.update_framed_background()
					elif e.key in [K_MINUS, K_KP_MINUS, 47]: # 47 is '-' on UX31A
						if self.frame_size > 0:
							self.frame_size -= 1
							self.create_new_frame()
							self.draw()
							self.update_framed_background()

					elif e.key == K_LEFT:
						self.previous_img()

					elif e.key == K_RIGHT:
						self.next_img()

			self.clock.tick(self.framerate)

		self.cleanup()

	# this function should only be executed py the play_thread
	def force_next_img(self):
		my_event = pygame.event.Event(FORCE_NEXT)
		pygame.event.post(my_event)

	def previous_img(self, dur=FAST):
		# free up memory
		self.images[self.filenames[(self.index+self.preload_count)%self.file_count]] = None
		self.scaled_images[self.filenames[(self.index+self.preload_count)%self.file_count]] = None
		self.threads[self.filenames[(self.index+self.preload_count)%self.file_count]] = None

		self.fadeout_img(move="none", dur=dur)

		self.index -= 1
		if self.index < 0:
			self.index = self.file_count - 1

		# wait for image to be loaded from seperate Thread
		self.threads[self.filenames[self.index]].join()

		self.create_new_frame()
		self.fadein_img(move="none", dur=dur) #down

		# preload image further to the left
		self.threads[self.filenames[(self.index - self.preload_count)%self.file_count]] = Thread(target = self.preload_img, args = ((self.index - self.preload_count)%self.file_count,))
		self.threads[self.filenames[(self.index - self.preload_count)%self.file_count]].start()

		if self.play:
			self.play_thread.cancel()
			self.play_thread = Timer(self.duration, self.force_next_img, args=())
			self.play_thread.start()

	def next_img(self, dur=FAST):
		# free up memory
		self.images[self.filenames[(self.index-self.preload_count)%self.file_count]] = None
		self.scaled_images[self.filenames[(self.index-self.preload_count)%self.file_count]] = None
		self.threads[self.filenames[(self.index-self.preload_count)%self.file_count]] = None

		self.fadeout_img(move="none", dur=dur)

		self.index += 1
		if self.index >= self.file_count:
			self.index = 0

		# wait for image to be loaded from seperate Thread
		self.threads[self.filenames[self.index]].join()

		self.create_new_frame()
		self.fadein_img(move="none", dur=dur) #up

		# preload image further to the right
		self.threads[self.filenames[(self.index + self.preload_count)%self.file_count]] = Thread(target = self.preload_img, args = ((self.index + self.preload_count)%self.file_count,))
		self.threads[self.filenames[(self.index + self.preload_count)%self.file_count]].start()

		if self.play:
			self.play_thread.cancel()
			self.play_thread = Timer(self.duration, self.force_next_img, args=())
			self.play_thread.start()

	def smooth_zoom(self, dur=0.5, hold=2., zoom=2.5):
		old_zoom = self.zoom

		frames = int(self.framerate*dur)

		kA= map(lambda x: sqrt(-(float(x)/frames) + 1), range(frames)) # sqrt(-x + 1) flips the graph aroung and shifts it to the right
		summe = sum(kA)
		kO = (zoom-self.zoom)/summe

		for zoom_shift in kA:
			self.zoom += zoom_shift*kO

			self.img = self.fit_img_to_zoom(self.images[self.filenames[self.index]])
			self.img_w, self.img_h = self.img.get_size()
			self.img_x = (self.width-self.img_w)/2
			self.img_y = (self.height-self.img_h)/2

			self.draw(frame=False)
			self.update_screen()

		time.sleep(hold)
		self.zoom = old_zoom
		self.create_new_frame()
		self.draw(frame=False)
		self.update_screen()


	def fadeout_img(self, dur=FAST, move="None"):
		frames = int(self.framerate*dur)

		transparency_shift = 255//frames
		assert(transparency_shift > 0)
		self.alpha = int(transparency_shift*frames)
		assert(self.alpha <= 255)

		x_shift = 0
		y_shift = 0
		if move == "left":
			x_shift = -((self.width//25)//frames)
		elif move == "right":
			x_shift = (self.width//25)//frames
		elif move == "up":
			y_shift = -((self.height//25)//frames)
		elif move == "down":
			y_shift = (self.height//25)//frames

		for frame in range(frames):
			self.alpha -= transparency_shift

			self.img_x += x_shift
			self.frame_x += x_shift
			x_extended = -x_shift

			self.img_y += y_shift
			self.frame_y += y_shift
			y_extended = -y_shift

			self.draw()
			self.update_framed_image(x_extended=x_extended, y_extended=y_extended)

			self.clock.tick(self.framerate)
		self.alpha = 255

	def fadein_img(self, dur=FAST, move="None"):
		frames = int(self.framerate*dur)

		transparency_shift = 255//frames
		assert(transparency_shift > 0)
		self.alpha = int(255-(transparency_shift*frames))
		assert(self.alpha >= 0)

		x_shift = 0
		y_shift = 0
		if move == "left":
			x_shift = -((self.width//25)//frames)
			self.img_x += abs(x_shift)*frames
			self.frame_x += abs(x_shift)*frames
		elif move == "right":
			x_shift = (self.width//25)//frames
			self.img_x -= x_shift*frames
			self.frame_x -= x_shift*frames
		elif move == "up":
			y_shift = -((self.height//25)//frames)
			self.img_y += abs(y_shift)*frames
			self.frame_y += abs(y_shift)*frames
		elif move == "down":
			y_shift = (self.height//25)//frames
			self.img_y -= y_shift*frames
			self.frame_y -= y_shift*frames

		for frame in range(frames):
			self.alpha += transparency_shift

			self.img_x += x_shift
			self.frame_x += x_shift
			x_extended = -x_shift

			self.img_y += y_shift
			self.frame_y += y_shift
			y_extended = -y_shift

			self.draw()
			self.update_framed_image(x_extended=x_extended, y_extended=y_extended)

			self.clock.tick(self.framerate)
		self.alpha = 255

	def setup_pygame(self):
		# control main loop rounds per second
		self.clock = pygame.time.Clock()

		# Initialize Music Player
		#pygame.mixer.init()

		# Initialize Display
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

		# holding down a key will fire a repeated event after 500ms
		pygame.key.set_repeat(500)

	def set_windowed(self):
		tmp = self.screen.convert()

		#flags = self.screen.get_flags()
		#bits = self.screen.get_bitsize()

		pygame.display.quit()
		pygame.display.init()

		pygame.display.set_caption(self.caption)
		
		self.screen = pygame.display.set_mode((self.width, self.height), RESIZABLE)

		hwnd = win32gui.GetForegroundWindow()
		win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

		self.screen.blit(tmp, (0, 0))
		pygame.display.flip()

		# holding down a key will fire a repeated event after 500ms
		pygame.key.set_repeat(500)

		self.fullscreen = False


	def set_fullscreen(self):
		tmp = self.screen.convert()

		#flags = self.screen.get_flags()
		#bits = self.screen.get_bitsize()

		pygame.display.quit()
		pygame.display.init()

		pygame.display.set_caption(self.caption)
		
		self.screen = pygame.display.set_mode((self.width, self.height), HWSURFACE|DOUBLEBUF|FULLSCREEN)
		self.screen.blit(tmp, (0, 0))
		pygame.display.flip()

		#pygame.key.set_mods(0) #HACK: work-a-round for a SDL bug??
		#pygame.mouse.set_cursor(*cursor)  # Duoas 16-04-2007

		# holding down a key will fire a repeated event after 500ms
		pygame.key.set_repeat(500)
	 
		self.fullscreen = True

	def create_new_frame(self):
		self.img = self.scaled_images[self.filenames[self.index]].convert()

		self.img_w, self.img_h = self.img.get_size()
		self.img_x = (self.width-self.img_w)/2
		self.img_y = (self.height-self.img_h)/2

		self.frame_x = self.img_x - self.frame_size
		self.frame_y = self.img_y - self.frame_size
		self.frame_w = self.img_w + 2*self.frame_size
		self.frame_h = self.img_h + 2*self.frame_size

		self.frame = pygame.Surface((self.frame_w, self.frame_h)).convert()
		self.frame.fill(FRAME_COLORS[self.frame_color])
		self.frame.fill(BACKGROUND_COLORS[self.background_color], (self.frame_size, self.frame_size, self.img_w, self.img_h))
		#pygame.draw.rect(self.screen, FRAME_COLORS[self.frame_color], (img_x-self.frame_size, img_y-self.frame_size, w + 2*self.frame_size, h + 2*self.frame_size))
		#pygame.draw.rect(self.screen, BACKGROUND_COLORS[self.background_color], (img_x, img_y, w, h))

	def draw(self, frame=True):
		self.screen.fill(BACKGROUND_COLORS[self.background_color])

		if frame:
			self.img.set_alpha(self.alpha)
			self.frame.set_alpha(self.alpha)

		self.screen.blit(self.frame, (self.frame_x, self.frame_y))
		self.screen.blit(self.img, (self.img_x, self.img_y))

	# should not be relevant
	def update_img(self):
		pygame.display.update((self.img_x, self.img_y, self.img_w, self.img_h))

	def update_framed_image(self, x_extended=0, y_extended=0):
		#self.screen.fill((0, 0, 255))
		x = self.frame_x
		y = self.frame_y
		w = self.frame_w
		h = self.frame_h

		if x_extended > 0:
			w += x_extended
		elif x_extended < 0:
			x += x_extended # Plus because x_extended is negative
			w -= x_extended # Minus because x_extended is negative
		if y_extended > 0:
			h += y_extended
		elif y_extended < 0:
			y += y_extended # Plus because y_extended is negative
			h -= y_extended # Minus because y_extended is negative

		pygame.display.update((x, y, w, h))


	def update_frame(self):
		#self.screen.fill((0, 255, 0))
		pygame.display.update([(self.frame_x, self.frame_y, self.frame_w, self.frame_size), (self.frame_x, self.height-self.img_y, self.frame_w, self.frame_size),
			(self.frame_x, self.img_y, self.frame_size, self.img_h), 
			(self.img_x+self.img_w, self.img_y, self.frame_size, self.img_h)])

	def update_background(self):
		#self.screen.fill((255, 0, 0))
		pygame.display.update([(0, 0, self.width, self.frame_y), (0, self.height-self.frame_y, self.width, self.frame_y),
			(0, self.frame_y, self.frame_x, self.height - 2*self.frame_y), 
			(self.width-self.frame_x, self.frame_y, self.frame_x, self.height - 2*self.frame_y)])

	def update_framed_background(self):
		#self.screen.fill((255, 0, 255))
		pygame.display.update([(0, 0, self.width, self.img_y), (0, self.height-self.img_y, self.width, self.img_y),
			(0, self.img_y, self.img_x, self.height - 2*self.img_y), 
			(self.width-self.img_x, self.img_y, self.img_x, self.height - 2*self.img_y)])

	def update_screen(self):
		pygame.display.flip()


	def cleanup(self):
		if self.play_thread:
			self.play_thread.cancel()

		pygame.mixer.quit()
		pygame.display.quit()
		pygame.quit()

		sys.exit(0)


BACKGROUND_COLORS = [(0, 0, 0), (60, 60, 60), (120, 120, 120), (200, 200, 200), (255, 255, 255)]
FRAME_COLORS = [(0, 0, 0), (60, 60, 60), (120, 120, 120), (200, 200, 200), (255, 255, 255)]

# Custom pygame events
FORCE_NEXT = USEREVENT + 1

if __name__ == "__main__":
	print "Slideshow - created by Leo Gaube - 2016\n"

	slideshow = Slideshow(1920, 1080)
	slideshow.load(r"C:\Users\Leo\Pictures\Skye", caption=r"Skye")
	slideshow.setup_pygame()
	slideshow.run()
