"""
import pandas as pd
import numpy as np

# 1. Create sample DataFrames
df1 = pd.DataFrame({
    "Column A": [1, 2, 3],
    "Column B": [4, 5, 6],
    "Column C": [7, 8, 9]
})

df2 = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["New York", "Los Angeles", "Chicago"]
})

# 2. Use ExcelWriter with a 'with' statement
file_name = 'multiple_sheets_output.xlsx'

with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
    # 3. Write each dataframe to a different worksheet
    df1.to_excel(writer, sheet_name='Sheet1_Data', index=False) # index=False prevents writing the DataFrame index to Excel
    df2.to_excel(writer, sheet_name='Sheet2_People', index=False)

# 4. The file is saved automatically here
print(f"Successfully created '{file_name}' with sheets 'Sheet1_Data' and 'Sheet2_People'.")
"""

import pandas as pd

names = {
    # Name: [recipes given, max level needed]
    "Caroline": [0, 7],
    "Clint": [0, 7],
    "Demetrius": [0, 7],
    "Emily": [0, 7],
    "Evelyn": [0, 7],
    "George": [0, 7],
    "Gus": [0, 7],
    "Jodi": [0, 7],
    "Kent": [0, 7],
    "Leo": [0, 7],
    "Lewis": [0, 7],
    "Linus": [0, 7],
    "Marnie": [0, 7],
    "Pam": [0, 7],
    "Pierre": [0, 3],
    "Robin": [0, 7],
    "Sandy": [0, 7],
    "Shane": [0, 7],
    "Willy": [0, 7],
}
numSourcesIDX = 0
maxLevelIDX = 1

df = pd.read_csv("data/recipes.csv")

for name, score in names.items():
    # print(name, score) 

    for line in df["Recipe Source(s)"]:
        if name in line:
            names[name][numSourcesIDX] += 1

            # temp = str(line).split("(Mail - ")
            # if len(temp) > 1 and temp[1][0].isdigit():
            #     # print(temp[1][0])
            #     level = int(temp[1][0])
            #     if level > names[name][maxLevelIDX]:
            #         names[name][maxLevelIDX] = level


for name, score in names.items():
    print(name, score)
