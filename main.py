import pandas as pd
import json
import os
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from ast import literal_eval
from ingredients import get_unchecked_ingredients

FONTSIZE = 16

# init recipes.csv
from generate_data.cooking_recipes import get_recipes
get_recipes()

# ---------- Helpers ----------
def parse_ingredients(df):
    recipes = []
    for i in range(len(df)):
        ingredients = literal_eval(df.iloc[i]['Ingredients'])
        names = [item.strip().split(' (')[0] for item in ingredients]
        recipes.append(', '.join(names))

    df['Recipe'] = recipes
    df.drop(columns=['Ingredients'], inplace=True)


# ---------- Load Data ----------
recipeDF = pd.read_csv('data/recipes.csv')
recipeDF = recipeDF[['Name', 'Ingredients', 'Recipe Source(s)']]
parse_ingredients(recipeDF)

ingredientsDF = get_unchecked_ingredients()
ingredientsDF.rename(columns={'Quantity Needed': 'Required'}, inplace=True)
ingredientsDF['Owned'] = 0
ingredientsDF['Need'] = (ingredientsDF['Required'] - ingredientsDF['Owned']).clip(lower=0).astype(int)

# ---------- Load State ----------
checked = set()
if os.path.exists('checked_rows.json'):
    with open('checked_rows.json', 'r') as f:
        try:
            checked = set(json.load(f))
        except json.JSONDecodeError:
            pass

owned_dict = {}
if os.path.exists('quantity_owned.json'):
    with open('quantity_owned.json', 'r') as f:
        try:
            owned_dict = json.load(f)
            for idx, qty in owned_dict.items():
                if int(idx) in ingredientsDF.index:
                    ingredientsDF.loc[int(idx), 'Owned'] = int(qty)
            ingredientsDF['Need'] = (ingredientsDF['Required'] - ingredientsDF['Owned']).clip(lower=0)
        except json.JSONDecodeError:
            pass


# ---------- Save ----------
def save_checked():
    with open('checked_rows.json', 'w') as f:
        json.dump(sorted(checked), f)


def save_owned():
    for idx in ingredientsDF.index:
        owned_dict[str(idx)] = int(ingredientsDF.loc[idx, 'Owned'])
    with open('quantity_owned.json', 'w') as f:
        json.dump(owned_dict, f)


# ---------- GUI ----------
root = tk.Tk()
root.title('Stardew Tracker')
root.geometry('1100x600')

font = tkfont.Font(size=FONTSIZE)
style = ttk.Style()
style.configure("Custom.Treeview.Heading", font=font)
style.configure(
    "Custom.Treeview",
    font=font,
    rowheight=font.metrics("linespace") + 6
)

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# ---------- Recipes Tab ----------
recipes_tab = ttk.Frame(notebook)
notebook.add(recipes_tab, text='Recipes')

# recipe_cols = ['\u2713'] + list(recipeDF.columns)
recipe_cols = ['\u2713', 'Name', 'Recipe', 'Recipe Source(s)']

recipes_tree = ttk.Treeview(
    recipes_tab,
    columns=recipe_cols,
    show='headings',
    style='Custom.Treeview'
)
recipes_tree.column('Name', width=1, anchor='w')
# recipes_tree.column('Name', width=80, anchor='w')


for c in recipe_cols:
    recipes_tree.heading(c, text=c)
    recipes_tree.column(c, anchor='w')

recipes_tree.column('\u2713', width=40, anchor='center')

for i, row in recipeDF.iterrows():
    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
    mark = '\u2713' if i in checked else ''
    recipes_tree.insert(
        '',
        'end',
        iid=str(i),
        tags=(tag,),
        values=[mark, row['Name'], row['Recipe'], row['Recipe Source(s)']]
    )

recipes_tree.pack(fill='both', expand=True)

# ---------- Ingredients Tab ----------
ingredients_tab = ttk.Frame(notebook)
notebook.add(ingredients_tab, text='Ingredients')

ingredient_cols = ['Ingredient', 'Required', 'Owned', 'Need']
ingredients_tree = ttk.Treeview(
    ingredients_tab,
    columns=ingredient_cols,
    show='headings',
    style='Custom.Treeview'
)

