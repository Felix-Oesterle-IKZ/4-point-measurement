#!/usr/bin/env python3
import daq6510 # Multimeter 1
import heizer  # Heizplatte & Temperaturmessung

import os
import time
from datetime import datetime
import yaml

import matplotlib.pyplot as plt
import numpy as np

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Erstellt den Ergebnis Ordner und bereitet die Datein vor.
# Gibt den path zum Ergebnisordner zurück
def createFiles():
    directory = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    parent_dir = "./data/"
    path = os.path.join(parent_dir, directory)
    os.mkdir(path)
    ### Pepare Files
    with open(os.path.join(path, "data.csv"), "w", encoding="utf-8") as f: 
        f.write("Angeleger Strom I,Gemessende Spannung U,spezifischer Wiederstand rho,Gemessende Temperatur [°C],Messdaten\n")
        
    with open(os.path.join(path, "mesurement_data"), "w", encoding="utf-8") as f: 
        f.write(f"""Zieltemperaturen: {tTargetList}\nSpannungen: {IList}\n""")
        
    return path


# Liest die Datei "settings.txt" ein.
# Erg: Wertelisten aus dem Rezept.
def readRezept(debugPrint=True):
    with open("settings.txt", "r", encoding="utf-8") as f:
        rezept = f.read().split("\n")
    
    tiefe = 0 # in mm
    tTarget = [] # in °C
    tToleranz = [] # in °C
    tTime = []   # in min
    tStationaer = [] # in min
    
    for temp in rezept:
        line = temp.replace(" ", "")
        
        if line.startswith("t:") == True:
            tiefe = line.replace("t:", "")
            
        elif line.startswith("i:"):
            IList = line.split(",")
            IList[0] = IList[0][2:] # remove the "i:"
            
        elif line.startswith("r:"):
            tTarget.append(line.split(",")[0])
            tToleranz.append(line.split(",")[1])
            tTime.append(line.split(",")[2])
            tStationaer.append(line.split(",")[3])
    
    # remove the "r:"
    for i in range(len(tTarget)):
        tTarget[i] = tTarget[i].replace("r:", "")
        
    if debugPrint == True:
        print(f"Tiefe: {tiefe}")
        print(f"tTarget: {tTarget}")
        print(f"tToleranz: {tToleranz}")
        print(f"tTime:   {tTime}")
        print(f"tStatio: {tStationaer}")
        print(f"IList:   {IList}")
        print("-----------------------\n")
    return tiefe, tTarget, tToleranz, tTime, tStationaer, IList

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
    isStationaer = False
    if len(temperaturListe) > tStationaer: # Nur prüfen wenn über StationarTime Einträge vohanden sind
        tempList = temperaturListe[int(-tStationaer*60):] # Liste der letzten Temperaturen erstellen...
        tempList.sort() # ...und sortieren
        #print(f"Größte   Temp:{round(tempList[-1],2)}\nKleinste Temp:{round(tempList[0],2)}")
        
        
        
        if tempList[-1] - tempList[0] <= StationaerAbweichung: # Wenn die größte die Temperaur und die Kleinste Temp. kleiner sind als der vorggebene Bereich
            isStationaer = True
            #print("Stationaer")
        else:
            isStationaer = False
            #print("Nicht Stationaer")
    return isStationaer

#Sends Command to 2540 (slow!)
def sendCommand2450(command):
    driver.get("http://admin:admin@172.20.22.127/commands.html")
    input_text_cmd = driver.find_element(By.ID, 'cmd')
    input_text_cmd.send_keys("*RCL 1")
    time.sleep(2)
    driver.find_element(By.ID, 'send').click()
    driver.quit()
    
# Ließt die Temperatur der Heizplatte, die Spannung der Probe und berechnet den Oberflächenwiedertand
# Vor: Tiefe der Probe t in m
# Erg: Werteliste
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


# Berechnet dden Durchschnitt einer Liste
def avrgOfList(liste):
    avrg = 0
    for x in liste:
        avrg = avrg + x
    return avrg/len(liste)
                                    ### ### ### BEGIN PREP ### ### ###
#Selenium vorbereiten
service = Service(executable_path='/usr/bin/chromedriver')
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# Load config data
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

daq = daq6510.Daq6510(config['DAQ-6510']) # Multimeter DAQ6510 vorbeiten

### Prepare Heizer
heizer.logging_on(True)
heizer_config = config['Heizer']['Schnittstelle']
sensor = heizer.HeizerPlatte(**heizer_config)


### Listen
tSensorList = [0] # Stores all Temperatures from sensor internaly
uList = [0] # Stores all Temperatures from Calibration instrument internaly


tiefe, tTargetList, tToleranceList, tTimeList, tStationaerList, IList = readRezept() # tTargetList ist die Liste der Zieltempraturen,# tTimeList ist die Liste der "Verweilzeiten"
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
#k = 1 # korrekturfaktor oE
#s = 0.03 #Strecke zwischen zwei Messspitzen in m
for i in range(len(tTargetList)): # Für jede Temperatur:
    
    tTarget     = float(tTargetList[i])
    tTolerance  = float(tToleranceList[i])
    tTime       = float(tTimeList[i])
    tStationaer = float(tStationaerList[i])
    data_points = 0
    sensor.change_SollTemp(str(tTarget))
    print(f"Nächste Temperatur!\ntTarget={tTarget}°C")
    
    with open(os.path.join(path, "mesurement_data"), "a", encoding="utf-8") as f:
        f.write(f"\nZieltemperatur: {tTarget}°C\n")
        
    for tempI in IList: #Für jeden Strom in jeder Temperatur:
        rho_2DList = []
        
        sendCommand2450(f"*RCL {tempI}")
        
        if int(tempI) == 0:
            I = 0.150
        elif int(tempI) == 2:
            I = 0.450
        elif int(tempI) == 4:
            I = 0.750
        else:
            print(f"ERROR: tempI={tempI}")
            
        print(f"Nächster Strom!\nI={I}A")
        while True:
            U, rho_2D, tSensor = getData(float(tiefe)/1000, True) # Get Data
        
            ### Save data internaly for plot Data function
            tSensorList.append(tSensor)
            uList.append(U)
        
            isStationaer = stationaerPruefung(tSensorList, tStationaer)
        
            ### Save data externaly
            line = f"{I},{U},{rho_2D},{tSensor},{isStationaer}\n"
            with open(os.path.join(path, "data.csv"), "a", encoding="utf-8") as f:
                f.write(line)
        
            ### Check if tSensor is in Target Area and stationary
            if tSensor <= (tTarget + tTolerance) and tSensor >= (tTarget - tTolerance) and isStationaer == True:
            
                if firstTime == True: #execute only first time in Loop
                    firstTime = False
                    data_points = 0
                    #beginMesurement(tTarget, I)
                    
                rho_2DList.append(rho_2D)
                """
                line = f"    {rho_2D}\n"
                with open(os.path.join(path,"mesurement_data"), "a") as f:
                    f.write(line)
                """
                data_points = data_points+1
            
                # Skip to next Step in Sequence
                if data_points >= tTime*60:
                    firstTime = True
                    with open(os.path.join(path,"mesurement_data"), "a", encoding="utf-8") as f:
                        line = f"  Oberflächenwiederstand bei {I}A: {round(avrgOfList(rho_2DList),3)}\n"
                        f.write(line)
                    break
        
        
            plotData(ax, fig, tSensorList, uList, tSensorLine, uLine)
        
            time.sleep(1)

# Programm beenden:
sensor.stop_heizung()