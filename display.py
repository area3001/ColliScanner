import pygame

class Display:
    def __init__(self):
        self.open()

    def show_image(self, image):
        image = self.scale_image(image)
        self.screen.blit(image, (0, 0))
        pygame.display.flip()

    def scale_image(self, image):
        return pygame.transform.scale(pygame.image.load(image), self.size)

    def open(self):
        pygame.display.init()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.size = self.screen.get_size()

    def close(self):
        pygame.display.quit()
