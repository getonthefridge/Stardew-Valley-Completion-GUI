import pandas as pd
import json
import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from ast import literal_eval
from ingredients import get_unchecked_ingredients

CHECKED_ROWS = 'checked_rows.json'
QUANTITY_OWNED = 'quantity_owned.json'

# ---------- Load Data ----------
recipeDF = pd.read_csv('data/recipes.csv')
recipeDF = recipeDF[['Name', 'Ingredients', 'Recipe Source(s)']]

ingredientsDF = get_unchecked_ingredients()
ingredientsDF['Quantity Owned'] = 0
ingredientsDF['Need to Get'] = ingredientsDF['Quantity Needed'] - ingredientsDF['Quantity Owned']

# Load saved states
# checked = set()
# if os.path.exists(CHECKED_ROWS):
#     with open(CHECKED_ROWS, 'w+') as f:
#         if len(f.read()) != 0:
#             checked = set(json.load(f))
#
#         # else:
#
# owned_dict = {}
# if os.path.exists(QUANTITY_OWNED):
#     with open(QUANTITY_OWNED, 'w+') as f:
#         if len(f.read()) != 0:
#             owned_dict = json.load(f)
#             for idx, qty in owned_dict.items():
#                 ingredientsDF.loc[int(idx), 'Quantity Owned'] = qty
#             ingredientsDF['Need to Get'] = ingredientsDF['Quantity Needed'] - ingredientsDF['Quantity Owned']
# Load saved states
checked = set()
if os.path.exists(CHECKED_ROWS):
    with open(CHECKED_ROWS, 'r') as f:  # <-- read mode
        content = f.read()
        if content.strip():  # only load if file is not empty
            checked = set(json.loads(content))

owned_dict = {}
if os.path.exists(QUANTITY_OWNED):
    with open(QUANTITY_OWNED, 'r') as f:  # <-- read mode
        content = f.read()
        if content.strip():
            owned_dict = json.loads(content)
            for idx, qty in owned_dict.items():
                ingredientsDF.loc[int(idx), 'Quantity Owned'] = qty
            ingredientsDF['Need to Get'] = ingredientsDF['Quantity Needed'] - ingredientsDF['Quantity Owned']




# ---------- Save functions ----------
def save_checked():
    with open(CHECKED_ROWS, 'w') as f:
        json.dump(sorted(checked), f)


def save_owned():
    for idx in ingredientsDF.index:
        owned_dict[str(idx)] = int(ingredientsDF.loc[idx, 'Quantity Owned'])
    with open(QUANTITY_OWNED, 'w') as f:
        json.dump(owned_dict, f)


# ---------- GUI ----------
root = tk.Tk()
root.title('Stardew Tracker')
root.geometry('1000x500')
font = tkfont.Font()
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# ---------- Recipes Tab ----------
recipes_tab = ttk.Frame(notebook)
notebook.add(recipes_tab, text='Recipes')

recipe_cols = ['✔'] + list(recipeDF.columns)
recipes_tree = ttk.Treeview(recipes_tab, columns=recipe_cols, show='headings')
for c in recipe_cols:
    recipes_tree.heading(c, text=c)
    recipes_tree.column(c, anchor='w')
recipes_tree.column('✔', width=40, anchor='center')

for i, row in recipeDF.iterrows():
    mark = '✔' if i in checked else ''
    recipes_tree.insert(
        '', 'end', iid=str(i),
        values=[mark, row['Name'], row['Ingredients'], row['Recipe Source(s)']]
    )

recipes_tree.pack(fill='both', expand=True)

# ---------- Ingredients Tab ----------
ingredients_tab = ttk.Frame(notebook)
notebook.add(ingredients_tab, text='Ingredients')

ingredient_cols = list(ingredientsDF.columns)
ingredients_tree = ttk.Treeview(ingredients_tab, columns=ingredient_cols, show='headings')
for c in ingredient_cols:
    ingredients_tree.heading(c, text=c)
    ingredients_tree.column(c, anchor='w')

for i, row in ingredientsDF.iterrows():
    ingredients_tree.insert(
        '', 'end', iid=str(i),
        values=[row['Ingredient'], row['Quantity Needed'], row['Quantity Owned'], row['Need to Get']]
    )

ingredients_tree.pack(fill='both', expand=True)


