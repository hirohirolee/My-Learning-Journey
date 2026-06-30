
"""
class clz1:
    var1 = "NCHU"
    
    def __init__(self):
        print ("Step 1")
    
    def cust1(self):
        print("Step X")
    
    def __del__ (self):
        print("Step last")


obj1 = clz1()
obj2 = clz1()
obj1.cust1()

print(obj1.var1)


class clz_g2(clz1):
    
    var2 = 2026

    def cust2(self):
        print("Add Step N")


class clz_g3(clz_g2):
    def cust2(self):
        print(self.cust1())
        print("Add Step N-1")
        return super().cust2()

obj3 = clz_g3()
obj3.cust2()

"""

from datetime import datetime
class proto:
    tm_interval = 0
    tm_price = 0
    tm_from = None
    tm_end = None

    def __init__(self, interval:int, price:int):
        self.tm_interval=interval
        self.tm_price=price
        print(self.tm_interval, "/", self.tm_price)

    def set_time_from(self, tm_from:str, fm="%Y/%m/%d %H:%M:%S"):
        self.tm_from = self.STOD(tm_from, fm)
        print(self.tm_from)

    def set_time_end(self, tm_end:str, fm="%Y/%m/%d %H:%M:%S"):
        self.tm_end = self.STOD(tm_end, fm)
        print(self.tm_end)

    def STOD(self, tm_str:str, fm="%Y/%m/%d %H:%M:%S"):
        return datetime.strptime(tm_str,fm)

    def get_time_diff_secs(self, tm_from:str|datetime, tm_end:str|datetime, fm="%Y/%m/%d %H:%M:%S"):
        if isinstance(tm_from,str):
            tm_from=self.STOD(tm_from, fm)
        if isinstance(tm_end,str):
            tm_end=self.STOD(tm_end, fm)
        return (tm_end - tm_from).total_seconds()

    def get_payment(self):
        tot_time = self.get_time_diff_secs(self.tm_from, self.tm_end)/60
        tot_bill = (tot_time // self.tm_interval)
        if tot_bill % self.tm_interval > 0:
            tot_bill = tot_bill + 1
        return tot_bill * self.tm_price
    

obj1 = proto (30, 10)
obj1.set_time_from("2026/06/29 00:00:00")
obj1.set_time_end("2026/06/29 01:00:00")
print(obj1.get_time_diff_secs("2026/06/29 00:00:00", "2026/06/29 01:00:00"))
print(obj1.get_payment())









        