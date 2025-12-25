import pandas as pd
from ast import literal_eval
import re


def get_unchecked_ingredients():
    recipeDF = pd.read_csv('data/recipes.csv')
    ingredientsCol = recipeDF['Ingredients'].tolist()

    maxIDX = len(recipeDF) - 1
    with open('checked_rows.json', 'w+') as f:
        if len(f.read()) != 0:
            text = list(f.read()[1:-1].split(', '))
            checkedIDXs = [int(num) for num in text]
        else:
            checkedIDXs = []
        # print(checkedIDXs)

    uncheckedIDXs = []
    for i in range(0, maxIDX):
        if i not in checkedIDXs:
            uncheckedIDXs.append(i)
    # print(uncheckedIDXs)

    neededIngredientsLists = [ingredientsCol[i] for i in uncheckedIDXs]
    neededDF = pd.DataFrame(columns=['Ingredient', 'Quantity Needed'])

    # pd.set_option('display.max_rows', None)

    for lst in neededIngredientsLists:
        for item in literal_eval(lst):
            txt = item.strip()
            txt = txt.split(' (')
            ingredientName = txt[0]
            ingredientQuantity = int(txt[1][:-1])

            if ingredientName not in neededDF['Ingredient'].tolist():
                neededDF.loc[len(neededDF)] = [ingredientName, ingredientQuantity]
            else:
                q = neededDF.loc[neededDF['Ingredient'] == ingredientName, 'Quantity Needed'].iloc[0]
                neededDF.loc[
                    neededDF['Ingredient'] == ingredientName, 'Quantity Needed'
                ] = q + ingredientQuantity
    return neededDF
    # print(neededDF)


# get_unchecked_ingredients().head().to_clipboard()
# print(get_ingredients())


def get_ingredients():
    try:
        recipeDF = pd.read_csv('data/recipes.csv')
        ingredientsCol = recipeDF['Ingredients'].tolist()

        dct = {c: [] for c in ['Ingredient', 'Quantity Needed']}
        df = pd.DataFrame(columns=['Ingredient', 'Quantity Needed'])

        for mealIngredients in ingredientsCol:
            # Convert string to list
            for i in literal_eval(mealIngredients):
                ingredientAndQuantity = i.strip()
                ingredients, quantity = re.match(r'^(.*?)\s*\((\d+)\)$', ingredientAndQuantity).groups()
                print(ingredients, quantity)

                # TODO finish dictionary
                if ingredients not in dct['Ingredient']:
                    dct['Ingredient'].append(ingredients)
                    dct['Quantity Needed'].append(int(quantity))



    except FileNotFoundError:
        print(
            'File not found. Please ensure the "recipes.csv" file is present in the "data" directory.'
        )
    except Exception as e:
        print(f'An error occurred: {e}')

# get_ingredients()