# ---------- Link Tables ----------
def update_ingredients_from_recipesssss(index, adding=True):
    '''Adjust Ingredients tab based on a recipe being checked or unchecked.'''
    ingredients_str = recipeDF.loc[index, 'Ingredients']  # the column with string list
    items = literal_eval(ingredients_str)
    for item in items:
        txt = item.strip()
        name, qty = txt.split(' (')
        qty = int(qty[:-1])
        if not adding:
            qty = -qty  # subtract if unchecking

        # find the ingredient in ingredientsDF
        match = ingredientsDF['Ingredient'] == name
        if match.any():
            # increase Quantity Owned if adding
            ingredientsDF.loc[match, 'Quantity Owned'] += qty
            # clamp to 0
            ingredientsDF.loc[match, 'Quantity Owned'] = ingredientsDF.loc[match, 'Quantity Owned'].clip(lower=0)
            # update Need to Get
            needed = ingredientsDF.loc[match, 'Quantity Needed']
            owned = ingredientsDF.loc[match, 'Quantity Owned']
            ingredientsDF.loc[match, 'Need to Get'] = (needed - owned).clip(lower=0)

            # update Treeview
            for row_id in ingredients_tree.get_children():
                if ingredients_tree.set(row_id, 'Ingredient') == name:
                    ingredients_tree.set(row_id, 'Quantity Owned', ingredientsDF.loc[match, 'Quantity Owned'].values[0])
                    ingredients_tree.set(row_id, 'Need to Get', ingredientsDF.loc[match, 'Need to Get'].values[0])
    save_owned()


def update_ingredients_from_recipe(index, adding=True):
    """Adjust Ingredients tab based on a recipe being checked or unchecked."""
    ingredients_str = recipeDF.loc[index, 'Ingredients']
    items = literal_eval(ingredients_str)
    for item in items:
        txt = item.strip()
        name, qty = txt.split(' (')
        qty = int(qty[:-1])
        if not adding:
            qty = -qty  # add back if unchecking

        match = ingredientsDF['Ingredient'] == name
        if match.any():
            # Subtract from Quantity Needed instead of modifying Quantity Owned
            ingredientsDF.loc[match, 'Quantity Needed'] -= qty
            # Don't go below 0
            ingredientsDF.loc[match, 'Quantity Needed'] = ingredientsDF.loc[match, 'Quantity Needed'].clip(lower=0)
            # Update Need to Get
            owned = ingredientsDF.loc[match, 'Quantity Owned']
            ingredientsDF.loc[match, 'Need to Get'] = (ingredientsDF.loc[match, 'Quantity Needed'] - owned).clip(lower=0)

            # Update Treeview
            for row_id in ingredients_tree.get_children():
                if ingredients_tree.set(row_id, 'Ingredient') == name:
                    ingredients_tree.set(row_id, 'Quantity Needed', ingredientsDF.loc[match, 'Quantity Needed'].values[0])
                    ingredients_tree.set(row_id, 'Need to Get', ingredientsDF.loc[match, 'Need to Get'].values[0])

    # Save owned quantities (if you still track them separately)
    save_owned()

def sort_treeview(tree, col, reverse=False):
    """Sort Treeview rows by a column without changing DataFrame indices."""
    # Get list of items and their values for this column
    data = [(tree.set(k, col), k) for k in tree.get_children('')]
    # Sort by column value
    data.sort(key=lambda t: t[0], reverse=reverse)
    # Rearrange in sorted order
    for index, (val, k) in enumerate(data):
        tree.move(k, '', index)


def treeview_sort_column(event, tree):
    col = tree.identify_column(event.x)
    col_index = int(col.replace('#','')) - 1
    col_name = tree['columns'][col_index]
    sort_treeview(tree, col_name, reverse=False)

