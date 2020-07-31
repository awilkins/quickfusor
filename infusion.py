
import picamera
import dothat
from dothat import backlight as bl
from dothat import lcd
import dothat.touch as b

import time
import io

import zbar

import Image

import StringIO
import ConfigParser

CAMERA_REZ = (1027, 768)
PATIENT_NAME = "patient"
INFUSION_RATE = "rate"
VOLUME = "volume"

def readfile(name):
    with open(name) as f:
        return f.read().replace("\n", "")


WAIT_MESSAGE = readfile("wait.txt")
MAX_SCANS = 3

class Buttons:
    def up(self):
        print("UP")
    
    def down(self):
        print("DOWN")
    
    def left(self):
        print("LEFT")
    
    def right(self):
        print("RIGHT")
        
    def button(self):
        print("BUTTON")
    
    def cancel(self):
        print("CANCEL")

class Wait:
    
    class ButtonHandler(Buttons):
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
    
    class ButtonHandler(Buttons):
        
        def __init__(self, parent):
            self.parent = parent
        
        def cancel(self):
            print('Cancelled    !')
            parent.notfound = False
    
    def __init__(self):
        self.buttons = Scan.ButtonHandler(self)
        self.count = 0
        self.notfound = True
        
    def render(self):
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
        
        self.count += 1
        
        for symbol in image:
            self.notfound = False
            # flash screen
            bl.rgb(0,0,0)
            time.sleep(0.2)             
            bl.rgb(100,180,100)
            time.sleep(0.2)
            bl.rgb(0,0,0)
            
            # parse data
            buf = StringIO.StringIO()
            buf.write("[DEFAULT]\n")
            buf.write(symbol.data)
            buf.seek(0)
            config = ConfigParser.ConfigParser()
            config.readfp(buf)
            
            if config.has_option('DEFAULT', PATIENT_NAME):
                self.name = config.get('DEFAULT', PATIENT_NAME)            
            if config.has_option('DEFAULT', INFUSION_RATE):
                self.rate = config.getfloat('DEFAULT', INFUSION_RATE)
            
            # start pump
            if self.name:
                pump.change_state(Verify(self.name, self.rate))
            else:
                pump.change_state(Infusion(self.rate))
        
        if self.notfound and self.count > MAX_SCANS:
            pump.change_state(Wait())
    
    def render_start(self):
        lcd.clear()
        bl.rgb(180, 80, 80)
        lcd.write("Scanning....")
    
class Verify:
    
    class ButtonHandler(Buttons):
        
        def __init__(self, parent):
            self.parent = parent
        
        def left(self):
            pump.change_state(Wait())
        
        def right(self):
            pump.change_state(Infusion(self.parent.rate))
    
    def __init__(self, name, rate):
        self.name = name
        self.rate = rate
        self.buttons = Verify.ButtonHandler(self)

    def render_start(self):
        lcd.clear()
        lcd.write("Is this         %s" % self.name)
        lcd.set_cursor_position(0, 2)
        lcd.write("NO           YES")
        bl.rgb(30,60,90)
    
    def render(self):
        pass

class Infusion:
    'State for when the pump is running'
    
    class ButtonHandler(Buttons):
        
        def __init__(self, parent):
            self.parent = parent
        
        def up(self):
            self.parent.rate += 1
        
        def down(self):
            self.parent.rate -= 1
        
        def cancel(self):
            pump.change_state(Wait())
        
    
    def __init__(self, rate):
        self.tick = 0
        self.rate = rate
        self.old_rate = -1
        self.buttons = Infusion.ButtonHandler(self)
    
    def render_start(self):
        lcd.clear()
        bl.rgb(0,100,0)
        
    def render(self):
        self.tick += self.rate
        self.tick %= 100
        
        if(self.rate != self.old_rate):
            lcd.clear()
            lcd.write("Infusing : %s ml/min" % self.rate)
            self.old_rate = self.rate
            
        bl.set_graph(self.tick / 100.0)

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

@b.on(b.DOWN)
def handle_button(ch, evt):
    pump.current_state.buttons.down()

@b.on(b.LEFT)
def handle_button(ch, evt):
    pump.current_state.buttons.left()
    
@b.on(b.RIGHT)
def handle_button(ch, evt):
    pump.current_state.buttons.right()

@b.on(b.CANCEL)
def handle_button(ch, evt):
    pump.current_state.buttons.cancel()



pump = Pump()

pump.run()