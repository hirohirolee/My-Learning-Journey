"""
讓用戶輸入一段5個字的內容，將其中大/小寫互換，不是英文則不變

"""

"""
orgStr = input ("請輸入5個字: ")
newStr = ""

if orgStr[0].upper() == orgStr[0].lower():
    newStr=newStr+ orgStr[0]

elif orgStr[0] == orgStr[0].upper():
    newStr =newStr + orgStr[0].lower()

else:
    newStr = newStr + orgStr[0].upper()

if orgStr[1].upper() == orgStr[1].lower():
    newStr=newStr+ orgStr[1]

elif orgStr[1] == orgStr[1].upper():
    newStr =newStr + orgStr[1].lower()

else:
    newStr = newStr + orgStr[1].upper()
    

if orgStr[2].upper() == orgStr[2].lower():
    newStr=newStr+ orgStr[2]

elif orgStr[2] == orgStr[2].upper():
    newStr =newStr + orgStr[2].lower()

else:
    newStr = newStr + orgStr[2].upper()


if orgStr[3].upper() == orgStr[3].lower():
    newStr=newStr+ orgStr[3]

elif orgStr[3] == orgStr[3].upper():
    newStr =newStr + orgStr[3].lower()

else:
    newStr = newStr + orgStr[3].upper()


if orgStr[4].upper() == orgStr[4].lower():
    newStr=newStr+ orgStr[4]

elif orgStr[4] == orgStr[4].upper():
    newStr =newStr + orgStr[4].lower()

else:
    newStr = newStr + orgStr[4].upper()


print (newStr)

"""

"""
 newStr=newStr+ orgStr[0] if orgStr[0].upper() == orgStr[0].lower() else newStr =newStr + orgStr[0].lower() if orgStr[0] == orgStr[0].upper() else newStr=newStr + orgStr[0].upper()

"""

"""
讓用戶輸入一段英文字，輸出每個字母第一次出現的位置和共出現幾次
範例:ABCAA
輸出:

C  Ndx Tot
-  --- ---
x 123 123
A 0   3
B 1   1
C 2   1

"""

orgStr= input ("請輸入一段英文字: ")
print("C Ndx Tot")
print("- --- ---")

for Ndx in range (len(orgStr)):
    C=orgStr[Ndx]
    if orgStr.index(C) != Ndx:
        continue
    Tot=orgStr.count(C)
    print(f"{C} {Ndx:3d} {Tot:3d}")


    
