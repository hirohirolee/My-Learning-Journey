import streamlit as st

import sys

# The string to be encrypted/decrypted
SYMBOLS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890 !?.`~@#$%^&*()_+-=[]{}|;:<>,/'

def getMode():
    while True:
        st.write('您想要加密 (encrypt) 還是解密 (decrypt)？\n(輸入 e 或 d)')
        mode = st.text_input().lower()
        if mode in 'encrypt e decrypt d'.split():
            return mode
        else:
            st.write('請輸入 "encrypt" 或 "e" 或是 "decrypt" 或 "d"。')

def getMessage():
    st.write('請輸入您的訊息：')
    return st.text_input()

def getKey():
    key = 0
    while True:
        st.write(f'請輸入密鑰數字 (1-{len(SYMBOLS) - 1})：')
        key = int(st.text_input())
        if (key >= 1 and key <= len(SYMBOLS) - 1):
            return key

def getTranslatedMessage(mode, message, key):
    if mode[0] == 'd':
        key = -key
    translated = ''

    for symbol in message:
        if symbol in SYMBOLS:
            symbolIndex = SYMBOLS.find(symbol)
            translatedIndex = symbolIndex + key
            
            # Handle wrap-around
            if translatedIndex >= len(SYMBOLS):
                translatedIndex = translatedIndex - len(SYMBOLS)
            elif translatedIndex < 0:
                translatedIndex = translatedIndex + len(SYMBOLS)

            translated += SYMBOLS[translatedIndex]
        else:
            # Append the symbol without encrypting/decrypting
            translated += symbol
    return translated

def main():
    st.write("==================================")
    st.write("      凱撒密碼 (Caesar Cipher)     ")
    st.write("==================================")
    st.write(f"目前支援加密的字元包含了英文字母、數字與常見符號，共 {len(SYMBOLS)} 個。")
    
    while True:
        mode = getMode()
        message = getMessage()
        key = getKey()

        st.write('\n為您轉換的結果如下：')
        st.write(getTranslatedMessage(mode, message, key))
        
        st.write('\n是否要繼續轉換其他訊息？(yes/no)')
        if not st.text_input().lower().startswith('y'):
            st.write("結束程式。")
            break

if __name__ == '__main__':
    main()
