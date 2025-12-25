import pandas as pd
from bs4 import BeautifulSoup
import re

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

def get_crops():
    file = 'html/crops.html'
    
    with open(file, 'r', encoding='utf-8') as file:
        html = file.read()
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    
    rawColumns = [header.text for header in table.find_all("th")]
    columns = []
    for col in rawColumns:
        columns.append(str(col.strip('\n')).strip())
        
    rows = table.find_all('tr')
    for row in rows:
        rawCells = row.find_all("td")
        cells = []
        for cell in rawCells:
            cells.append(str(cell.text.strip('\n')).strip())
        # print(cells)
        
    cleanedRows = []
    print(rows[1].text.strip('\n'))
        

get_crops()