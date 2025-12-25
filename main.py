import pandas as pd
import json
import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

from ingredients import get_unchecked_ingredients

CHECKED_ROWS = "checked_rows.json"
QUANTITY_OWNED = "quantity_owned.json"

# ---------- Load Data ----------
recipeDF = pd.read_csv("data/recipes.csv")
recipeDF = recipeDF[['Name', 'Ingredients', 'Recipe Source(s)']]

ingredientsDF = get_unchecked_ingredients()
ingredientsDF['Quantity Owned'] = 0
ingredientsDF['Need to Get'] = ingredientsDF['Quantity Needed'] - ingredientsDF['Quantity Owned']

# Load saved states
if os.path.exists(CHECKED_ROWS):
    with open(CHECKED_ROWS, "r") as f:
        checked = set(json.load(f))
else:
    checked = set()

if os.path.exists(QUANTITY_OWNED):
    with open(QUANTITY_OWNED, "r") as f:
        owned_dict = json.load(f)
        for idx, qty in owned_dict.items():
            ingredientsDF.loc[int(idx), 'Quantity Owned'] = qty
        ingredientsDF['Need to Get'] = ingredientsDF['Quantity Needed'] - ingredientsDF['Quantity Owned']
else:
    owned_dict = {}

# ---------- Save functions ----------
def save_checked():
    with open(CHECKED_ROWS, "w") as f:
        json.dump(sorted(checked), f)

def save_owned():
    for idx in ingredientsDF.index:
        owned_dict[str(idx)] = int(ingredientsDF.loc[idx, 'Quantity Owned'])
    with open(QUANTITY_OWNED, "w") as f:
        json.dump(owned_dict, f)

# ---------- GUI ----------
root = tk.Tk()
root.title("Stardew Tracker")
root.geometry("1000x500")
font = tkfont.Font()
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

# ---------- Recipes Tab ----------
recipes_tab = ttk.Frame(notebook)
notebook.add(recipes_tab, text="Recipes")

recipe_cols = ["✔"] + list(recipeDF.columns)
recipes_tree = ttk.Treeview(recipes_tab, columns=recipe_cols, show="headings")
for c in recipe_cols:
    recipes_tree.heading(c, text=c)
    recipes_tree.column(c, anchor="w")
recipes_tree.column("✔", width=40, anchor="center")

for i, row in recipeDF.iterrows():
    mark = "✔" if i in checked else ""
    recipes_tree.insert(
        "", "end", iid=str(i),
        values=[mark, row["Name"], row["Ingredients"], row["Recipe Source(s)"]]
    )

recipes_tree.pack(fill="both", expand=True)

# ---------- Ingredients Tab ----------
ingredients_tab = ttk.Frame(notebook)
notebook.add(ingredients_tab, text="Ingredients")

ingredient_cols = list(ingredientsDF.columns)
ingredients_tree = ttk.Treeview(ingredients_tab, columns=ingredient_cols, show="headings")
for c in ingredient_cols:
    ingredients_tree.heading(c, text=c)
    ingredients_tree.column(c, anchor="w")

for i, row in ingredientsDF.iterrows():
    ingredients_tree.insert(
        "", "end", iid=str(i),
        values=[row['Ingredient'], row['Quantity Needed'], row['Quantity Owned'], row['Need to Get']]
    )

ingredients_tree.pack(fill="both", expand=True)

# ---------- Click Handlers ----------
def on_click(event):
    current_tab = notebook.select()
    tab_text = notebook.tab(current_tab, "text")

    # Recipes tab
    if tab_text == "Recipes" and event.num == 1:
        row_id = recipes_tree.identify_row(event.y)
        if not row_id:
            return
        index = int(row_id)
        if index in checked:
            checked.remove(index)
            recipes_tree.set(row_id, "✔", "")
        else:
            checked.add(index)
            recipes_tree.set(row_id, "✔", "✔")
        save_checked()

    # Ingredients tab
    elif tab_text == "Ingredients":
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
recipes_tree.bind("<Button-1>", on_click)
ingredients_tree.bind("<Button-1>", on_click)  # Left click
ingredients_tree.bind("<Button-3>", on_click)  # Right click

# ---------- Auto-size columns ----------
for tree, cols in [(recipes_tree, recipe_cols), (ingredients_tree, ingredient_cols)]:
    for c in cols:
        max_width = font.measure(c)
        for item in tree.get_children():
            max_width = max(max_width, font.measure(str(tree.set(item, c))))
        tree.column(c, width=max_width + 20)

# ---------- Start GUI ----------
root.mainloop()
