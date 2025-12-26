from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
import re

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", None)


def get_recipes():
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
        # with open("html/recipes.html", "r", encoding="utf-8") as file:
        BASE_DIR = Path(__file__).resolve().parent
        with open(Path(__file__).resolve().parents[1] / "html" / "recipes.html", encoding="utf-8") as file:
            html = file.read()

        soup = BeautifulSoup(html, "html.parser")

        recipe_table = soup.find("table")

        # Get columns
        # ['Image\n            ', 'Name', 'Description', 'Ingredients', 'Energy\xa0/ Health', 'Buff(s)', 'Buff Duration', 'Recipe Source(s)', 'Sell Price\n            ']
        rawColumns = [header.text for header in recipe_table.find_all("th")]
        columns = []
        for col in rawColumns:
            col = col.replace("\n", "").replace("\xa0", " ").strip()
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
            recipeText = (list(recipeSources.split('\n')))
            # print(recipeSources)
            # recipeSources = re.split(r"Year \d+\s*", recipeText, maxsplit=1)
            # recipeSources = [item.strip() for item in recipeSources if item.strip()]
            # for i, recipe in enumerate(recipeSources):
            #     if "data-sort-value" in recipe:
            #         recipeSources[i] = re.sub(r'data-sort-value="[^"]*">', "", recipe)
            # print(recipeSources)

            for i, source in enumerate(recipeText):
                if '(Mail -' in source:
                    txt = source.split('(Mail -')
                    playerName = txt[0][:-1]
                    lvl = int(txt[1].split('+')[0][1:])
                    recipeText[i] = playerName + ' ' + str(lvl) + '\u2665'

                elif 'The Queen of Sauce' in source:
                    txt = ''
                    tvDate = ''
                    saloonPrice = ''
                    if 'Stardrop Saloon' not in source:
                        tvDate = source.replace('The Queen of Sauce', 'TV: ').replace(', ', ' ')
                    else:
                        saloonPrice = 'Stardrop Saloon: ' + source.split('Stardrop Saloon')[1].split('">')[1]
                    txt += f'{tvDate}, {saloonPrice}'
                    recipeText[i] = txt  # ← assign back

                elif 'Ginger Island Resort' in source:
                    recipeText[i] = 'Ginger Island Resort: 2000g'
                elif 'Stardrop Saloon' in source:
                    recipeText[i] = 'Stardrop Saloon: ' + source.split('Stardrop Saloon')[1].split('">')[1]
                elif 'Dwarf Shop' in source:
                    recipeText[i] = 'Dwarf Shop: ' + source.split('Dwarf Shop')[1].split('">')[1]



            # recipeText_cleaned = [s.strip() for s in recipeText if s.strip() != '']
            # recipeText_cleaned = [s[2:] for s in recipeText_cleaned if s.startswith(', ') ]
            recipeText_cleaned = [s.lstrip(',').rstrip(',').strip() for s in recipeText if s.strip() != '']
            recipeText_str = ', '.join(recipeText_cleaned)


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
                recipeText_str,
                sellPrice,
            ]
            # print(data)

            cleanedRows.append(data)

        df = pd.DataFrame(cleanedRows, columns=columns)
        df.to_csv(Path(__file__).resolve().parents[1] / "data" / "recipes.csv", index=False)
        return df

    except FileNotFoundError:
        print(
            f"File ({file}) not found. Please ensure the HTML file is in the correct location."
        )
        return empty_df

    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return empty_df


# print(get_recipes())
get_recipes()
