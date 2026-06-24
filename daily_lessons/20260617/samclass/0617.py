"""
本學院以「培育農業生產科學、自然資源經營與保育、農村社群發展等專業，兼具有整合、創新能力及國際觀之現代青年。」為教育目標；自我定位為「發展永續與創新的農業科學」與「營造和諧與安全的自然環境」。學生之核心能力為「農學專業知識創新與實務技能應用」、「跨領域整合與自主學習」、「溝通表達與團隊合作」、及「落實人文關懷」；基本素養為「具備農學專業知能」、「實事求是與刻苦耐勞的精神」、「關懷社會、服務人群的情操」、以及「國際的視野」。

本學院擁有堅強師資陣容與優良儀器設備，在國內外已培育出許多優秀農業科技人才，此外在研發農業暨自然資源保育科技、富麗鄉村及服務推廣也均有卓著的貢獻。展望未來，本院除繼續發展既有特色，培育現代農業科技人才外，更將強化自然資源之教學與研究，並以生物科技、自然資源保育和永續農業為發展重點，維護人類健康與生態環境和諧，造福社群。

為了確保學生之受教品質和紮實農業暨自然資源相關訓練，各系所及學程在教學方面的多樣化、網路化和國際化上，均有長足的進步；尤其在教學國際化方面，許多單位都有與國外學校合作教學的經驗。本院發展多元且外籍學生逐年增多，國際交流日益頻繁，因此強化課程整合與英語教學已成為當前的努力目標。


"""
"""
orgStr = """
"""
本學院以「培育農業生產科學、自然資源經營與保育、農村社群發展等專業，兼具有整合、創新能力及國際觀之現代青年。」為教育目標；自我定位為「發展永續與創新的農業科學」與「營造和諧與安全的自然環境」。學生之核心能力為「農學專業知識創新與實務技能應用」、「跨領域整合與自主學習」、「溝通表達與團隊合作」、及「落實人文關懷」；基本素養為「具備農學專業知能」、「實事求是與刻苦耐勞的精神」、「關懷社會、服務人群的情操」、以及「國際的視野」。

本學院擁有堅強師資陣容與優良儀器設備，在國內外已培育出許多優秀農業科技人才，此外在研發農業暨自然資源保育科技、富麗鄉村及服務推廣也均有卓著的貢獻。展望未來，本院除繼續發展既有特色，培育現代農業科技人才外，更將強化自然資源之教學與研究，並以生物科技、自然資源保育和永續農業為發展重點，維護人類健康與生態環境和諧，造福社群。

為了確保學生之受教品質和紮實農業暨自然資源相關訓練，各系所及學程在教學方面的多樣化、網路化和國際化上，均有長足的進步；尤其在教學國際化方面，許多單位都有與國外學校合作教學的經驗。本院發展多元且外籍學生逐年增多，國際交流日益頻繁，因此強化課程整合與英語教學已成為當前的努力目標。
"""
"""

"""
"""
st = set(orgStr)

print(st)
print(len(st))
"""

"""
st=set(orgStr)
dt = dict()
for c in st:
    dt[c]=orgStr.count(c)
print(dt)
"""

"""

隨機產生15個1~15之間的整數，找出其中的第2大數值 不能使用排序函式
"""


"""
import random
random.seed(17)
sample = random.choices(range (1, 17),k=15)
num_max = None
num_max2 = None
for num in sample:
    if num_max is None or num_max < num:
        num_max2 = num_max
        num_max = num
    elif num_max2 is None or num_max2 < num:
        num_max2 = num

sample.sort(reverse=True)
print(f"\n原始 sample: {sample}")
print(f"第二大數值: {sample[1]}")

"""

"""
利用user名單，搭配隨機功能，為每一位user產生一個介於(1~100)的成績 ，再從中找出最高分的user

"""
"""
import random
user_list = ["Aaric", "Abbot", "Ace", "Ackerley", "Adam", "Adney", 
            "Bab", "Bamboo", "Ben", "Bunny", "Betty", "Baha", 
            "Cindy", "Candy", "Cathy", "Cakra", "Carin", "Caroline",
            "Deny", "Dacy", "Danna", "Debbi", "Devon", "Diza","Dob"]

user_dict=dict()
for user in user_list:
    user_dict[user] = random.randint(1,100)

print(user_dict)
user_na = []
max_scor = None
for k, v in user_dict.items():
    if max_scor is None or v > max_scor:
        max_scor = v
        user_na = [k]
    elif v == max_scor:
        user_na.append(k) 

print("最高分", user_na, ": ", max_scor)



for k, v in user_dict.items():
    if user_na == None:
        user_na = k
        max_scor = v
    elif v == max_scor:
        user_na.append(k)  
else:   
    print(user_na, "/", max_scor) 
"""

"""
1. 買甚麼
2. 買多少
3. 多少錢
4. 夠不夠
除錯

products = {
    "apple":{
        "price":30,
        "stock":50
    },
    "banana":{
        "price":20,
        "stock":80
    },
    "orange":{
        "price":10,
        "stock":100
    },
    "grape":{
        "price":30,
        "stock":60
    },
    "mango":{
        "price": 40,
        "stock":150
    },
    "lemon":{
        "price":50,
        "stock":80
    }
}

"""
from PIL.Image import item
products = {
    "apple":{
        "price":30,
        "stock":50
    },
    "banana":{
        "price":20,
        "stock":80
    },
    "orange":{
        "price":10,
        "stock":100
    },
    "grape":{
        "price":30,
        "stock":60
    },
    "mango":{
        "price": 40,
        "stock":150
    },
    "lemon":{
        "price":50,
        "stock":80
    }
}
items = tuple(products.keys())
item_str ="空白:結帳"
for n,v in enumerate(items):
    item_str = item_str + f", {n+1}: {v}"
print(item_str)

