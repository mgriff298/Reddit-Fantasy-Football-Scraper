from selenium import webdriver
from selenium.webdriver.common.by import By
import string

# initiate driver, upper case alphabet, and results list
driver = webdriver.Chrome()
alph = string.ascii_uppercase

elementList = []

# navigate through all pages containing players' names, grab data, and place in results list
for page in alph:
    url = 'https://www.footballdb.com/players/current.html?letter=' + page
    driver.get(url)
    table = driver.find_element(By.CLASS_NAME, 'divtable.divtable-striped')    
    elementList.append(table.text)

# create and open a text file and write results to it
playerNames = open('PlayerNames.txt', 'w')
playerNames.writelines(elementList)

# close out of text file and driver
playerNames.close()
print(elementList)
driver.close()