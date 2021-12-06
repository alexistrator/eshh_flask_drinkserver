from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import re

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
    global READY
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
            return render_template('/admin/conf_robot.html', options=options())
        else:
            selection = request.form
            keys = list(selection.keys())
            print(keys)
            
            for i in range(0,len(keys)):
                
                if re.match('^pump', keys[i]):
                    beverages[keys[i]] = selection[keys[i]]
                if re.match('^valve', keys[i]):
                    beverages[keys[i]] = selection[keys[i]]
                # when all is done, change READY to True, or keep it false, if the input is not correct

            # TODO: 
            # also read the base value of the distance sensor!!


            READY = True
            print(beverages)
            print(READY)
            # redirect to /
            return redirect('/')

@app.route('/admin/robot_configuration', methods=['GET', 'POST'])
def robot_conf():
    global READY

    if request.method == 'GET':
        READY = False
        print(beverages)
        return render_template('/admin/conf_robot_edit.html', options=options(), beverages=beverages)
    
    else:
        return redirect('/')


# --- DRINKS ---

@app.route('/drinks')
def drinks():

    # get all the data we need to resolve the drinks
    all_drinks = Drink.query.order_by(Drink.title).all()
    all_recipes = Recipe.query.all()
    all_liquids = Liquid.query.all()
    
    return render_template('drinks.html', drinks=all_drinks, recipes=all_recipes)

@app.route('/admin/add_drink', methods=['GET', 'POST'])
def add_drink():


# get all the data we need to resolve the drinks
    all_drinks, all_recipes, all_liquids = load_drinks_data()

    if request.method == 'POST':
        

        drink_title = request.form['title']
        drink_description = request.form['description']

        same_drinks = Drink.query.filter_by(title=drink_title).all()
        
        if len(same_drinks) == 0:
            # Create new drink row:
            new_drink = Drink(title=drink_title, description=drink_description)
            db.session.add(new_drink)
            db.session.commit()

            drink_id = new_drink.id
            keys = list(request.form.keys())
        
            for i in range(0, len(keys), 2):
                key = keys[i]
                print(key)
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
            all_drinks, all_recipes, all_liquids = load_drinks_data() 
            success_code = "added the fucking drink, let's get wasted now!!"
            return render_template('/admin/add_drink.html', status_code=success_code, options=options(),
                    drinks=all_drinks, recipes=all_recipes)
        else:
            print("did nothing, drink already exists")
            error_code = "drink already exists, get rekt noob"
            return render_template('/admin/add_drink.html',
                    status_code=error_code, options=options(),
                    drinks=all_drinks, recipes=all_recipes)
    
    else:
        all_drinks, all_recipes, all_liquids = load_drinks_data()
        return render_template('/admin/add_drink.html', options=options(),
                    drinks=all_drinks, recipes=all_recipes)

@app.route('/admin/drinks/delete/<int:id>')
def delete(id):
    recipe = Recipe.query.filter_by(id_drink=id).all()    
    drink = Drink.query.get_or_404(id)
    for rec in recipe:
        db.session.delete(rec)
    db.session.delete(drink)
    db.session.commit()
    return redirect('/admin/add_drink')

@app.route('/admin/drinks/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    drink = Drink.query.get_or_404(id)
    recipe = Recipe.query.filter_by(id_drink=drink.id).all()
    all_liquids = Liquid.query.all()
    if request.method == 'POST':
        drink.title = request.form['title']
        drink.description = request.form['description']
        db.session.commit()
        return redirect('/admin/add_drink')
    else:
        return render_template('/admin/edit_drink.html', drink=drink, recipe=recipe, all_liquids=all_liquids, options=options())


# --- LIQUIDS ---

@app.route('/admin/add_liquid', methods=['GET', 'POST'])
def add_liquid():
    if request.method == 'POST':
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
    return redirect('/admin/add_liquid')

@app.route('/admin/liquid/edit/<int:id>', methods=['GET', 'POST'])
def edit_liquid(id):
    liquid = Liquid.query.get_or_404(id)
    #recipe = Recipe.query.filter_by(id_drink=drink.id).all()
    #all_liquids = Liquid.query.all()

    if request.method == 'POST':
        liquid.name = request.form['name']
        liquid.description = request.form['description']
        liquid.alc_category = request.form['category']
        liquid.alc_content = request.form['alc_volume']
        db.session.commit()
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
# FUNCTIONS BACKEND 
#
########################################################################################################################


# handle the pouring process:


# handle the site logic
def print_hello():
    print("hello")

# tare and handle the scale

# handle the distance sensor

# load all the data needed to display available drinks:
def load_drinks_data():
  # get all the data we need to resolve the drinks
    all_drinks = Drink.query.order_by(Drink.title).all()
    all_recipes = Recipe.query.all()
    all_liquids = Liquid.query.all()

    return all_drinks, all_recipes, all_liquids 

########################################################################################################################
#
# FUNCTIONS JINJA
#
########################################################################################################################

def get_recipes_for_drink(id_drink_req:int, all_recipes):
    all_recipes = Recipe.query.filter_by(id_drink=id_drink_req).all()
    return all_recipes

def get_liquid_by_id(id_liquid_req:int, all_liquids):
    liquid = Liquid.query.filter_by(id=id_liquid_req).first().name
    return liquid

# TODO write a function to get the available drinks with the given bottle configuration

def set_robot_configuration(conf_array):
    return

def options():
    liquids = Liquid.query.all()
    return liquids

# make the functions available for jinja, so they can be called from the html-file.
app.jinja_env.globals.update(get_recipes_for_drink=get_recipes_for_drink)
app.jinja_env.globals.update(get_liquid_by_id=get_liquid_by_id)

if __name__== '__main__':
    app.run(debug=True, port=5000 
            # ,host='192.168.1.141'
            ,host='127.0.0.1')
    
