import time
import sys
import logging
from core.controller import ScraperController

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)

url = "https://www.google.com/maps/place/%E4%B8%AD%E8%88%88%E5%A5%B6%E8%8C%B6/@24.1188173,120.6713679,17z/data=!4m8!3m7!1s0x34693d0a69daecb1:0x26270e2bf9b118c9!8m2!3d24.1188124!4d120.6739482!9m1!1b1!16s%2Fg%2F11gx_dwdfb?entry=ttu&g_ep=EgoyMDI2MDcyMi4wIKXMDSoASAFQAw%3D%3D"

print("Starting controller test...")
controller = ScraperController()
controller.start([url])

while controller._is_running:
    time.sleep(1)
    while not controller._metrics_queue.empty():
        print("Metric:", controller._metrics_queue.get())

print("Finished! Total results:", len(controller.results))
if controller.results:
    print("First post comments count:", len(controller.results[0].comments))