def on_tree_click(event, tree, tab_name):
    """
    Handles clicks on a Treeview:
    - Header click → sorts the column alphabetically
    - Row click → performs the normal click actions (check/uncheck or increment/decrement)
    """
    region = tree.identify_region(event.x, event.y)

    if region == "heading":
        # Header clicked → sort this column
        col = tree.identify_column(event.x)
        col_index = int(col.replace('#', '')) - 1
        col_name = tree['columns'][col_index]
        reverse = False

        # Optional: toggle reverse if already sorted
        current_sort = getattr(tree, "_sort_reverse", {})
        reverse = current_sort.get(col_name, False)
        sort_treeview(tree, col_name, reverse=reverse)
        current_sort[col_name] = not reverse
        tree._sort_reverse = current_sort

    elif region == "cell":
        # Row clicked → handle according to tab
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        index = int(row_id)

        if tab_name == "Recipes" and event.num == 1:
            # Check/uncheck recipe
            if index in checked:
                checked.remove(index)
                tree.set(row_id, "✔", "")
                update_ingredients_from_recipe(index, adding=False)
            else:
                checked.add(index)
                tree.set(row_id, "✔", "✔")
                update_ingredients_from_recipe(index, adding=True)
            save_checked()

        elif tab_name == "Ingredients":
            # Adjust Quantity Owned
            qty_owned = ingredientsDF.loc[index, "Quantity Owned"]
            if event.num == 1:  # Left click → increment
                ingredientsDF.loc[index, "Quantity Owned"] = qty_owned + 1
            elif event.num == 3:  # Right click → decrement, min 0
                ingredientsDF.loc[index, "Quantity Owned"] = max(qty_owned - 1, 0)

            # Update Need to Get
            needed = ingredientsDF.loc[index, "Quantity Needed"]
            owned = ingredientsDF.loc[index, "Quantity Owned"]
            ingredientsDF.loc[index, "Need to Get"] = max(needed - owned, 0)

            # Update Treeview
            tree.set(row_id, "Quantity Owned", ingredientsDF.loc[index, "Quantity Owned"])
            tree.set(row_id, "Need to Get", ingredientsDF.loc[index, "Need to Get"])
            save_owned()


# ---------- Click Handlers ----------
def on_click(event):
    current_tab = notebook.select()
    tab_text = notebook.tab(current_tab, 'text')

    # Recipes tab
    if tab_text == 'Recipes' and event.num == 1:
        row_id = recipes_tree.identify_row(event.y)
        if not row_id:
            return
        index = int(row_id)
        if index in checked:
            checked.remove(index)
            recipes_tree.set(row_id, '✔', '')
            update_ingredients_from_recipe(index, adding=False)
        else:
            checked.add(index)
            recipes_tree.set(row_id, '✔', '✔')
            update_ingredients_from_recipe(index, adding=True)
        save_checked()

    # Ingredients tab
    elif tab_text == 'Ingredients':
        row_id = ingredients_tree.identify_row(event.y)
        if not row_id:
            return
        index = int(row_id)
        qty_owned = ingredientsDF.loc[index, 'Quantity Owned']

        if event.num == 1:  # Left click → increment
            ingredientsDF.loc[index, 'Quantity Owned'] = qty_owned + 1
        elif event.num == 3:  # Right click → decrement, min 0
            ingredientsDF.loc[index, 'Quantity Owned'] = max(qty_owned - 1, 0)

        # Update Need to Get
        needed = ingredientsDF.loc[index, 'Quantity Needed']
        owned = ingredientsDF.loc[index, 'Quantity Owned']
        ingredientsDF.loc[index, 'Need to Get'] = max(needed - owned, 0)

        # Update Treeview
        ingredients_tree.set(row_id, 'Quantity Owned', ingredientsDF.loc[index, 'Quantity Owned'])
        ingredients_tree.set(row_id, 'Need to Get', ingredientsDF.loc[index, 'Need to Get'])
        save_owned()


# Bind clicks
# recipes_tree.bind('<Button-1>', on_click)
# ingredients_tree.bind('<Button-1>', on_click)  # Left click
# ingredients_tree.bind('<Button-3>', on_click)  # Right click
recipes_tree.bind("<Button-1>", lambda e: on_tree_click(e, recipes_tree, "Recipes"))
ingredients_tree.bind("<Button-1>", lambda e: on_tree_click(e, ingredients_tree, "Ingredients"))
ingredients_tree.bind("<Button-3>", lambda e: on_tree_click(e, ingredients_tree, "Ingredients"))  # right click


# ---------- Auto-size columns ----------
for tree, cols in [(recipes_tree, recipe_cols), (ingredients_tree, ingredient_cols)]:
    for c in cols:
        max_width = font.measure(c)
        for item in tree.get_children():
            max_width = max(max_width, font.measure(str(tree.set(item, c))))
        tree.column(c, width=max_width + 20)

# ---------- Start GUI ----------
root.mainloop()
