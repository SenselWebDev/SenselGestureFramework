#!/usr/bin/python

from Tkinter import *
from wheel_menu_framework import *

root = Tk()
wheel = WheelMenu(0,0)

def point(event):
	wheel.clearWheel(c)
	wheel.changeLoc(event.x, event.y)
	#wheel.drawWheel(c)
	wheel.highlightSide(c,180)

c = Canvas(root, bg="white", width=1000, height= 1000)

c.configure(cursor="crosshair")

c.pack()

c.bind("<Button-1>", point)

root.mainloop()