import pandas as pd
from ast import literal_eval
import json


def get_unchecked_ingredients():
    recipeDF = pd.read_csv('data/recipes.csv')
    ingredientsCol = recipeDF['Ingredients'].tolist()

    maxIDX = len(recipeDF) - 1
    with open('checked_rows.json', 'r') as f:
        content = f.read().strip()
        if content:
            checkedIDXs = json.loads(content)
        else:
            checkedIDXs = []

    uncheckedIDXs = []
    for i in range(0, maxIDX):
        if i not in checkedIDXs:
            uncheckedIDXs.append(i)

    neededIngredientsLists = [ingredientsCol[i] for i in uncheckedIDXs]
    neededDF = pd.DataFrame(columns=['Ingredient', 'Required'])

    for lst in neededIngredientsLists:
        for item in literal_eval(lst):
            txt = item.strip()
            txt = txt.split(' (')
            ingredientName = txt[0]
            ingredientQuantity = int(txt[1][:-1])

            if ingredientName not in neededDF['Ingredient'].tolist():
                neededDF.loc[len(neededDF)] = [ingredientName, ingredientQuantity]
            else:
                q = neededDF.loc[neededDF['Ingredient'] == ingredientName, 'Required'].iloc[0]
                neededDF.loc[
                    neededDF['Ingredient'] == ingredientName, 'Required'
                ] = q + ingredientQuantity

    return neededDF


def parse_ingredients(df):
    items = []
    for i in range(len(df)):
        ingredients = literal_eval(df.iloc[i]['Ingredients'])
        names = [item.strip().split(' (')[0] for item in ingredients]
        text = ''
        for name in names:
            text += name + ', '
        text = text[:-2]
        items.append(text)
    df['Recipe'] = items


