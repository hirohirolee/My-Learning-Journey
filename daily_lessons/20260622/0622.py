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
# --- 組合品項的名稱對應編號
items = tuple(products.keys())
item_str = "空白:結帳"
for n, v in enumerate(items):
    item_str =  item_str + f", {n+1}:{v}"
# --- 購物明細清單
pur_list = []
# --- 收集結帳的內容
while True:
    print("-" * 80)
    item_num = input(f"品項:{item_str} : ").strip()
    if item_num == "":
        break
    else:
        item_num = int(item_num) - 1
    # --- 輸入品項代號錯誤
    if item_num < 0 or item_num >= len(items):
        print("品項輸入錯誤!")
        continue
    # --- 收集品項數量
    item_dict = {"name"  : items[item_num],
                 "price" : products[items[item_num]]["price"],
                 "stock" : products[items[item_num]]["stock"],}
    while True:
        item_qty = input(f"請輸入{item_dict['name']} ({item_dict['stock']}), 空白:放棄 : ").strip()
        if item_qty == "": 
            break
        else:
            item_qty = int(item_qty)
        # ---
        if item_qty <= 0 or item_qty > item_dict["stock"]:
            print("數量輸入錯誤!")
        else:
            break
    # ---
    if item_qty != "":
        pur_dict = {"name"  : items[item_num]                   ,
                    "price" : products[items[item_num]]["price"],
                    "qty"   : item_qty                          ,
                    "amt"   : products[items[item_num]]["price"] * item_qty ,
                    }
        # --- 扣庫存
        pur_list.append(pur_dict)
        products[items[item_num]]["stock"] -= item_qty
# --- 輸出採購明細
print("-" * 80)
print("Item       Pric Qty  Amt")
print("---------- ---- ---- --------")
tot_qty = 0
tot_amt = 0
for row in pur_list:
    tot_qty += row['qty']
    tot_amt += row['amt']
    # ---
    print(f"{row['name']:10s} {row['price']:4d} {row['qty']:4d} {row['amt']:8d}")
# ---
print("---------- ---- ---- --------")
print(f"合計:           {tot_qty:4d} {tot_amt:8d}")

