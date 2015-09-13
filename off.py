# Small program to turn off the display

import dothat
from dothat import backlight as bl
from dothat import lcd

bl.off()
bl.set_graph(0)
lcd.clear()