for c in ingredient_cols:
    ingredients_tree.heading(c, text=c)
    ingredients_tree.column(c, anchor='w')

for i, row in ingredientsDF.iterrows():
    tag = 'evenrow' if i % 2 == 0 else 'oddrow'
    ingredients_tree.insert(
        '',
        'end',
        iid=str(i),
        tags=(tag,),
        values=[row['Ingredient'], row['Required'], row['Owned'], row['Need']]
    )

ingredients_tree.pack(fill='both', expand=True)

# ---------- Row banding ----------
for tree in (recipes_tree, ingredients_tree):
    tree.tag_configure('evenrow', background='#f0f0ff')
    tree.tag_configure('oddrow', background='#ffffff')


# ---------- Logic ----------
def update_ingredients_from_recipe(index, adding=True):
    ingredients_str = pd.read_csv('data/recipes.csv').loc[index, 'Ingredients']
    items = literal_eval(ingredients_str)

    for item in items:
        name, qty = item.strip().split(' (')
        qty = int(qty[:-1])
        if not adding:
            qty = -qty

        match = ingredientsDF['Ingredient'] == name
        if match.any():
            ingredientsDF.loc[match, 'Required'] -= qty
            ingredientsDF.loc[match, 'Required'] = ingredientsDF.loc[match, 'Required'].clip(lower=0)

            owned = ingredientsDF.loc[match, 'Owned']
            ingredientsDF.loc[match, 'Need'] = (ingredientsDF.loc[match, 'Required'] - owned).clip(lower=0)

            for row_id in ingredients_tree.get_children():
                if ingredients_tree.set(row_id, 'Ingredient') == name:
                    ingredients_tree.set(row_id, 'Required', int(ingredientsDF.loc[match, 'Required'].values[0]))
                    ingredients_tree.set(row_id, 'Need', int(ingredientsDF.loc[match, 'Need'].values[0]))

    save_owned()


def wrap_text(text, width=30):
    import textwrap
    return '\n'.join(textwrap.wrap(text, width))


def sort_treeview(tree, col, reverse=False):
    data = [(tree.set(k, col), k) for k in tree.get_children('')]
    data.sort(key=lambda t: t[0], reverse=reverse)

    for i, (_, k) in enumerate(data):
        tree.move(k, '', i)
        tree.item(k, tags=('evenrow' if i % 2 == 0 else 'oddrow',))


def on_tree_click(event, tree, tab_name):
    region = tree.identify_region(event.x, event.y)

    if region == 'heading':
        col = tree.identify_column(event.x)
        col_index = int(col.replace('#', '')) - 1
        col_name = tree['columns'][col_index]

        reverse = getattr(tree, '_reverse', {}).get(col_name, False)
        sort_treeview(tree, col_name, reverse)

        tree._reverse = getattr(tree, '_reverse', {})
        tree._reverse[col_name] = not reverse
        return

    if region != 'cell':
        return

    row_id = tree.identify_row(event.y)
    if not row_id:
        return

    index = int(row_id)

    if tab_name == 'Recipes':
        if index in checked:
            checked.remove(index)
            tree.set(row_id, '\u2713', '')
            update_ingredients_from_recipe(index, adding=False)
        else:
            checked.add(index)
            tree.set(row_id, '\u2713', '\u2713')
            update_ingredients_from_recipe(index, adding=True)
        save_checked()

    else:
        owned = ingredientsDF.loc[index, 'Owned']
        if event.num == 1:
            ingredientsDF.loc[index, 'Owned'] = owned + 1
        elif event.num == 3:
            ingredientsDF.loc[index, 'Owned'] = max(owned - 1, 0)

        req = ingredientsDF.loc[index, 'Required']
        ingredientsDF.loc[index, 'Need'] = max(req - ingredientsDF.loc[index, 'Owned'], 0)

        tree.set(row_id, 'Owned', ingredientsDF.loc[index, 'Owned'])
        tree.set(row_id, 'Need', ingredientsDF.loc[index, 'Need'])
        save_owned()


