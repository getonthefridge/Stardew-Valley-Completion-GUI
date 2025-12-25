import pandas as pd
from bs4 import BeautifulSoup
import re

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)

def get_recipes():
    file = "html/recipes.html"
    empty_df = pd.DataFrame(
        columns=[
            "Image",
            "Name",
            "Description",
            "Ingredients",
            "Energy / Health",
            "Buff(s)",
            "Buff Duration",
            "Recipe Source(s)",
            "Sell Price",
        ]
    )

    try:
        with open(file, "r", encoding="utf-8") as file:
            html = file.read()

        soup = BeautifulSoup(html, "html.parser")

        recipe_table = soup.find("table")

        # Get columns
        # ['Image\n            ', 'Name', 'Description', 'Ingredients', 'Energy\xa0/ Health', 'Buff(s)', 'Buff Duration', 'Recipe Source(s)', 'Sell Price\n            ']
        rawColumns = [header.text for header in recipe_table.find_all("th")]
        columns = []
        for col in rawColumns:
            col = col.replace("\n", "").replace("\xa0", " ").strip()
            # col = col.replace("\xa0", " ")
            # col = col.strip()
            columns.append(col)

        # Get rows
        rows = recipe_table.find_all("tr")[1:]  # Skip the header row
        rawRows = []
        for row in rows:
            cells = row.find_all("td")
            rawRow = [
                cell.text.strip()
                .replace("\n", "")
                .replace("\xa0", " ")
                .replace("                        ", " ")
                for cell in cells
            ]
            # print(len(rawRow))
            if len(rawRow) > 2:
                rawRows.append(rawRow)

        # Clean rows
        cleanedRows = []
        for row in rawRows:
            # print(row[8]) # TODO - gaps within the table are causing issues

            image = row[0]
            if image == "":
                image = None

            name = row[1]
            description = row[2]

            ingredients = re.findall(
                r".*?\(\d+\)", row[3]
            )  # parse 'ingredient (num) ingredient (num)' into a list

            energyAndHealth = row[4].replace(" ", " Energy, ") + " Health"

            buffs = re.findall(r".*?\([^)]+\)", row[5])
            if len(buffs) == 0:
                buffs = None

            buffDuration = row[6]
            if buffDuration == "N/A":
                buffDuration = None

            recipeSources = row[7]
            recipeText = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", row[7])
            recipeSources = re.split(r"Year \d+\s*", recipeText, maxsplit=1)
            recipeSources = [item.strip() for item in recipeSources if item.strip()]
            for i, recipe in enumerate(recipeSources):
                if "data-sort-value" in recipe:
                    recipeSources[i] = re.sub(r'data-sort-value="[^"]*">', "", recipe)
            
            
            # # fix missing space between letters and numbers
            # recipeText = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', row[7])
            # # split after the year
            # recipeSources = re.split(r'Year \d+\s*', recipeText, maxsplit=1)
            # recipeSources = [item.strip() for item in recipeSources if item.strip()]
            # # remove all data-sort-value variants
            # for i, recipe in enumerate(recipeSources):
            #     recipeSources[i] = re.sub(
            #         r'data-sort-value="+[^"]*"+>', 
            #         '', 
            #         recipe
            #     )
            
            
            
            
            
            

            sellPrice = row[8]
            sellPrice = re.sub(r'data-sort-value="[^"]*">', "", sellPrice)

            data = [
                image,
                name,
                description,
                ingredients,
                energyAndHealth,
                buffs,
                buffDuration,
                recipeSources,
                sellPrice,
            ]

            cleanedRows.append(data)

            # print(
            #     f'name: {name}\ndescription: {description}\ningredients: {ingredients}\nenergyAndHealth: {energyAndHealth}\nbuffs: {buffs}\nbuffDuration: {buffDuration}\nrecipeSources: {recipeSources}\nsellPrice: {sellPrice}\n{"*" * 50}'
            # )

        # df = pd.DataFrame(cleanedRows, columns=[str(col) for col in data])
        df = pd.DataFrame(cleanedRows, columns=columns)
        df.to_csv("data\\recipes.csv", index=False)
        return df

    except FileNotFoundError:
        print(
            f"File ({file}) not found. Please ensure the HTML file is in the correct location."
        )
        return empty_df

    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return empty_df


print(get_recipes())
