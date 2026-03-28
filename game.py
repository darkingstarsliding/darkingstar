import pygame
from module.logger import MyLogger
from public import globvalue

if __name__=='__main__':
    logger=MyLogger(__name__)
    globvalue.logger=logger
    
    #pygame init
    pg=pygame.init()
