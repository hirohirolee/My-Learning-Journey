import streamlit as st

import random
import time
import sys

def getNewBoard():
    # Board is a list of 8 lists, each with 8 strings
    return [[' ' for _ in range(8)] for _ in range(8)]

def drawBoard(board):
    HLINE = '  +---+---+---+---+---+---+---+---+'
    st.write('    1   2   3   4   5   6   7   8')
    st.write(HLINE)
    for y in range(8):
        st.write('%s |' % (y+1), end='')
        for x in range(8):
            st.write(' %s |' % board[x][y], end='')
        st.write('\n' + HLINE)

def resetBoard(board):
    for x in range(8):
        for y in range(8):
            board[x][y] = ' '
    board[3][3] = 'X'
    board[3][4] = 'O'
    board[4][3] = 'O'
    board[4][4] = 'X'

def isOnBoard(x, y):
    return 0 <= x <= 7 and 0 <= y <= 7

def isValidMove(board, tile, xstart, ystart):
    # Returns False if the move is invalid, or a list of tiles to flip if valid.
    if board[xstart][ystart] != ' ' or not isOnBoard(xstart, ystart):
        return False

    board[xstart][ystart] = tile # temporarily place tile
    otherTile = 'O' if tile == 'X' else 'X'
    tilesToFlip = []

    directions = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]

    for xdir, ydir in directions:
        x, y = xstart, ystart
        x += xdir
        y += ydir
        if isOnBoard(x, y) and board[x][y] == otherTile:
            # There is a piece belonging to the other player next to our piece.
            x += xdir
            y += ydir
            if not isOnBoard(x, y):
                continue
            while board[x][y] == otherTile:
                x += xdir
                y += ydir
                if not isOnBoard(x, y):
                    break
            if not isOnBoard(x, y):
                continue
            if board[x][y] == tile:
                # There are pieces to flip over. Go in the reverse direction until we reach the original space.
                while True:
                    x -= xdir
                    y -= ydir
                    if x == xstart and y == ystart:
                        break
                    tilesToFlip.append([x, y])

    board[xstart][ystart] = ' ' # restore empty space
    if len(tilesToFlip) == 0:
        return False
    return tilesToFlip

def getValidMoves(board, tile):
    validMoves = []
    for x in range(8):
        for y in range(8):
            if isValidMove(board, tile, x, y) != False:
                validMoves.append([x, y])
    return validMoves

def getScoreOfBoard(board):
    xscore = 0
    oscore = 0
    for x in range(8):
        for y in range(8):
            if board[x][y] == 'X':
                xscore += 1
            if board[x][y] == 'O':
                oscore += 1
    return {'X': xscore, 'O': oscore}

def makeMove(board, tile, xstart, ystart):
    tilesToFlip = isValidMove(board, tile, xstart, ystart)
    if tilesToFlip == False:
        return False

    board[xstart][ystart] = tile
    for x, y in tilesToFlip:
        board[x][y] = tile
    return True

def getBoardCopy(board):
    dupeBoard = getNewBoard()
    for x in range(8):
        for y in range(8):
            dupeBoard[x][y] = board[x][y]
    return dupeBoard

def isOnCorner(x, y):
    return (x == 0 and y == 0) or (x == 7 and y == 0) or (x == 0 and y == 7) or (x == 7 and y == 7)

def getComputerMove(board, computerTile):
    possibleMoves = getValidMoves(board, computerTile)
    if not possibleMoves:
        return None

    # randomize order to prevent predictable games
    random.shuffle(possibleMoves)

    # 1. Take a corner if available
    for x, y in possibleMoves:
        if isOnCorner(x, y):
            return [x, y]

    # 2. Greedy algorithm - find move that scores the most points
    bestScore = -1
    bestMove = []
    for x, y in possibleMoves:
        dupeBoard = getBoardCopy(board)
        makeMove(dupeBoard, computerTile, x, y)
        score = getScoreOfBoard(dupeBoard)[computerTile]
        if score > bestScore:
            bestMove = [x, y]
            bestScore = score
    return bestMove

