#!/usr/bin/env python3
import daq6510 # Multimeter 1
import heizer  # Heizplatte & Temperaturmessung

import os
import time
from datetime import datetime
import yaml
import atexit

import matplotlib.pyplot as plt
import numpy as np
import usbtmc



# Erstellt den Ergebnisordner und erstellt die Datein, sowie die erste Zeile der .cvs Datein
# Erg: Gibt den path zum Ergebnisordner zurück
def createFiles():
    date = datetime.now().strftime('%Y-%m-%d')
    parent_dir = "./data/"
    
    # Automatische Erzeugung von eindeutigen Filenamen, ohne das eine alte Datei überschrieben wird:
    directoryIndex = '#'+str(1).zfill(2)
    directory = f"{date}_{directoryIndex}" # Andere Dateiendungen (z.B. dat) auch möglich
    j = 1
    while os.path.exists(parent_dir + '/' + directory): # Schaut ob es den Namen schon in dem Verzeichnis gibt ...
        j = j + 1 # ... wenn ja wird der FleOutIndex (j) solange erhöht bis es eine neue Datei erstellen kann
        directoryIndex = '#'+str(j).zfill(2)
        directory = f"{date}_{directoryIndex}"
    
    path = os.path.join(parent_dir, directory)
    os.mkdir(path)
    
    # Pepare Files
    with open(os.path.join(path, "data.csv"), "w", encoding="utf-8") as f: 
        f.write("Angeleger Strom I,Gemessende Spannung U [mV],spezifischer Wiederstand rho,Gemessende Temperatur [degC],Messdaten\n")
        
    with open(os.path.join(path, "measurement_data.csv"), "w", encoding="utf-8") as f: 
        f.write(f"T_soll [degC],T_ist_avg [degC],T_ist_std [degC],I [A],U_avg [mV],U_std [mV]\n")
        
    return path


# Liest die Datei "settings.txt" ein.
# Erg: Wertelisten aus dem Rezept; für detalierte Beschreibung siehe debugPrint Fuktion
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
        print(f"Tiefe:          {tiefe}") # Tiefe der Probe
        print(f"tTarget:        {tTarget}") # Liste der Zieltemeraturen
        print(f"tToleranz:      {tToleranz}") # Liste des Tolranzbereich für die Zieltemeraturen
        print(f"tTime:          {tTime}") # Liste der Zeiten die für die Messung verwedet werden soll
        print(f"tStatio:        {tStationaer}") # Liste der Zeiten, die die Temperatur stationär sein soll
        print(f"tStatioToleranz:{tStationaerTolerace}") # Liste der Toleranz der Stationärtemperatur
        print(f"IList:          {IList}") # Liste der Ströme die angelegt werden; gilt für jede Zieltemperatur tTarget
        print("-----------------------\n")
        
    return tiefe, tTarget, tToleranz, tTime, tStationaer, tStationaerTolerace, IList

# Erg: Plotet mit den neusten Werten neu
def plotData(ax, List, Line):
    x = np.linspace(0,len(List),len(List))
    Line.set_xdata(x)
    ax.set_xlim([1, len(List)+1])
    
    if List != None:
        Line.set_ydata(List) # plot new line
        

# Prüft ob die Temperatur Stationär ist, gibt True zurück wenn ja.
# Vor: tList:               Liste der Temperaturen die geprüft werden sollen
#      tStationär:          Wie lang die Stationärität daueren soll in Minuten
#      tStationaerTolerace: Welche Temperaturabweichung "geduldet" wird in °C
def stationaerPruefung(tList, tStationaer, tStationaerTolerace):
    isStationaer = False
    if len(tList) > tStationaer: # Nur prüfen wenn über StationarTime Einträge vohanden sind
        tempList = tList[int(-tStationaer * 60):] # Liste der letzten Temperaturen erstellen...
        tempList.sort() # ...und sortieren
        #print(f"Größte   Temp:{round(tempList[-1],2)}\nKleinste Temp:{round(tempList[0],2)}")
        
        
        
        if tempList[-1] - tempList[0] <= tStationaerTolerace: # Wenn die größte die Temperaur und die Kleinste Temp. kleiner sind als der vorggebene Bereich
            isStationaer = True
            #print("Stationaer")
        else:
            isStationaer = False
            #print("Nicht Stationaer")
    return isStationaer



