import re
from flask_sqlalchemy import SQLAlchemy
from app import Drink, Recipe, Liquid

########################################################################################################################
#
# LIQUIDS
#
########################################################################################################################

def get_liduid_by_id(id:int):
    liquid_name = Liquid.query.filter_by(id=id).first().name
    return liquid_name

def add_liquid_to_db(db, request):
    name_liquid = request.form['name']
    description_liquid = request.form['description']
    category_liquid = request.form['category']
    alcohol_volume = request.form['alc_volume']
        
    new_liquid = Liquid(name=name_liquid, 
                            alc_category=category_liquid, 
                            description=description_liquid, 
                            alc_content=alcohol_volume)
    db.session.add(new_liquid)
    db.session.commit()

# TODO PRIO2 get rid of sessions problems that hinder this function from working
def delete_liquid_from_db(db, id):
    liquid = Liquid.query.get_or_404(id)
    db.session.delete(liquid)
    db.session.commit()    

def edit_liquid_in_db(liquid, request, db):
    liquid.name = request.form['name']
    liquid.description = request.form['description']
    liquid.alc_category = request.form['category']
    liquid.alc_content = request.form['alc_volume']
    db.session.commit()    

def get_all_liquids_db():
    liquids = Liquid.query.all()
    return liquids

########################################################################################################################
#
# DRINKS OPERATIONS
#
########################################################################################################################

# returns all the data needed to display drinks on the front end
def get_data_for_drinks():
    all_drinks = Drink.query.order_by(Drink.title).all()
    all_recipes = Recipe.query.all()
    all_liquids = Liquid.query.all()

    return all_drinks, all_recipes, all_liquids

# is used when adding a new drink - will return True if is duplicate
def check_drink_duplicates(drink_title):
    duplicates = Drink.query.filter_by(title=drink_title).all()
    if len(duplicates) > 0:
        return True
    else:
        return False

# is used to add a new drink-row to the Drink-Table    
def add_drink_to_db(db:SQLAlchemy, drink_title, drink_description):
    new_drink = Drink(title=drink_title, description=drink_description)
    db.session.add(new_drink)
    db.session.commit()
    return new_drink.id

# returns the drinks that can be made with the current configuration
def get_drinks_doable(beverages, all_recipes, all_liquids):
    doable_drinks = []
    liquid_ids = []
    for key in beverages:
        if beverages[key] != "":
            # these are all the liquids the automat can serve with the actual conf
            liquid_ids.append(Liquid.query.filter_by(name=beverages[key]).first().id)
    
    for id in liquid_ids:
        try:
            # all potential drinks containin that liquid
            drink_id = Recipe.query.filter_by(id_liquid=id).all()
            # check if the drink has all needed ingredients
            if drink_id is not None:
                for recipe in drink_id:
                    drink_id_from_recipe = recipe.id_drink
                    drink_recipe = Recipe.query.filter_by(id_drink=drink_id_from_recipe).all()
                    all_drinks_liquids = [i.id_liquid for i in drink_recipe]
                    if set(all_drinks_liquids).issubset(set(liquid_ids)):
                        stuff = Drink.query.filter_by(id=recipe.id_drink).first()
                        if stuff is not None and stuff not in doable_drinks:
                            doable_drinks.append(stuff)
        except Exception as e:
            print(e)
            print('there were no doable drinks')
    return doable_drinks

# adds new recipe-rows to the recipe table. As many as there are ingredients in a drink.
def add_recipe_to_db(db, keys, request, drink_id):
    for i in range(0, len(keys), 2):
        key = keys[i]
        if key not in ['title','description'] and request.form[keys[i + 1]] != "":
        # this is terrible, i should check with regex which case it is, which in turn allows me to
        # get rid of the stupid if in condition
            try:
                liquid_id = Liquid.query.filter_by(name=request.form[key]).first().id
            except:
                pass
            try:
                liquid_amount = request.form[keys[i + 1]]
            except:
                pass
            new_recipe = Recipe(id_drink= drink_id, id_liquid= liquid_id, ml_liquid=liquid_amount)
            db.session.add(new_recipe)
            db.session.commit()
    success_code = "Drink added successfully. Let's drink!"
    return success_code

# doesn't work from here due to session problems. Is located in app.py, but should come over here once we have time to
# fix this
def delete_drink_from_db(db, id):
    recipe = Recipe.query.filter_by(id_drink=id).all()    
    drink = Drink.query.get_or_404(id)
    for rec in recipe:
        db.session.delete(rec)
    db.session.delete(drink)
    db.session.commit()

# edits the drink row of a certain drink in the drink-table
def edit_drink_from_db(db, request, drink):
    drink.title = request.form['title']
    drink.description = request.form['description']
    db.session.commit()    

########################################################################################################################
#
# RECIPES OPERATIONS
#
########################################################################################################################

def get_recipe_for_drink(id:int):
    recipe = Recipe.query.filter_by(id_drink=id).all()
    return recipe

########################################################################################################################
#
# TUBE CONFIGURATIONS
#
########################################################################################################################

# is used whenever we make changes to the tube configuration. Loads the previous one, overwrite with the new one, keeping
# untouched old configurations 
def set_current_tube_conf(request, beverages):
    selection = request.form
    keys = list(selection.keys())
    print(beverages)
    for i in range(0,len(keys)):
        if re.match('^pump', keys[i]):
            beverages[keys[i]] = selection[keys[i]]
        if re.match('^valve', keys[i]):
            beverages[keys[i]] = selection[keys[i]]
    return beverages





