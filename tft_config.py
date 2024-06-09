from machine import Pin, SPI
import gc9a01

def config():
    spi = SPI(1, baudrate=20000000, polarity=0, phase=0)
    tft = gc9a01.GC9A01(spi, 240, 240, reset=Pin(12, Pin.OUT), dc=Pin(8, Pin.OUT), cs=Pin(9, Pin.OUT), backlight=Pin(25, Pin.OUT), rotation=0)
    tft.init()
    return tft