# Ließt die Temperatur der Heizplatte, die Spannung der Probe und berechnet den Oberflächenwiedertand
# Vor: Tiefe der Probe t in m
# Erg: Werteliste mit der Spannung U, des spezifischer Wiederstand rho_2D und der Temperatur T
def getData(t, debugPrint=False):
    
    U = round(float(daq.read().split(",")[1])*1000, 6) # Spannung die gemessen wird
    if U >= 100: U = 0 # Spannung auf Null setzen wenn nichts gemessen wird
    
    # Formeln siehe: https://iopscience.iop.org/article/10.1088/0953-8984/27/22/223201/pdf
    rho_2D = round(4.532 * (U/I) * t, 4) # spezifischer Wiederstand
        
    T = sensor.get_istwert()
        
    if debugPrint == True:
        print(f"U={U} mV")
        print(f"rho_2D={rho_2D}")
        print(f"{T}°C", end="\n\n")
    return U, rho_2D, T
    
# Schließt das Programm ordnugsgemäß
def on_close(event):
    sensor.stop_heizung() # Stopt die Heizung
    SourceMeter.write("SOURce:CURRent 0") # Schaltet den Strom auf 0A
    print("Program wurde ordungsgemäß geschlossen!")
    exit()
###########################################################################################
                                    ### ### ### BEGIN PREP ### ### ###
# Load config data
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)



# Multimeter DAQ6510 vorbeiten
daq = daq6510.Daq6510(config['DAQ-6510'])

# 2450SourceMeter vorbereiten
SourceMeter =  usbtmc.Instrument("USB::0x05e6::0x2450::INSTR")
print(SourceMeter.ask("*IDN?"))
SourceMeter.write("*RCL 0") #4-Spizzenmessung einstellen
SourceMeter.write("SOURce:CURRent 0")
SourceMeter.write(":OUTPut:STATe ON")


# Prepare Heizer
heizer.logging_on(True)
heizer_config = config['Heizer']['Schnittstelle']
sensor = heizer.HeizerPlatte(**heizer_config)
sensor.start_heizung()


# Listen, Variablen
tList = [0] # Speichert alle gemessenden Temperaturen intern
uList = [0] # Speichert alle gemessenden Spannungn intern
iList = [0] # Speichert alle gesetzten Ströme intern

#liest alle Listen der settings.txt ein. Für eine Erklärung siehe readRezept() Funktion
tiefe, tTargetList, tToleranceList, tTimeList, tStationaerList, tStationaerToleraceList, IList = readRezept()

path = createFiles()


# Plot Prep.
x = 0

plt.ion()
fig = plt.figure(figsize=(8,8)) # Fenster Größe des Diagrammes festlegen
fig.suptitle("Programm wird beendet, wenn Plot geschlossen wird!",fontsize=14) # Erzeugt eine Gesamt Überschrifft des Graphen

# Graph: Spannung
ax1 = plt.subplot(211)
ax1.set_ylim([0, 1.1])
uLine, = ax1.plot(x, uList) # plottet Spannung
iLine, = ax1.plot(x, iList) # plottet Strom
plt.title("Spannung, Strom", fontsize=12)
plt.xlabel("Zeit [s]",fontsize=10)
plt.ylabel("Spannung [mV], Strom [A]",fontsize=10)
plt.grid()

# Graph: Temperatur
ax2 = plt.subplot(212)
ax2.set_ylim([0, 300])
tLine, = ax2.plot(x, tList) # plottet Temperatur
plt.title("Temperatur", fontsize=12)
plt.xlabel("Zeit [s]",fontsize=10)
plt.ylabel("Temperatur [°C]",fontsize=10)
plt.grid()

