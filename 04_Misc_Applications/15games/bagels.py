import random

NUM_DIGITS = 3
MAX_GUESSES = 10

def main():
    print(f'''貝果遊戲 (Bagels)
我會想一個 {NUM_DIGITS} 位數，每個數字都不重複。
請試著猜出這個數字。我會給你以下提示：
當我說：    代表：
  Pico      有一個數字猜對了，但位置不對。
  Fermi     有一個數字猜對了，且位置也對了。
  Bagels    沒有任何數字猜對。

例如，如果我想的數字是 248 而你猜 843，我會給你提示：Fermi Pico。''')

    while True:
        secretNum = getSecretNum()
        print('\n我已經想到一個數字了。')
        print(f'你有 {MAX_GUESSES} 次機會猜出它。')

        numGuesses = 1
        while numGuesses <= MAX_GUESSES:
            guess = ''
            while len(guess) != NUM_DIGITS or not guess.isdecimal():
                print(f'\n第 {numGuesses} 次猜測：')
                guess = input('> ')

            clues = getClues(guess, secretNum)
            print(clues)
            numGuesses += 1

            if guess == secretNum:
                break
            if numGuesses > MAX_GUESSES:
                print('你已經用完所有的猜測次數了。')
                print(f'正確答案是：{secretNum}')

        print('你想再玩一次嗎？ (yes 或 no)')
        if not input('> ').lower().startswith('y'):
            break
    print('謝謝遊玩！')

def getSecretNum():
    """回傳一個長度為 NUM_DIGITS 的字串，且所有數字都不重複。"""
    numbers = list('0123456789')
    random.shuffle(numbers)
    
    # 取得前 NUM_DIGITS 個數字組成密碼
    secretNum = ''
    for i in range(NUM_DIGITS):
        secretNum += numbers[i]
    return secretNum

def getClues(guess, secretNum):
    """回傳提示字串，包含 pico、fermi 或 bagels"""
    if guess == secretNum:
        return '恭喜你！猜對了！'

    clues = []
    for i in range(len(guess)):
        if guess[i] == secretNum[i]:
            # 數字對了，位置也對了
            clues.append('Fermi')
        elif guess[i] in secretNum:
            # 數字對了，但位置不對
            clues.append('Pico')

    if len(clues) == 0:
        return 'Bagels'
    else:
        # 將提示按字母排序，以免透露位置資訊
        clues.sort()
        return ' '.join(clues)

if __name__ == '__main__':
    main()
