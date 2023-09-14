# 4-point-measurement
Measure voltage and specific resistance with the 4-Point-methode

## <u> 1. About Us: </u>
This project is used to measure voltage and specific resistance with the 4-point method. The Python script completely automates the process.

The project is being processed by the model experiments group at the IKZ - Leibniz Institut für Kristallzüchtung.

---
## <u> 2. Introduction: </u>
The 4-Point method uses four probes to measure voltage at a set current, which is induced by two of the four probes. The specific resistance can be calculated with the known and measured values. For additional information, read here: https://iopscience.iop.org/article/10.1088/0953-8984/27/22/223201/pdf.

---
##  <u> 3. Hardware setup: </u>
A Raspberry Pi 400 is used as the computer. Connected to the Pi are the "2450 SourceMeter" with USB, the "DAQ6510" with RS232 to USB, and the "IKA C-MAG HS 7" with RS232 to USB. The sample is placed on the heating plate. The four probes are placed on the sample with sufficient weight (!) and are connected to the "2450 SourceMeter"which is capable of the 4-point-measurement method. Two more probes are placed at the back of the probes that measure the voltage and are connected to the "DAQ6510," which ensures higher accuracy.

---
##  <u> 4. Software setup: </u>
The internal script "Setup00" of the "2450 SourceMeter" has to be configured for 4-point-measurement.
The following external libraries are used: yaml, atexit, matplotlib, numpy, usbtmc


---
##  <u> 5. Usage of the scripts: </u>
Before using "hauptprogramm.py" "config.yml" and "settings.txt" have to be configured.
"config.yml" is used to configure the DAQ6510 and the heating plate (IKA or Eurotherm).
"settings.txt" is used to configure the depth of the sample, the currents used and the temperature settings. Read settings.txt for detailed information.
The "2540 SourceMeter" is configured directly in the script, no configuration should be needed.
A method to control the "2540 SourceMeter" over the Internet and Selenium can be found in 2450SourceMeterWithInternet.py, but it is not used.
If all settings are configured, hauptprogramm.py can be started. The program should start and run automatically, with no further action needed. If a plot appears and moves once a second, the program runs as intended. The program is finished when the plot closes. If the plot is closed early, the program will halt. 

---
##  <u> 6. Results: </u>
Results are stored in the "data" folder. A list of every value record can be found in "data.csv". A list of average measurement data and standard deviations can be found in "measerment_data.csv". Also, a screenshot of the plot is found in the folder.