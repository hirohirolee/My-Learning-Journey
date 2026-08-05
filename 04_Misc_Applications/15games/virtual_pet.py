import random
import time
import os
import json
import sys

SAVE_FILE = "virtual_pet_save.json"

PET_SPECIES = {
    "1": {
        "name": "小貓咪 (Cat)",
        "type": "cat",
        "fav_food": "鮮魚罐頭",
        "ascii_baby": r"""
 /\_/\  
( o.o ) 
 > ^ <  [幼年貓]
""",
        "ascii_adult": r"""
 /\_/\   
(  . . )  
=( I )=  [成年酷貓]
""",
        "ascii_legend": r"""
 /\_/\   ✨ 👑 ✨
( ✪ W ✪)  
 /|   |\  [傳奇喵皇]
"""
    },
    "2": {
        "name": "小柴犬 (Dog)",
        "type": "dog",
        "fav_food": "美味肉骨頭",
        "ascii_baby": r"""
 /^ ^\ 
( u.u )
 \ v /  [幼年犬]
""",
        "ascii_adult": r"""
 ( \_v_/ )
 (  o.o  )
  (___)=  [成年忠犬]
""",
        "ascii_legend": r"""
  / \__/ \  ✨ 👑 ✨
 (  •̀ 3 •́ ) 
 /|  🐾  |\ [神級神犬]
"""
    },
    "3": {
        "name": "小龍龍 (Dragon)",
        "type": "dragon",
        "fav_food": "火爆辣烤肉",
        "ascii_baby": r"""
 (o.o) 
 <( )> 
  ^^    [幼年龍]
""",
        "ascii_adult": r"""
  /\_/\  
 ( o.o )~🐲 
 <(   )> 
  ^^ ^^ [飛天巨龍]
""",
        "ascii_legend": r"""
   / \___/ \   ✨ 👑 ✨
  (  🔥 w 🔥 )~🔥🐉🔥
  /(   ❤️   )\
   ^^     ^^   [傳奇神龍]
"""
    }
}

