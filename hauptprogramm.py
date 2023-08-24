#!/usr/bin/env python3
import daq6510
import heizer

import os
import time
from datetime import datetime
import yaml

import matplotlib.pyplot as plt
import numpy as np

def createFiles():
    directory = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    parent_dir = "./data/"
    path = os.path.join(parent_dir, directory)
    os.mkdir(path)
    ### Pepare Files
    with open(os.path.join(path, "data.csv"), "w") as f: 
        f.write("tSensor,voltage\n")
        
    with open(os.path.join(path, "mesurement_data"), "w") as f: 
        f.write(f"""Zieltemperaturn: {tTargetList}:\nSpannungen: {IList}\n\n""")
        
# Liest das Rezept ein
#Erg: Wertelisten aus dem Rezept
def readRezept(debugPrint=True):
    firstLine = True
    with open("rezept.txt", "r") as f:
        rezept = f.read().split("\n")
    tTarget = [] # in °C
    tTime = []   # in minuten
    tStationaer = [] # in minuten
    for x in rezept:
        if firstLine == True:
            firstLine = False
            IList = x.split(",")
        else:
            tTarget.append(x.split(",")[0])
            tTime.append(x.split(",")[1])
            tStationaer.append(x.split(",")[2])
    if debugPrint == True:
        print(f"tTarget: {tTarget}")
        print(f"tTime:   {tTime}")
        print(f"tStatio: {tStationaer}")
        print(f"IList:   {IList}")
    return tTarget, tTime, tStationaer, IList



# Erg: Plotet mit den neusten Werten neu und legt die Grezen des Graphen neu fest.
def plotData(ax, fig, tSensorList, vList, tSensorLine, vLine):
    x1 = np.linspace(0,len(tSensorList),len(tSensorList))
    x2 = np.linspace(0,len(uList),len(uList))
    tSensorLine.set_xdata(x1)
    uLine.set_xdata(x2)
    ax.set_xlim([0, len(tSensorList)+1])
    
    if tSensorList != None:
        tSensorLine.set_ydata(tSensorList) #plot new line
        vLine.set_ydata(vList) #plot new line
        ax.set_ylim([0, 30])
        #limList = tSensorList
        #limList.sort()
        #limList = limList[1:]
        #ax.set_ylim([ float(limList[0])-1, float(limList[-1])+1 ])
    else:
        ax.set_ylim([-.1, 100])
        
    fig.canvas.draw()
    fig.canvas.flush_events()


### Prüfen ob die Temperatur Stationär ist
def stationaerPruefung(temperaturListe, tStationaer, StationaerAbweichung=1):
    if len(temperaturListe) > tStationaer: # Nur prüfen wenn über StationarTime Einträge vohanden sind
        tempList = temperaturListe[-tStationaer:] # Liste der letzten StationarTime Temperaturen erstellen...
        tempList.sort() # ...und sorteiren
        #print(f"Größte   Temp:{round(tempList[-1],2)}\nKleinste Temp:{round(tempList[0],2)}")
        
        if tempList[-1] - tempList[0] <= StationaerAbweichung: # Wenn die größte die Temperaur und die Kleinste Temp. kleiner sind als der vorggebene Bereich
            isStationaer = True
            #print("Stationaer")
        else:
            isStationaer = False
            #print("Nicht Stationaer")
    return isStationaer

def beginMesurement(tTarget):
    print("Messung beginnt!")
    with open("mesurement_data", "a") as f:
        f.write(f"Zieltemperatur: {tTarget}°C; geplante")
    

