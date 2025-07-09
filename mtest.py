import pygame 


pygame.init()

path = r"B:\Py\Apps\MILIMP\data\mp3_converted\Anime_86_avid.mp3"
pygame.mixer.music.load(path)
pygame.mixer.music.play()


while True:
    time = pygame.time.get_ticks()
    #time*=2
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.set_pos(time/1000)
