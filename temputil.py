import pygame
import os

for file in os.listdir("user_data/categories/61"):
    path = f"user_data/categories/61/{file}"
    img = pygame.image.load(path)
    neww = img.height * 0.6428571429
    if neww <= img.width:
        os.remove(path)
        newimg = img.subsurface((img.width / 2 - neww / 2, 0, neww, img.height))
        pygame.image.save(newimg, path)