"""
# Funktion für das Autosrollen
def AutoScroll(Graph, AutoStop, xVon, xEnde, yVon, yEnde, minusY, plusY): 
    if AutoStop == False:                                     # Autoscrollen ist aktiv
        Graph.axis('auto')                                  # Schaltet Autoscaling wieder ein!
        Graph.relim()                                       # Neu Berechnung der Datengrenzen
        ymin, ymax = Graph.get_ylim()                       # holt den max. und min. Wert aus dem jeweiligen Diagramm und ...
        Graph.set_ylim(ymin - minusY, ymax + plusY)         # ... setzt die neuen Grenzen für die Y-Achse und ...
        Graph.set_xlim(0,listTiRe[-1] + 10)                 # ... X-Achse (mit dem Plus und Minus, kann man Abstände zu den Achsen erstellen) ein
    elif AutoStop == True:                                    # Autoscrollen wurde deaktiviert
        Graph.axis([xVon,xEnde,yVon,yEnde])               # Übernimmt die Werte des Manuellen Anpassen der Achsen aus den Eingabefeldern!
"""


                                    ### ### ### BEGIN PREP ### ### ###


'''
sensor = adafruit.Adafruit(name="Pt100", GPIO="D24",res=100,refres=430,wire=4,Vergleichssensor=True)
tSensor = float(sensor.get_temperatur())
print(f"T_sensor = {round(tSensor,2)}°C")
'''

# Load config data
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

daq = daq6510.Daq6510(config['DAQ-6510']) # Multimeter DAQ6510 vorbeiten

### Prepare Heizer
heizer.logging_on(True)
heizer_config = config['Heizer']['Schnittstelle']
sensor = heizer.HeizerPlatte(**heizer_config)

### Variables
tolerance = 1 #°C
### Listen
tSensorList = [0] # Stores all Temperatures from sensor internaly
uList = [0] # Stores all Temperatures from Calibration instrument internaly
tTargetList, tTimeList, tStationaerList, IList = readRezept() # tTargetList ist die Liste der Zieltempraturen,# tTimeList ist die Liste der "Verweilzeiten"

createFiles()
### Plot Prep.
x1 = 0
x2 = 0
fig, ax = plt.subplots(figsize=(10, 8))
plt.title("Temperatur über Zeit", fontsize=20)
plt.xlabel("Zeit [s]",fontsize=18)
plt.ylabel("Temperatur [°C]",fontsize=18)
plt.grid()
plt.ion()
plt.show()
tSensorLine, = plt.plot(x1, tSensorList)
uLine, = plt.plot(x2, uList)



                         ### ### ### BEGIN LOOP ### ### ###
t = 0.004 # Tiefe in m
k = 1 # korrekturfaktor oE
s = 0.03 #Strecke zwischen zwei Messspitzen in m
for i in range(len(tTargetList)):
    tTarget     = float(tTargetList[i])
    tTime       = int(tTimeList[i])
    tStationaer = int(tStationaerList[i])
    while True:
        I = 0.1 # Ampere die angelgt sind
        U = round(float(daq.read().split(",")[1]),4) # Volt die gemessen werden
        if U >= 100: U = 0 # Strom auf Null setzen wenn nichts gemessen wird
        
        # Formeln siehe: https://iopscience.iop.org/article/10.1088/0953-8984/27/22/223201/pdf
        rho_2D = 4.532 * (U/I) * t # spezifischer Wiederstand
        #rho_3D = (2*np.pi*s/(2-np.sqrt(2)))*(U/I) # Bulk resistivity
        
        #print(f"U={U} V")
        #print(f"rho_2D={rho_2D}")
        #print(f"rho_3D={rho_3D}")
    
        tSensor = sensor.get_istwert()
        print(f"{tSensor} °C")
        
        

        ### Save data internaly
        tSensorList.append(tSensor)
        uList.append(U)
        
        isStationaer = stationaerPruefung(tSensorList, tStationaer)
        
        ### Save data externaly
        with open("data.csv", "a") as f:
            f.write(f"{tSensor},{U}\n")
        
        
        
        ### Check if tSensor is in Target Area and stationary
        if tSensor <= (tTarget + tolerance) and tSensor >= (tTarget - tolerance) and isStationaer == True:
            
            beginMesurement()
            line = f"{I},{U},{rho_2D},{tSensor}"
            
            with open("mesurement_data", "a") as f:
                f.write(line)
        
        plotData(ax, fig, tSensorList, uList, tSensorLine, uLine)
        
        time.sleep(1)
    
    