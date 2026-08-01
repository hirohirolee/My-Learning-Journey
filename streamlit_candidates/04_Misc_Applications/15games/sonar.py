import streamlit as st
st.title('sonar.py - 自動化展示')
st.info('這是從原專案腳本自動包裝產生的互動式介面。')

import random
import sys
import math

def getNewBoard():
    # Create a new 60x15 board data structure.
    board = []
    for x in range(60): # The main list is a list of 60 lists.
        board.append([])
        for y in range(15): # Each list in the main list has 15 single-character strings.
            # Use different characters for the ocean to make it more readable.
            if random.randint(0, 1) == 0:
                board[x].append('~')
            else:
                board[x].append('`')
    return board

def drawBoard(board):
    # Draw the board data structure.
    tensDigitsLine = '    ' # Initial space for the numbers down the left side of the board
    for i in range(1, 6):
        tensDigitsLine += (' ' * 9) + str(i)

    # Print the numbers across the top of the board.
    st.write(tensDigitsLine)
    st.write('   ' + ('0123456789' * 6))
    st.write()

    # Print each of the 15 rows.
    for row in range(15):
        # Single-digit numbers need to be padded with an extra space.
        if row < 10:
            extraSpace = ' '
        else:
            extraSpace = ''

        # Create the string for this row on the board.
        boardRow = ''
        for column in range(60):
            boardRow += board[column][row]

        st.write('%s%s %s %s' % (extraSpace, row, boardRow, row))

    # Print the numbers across the bottom of the board.
    st.write()
    st.write('   ' + ('0123456789' * 6))
    st.write(tensDigitsLine)

def getRandomChests(numChests):
    # Create a list of chest data structures (two-item lists of x, y int coordinates).
    chests = []
    while len(chests) < numChests:
        newChest = [random.randint(0, 59), random.randint(0, 14)]
        if newChest not in chests: # Make sure a chest is not already here.
            chests.append(newChest)
    return chests

def isOnBoard(x, y):
    # Return True if the coordinates are on the board; otherwise, return False.
    return x >= 0 and x <= 59 and y >= 0 and y <= 14

def makeMove(board, chests, x, y):
    # Change the board data structure with a sonar device character. Remove treasure chests from the chests list as they are found.
    # Return False if this is an invalid move.
    # Otherwise, return the string of the result of this move.
    smallestDistance = 100 # Any chest will be closer than 100.
    for cx, cy in chests:
        distance = math.sqrt((cx - x) * (cx - x) + (cy - y) * (cy - y))

        if distance < smallestDistance: # We want the closest treasure chest.
            smallestDistance = distance

    smallestDistance = round(smallestDistance)

    if smallestDistance == 0:
        # xy is directly on a treasure chest!
        chests.remove([x, y])
        return '您找到了沉沒的寶藏！'
    else:
        if smallestDistance < 10:
            board[x][y] = str(smallestDistance)
            return f'聲納探測到距離 {smallestDistance} 處有寶藏。'
        else:
            board[x][y] = 'X'
            return '聲納沒有探測到任何東西，所有寶藏都在這台設備的探測範圍之外。'

def enterPlayerMove(previousMoves):
    # Let the player enter their move. Return a two-item list of int xy coordinates.
    st.write('您要將下一個聲納設備投放在哪裡？(X座標 0-59 Y座標 0-14) (或輸入 quit 離開)')
    while True:
        move = st.text_input()
        if move.lower() == 'quit':
            st.write('遊戲結束！')
            sys.exit()

        move = move.split()
        if len(move) == 2 and move[0].isdigit() and move[1].isdigit() and isOnBoard(int(move[0]), int(move[1])):
            if [int(move[0]), int(move[1])] in previousMoves:
                st.write('您已經在這裡投放過聲納了。')
                continue
            return [int(move[0]), int(move[1])]

        st.write('輸入座標無效，請輸入一個數字（0-59），空一格，再輸入一個數字（0-14）。')

def showInstructions():
    st.write('''
==================================================
           聲納尋寶遊戲 (Sonar Treasure Hunt)      
==================================================

遊戲說明：
您是一艘配備聲納的尋寶船的船長！
您的任務是在海洋中找到 3 個沉沒的寶藏箱。
但這並不容易，因為您只帶了 20 個聲納探測儀。

海洋廣闊，座標的 X 軸從左到右為 0 到 59，Y 軸從上到下為 0 到 14。
當您投放聲納時，它會告訴您距離最近的寶藏箱有多遠：
- 若距離小於 10，會顯示一個數字代表距離。
- 若距離大於等於 10，會顯示 'X' 代表探測不到。
- 若剛好擊中，就會尋獲寶藏！

祝您好運，船長！
''')

def playAgain():
    # This function returns True if the player wants to play again, otherwise it returns False.
    st.write('想再玩一次嗎？(yes 或 no)')
    return st.text_input().lower().startswith('y')

def main():
    showInstructions()

    while True:
        # Game setup
        sonarDevices = 20
        theBoard = getNewBoard()
        theChests = getRandomChests(3)
        drawBoard(theBoard)
        previousMoves = []

        while sonarDevices > 0:
            # Show sonar device and chest statuses.
            st.write(f'您還有 {sonarDevices} 個聲納探測儀。海洋中還有 {len(theChests)} 個寶藏箱。')

            x, y = enterPlayerMove(previousMoves)
            previousMoves.append([x, y]) # we must track all moves so that sonars can be updated.

            moveResult = makeMove(theBoard, theChests, x, y)
            if moveResult == False:
                continue
            else:
                if moveResult == '您找到了沉沒的寶藏！':
                    # Update all the sonars currently on the map.
                    for x, y in previousMoves:
                        makeMove(theBoard, theChests, x, y)
                drawBoard(theBoard)
                st.write(moveResult)

            if len(theChests) == 0:
                st.write('太棒了！您找到了所有隱藏的寶藏！恭喜您！')
                break

            sonarDevices -= 1

        if sonarDevices == 0:
            st.write('我們耗盡了所有的聲納設備！現在只能轉向回航，無法找到剩下的寶藏了。')
            st.write('遊戲結束。')
            st.write('剩下的寶藏位於：')
            for x, y in theChests:
                st.write(f'  X: {x}, Y: {y}')

        if not playAgain():
            break

if __name__ == '__main__':
    main()
