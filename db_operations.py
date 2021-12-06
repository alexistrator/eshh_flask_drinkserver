import re

from flask_sqlalchemy import SQLAlchemy
from app import Drink, Recipe, Liquid

def set_current_tube_conf(request, beverages):
    selection = request.form
    keys = list(selection.keys())
    print(keys)
    for i in range(0,len(keys)):
        if re.match('^pump', keys[i]):
            beverages[keys[i]] = selection[keys[i]]
            if re.match('^valve', keys[i]):
                beverages[keys[i]] = selection[keys[i]]
                # when all is done, change READY to True, or keep it false, if the input is not correct
    return beverages

def get_data_for_drinks():
    all_drinks = Drink.query.order_by(Drink.title).all()
    all_recipes = Recipe.query.all()
    all_liquids = Liquid.query.all()

    return all_drinks, all_recipes, all_liquids

def check_drink_duplicates(drink_title):
    return Drink.query.filter_by(title=drink_title).all()

def add_drink_to_db(db:SQLAlchemy, drink_title, drink_description):
    new_drink = Drink(title=drink_title, description=drink_description)
    db.session.add(new_drink)
    db.session.commit()
    return new_drink.id

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
    success_code = "added the fucking drink, let's get wasted now!!"
    return success_code

# der boi funktioniert wegen session probleme nicht
def delete_drink_from_db(db, id):
    recipe = Recipe.query.filter_by(id_drink=id).all()    
    drink = Drink.query.get_or_404(id)
    for rec in recipe:
        db.session.delete(rec)
    db.session.delete(drink)
    db.session.commit()

def edit_drink_from_db(db, request, drink):
    drink.title = request.form['title']
    drink.description = request.form['description']
    db.session.commit()    

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

# TODO: get rid of sessions problems that hinder this function from working
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