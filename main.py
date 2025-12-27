#!/usr/bin/env python3
"""ML Siege - Main entry point."""

import pygame
from src.game import Game


def main():
    """Initialize and run the game."""
    # Initialize pygame
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    
    # Create and run game
    game = Game()
    
    try:
        game.run()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