plt.tight_layout()
plt.show()
fig.canvas.mpl_connect('close_event', on_close) # Programm wird beendet, wenn Plot geschlossen wird!

###########################################################################################
                         ### ### ### BEGIN LOOP ### ### ###

for i in range(len(tTargetList)): # Für jede Temperatur:
    
    # Erstellt die aktuellen Variablen zur Temperatur aus den settings.txt Listen
    tTarget     = float(tTargetList[i])
    tTolerance  = float(tToleranceList[i])
    tTime       = float(tTimeList[i])
    tStationaer = float(tStationaerList[i])
    tStationaerTolerace = float(tStationaerToleraceList[i])
    
    #Änderung der Zieltemperaur auf tTarget
    sensor.change_SollTemp(str(tTarget))
    print(f"Nächste Temperatur!\n  tTarget={tTarget}°C")
        
    for tempI in IList: # Für jeden Strom (in jeder Temperatur):
        
        uListTemp = [] #  speichert Spannungen in aktueller Messung
        tListTemp = [] #  speichert Temperaturen in aktueller Messung
        data_points = 0 # speichert wie viele Messpunkte es gibt (in aktueller Messung)
        
        #Änderung des Stroms auf I
        I = float(tempI)
        SourceMeter.write(f"SOURce:CURRent {I}")
        print(f"Nächster Strom!\n  I={I}A")
        
        while True: # Hauptloop beginnt
            
            calcStart = time.time() #Speichert Zeit wann der Loop beginnt (um Berechnungszeit festzustellen)
            
            U, rho_2D, T = getData(float(tiefe)/1000, False) # Get Data
        
            # Save data internaly for plot Data function
            tList.append(T) #speichert Temperatur
            uList.append(U) #speichert Spannung
            iList.append(I) #speichert Strom
            
            isStationaer = stationaerPruefung(tList, tStationaer, tStationaerTolerace) #prüft Stationärität
        
            # Save data externaly in data.csv file
            line = f"{I},{U},{rho_2D},{T},{isStationaer}\n"
            with open(os.path.join(path, "data.csv"), "a", encoding="utf-8") as f:
                f.write(line)
        
            # Check if T is in Target Area and stationary
            if T <= (tTarget + tTolerance) and T >= (tTarget - tTolerance) and isStationaer == True:
                uListTemp.append(U) # Speichert alle Spannungen (in mV) der aktuellen Messung
                tListTemp.append(T) # Speichert alle Temperaturn der aktuellen Messung
                data_points = data_points + 1
            
                # Skip to next Step in Sequence
                if data_points >= tTime * 60:
                    # Speichert gerundete Werte der aktuellen Messung in measurement_data.csv datei
                    # Achtung: passiert erst am Schluss der akteullen Messung!
                    with open(os.path.join(path,"measurement_data.csv"), "a", encoding="utf-8") as f:
                        line = f"{tTarget},{round(np.mean(tListTemp),6)},{round(np.std(tListTemp),6)},{I},{round(np.mean(uListTemp),6)},{round(np.std(uListTemp),6)}\n"
                        f.write(line)
                    break # Beendet die aktuelle Messung und springt zur nächsten
            
            # plottet die verschiedenen Linien
            plotData(ax1, uList, uLine)
            plotData(ax1, iList, iLine)
            plotData(ax2, tList, tLine)
            
            # aktualiesiert den Graphen
            fig.canvas.draw()
            fig.canvas.flush_events()

            calcEnd = time.time() # speichert Zeit am Ende der Berechnung
            
            # adjust for calculation time so every step is exactly 1s appart
            calcTime = calcEnd - calcStart
            if calcTime < 1:
                time.sleep(1 - calcTime)
            else:
                print(f"Achtung: Berechnungszeit ist größer als der Messabstand!\n  calcTime={round(calcTime,2)}s")
        
        plt.savefig(os.path.join(path,"plot.png")) # save Plot after every current

plt.close() # Beendet das Skript in den der Plot geschlossen wird und die on_close() Funktion ausgelößt wird