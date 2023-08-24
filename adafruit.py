# Bibliotheken:
import board
import digitalio
import adafruit_max31865

import random
#import numpy as np                              
#import matplotlib.pyplot as plt    
import logging            

# Test und Debug Funktion (bzw. Werte) vorbereiten
global test_on, dbg_on, log

test_on = False
dbg_on = False

def truth_pt100(test, dbg):
    global test_on, dbg_on

    test_on = test
    dbg_on = dbg

# Logging auch in Geräte Programm:
def logging_on(log_status):
    global log
    log = log_status

class Adafruit:
    # Dictionaries für die Pin-Belegung am Raspberry Pi
    pin = {'D0':board.D0, 'D1':board.D1, 'D2':board.D2, 'D3':board.D3, 'D4':board.D4,
           'D5':board.D5, 'D6':board.D6, 'D7':board.D7, 'D8':board.D8, 'D9':board.D9,
           'D10':board.D10, 'D11':board.D11, 'D12':board.D12, 'D13':board.D13, 'D14':board.D14,
           'D15':board.D15, 'D16':board.D16, 'D17':board.D17, 'D18':board.D18, 'D19':board.D19,
           'D20':board.D20, 'D21':board.D21, 'D22':board.D22, 'D23':board.D23, 'D24':board.D24,
           'D25':board.D25, 'D26':board.D26        
        }
    
    def __init__(self, name, GPIO, res, refres, wire, Vergleichssensor):
        self.name = name
        self.GPIO = Adafruit.pin.get(GPIO)
        self.res = res
        self.refres = refres
        self.wire = wire
        self.list = []
        self.vergleich = Vergleichssensor

        self.init_adafruit()
        #if log == True:   logging.info(f'Adafruit {self.name} initialisiert + alles übergeben! - Funktion __init__()') 

    def init_adafruit(self):                                    # Gerät Initialisieren            
        if not test_on:
            spi = board.SPI()
            cs = digitalio.DigitalInOut(self.GPIO)                             # GPIO = z.B. board.D16
            sensor = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=self.res, ref_resistor=self.refres, wires=self.wire)
            self.sensor = sensor                                                  
            print(f'Adafruit PT100 {self.name} initialisiert!')
            if dbg_on == True:
                print(f'Sensor am {self.GPIO} / Widerstand = {self.res} Ohm / Ref. Widerstand = {self.refres}/ {self.wire}-Leiter Verkabelung\n')
                print(self.sensor)
            #if log == True:   logging.info(f'Adafruit {self.name} initialisiert! - init_adafruit()') 

    def get_temperatur(self):                                   # Istwert Temperatur auslesen                                        
        if test_on == False:
            tempA = self.sensor.temperature
            if dbg_on == True:
                print(f'Reading from {self.sensor}: {tempA} °C') 
            #if log == True:   logging.info(f'get_temperatur() ausgeführt - Adafruit')
        else:
            tempA = random.uniform(15,25)                                  
        return tempA

    # Grafik Einstellungen und Adafruit Liste verwalten:
    def update_list(self):
        self.list.append(self.get_temperatur())

    def grafik(self, graph, x_list):
        self.line, = graph.plot(x_list, self.list, label=self.name)

    def update(self, x_list):
        self.line.set_xdata(x_list)               
        self.line.set_ydata(self.list)