class VirtualPet:
    def __init__(self, name, species_id):
        self.name = name
        self.species_id = species_id
        self.species_info = PET_SPECIES[species_id]
        
        # 核心屬性 (0-100)
        self.hunger = 80       # 飽食度
        self.happiness = 80    # 快樂度
        self.energy = 90       # 體力
        self.cleanliness = 90  # 清潔度
        self.health = 100      # 健康度
        
        self.age = 0           # 年齡(天)
        self.exp = 0           # 經驗值
        self.level = 1         # 等級
        self.coins = 100       # 金幣
        self.poop_count = 0    # 大便數量
        self.is_sick = False   # 生病狀態
        
        # 背包道具
        self.inventory = {
            "普通飼料": 3,
            "高級罐頭": 1,
            "玩具球": 1,
            "特效感冒藥": 1
        }

    def get_stage_ascii(self):
        if self.level >= 10:
            return self.species_info["ascii_legend"]
        elif self.level >= 5:
            return self.species_info["ascii_adult"]
        else:
            return self.species_info["ascii_baby"]

    def get_stage_name(self):
        if self.level >= 10:
            return "傳奇期 (Legendary)"
        elif self.level >= 5:
            return "成年期 (Adult)"
        else:
            return "幼年期 (Baby)"

    def tick(self):
        """時間流逝，屬性消耗與隨機事件"""
        self.hunger = max(0, self.hunger - random.randint(3, 6))
        self.happiness = max(0, self.happiness - random.randint(2, 5))
        self.energy = max(0, self.energy - random.randint(2, 4))
        
        # 當大便過多時，清潔度下降加快
        clean_loss = 3 + self.poop_count * 5
        self.cleanliness = max(0, self.cleanliness - clean_loss)
        
        # 隨機大便 (15% 機率)
        if random.random() < 0.15:
            self.poop_count += 1
            
        # 健康度判定
        if self.hunger < 20 or self.cleanliness < 30 or self.poop_count >= 3:
            if random.random() < 0.35:
                self.is_sick = True
                
        if self.is_sick:
            self.health = max(0, self.health - random.randint(5, 10))
            self.happiness = max(0, self.happiness - 5)
            
        # 經驗值與升級
        self.exp += 5
        if self.exp >= self.level * 30:
            self.exp -= self.level * 30
            self.level += 1
            print(f"\n🎉 恭喜！{self.name} 升級到了 Level {self.level}！")
            if self.level == 5 or self.level == 10:
                print(f"✨✨ {self.name} 進化到了 [{self.get_stage_name()}]！ ✨✨")
            time.sleep(1)

    def draw_status_bar(self, label, value, max_val=100, symbol="█", empty_symbol="░"):
        bars = int((value / max_val) * 10)
        bar_str = symbol * bars + empty_symbol * (10 - bars)
        return f"{label}: [{bar_str}] {value}/{max_val}"

    def show_status(self):
        print("\n" + "=" * 50)
        print(f" 🐾 寵物名稱: {self.name} ({self.species_info['name']}) | 階段: {self.get_stage_name()}")
        print(f" ⭐ 等級: Lv.{self.level} (EXP: {self.exp}/{self.level*30}) | 💰 金幣: {self.coins} G")
        print(self.get_stage_ascii())
        
        if self.is_sick:
            print(" ⚠️  【狀態：生病中！請盡快治療！】 ⚠️")
        if self.poop_count > 0:
            print(f" 💩 房間裡有 {self.poop_count} 堆大便！需要清理！")
            
        print("-" * 50)
        print(self.draw_status_bar("🍖 飽食度", self.hunger))
        print(self.draw_status_bar("❤️ 快樂度", self.happiness))
        print(self.draw_status_bar("⚡ 體  力", self.energy))
        print(self.draw_status_bar("🛁 清潔度", self.cleanliness))
        print(self.draw_status_bar("🏥 健康度", self.health))
        print("=" * 50)

    def feed(self):
        print("\n🍲 【餵食寵物】")
        print(f"1. 普通飼料 (庫存: {self.inventory.get('普通飼料', 0)}) -> +20 飽食")
        print(f"2. 高級罐頭 (庫存: {self.inventory.get('高級罐頭', 0)}) -> +40 飽食, +15 快樂")
        print(f"3. 喜愛食物 [{self.species_info['fav_food']}] (需至商店購買)")
        print("0. 取消")
        
        choice = input("請選擇投餵食物 (0-3): ").strip()
        if choice == '1':
            if self.inventory.get("普通飼料", 0) > 0:
                self.inventory["普通飼料"] -= 1
                self.hunger = min(100, self.hunger + 20)
                print(f"😋 {self.name} 開心地吃了普通飼料！飽食度增加！")
            else:
                print("❌ 庫存不足！請先去商店購買。")
        elif choice == '2':
            if self.inventory.get("高級罐頭", 0) > 0:
                self.inventory["高級罐頭"] -= 1
                self.hunger = min(100, self.hunger + 40)
                self.happiness = min(100, self.happiness + 15)
                print(f"😻 {self.name} 津津有味地吃了高級罐頭！超級滿足！")
            else:
                print("❌ 庫存不足！請先去商店購買。")
        elif choice == '3':
            fav = self.species_info['fav_food']
            if self.inventory.get(fav, 0) > 0:
                self.inventory[fav] -= 1
                self.hunger = min(100, self.hunger + 50)
                self.happiness = min(100, self.happiness + 30)
                print(f"💖 {self.name} 吃到最愛的【{fav}】，高興得跳了起來！")
            else:
                print(f"❌ 庫存沒有【{fav}】！")

    def play_minigame(self):
        if self.energy < 15:
            print(f"\n😴 {self.name} 太累了，沒有體力陪你玩了！請讓牠休息。")
            return
            
        print("\n⚽ 【陪寵物玩遊戲 - 猜拳大對決】")
        print("贏了可以賺取金幣並大幅提升寵物快樂度！")
        choices = ["剪刀", "石頭", "布"]
        user_choice = input("請出拳 (1. 剪刀 / 2. 石頭 / 3. 布): ").strip()
        
        choice_map = {"1": "剪刀", "2": "石頭", "3": "布"}
        if user_choice not in choice_map:
            print("無效出拳。")
            return
            
        player_hand = choice_map[user_choice]
        pet_hand = random.choice(choices)
        
        print(f"\n你出了 [{player_hand}]，{self.name} 出了 [{pet_hand}]！")
        self.energy = max(0, self.energy - 15)
        
        if player_hand == pet_hand:
            print("🤝 平手！大家玩得很開心！")
            self.happiness = min(100, self.happiness + 10)
            self.coins += 10
        elif (player_hand == "剪刀" and pet_hand == "布") or \
             (player_hand == "石頭" and pet_hand == "剪刀") or \
             (player_hand == "布" and pet_hand == "石頭"):
            print(f"🎉 你贏了！{self.name} 服氣地看著你！獲得 30 金幣！")
            self.happiness = min(100, self.happiness + 25)
            self.coins += 30
        else:
            print(f"😜 {self.name} 贏了！牠高興地圍著你轉圈圈！獲得 15 金幣！")
            self.happiness = min(100, self.happiness + 20)
            self.coins += 15

    def clean(self):
        print("\n🛁 【清理與洗澡】")
        cleaned_any = False
        if self.poop_count > 0:
            print(f"🧹 清理了 {self.poop_count} 堆大便，房間恢復乾淨！")
            self.poop_count = 0
            cleaned_any = True
            
        if self.cleanliness < 90:
            self.cleanliness = min(100, self.cleanliness + 40)
            print(f"🚿 給 {self.name} 洗了個香噴噴的熱水澡！清潔度提升！")
            cleaned_any = True
            
        if not cleaned_any:
            print(f"✨ {self.name} 和房間現在已經非常乾淨囉！不需要清理。")

    def sleep(self):
        print(f"\n😴 {self.name} 蓋上小被被睡覺了... Zzz...")
        for _ in range(3):
            time.sleep(0.6)
            sys.stdout.write(". ")
            sys.stdout.flush()
        print()
        self.energy = 100
        self.hunger = max(0, self.hunger - 15)
        print(f"🌅 太陽升起，{self.name} 睡醒了！體力完全恢復 (100/100)！")

    def visit_doctor(self):
        if not self.is_sick and self.health >= 80:
            print(f"\n🏥 醫生檢查後表示：{self.name} 非常健康，不需要看病！")
            return
            
        cost = 40
        print(f"\n🏥 【寵物醫院】 看診費用需要 {cost} G。")
        if self.coins >= cost:
            self.coins -= cost
            self.is_sick = False
            self.health = 100
            print(f"💉 醫生幫 {self.name} 打了一針並吃了維他命，健康度完全恢復！")
        else:
            print(f"❌ 金幣不足！你需要 {cost} G，但目前只有 {self.coins} G。")

    def walk_explore(self):
        if self.energy < 20:
            print(f"\n🐾 {self.name} 太累了，無法去公園散步！")
            return
            
        self.energy = max(0, self.energy - 20)
        print(f"\n🏞️ 帶 {self.name} 到公園散步冒險...")
        time.sleep(1)
        
        events = [
            "撿到了遺失的金幣口袋！(+50 G)",
            "在草叢裡遇到了其他小夥伴，開心玩耍！(+20 快樂)",
            "發現了一罐隱藏的【高級罐頭】！",
            "突然下起了雨，稍微淋濕了！(-10 清潔度)",
            "幸運地找到了【特效感冒藥】！"
        ]
        ev = random.choice(events)
        print(f"🎁 散步事件：{self.name} {ev}")
        
        if "50 G" in ev:
            self.coins += 50
        elif "20 快樂" in ev:
            self.happiness = min(100, self.happiness + 20)
        elif "高級罐頭" in ev:
            self.inventory["高級罐頭"] = self.inventory.get("高級罐頭", 0) + 1
        elif "清潔度" in ev:
            self.cleanliness = max(0, self.cleanliness - 10)
        elif "特效感冒藥" in ev:
            self.inventory["特效感冒藥"] = self.inventory.get("特效感冒藥", 0) + 1

    def shop(self):
        fav = self.species_info['fav_food']
        items = {
            "1": ("普通飼料", 15, "飽食度 +20"),
            "2": ("高級罐頭", 30, "飽食度 +40, 快樂 +15"),
            "3": (fav, 50, f"最愛食物！飽食 +50, 快樂 +30"),
            "4": ("特效感冒藥", 45, "治癒生病狀態")
        }
        
        while True:
            print("\n" + "=" * 40)
            print(f" 🛍️ 【寵物道具商店】 (目前金幣: {self.coins} G)")
            print("=" * 40)
            for k, (iname, price, desc) in items.items():
                print(f"{k}. {iname:<10} | {price:>3} G | {desc}")
            print("0. 離開商店")
            
            c = input("請選擇購買道具 (0-4): ").strip()
            if c == '0':
                break
            elif c in items:
                iname, price, desc = items[c]
                if self.coins >= price:
                    self.coins -= price
                    self.inventory[iname] = self.inventory.get(iname, 0) + 1
                    print(f"🛒 成功購買了【{iname}】！已加入背包。")
                else:
                    print("❌ 金幣不足！去陪寵物玩遊戲或散步賺錢吧！")

    def save_game(self):
        data = {
            "name": self.name,
            "species_id": self.species_id,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "cleanliness": self.cleanliness,
            "health": self.health,
            "age": self.age,
            "exp": self.exp,
            "level": self.level,
            "coins": self.coins,
            "poop_count": self.poop_count,
            "is_sick": self.is_sick,
            "inventory": self.inventory
        }
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("💾 遊戲進度已成功儲存！")

    @classmethod
    def load_game(cls):
        if not os.path.exists(SAVE_FILE):
            return None
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            pet = cls(data["name"], data["species_id"])
            pet.hunger = data.get("hunger", 80)
            pet.happiness = data.get("happiness", 80)
            pet.energy = data.get("energy", 90)
            pet.cleanliness = data.get("cleanliness", 90)
            pet.health = data.get("health", 100)
            pet.age = data.get("age", 0)
            pet.exp = data.get("exp", 0)
            pet.level = data.get("level", 1)
            pet.coins = data.get("coins", 100)
            pet.poop_count = data.get("poop_count", 0)
            pet.is_sick = data.get("is_sick", False)
            pet.inventory = data.get("inventory", {})
            return pet
        except Exception as e:
            print(f"讀取存檔失敗: {e}")
            return None

