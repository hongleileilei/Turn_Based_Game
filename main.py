import pygame as pg
from source import constants as c
from source import tool, screen, level

def main():
    # Create Game Control Class
    game = tool.Control()
    # Create Game Status Dict
    state_dict = {c.MAIN_MENU: screen.MainMenu(),
                  c.LEVEL_START: screen.LevelStartScreen(),
                  c.LEVEL_LOSE: screen.LevelLoseScreen(),
                  c.LEVEL_WIN: screen.LevelWinScreen(),
                  c.LEVEL: level.Level()}
    # Append Status Dict to Control class and initialize the starting
    # Status as MainMenu()
    game.setupStates(state_dict, c.MAIN_MENU)
    # Start the game
    game.main()

if __name__=='__main__':
    # Main function driver
    main()
    # Release the pygame
    pg.quit()
