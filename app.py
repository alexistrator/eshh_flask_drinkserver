from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import re
import db_operations
import pouring_operations

# UNCOMMENT IF RUNNING FROM RASPI:
#from RPi import GPIO

########################################################################################################################
#
# STATUS VARIABLES
#
########################################################################################################################

READY = False
ERROR = False
BASE_VALUE = 0

########################################################################################################################
#
# ROBOT CONFIGURATION
#
########################################################################################################################

beverages = {
        "pump_1":"",
        "pump_2":"",
        "pump_3":"",
        "pump_4":"",
        "pump_5":"",
        "valve":""
        }

########################################################################################################################
#
# GPIO CONFIGURATION
#
########################################################################################################################

# Pins for the pumps:

pump1 = 0
pump2 = 0
pump3 = 0

# Pins for the scale:

scale_out = 0 
scale_in1 = 0
scale_in2 = 0

# Pins for the distance sensor:

distance1 = 0
distance2 = 0
distance3 = 0

# Pins for the LED Stripes

rgb1 = 0
rgb2 = 0
rgb3 = 0

app = Flask(__name__)

########################################################################################################################
#
# DATABASE
#
########################################################################################################################

# Tell flask where the database can be found / what database we want to use:
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///drinks.db'
db = SQLAlchemy(app)

# Model the database:
class Drink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self): # displays something to the screen after creating a blogpost
        return 'Drink ' + str(self.id)

