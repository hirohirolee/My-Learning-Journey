import pygame
import random
import sys
from pygame.locals import *

WINDOWWIDTH = 600
WINDOWHEIGHT = 600
TEXTCOLOR = (255, 255, 255)
BACKGROUNDCOLOR = (0, 0, 0)
FPS = 40
BADDIEMINSIZE = 15
BADDIEMAXSIZE = 45
BADDIEMINSPEED = 2
BADDIEMAXSPEED = 8
ADDNEWBADDIERATE = 6
PLAYERMOVERATE = 5

def terminate():
    pygame.quit()
    sys.exit()

def waitForPlayerToPressKey():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return

def drawText(text, font, surface, x, y):
    textobj = font.render(text, 1, TEXTCOLOR)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def playerHasHitBaddie(playerRect, baddies):
    for b in baddies:
        if playerRect.colliderect(b['rect']):
            return True
    return False

def main():
    pygame.init()
    mainClock = pygame.time.Clock()
    windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Dodger - Space Evasion')
    pygame.mouse.set_visible(False)

    font = pygame.font.SysFont(None, 48)

    # 讀取音效與音樂
    try:
        gameOverSound = pygame.mixer.Sound('assets/gameover.wav')
        pygame.mixer.music.load('assets/music.wav')
    except Exception as e:
        print("Warning: Could not load sound files from assets/")
        gameOverSound = None

    # 讀取圖片素材
    try:
        playerImage = pygame.image.load('assets/player.png')
        playerImage = pygame.transform.scale(playerImage, (50, 50))
        baddieImage = pygame.image.load('assets/baddie.png')
    except Exception as e:
        print("Error: Could not load image files from assets/. Make sure player.png and baddie.png exist.")
        sys.exit()
        
    playerRect = playerImage.get_rect()
    
    drawText('Dodger', font, windowSurface, (WINDOWWIDTH / 3), (WINDOWHEIGHT / 3))
    drawText('Press a key to start.', font, windowSurface, (WINDOWWIDTH / 3) - 30, (WINDOWHEIGHT / 3) + 50)
    pygame.display.update()
    waitForPlayerToPressKey()

    topScore = 0

    while True:
        baddies = []
        score = 0
        playerRect.topleft = (WINDOWWIDTH / 2, WINDOWHEIGHT - 60)
        moveLeft = moveRight = moveUp = moveDown = False
        baddieAddCounter = 0
        
        try:
            pygame.mixer.music.play(-1, 0.0) # -1 means loop indefinitely
        except:
            pass

        while True: # the game loop
            score += 1

            for event in pygame.event.get():
                if event.type == QUIT:
                    terminate()
                if event.type == KEYDOWN:
                    if event.key == K_LEFT or event.key == K_a:
                        moveRight = False
                        moveLeft = True
                    if event.key == K_RIGHT or event.key == K_d:
                        moveLeft = False
                        moveRight = True
                    if event.key == K_UP or event.key == K_w:
                        moveDown = False
                        moveUp = True
                    if event.key == K_DOWN or event.key == K_s:
                        moveUp = False
                        moveDown = True
                if event.type == KEYUP:
                    if event.key == K_ESCAPE:
                        terminate()
                    if event.key == K_LEFT or event.key == K_a:
                        moveLeft = False
                    if event.key == K_RIGHT or event.key == K_d:
                        moveRight = False
                    if event.key == K_UP or event.key == K_w:
                        moveUp = False
                    if event.key == K_DOWN or event.key == K_s:
                        moveDown = False
                if event.type == MOUSEMOTION:
                    # Let mouse also control the player
                    playerRect.centerx = event.pos[0]
                    playerRect.centery = event.pos[1]

            # Add new baddies
            baddieAddCounter += 1
            if baddieAddCounter == ADDNEWBADDIERATE:
                baddieAddCounter = 0
                baddieSize = random.randint(BADDIEMINSIZE, BADDIEMAXSIZE)
                newBaddie = {
                    'rect': pygame.Rect(random.randint(0, WINDOWWIDTH - baddieSize), 0 - baddieSize, baddieSize, baddieSize),
                    'speed': random.randint(BADDIEMINSPEED, BADDIEMAXSPEED),
                    'surface': pygame.transform.scale(baddieImage, (baddieSize, baddieSize))
                }
                baddies.append(newBaddie)

            # Move the player
            if moveLeft and playerRect.left > 0:
                playerRect.move_ip(-1 * PLAYERMOVERATE, 0)
            if moveRight and playerRect.right < WINDOWWIDTH:
                playerRect.move_ip(PLAYERMOVERATE, 0)
            if moveUp and playerRect.top > 0:
                playerRect.move_ip(0, -1 * PLAYERMOVERATE)
            if moveDown and playerRect.bottom < WINDOWHEIGHT:
                playerRect.move_ip(0, PLAYERMOVERATE)

            # Move the mouse cursor to match the player if it moves by keyboard
            pygame.mouse.set_pos(playerRect.centerx, playerRect.centery)

            # Move the baddies
            for b in baddies:
                b['rect'].move_ip(0, b['speed'])

            # Delete baddies that have fallen past the bottom
            for b in baddies[:]:
                if b['rect'].top > WINDOWHEIGHT:
                    baddies.remove(b)

            # Draw the game world
            windowSurface.fill(BACKGROUNDCOLOR)

            drawText('Score: %s' % (score), font, windowSurface, 10, 0)
            drawText('Top Score: %s' % (topScore), font, windowSurface, 10, 40)

            windowSurface.blit(playerImage, playerRect)
            for b in baddies:
                windowSurface.blit(b['surface'], b['rect'])

            pygame.display.update()

            # Check if any of the baddies have hit the player
            if playerHasHitBaddie(playerRect, baddies):
                if score > topScore:
                    topScore = score
                break
                
            mainClock.tick(FPS)

        # Stop music and play game over sound
        try:
            pygame.mixer.music.stop()
            if gameOverSound:
                gameOverSound.play()
        except:
            pass

        drawText('GAME OVER', font, windowSurface, (WINDOWWIDTH / 3), (WINDOWHEIGHT / 3))
        drawText('Press a key to play again.', font, windowSurface, (WINDOWWIDTH / 3) - 80, (WINDOWHEIGHT / 3) + 50)
        pygame.display.update()
        waitForPlayerToPressKey()

        try:
            if gameOverSound:
                gameOverSound.stop()
        except:
            pass

if __name__ == '__main__':
    main()