def create_new_pet():
    print("\n" + "=" * 50)
    print("      🥚 【領養你的電子寵物】 🥚")
    print("=" * 50)
    print("請選擇你要領養的寵物品種：")
    for k, info in PET_SPECIES.items():
        print(f"{k}. {info['name']} (最愛食物: {info['fav_food']})")
        
    sp_choice = input("請選擇品種 (1-3): ").strip()
    if sp_choice not in PET_SPECIES:
        sp_choice = "1"
        
    pet_name = input("請為你的寵物取個可愛的名字: ").strip()
    if not pet_name:
        pet_name = "波波 (BoBo)"
        
    return VirtualPet(pet_name, sp_choice)

def main():
    print("\n" + "=" * 50)
    print("      🐾  電子寵物大冒險 (Virtual Pet)  🐾")
    print("=" * 50)
    
    pet = None
    if os.path.exists(SAVE_FILE):
        ans = input("發現上次的遊戲存檔！是否載入舊紀錄？(Y/N): ").strip().upper()
        if ans == 'Y':
            pet = VirtualPet.load_game()
            
    if not pet:
        pet = create_new_pet()

    while True:
        # 每輪時間流逝
        pet.tick()
        
        # 檢查寵物生命跡象
        if pet.health <= 0:
            print("\n" + "💀" * 25)
            print(f"😭 很遺憾，{pet.name} 因為長期健康不佳過世了...")
            print("請好好照顧下一隻寵物！")
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            break

        pet.show_status()
        
        print("\n請選擇互動指令：")
        print("1. 🍲 餵食寵物")
        print("2. ⚽ 陪玩小遊戲 (賺金幣+提升快樂)")
        print("3. 🛁 打掃房間/洗澡")
        print("4. 😴 睡覺休息 (完全恢復體力)")
        print("5. 🏥 帶去看醫生")
        print("6. 🏞️ 公園散步冒險")
        print("7. 🛍️ 道具商店")
        print("8. 💾 儲存進度")
        print("0. 🚪 退出遊戲")
        
        choice = input("\n請輸入選擇 (0-8): ").strip()
        
        if choice == '1':
            pet.feed()
        elif choice == '2':
            pet.play_minigame()
        elif choice == '3':
            pet.clean()
        elif choice == '4':
            pet.sleep()
        elif choice == '5':
            pet.visit_doctor()
        elif choice == '6':
            pet.walk_explore()
        elif choice == '7':
            pet.shop()
        elif choice == '8':
            pet.save_game()
        elif choice == '0':
            pet.save_game()
            print("\n👋 感謝遊玩！下次再來看顧你的寵物吧！")
            break
        else:
            print("無效選項，請重新選擇。")
            
        time.sleep(0.5)

if __name__ == '__main__':
    main()