class Liquid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    alc_category = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    alc_content = db.Column(db.Float, nullable=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_drink = db.Column(db.Integer, nullable=False)
    id_liquid = db.Column(db.Integer, nullable=False)
    ml_liquid = db.Column(db.Integer, nullable=False)    
    # 4) This would be fun: Amount of times that it was made. Each execution would be +1.

########################################################################################################################
#
# ROUTING, ADDING/DELETING/UPDATING
#
########################################################################################################################

# --- ROBOT CONFIGURATION --
@app.route('/', methods=['GET', 'POST'])
def index():
    global READY, beverages
    try:
        print(READY)
    except:
        print("initializing variable READY")
        READY = False
        pass

    if READY and request.method == 'GET':
        return redirect('/drinks')
    else:
        if request.method == 'GET':
            return render_template('/admin/conf_robot.html', options=db_operations.get_all_liquids_db())
        else:
            beverages = db_operations.set_current_tube_conf(request, beverages)
            READY = True
            return redirect('/')

@app.route('/admin/robot_configuration', methods=['GET', 'POST'])
def robot_conf():
    global READY
    if request.method == 'GET':
        print(beverages)
        return render_template('/admin/conf_robot_edit.html', options=db_operations.get_all_liquids_db(), beverages=beverages)
    else:
        READY = False
        return redirect('/')

# --- DRINKS ---
@app.route('/drinks')
def drinks():
    all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
    doable_drinks = db_operations.get_drinks_doable(beverages, all_recipes, all_liquids)
    return render_template('drinks.html'
                            ,drinks=doable_drinks 
                            ,recipes=all_recipes)

@app.route('/admin/add_drink', methods=['GET', 'POST'])
def add_drink():
    all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
    if request.method == 'POST':
        drink_title = request.form['title']
        drink_description = request.form['description']
        same_drinks = db_operations.check_drink_duplicates(drink_title)
        
        if len(same_drinks) == 0:
            drink_id = db_operations.add_drink_to_db(db, drink_title, drink_description)
            keys = list(request.form.keys())
            success_code = db_operations.add_recipe_to_db(db, keys, request, drink_id)
            all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
            return render_template('/admin/add_drink.html', status_code=success_code, options=db_operations.get_all_liquids_db(),
                    drinks=all_drinks, recipes=all_recipes)
        else:
            print("did nothing, drink already exists")
            error_code = "Drink with this title already exists. Be creative"
            # TODO: Keep the configuration I was trying to add. This is a nice to have. No Priority.
            return render_template('/admin/add_drink.html',
                    status_code=error_code, options=db_operations.get_all_liquids_db(),
                    drinks=all_drinks, recipes=all_recipes)
    else:
        all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
        return render_template('/admin/add_drink.html', options=db_operations.get_all_liquids_db(),
                    drinks=all_drinks, recipes=all_recipes)

@app.route('/admin/drinks/delete/<int:id>')
def delete(id):
    recipe = Recipe.query.filter_by(id_drink=id).all()    
    drink = Drink.query.get_or_404(id)
    for rec in recipe:
        db.session.delete(rec)
    db.session.delete(drink)
    db.session.commit()
    # TODO: Fix session problems when using this external function
    # Session Problems
    #db_operations.delete_drink_from_db(db, id)
    return redirect('/admin/add_drink')

# TODO: change recipes according to the edit done to the drink. 
# might be a little bit of work
@app.route('/admin/drinks/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    drink = Drink.query.get_or_404(id)
    recipe = Recipe.query.filter_by(id_drink=drink.id).all()
    all_liquids = Liquid.query.all()
    if request.method == 'POST':
        drink.title = request.form['title']
        drink.description = request.form['description']
        db.session.commit()
        keys = list(request.form.keys())
        # delete the current recipes available
        for rec in recipe:
            print('deleting:')
            print(rec.id_liquid)
            db.session.delete(rec)
        # commit the deletion
        db.session.commit()
        # generate new recipe for the drink
        db_operations.add_recipe_to_db(db, keys, request, drink.id)
        return redirect('/admin/add_drink')
    else:
        return render_template('/admin/edit_drink.html', drink=drink, recipe=recipe, all_liquids=all_liquids, options=db_operations.get_all_liquids_db())

# --- LIQUIDS ---
@app.route('/admin/add_liquid', methods=['GET', 'POST'])
def add_liquid():
    if request.method == 'POST':
        db_operations.add_liquid_to_db(db, request)
        all_liquids = Liquid.query.all()  
        return redirect('/admin/add_liquid')
    else:
        all_liquids = Liquid.query.all()
        return render_template('/admin/add_liquid.html', liquids=all_liquids)


@app.route('/liquids')
def show_liquids():
    all_liquids = Liquid.query.all()
    return render_template('liquids.html', liquids=all_liquids)
   

@app.route('/admin/liquid/delete/<int:id>')
def delete_liquid(id):
    liquid = Liquid.query.get_or_404(id)
    db.session.delete(liquid)
    db.session.commit()
    
    # TODO: Get rid of session problems when deleting
    #db_operations.delete_liquid_from_db(db, id)
    return redirect('/admin/add_liquid')

@app.route('/admin/liquid/edit/<int:id>', methods=['GET', 'POST'])
def edit_liquid(id):
    liquid = Liquid.query.get_or_404(id)
    if request.method == 'POST':
        db_operations.edit_liquid_in_db(liquid, request, db)
        return redirect('/admin/add_liquid')
    else:
        return render_template('/admin/edit_liquid.html', liquid=liquid)


# --- DRINK MAKING PROCESS
@app.route('/serving/initiate/select_drink/<int:id>', methods=['GET', 'POST'])
def start_pouring_process(id):
    if request.method == 'GET':
        return render_template('/serving/initiation.html', id_drink=id)

@app.route('/serving/initiate/check_glass', methods=['GET', 'POST'])
def check_glass_placement():
    INSERTED = False
    if request.method == 'GET':
        return render_template('/serving/glass_check.html')
    else:
        if request.form['continue_button'] == 'Continue':
            print('checking distance sensor')
            # get distance sensor value, and compare it to BASE_VALUE
            # if outside of normal range, confirm glass placement
            # tare the scale
            # instead of returning a template, i shoul be redirecting to the pouring process per se
            # in order to do this, i should look into how sessions work, it's starting to get messy if i have to 
            # spaghetti pass all variables 
            return render_template('/serving/pouring_process.html')


########################################################################################################################
#
# FUNCTIONS JINJA
#
########################################################################################################################

def get_recipes_for_drink(id_drink_req:int, all_recipes):
    try:
        all_recipes = Recipe.query.filter_by(id_drink=id_drink_req).all()
    except:
        all_recipes = []
    return all_recipes

def get_liquid_by_id(id_liquid_req:int, all_liquids):
    liquid = Liquid.query.filter_by(id=id_liquid_req).first().name
    return liquid

# make the functions available for jinja, so they can be called from the html-file.
app.jinja_env.globals.update(get_recipes_for_drink=get_recipes_for_drink)
app.jinja_env.globals.update(get_liquid_by_id=get_liquid_by_id)

if __name__== '__main__':
    app.run(debug=True, port=5000 
            # ,host='192.168.1.141'
            #,host='192.168.223.176'
            #,host='192.168.223.211'
            ,host='127.0.0.1'
            )


