# Achtung!
# "import Selenium" ist nicht ausreichend, Webdriver muss zusätzlich installiert werden.
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

#Sends Command to 2540 over LAN
def sendCommand2450(command):
    driver.get("http://admin:admin@172.20.22.127/commands.html")
    input_text_cmd = driver.find_element(By.ID, 'cmd')
    input_text_cmd.send_keys(command)
    time.sleep(1.9)
    driver.find_element(By.ID, 'send').click()
    #driver.quit()
    
# Selenium vorbereiten
service = Service(executable_path='/usr/bin/chromedriver')
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

#sendCommand2450(":OUTPut:STATe ON")

