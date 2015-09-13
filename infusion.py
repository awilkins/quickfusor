
import picamera
import dothat
from dothat import backlight as bl
from dothat import lcd
import dothat.touch as b

import time
import io

import zbar

import Image

CAMERA_REZ = (1027, 768)

def readfile(name):
    with open(name) as f:
        return f.read().replace("\n", "")


WAIT_MESSAGE = readfile("wait.txt")

class Wait:
    
    class ButtonHandler():
        def button(self):
            pump.change_state(Scan())
    
    'State for when the pump is waiting to start'    
    def __init__(self):
        self.started = False
        self.buttons = Wait.ButtonHandler()
    
    def render_start(self):
        lcd.clear()
        bl.set_graph(0)
        bl.rgb(180,180,180)
        lcd.write(WAIT_MESSAGE)
        started = True
    
    def render(self):
        pass
    
class Scan:
    'State that scans a QR and gets on with things'
    
    def render(self):
        pass
    
    def render_start(self):
        lcd.clear()
        bl.rgb(180, 80, 80)
        lcd.write("Scanning....")
        
        notfound = True
        
        while notfound:
            snap = io.BytesIO()
            
            with picamera.PiCamera() as camera:
                camera.resolution = CAMERA_REZ
                camera.start_preview()
                time.sleep(1)
                camera.capture(snap, format='jpeg')
            
            snap.seek(0)
            pimage = Image.open(snap).convert('L')
            
            scanner = zbar.ImageScanner()
            scanner.parse_config('enable')
            
            width, height = pimage.size
            raw = pimage.tostring()
            
            image = zbar.Image(width, height, 'Y800', raw)
            
            scanner.scan(image)
            
            for symbol in image:
                notfound = False
                # flash screen
                bl.rgb(0,0,0)
                time.sleep(0.2)
                bl.rgb(180,180,180)
                time.sleep(0.2)
                bl.rgb(0,0,0)
                
                # parse data
                
                # start pump
                
                pump.change_state(Infusion())
        
    
class Infusion:
    'State for when the pump is running'
    
    def __init__(self):
        self.tick = 0
    
    def render_start(self):
        lcd.clear()
        bl.rgb(0,180,0)
        lcd.write("INFUSING STUFF")
        
    def render(self):
        self.tick += 1
        self.tick %= 10
        bl.set_graph(self.tick / 10.0)

class Broken:
    
    def render_start(self):
        lcd.clear()
        bl.rgb(255,0,0)
        lcd.write("NOT DONE YET")
    
    def render(self):
        pass

#----------------

# setup

class Pump:
    
    def __init__(self):
        self.current_state = None

    def change_state(self, new_state):
        self.current_state = new_state
        self.current_state.render_start()
        
    def run(self):
        self.change_state(Wait())
        while 1:
            self.current_state.render()
            time.sleep(0.1)

@b.on(b.BUTTON)
def handle_button(ch, evt):
    pump.current_state.buttons.button()

@b.on(b.UP)
def handle_button(ch, evt):
    pump.current_state.buttons.up()


pump = Pump()

pump.run()