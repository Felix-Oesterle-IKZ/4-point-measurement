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
        
    with open(os.path.join(path, "measurement_data.csv"), "w", encoding="utf-8") as f: 
        f.write(f"T_soll [°C],I [A],U_avg [V],U_std [V]\n")
        
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
    tStationaerTolerace = []
    
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
            tStationaerTolerace.append(line.split(",")[4])
    
    # remove the "r:"
    for i in range(len(tTarget)):
        tTarget[i] = tTarget[i].replace("r:", "")
        
    if debugPrint == True:
        print(f"Tiefe:          {tiefe}")
        print(f"tTarget:        {tTarget}")
        print(f"tToleranz:      {tToleranz}")
        print(f"tTime:          {tTime}")
        print(f"tStatio:        {tStationaer}")
        print(f"tStatioToleranz:{tStationaerTolerace}")
        print(f"IList:          {IList}")
        print("-----------------------\n")
        
    return tiefe, tTarget, tToleranz, tTime, tStationaer, tStationaerTolerace, IList

# Erg: Plotet mit den neusten Werten neu und legt die Grezen des Graphen neu fest.
def plotData(ax, fig, List, Line):
    #x1 = np.linspace(0,len(tSensorList),len(tSensorList))
    x2 = np.linspace(0,len(List),len(List))
    #tSensorLine.set_xdata(x1)
    Line.set_xdata(x2)
    ax.set_xlim([0, len(List)+1])
    
    if List != None:
        #tSensorLine.set_ydata(tSensorList) #plot new line
        uLine.set_ydata(List) #plot new line
        ax.set_ylim([0, 2])
        
    fig.canvas.draw()
    fig.canvas.flush_events()

### Prüfen ob die Temperatur Stationär ist
def stationaerPruefung(temperaturListe, tStationaer, tStationaerTolerace):
    isStationaer = False
    if len(temperaturListe) > tStationaer: # Nur prüfen wenn über StationarTime Einträge vohanden sind
        tempList = temperaturListe[int(-tStationaer*60):] # Liste der letzten Temperaturen erstellen...
        tempList.sort() # ...und sortieren
        #print(f"Größte   Temp:{round(tempList[-1],2)}\nKleinste Temp:{round(tempList[0],2)}")
        
        
        
        if tempList[-1] - tempList[0] <= tStationaerTolerace: # Wenn die größte die Temperaur und die Kleinste Temp. kleiner sind als der vorggebene Bereich
            isStationaer = True
            #print("Stationaer")
        else:
            isStationaer = False
            #print("Nicht Stationaer")
    return isStationaer

#Sends Command to 2540 over LAN
def sendCommand2450(command):
    driver.get("http://admin:admin@172.20.22.127/commands.html")
    input_text_cmd = driver.find_element(By.ID, 'cmd')
    input_text_cmd.send_keys(command)
    time.sleep(1.9)
    driver.find_element(By.ID, 'send').click()
    #driver.quit()
    
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
    
    
###########################################################################################
                                    ### ### ### BEGIN PREP ### ### ###
# Load config data
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

# Selenium vorbereiten
service = Service(executable_path='/usr/bin/chromedriver')
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

# 2450 SorceMeter vorbereiten
sendCommand2450(f"*RCL 0") #4-Spizzenmessung einstellen
sendCommand2450(":OUTPut:STATe ON")

# Multimeter DAQ6510 vorbeiten
daq = daq6510.Daq6510(config['DAQ-6510'])



# Prepare Heizer
heizer.logging_on(True)
heizer_config = config['Heizer']['Schnittstelle']
sensor = heizer.HeizerPlatte(**heizer_config)
sensor.start_heizung()

# Listen, Variablen
tSensorList = [0] # Stores all Temperatures from sensor internaly
uList = [0] # Stores all Temperatures from Calibration instrument internaly
tiefe, tTargetList, tToleranceList, tTimeList, tStationaerList, tStationaerToleraceList, IList = readRezept() # tTargetList ist die Liste der Zieltempraturen,# tTimeList ist die Liste der "Verweilzeiten"
path = createFiles()

# Plot Prep.
x1 = 0
x2 = 0
fig, ax = plt.subplots(figsize=(8, 6))
plt.title("Spannung über Zeit", fontsize=16)
plt.xlabel("Zeit [s]",fontsize=14)
plt.ylabel("Spannung [V]",fontsize=14)
ax.set_ylim([0, 1])
plt.grid()
plt.ion()
plt.show()
tSensorLine, = plt.plot(x1, tSensorList)
uLine, = plt.plot(x2, uList)

###########################################################################################
                         ### ### ### BEGIN LOOP ### ### ###

for i in range(len(tTargetList)): # Für jede Temperatur:
    
    tTarget     = float(tTargetList[i])
    tTolerance  = float(tToleranceList[i])
    tTime       = float(tTimeList[i])
    tStationaer = float(tStationaerList[i])
    tStationaerTolerace = float(tStationaerToleraceList[i])
    data_points = 0
    sensor.change_SollTemp(str(tTarget))
    print(f"Nächste Temperatur!\ntTarget={tTarget}°C")
        
    for tempI in IList: #Für jeden Strom in jeder Temperatur:
        uListTemp = []
        data_points = 0
        
        I = float(tempI)
        sendCommand2450(f"SOURce:CURRent {I}")
        
        print(f"Nächster Strom!\n  I={I}A")
        while True:
            U, rho_2D, tSensor = getData(float(tiefe)/1000, False) # Get Data
        
            ### Save data internaly for plot Data function
            tSensorList.append(tSensor)
            uList.append(U)
        
            isStationaer = stationaerPruefung(tSensorList, tStationaer, tStationaerTolerace)
        
            ### Save data externaly
            line = f"{I},{U},{rho_2D},{tSensor},{isStationaer}\n"
            with open(os.path.join(path, "data.csv"), "a", encoding="utf-8") as f:
                f.write(line)
        
            ### Check if tSensor is in Target Area and stationary
            if tSensor <= (tTarget + tTolerance) and tSensor >= (tTarget - tTolerance) and isStationaer == True:
                uListTemp.append(U)
                data_points = data_points+1
            
                # Skip to next Step in Sequence
                if data_points >= tTime*60:
                    firstTime = True
                    with open(os.path.join(path,"measurement_data.csv"), "a", encoding="utf-8") as f:
                        line = f"{tTarget},{I},{round(np.mean(uListTemp),4)},{round(np.std(uListTemp),4)}\n"
                        f.write(line)
                    uListTemp = []
                    break
        
            plotData(ax, fig, uList, uLine)
            #plotData(ax, fig, tSensorList, tSensorLine)
            
            time.sleep(1)

# Programm beenden:
sensor.stop_heizung()
plt.savefig(os.path.join(path,"plot.png"))
plt.close()
driver.quit()