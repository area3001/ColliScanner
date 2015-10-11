import pygame
import io
from PIL import Image

class Display:
	def __init__(self):
		self.open()

	def show_product(self, image, brand, description):
		img = Image.open(io.BytesIO(image))
		gameimg = pygame.image.fromstring(img.tobytes(), img.size, "RGB")
		gameimgpos = gameimg.get_rect(centerx=self.screen.get_width()/2, centery=self.screen.get_height()/2)
		self.screen.blit(gameimg, gameimgpos)

		font = pygame.font.Font(None, 36)
		text = font.render("%s - %s" % (brand, description), 1, (255, 255, 255))
		textpos = text.get_rect(midtop=(self.screen.get_width()/2, (self.screen.get_height()/2 + gameimg.get_height()/2 + 10)))
		self.screen.blit(text, textpos)

		pygame.display.flip()

	def show_message(self, message):
		font = pygame.font.Font(None, 36)
		text = font.render(message, 1, (255, 255, 255))
		textpos = text.get_rect(centerx=self.screen.get_width()/2, centery=self.screen.get_height()/2)
		self.screen.blit(text, textpos)

		pygame.display.flip()

	def open(self):
		pygame.init()
		pygame.display.init()
		pygame.mouse.set_visible(False)
		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.size = self.screen.get_size()

	def close(self):
		pygame.display.quit()