# ---------- Bind ----------
recipes_tree.bind('<Button-1>', lambda e: on_tree_click(e, recipes_tree, 'Recipes'))
ingredients_tree.bind('<Button-1>', lambda e: on_tree_click(e, ingredients_tree, 'Ingredients'))
ingredients_tree.bind('<Button-3>', lambda e: on_tree_click(e, ingredients_tree, 'Ingredients'))

root.mainloop()





# # TODO
# #   change ingredient column (list items, not quantity)
#
# import pandas as pd
# import json
# import os
# import tkinter as tk
# from tkinter import ttk
# import tkinter.font as tkfont
# from ast import literal_eval
# from ingredients import get_unchecked_ingredients, parse_ingredients
#
# FONTSIZE = 16
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
#
# # ---------- Load Data ----------
# recipeDF = pd.read_csv('data/recipes.csv')
# recipeDF = recipeDF[['Name', 'Ingredients', 'Recipe Source(s)']]
#
#
#
# ingredientsDF = get_unchecked_ingredients()
# parse_ingredients(recipeDF)
# ingredientsDF['Owned'] = 0
# ingredientsDF['Need'] = ingredientsDF['Required'] - ingredientsDF['Owned']
# print(recipeDF)
# # Safe loading
# checked = set()
# if os.path.exists('checked_rows.json'):
#     with open('checked_rows.json', 'r') as f:
#         try:
#             loaded = json.load(f)
#             if isinstance(loaded, list):
#         except json.JSONDecodeError:
#             checked = set()
#
# owned_dict = {}
# if os.path.exists('quantity_owned.json'):
#     with open('quantity_owned.json', 'r') as f:
#         try:
#             loaded = json.load(f)
#             if isinstance(loaded, dict):
#                 owned_dict = loaded
#                 for idx, qty in owned_dict.items():
#                     if int(idx) in ingredientsDF.index:
#                         ingredientsDF.loc[int(idx), 'Owned'] = qty
#             ingredientsDF['Need'] = (ingredientsDF['Required'] - ingredientsDF['Owned']).clip(
#                 lower=0).astype(int)
#         except json.JSONDecodeError:
#             owned_dict = {}
#
#
# # ---------- Save functions ----------
# def save_checked():
#     with open('checked_rows.json', 'w') as f:
#         json.dump(sorted(checked), f)
#
#
# def save_owned():
#     for idx in ingredientsDF.index:
#         owned_dict[str(idx)] = int(ingredientsDF.loc[idx, 'Owned'])
#     with open('quantity_owned.json', 'w') as f:
#         json.dump(owned_dict, f)
#
#
# # ---------- GUI ----------
# root = tk.Tk()
# root.title('Stardew Tracker')
# root.geometry('1000x500')
#
# font = tkfont.Font(size=FONTSIZE)
# style = ttk.Style()
# style.configure("Custom.Treeview.Heading", font=font)
# style.configure("Custom.Treeview", font=font, rowheight=font.metrics("linespace") + 4)  # 4px padding
#
# notebook = ttk.Notebook(root)
# notebook.pack(fill='both', expand=True)
#
# # ---------- Recipes Tab ----------
# recipes_tab = ttk.Frame(notebook)
# notebook.add(recipes_tab, text='Recipes')
#
# recipe_cols = ['\u2713'] + list(recipeDF.columns)
# recipes_tree = ttk.Treeview(recipes_tab, columns=recipe_cols, show='headings', style='Custom.Treeview')
# for c in recipe_cols:
#     recipes_tree.heading(c, text=c)
#     recipes_tree.column(c, anchor='w')
# recipes_tree.column('\u2713', width=40, anchor='center')
#
# for i, row in recipeDF.iterrows():
#     tag = 'evenrow' if i % 2 == 0 else 'oddrow'
#     mark = '\u2713' if i in checked else ''
#     recipes_tree.insert(
#         '', 'end', iid=str(i), tags=(tag,),
#         values=[mark, row['Name'], row['Ingredients'], row['Recipe Source(s)']]
#     )
#
# recipes_tree.pack(fill='both', expand=True)
#
# # ---------- Ingredients Tab ----------
# ingredients_tab = ttk.Frame(notebook)
# notebook.add(ingredients_tab, text='Ingredients')
#
# ingredient_cols = list(ingredientsDF.columns)
# ingredients_tree = ttk.Treeview(ingredients_tab, columns=ingredient_cols, show='headings', style='Custom.Treeview')
#
# for c in ingredient_cols:
#     ingredients_tree.heading(c, text=c)
#     ingredients_tree.column(c, anchor='w')
#
# for i, row in ingredientsDF.iterrows():
#     tag = 'evenrow' if i % 2 == 0 else 'oddrow'
#     ingredients_tree.insert(
#         '', 'end', iid=str(i), tags=(tag,),
#         values=[row['Ingredient'], row['Required'], row['Owned'], row['Need']]
#     )
#
# ingredients_tree.pack(fill='both', expand=True)
#
# # ---------- Configure tag styles ----------
# recipes_tree.tag_configure('evenrow', background='#f0f0ff')  # light blue
# recipes_tree.tag_configure('oddrow', background='#ffffff')  # white
# ingredients_tree.tag_configure('evenrow', background='#f0f0ff')
# ingredients_tree.tag_configure('oddrow', background='#ffffff')
#
#
# # ---------- Link Tables ----------
# def update_ingredients_from_recipe(index, adding=True):
#     ingredients_str = recipeDF.loc[index, 'Ingredients']
#     items = literal_eval(ingredients_str)
#     for item in items:
#         txt = item.strip()
#         name, qty = txt.split(' (')
#         qty = int(qty[:-1])
#         if not adding:
#             qty = -qty  # add back if unchecking
#
#         match = ingredientsDF['Ingredient'] == name
#         if match.any():
#             # Subtract from Quantity Needed instead of modifying Quantity Owned
#             ingredientsDF.loc[match, 'Required'] -= qty
#             # Don't go below 0
#             ingredientsDF.loc[match, 'Required'] = ingredientsDF.loc[match, 'Required'].clip(lower=0)
#             # Update Need to Get
#             owned = ingredientsDF.loc[match, 'Owned']
#             ingredientsDF.loc[match, 'Need'] = (ingredientsDF.loc[match, 'Required'] - owned).clip(
#                 lower=0)
#
#             # Update Treeview
#             for row_id in ingredients_tree.get_children():
#                 if ingredients_tree.set(row_id, 'Ingredient') == name:
#                     ingredients_tree.set(row_id, 'Required',
#                                          int(ingredientsDF.loc[match, 'Required'].values[0]))
#                     ingredients_tree.set(row_id, 'Need', int(ingredientsDF.loc[match, 'Need'].values[0]))
#
#     # Save owned quantities (if you still track them separately)
#     save_owned()
#
#
# def sort_treeview(tree, col, reverse=False):
#     # Get list of items and their values for this column
#     data = [(tree.set(k, col), k) for k in tree.get_children('')]
#     # Sort by column value
#     data.sort(key=lambda t: t[0], reverse=reverse)
#     # Rearrange in sorted order
#     for index, (val, k) in enumerate(data):
#         tree.move(k, '', index)
#         # Reapply banded row tags
#         tag = 'evenrow' if index % 2 == 0 else 'oddrow'
#         tree.item(k, tags=(tag,))
#
#
# def treeview_sort_column(event, tree):
#     col = tree.identify_column(event.x)
#     col_index = int(col.replace('#', '')) - 1
#     col_name = tree['columns'][col_index]
#     sort_treeview(tree, col_name, reverse=False)
#
#
# def on_tree_click(event, tree, tab_name):
#     """
#     Handles clicks on a Treeview:
#     - Header click → sorts the column alphabetically
#     - Row click → performs the normal click actions (check/uncheck or increment/decrement)
#     """
#     region = tree.identify_region(event.x, event.y)
#
#     if region == "heading":
#         # Header clicked → sort this column
#         col = tree.identify_column(event.x)
#         col_index = int(col.replace('#', '')) - 1
#         col_name = tree['columns'][col_index]
#         reverse = False
#
#         # Optional: toggle reverse if already sorted
#         current_sort = getattr(tree, "_sort_reverse", {})
#         reverse = current_sort.get(col_name, False)
#         sort_treeview(tree, col_name, reverse=reverse)
#         current_sort[col_name] = not reverse
#         tree._sort_reverse = current_sort
#
#     elif region == "cell":
#         # Row clicked → handle according to tab
#         row_id = tree.identify_row(event.y)
#         if not row_id:
#             return
#         index = int(row_id)
#
#         if tab_name == "Recipes" and event.num == 1:
#             # Check/uncheck recipe
#             if index in checked:
#                 checked.remove(index)
#                 tree.set(row_id, "\u2713", "")
#                 update_ingredients_from_recipe(index, adding=False)
#             else:
#                 checked.add(index)
#                 tree.set(row_id, "\u2713", "\u2713")
#                 update_ingredients_from_recipe(index, adding=True)
#             save_checked()
#
#         elif tab_name == "Ingredients":
#             # Adjust Quantity Owned
#             qty_owned = ingredientsDF.loc[index, "Quantity Owned"]
#             if event.num == 1:  # Left click → increment
#                 ingredientsDF.loc[index, "Quantity Owned"] = qty_owned + 1
#             elif event.num == 3:  # Right click → decrement, min 0
#                 ingredientsDF.loc[index, "Quantity Owned"] = max(qty_owned - 1, 0)
#
#             # Update Need to Get
#             needed = ingredientsDF.loc[index, "Quantity Needed"]
#             owned = ingredientsDF.loc[index, "Quantity Owned"]
#             ingredientsDF.loc[index, "Need to Get"] = max(needed - owned, 0)
#
#             # Update Treeview
#             tree.set(row_id, "Quantity Owned", ingredientsDF.loc[index, "Quantity Owned"])
#             tree.set(row_id, "Need to Get", ingredientsDF.loc[index, "Need to Get"])
#             save_owned()
#
#
# # ---------- Click Handlers ----------
# def on_click(event):
#     current_tab = notebook.select()
#     tab_text = notebook.tab(current_tab, 'text')
#
#     # Recipes tab
#     if tab_text == 'Recipes' and event.num == 1:
#         row_id = recipes_tree.identify_row(event.y)
#         if not row_id:
#             return
#         index = int(row_id)
#         if index in checked:
#             checked.remove(index)
#             recipes_tree.set(row_id, '\u2713', '')
#             update_ingredients_from_recipe(index, adding=False)
#         else:
#             checked.add(index)
#             recipes_tree.set(row_id, '\u2713', '\u2713')
#             update_ingredients_from_recipe(index, adding=True)
#         save_checked()
#
#     # Ingredients tab
#     elif tab_text == 'Ingredients':
#         row_id = ingredients_tree.identify_row(event.y)
#         if not row_id:
#             return
#         index = int(row_id)
#         qty_owned = ingredientsDF.loc[index, 'Owned']
#
#         if event.num == 1:  # Left click → increment
#             ingredientsDF.loc[index, 'Owned'] = qty_owned + 1
#         elif event.num == 3:  # Right click → decrement, min 0
#             ingredientsDF.loc[index, 'Owned'] = max(qty_owned - 1, 0)
#
#         # Update Need to Get
#         needed = ingredientsDF.loc[index, 'Required']
#         owned = ingredientsDF.loc[index, 'Owned']
#         ingredientsDF.loc[index, 'Need'] = max(needed - owned, 0)
#
#         # Update Treeview
#         ingredients_tree.set(row_id, 'Owned', ingredientsDF.loc[index, 'Owned'])
#         ingredients_tree.set(row_id, 'Need', ingredientsDF.loc[index, 'Need'])
#         save_owned()
#
#
# # Bind clicks
# recipes_tree.bind("<Button-1>", lambda e: on_tree_click(e, recipes_tree, "Recipes"))
# ingredients_tree.bind("<Button-1>", lambda e: on_tree_click(e, ingredients_tree, "Ingredients"))
# ingredients_tree.bind("<Button-3>", lambda e: on_tree_click(e, ingredients_tree, "Ingredients"))
#
# root.mainloop()