def getPlayerMove(board, playerTile):
    validMoves = getValidMoves(board, playerTile)
    if not validMoves:
        return None

    DIGITS1TO8 = '1 2 3 4 5 6 7 8'.split()
    while True:
        st.write('輸入您的下棋座標 (行 列)，例如 3 4，或輸入 q 退出：')
        move = st.text_input().lower().strip()
        if move == 'q':
            st.write("遊戲結束！")
            sys.exit()

        if len(move) >= 3 and move[0] in DIGITS1TO8 and move[2] in DIGITS1TO8:
            x = int(move[0]) - 1
            y = int(move[2]) - 1
            if isValidMove(board, playerTile, x, y) == False:
                st.write('無效的步數，請確認是否能翻轉對方的棋子。')
                continue
            else:
                return [x, y]
        else:
            st.write('無效的輸入。請輸入行號(1-8)和列號(1-8)，中間以空白分隔。')

def main():
    st.write("==================================")
    st.write("       黑白棋 (Reversi) 遊戲        ")
    st.write("==================================")

    st.write("請選擇遊戲模式：")
    st.write("1. 玩家對抗電腦")
    st.write("2. 電腦對抗電腦 (AI 模擬)")
    mode = '1'
    while True:
        ans = st.text_input("> ").strip()
        if ans in ('1', '2'):
            mode = ans
            break
        st.write("請輸入 1 或 2。")

    if mode == '1':
        st.write("您想當先手的黑子 (X) 還是後手的白子 (O)？")
        while True:
            ans = st.text_input("請輸入 X 或 O: ").upper().strip()
            if ans in ('X', 'O'):
                playerTile = ans
                computerTile = 'O' if playerTile == 'X' else 'X'
                break
            st.write("無效的輸入。")
    else:
        playerTile = None # AI vs AI mode
        computerTile = None

    board = getNewBoard()
    resetBoard(board)
    turn = 'X' # X always goes first

    while True:
        drawBoard(board)
        scores = getScoreOfBoard(board)
        st.write(f"分數 - 黑子 (X): {scores['X']}  白子 (O): {scores['O']}")
        st.write(f"現在輪到 {turn} 下棋。")
        
        validMoves = getValidMoves(board, turn)
        if not validMoves:
            st.write(f"{turn} 無法下棋，跳過此回合。")
            turn = 'O' if turn == 'X' else 'X'
            if not getValidMoves(board, turn):
                st.write("雙方皆無法下棋，遊戲結束！")
                break
            continue

        if mode == '1':
            if turn == playerTile:
                move = getPlayerMove(board, playerTile)
                if move:
                    makeMove(board, playerTile, move[0], move[1])
            else:
                st.write("電腦正在思考中...")
                time.sleep(1)
                move = getComputerMove(board, computerTile)
                if move:
                    makeMove(board, computerTile, move[0], move[1])
                    st.write(f"電腦選擇下在 {move[0]+1} {move[1]+1}")
        else:
            # AI vs AI
            st.write("AI 正在思考中...")
            time.sleep(0.5)
            move = getComputerMove(board, turn)
            if move:
                makeMove(board, turn, move[0], move[1])
                st.write(f"AI ({turn}) 選擇下在 {move[0]+1} {move[1]+1}")
        
        turn = 'O' if turn == 'X' else 'X'
        st.write("-" * 34)

    drawBoard(board)
    scores = getScoreOfBoard(board)
    st.write("=============== 結算 ===============")
    st.write(f"最終分數 - 黑子 (X): {scores['X']}  白子 (O): {scores['O']}")
    if scores['X'] > scores['O']:
        st.write("黑子 (X) 獲勝！")
    elif scores['X'] < scores['O']:
        st.write("白子 (O) 獲勝！")
    else:
        st.write("平手！")

if __name__ == '__main__':
    main()
