import rui3pylib
import time

rui3 = rui3pylib.RUI3node("COM1")

rui3.connect()

time.sleep(5)

rui3.close()

