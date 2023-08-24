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
        f.write("Angeleger Strom I,Gemessende Spannung U,spezifischer Wiederstand rho,Gemessende Temperatur [°C],Messdaten\n")
        
    with open(os.path.join(path, "mesurement_data"), "w") as f: 
        f.write(f"""Zieltemperaturn: {tTargetList}\nSpannungen: {IList}\n""")
        
    return path
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

def beginMesurement(tTarget, I):
    print("Messung beginnt!")
    #dt = datetime.now()
    with open(os.path.join(path, "mesurement_data"), "a") as f:
        f.write(f"\nZieltemperatur: {tTarget}°C\n  Aktueller Strom: {I}A\n")
    data_points = 0
    return data_points


def getData(t, debugPrint=False):
        U = round(float(daq.read().split(",")[1]), 4) # Volt die gemessen werden
        if U >= 100: U = 0 # Strom auf Null setzen wenn nichts gemessen wird
        
        # Formeln siehe: https://iopscience.iop.org/article/10.1088/0953-8984/27/22/223201/pdf
        rho_2D = round(4.532 * (U/I) * t, 4) # spezifischer Wiederstand
        #rho_3D = (2*np.pi*s/(2-np.sqrt(2)))*(U/I) # Bulk resistivity
        tSensor = sensor.get_istwert()
        
        if debugPrint == True:
            print(f"U={U} V")
            print(f"rho_2D={rho_2D}")
            print(f"{tSensor}°C", end="\n\n")
        return U, rho_2D, tSensor


                                    ### ### ### BEGIN PREP ### ### ###

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

path = createFiles()
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
firstTime = True
t = 0.004 # Tiefe in m
#k = 1 # korrekturfaktor oE
#s = 0.03 #Strecke zwischen zwei Messspitzen in m
for i in range(len(tTargetList)): # Für jede Temperatur:
    
    tTarget     = float(tTargetList[i])
    tTime       = int(tTimeList[i])
    tStationaer = int(tStationaerList[i])
    data_points = 0
    
    for tempI in IList: #Für jeden Strom in jeder Temperatur:
        
        I = float(tempI) # Ansteuerung hier impementieren!
        print(I)
        while True:
            U, rho_2D, tSensor = getData(t, True) # Get Data
        
            ### Save data internaly for plot Data function
            tSensorList.append(tSensor)
            uList.append(U)
        
            isStationaer = stationaerPruefung(tSensorList, tStationaer)
        
            ### Save data externaly
            line = f"{I},{U},{rho_2D},{tSensor},{isStationaer}\n"
            with open(os.path.join(path, "data.csv"), "a") as f:
                f.write(line)
        
            ### Check if tSensor is in Target Area and stationary
            if tSensor <= (tTarget + tolerance) and tSensor >= (tTarget - tolerance) and isStationaer == True:
            
                if firstTime == True: #execute only first time in Loop
                    firstTime = False
                    data_points = beginMesurement(tTarget, I)
            
                line = f"    {rho_2D}\n"
                with open(os.path.join(path,"mesurement_data"), "a") as f:
                    f.write(line)
                data_points = data_points+1
            
                # Skip to next Step in Sequence
                if data_points >= tTime:
                    firstTime = True
                    break
        
        
            plotData(ax, fig, tSensorList, uList, tSensorLine, uLine)
        
            time.sleep(1)