from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import re
import db_operations
import pouring_operations
import multiprocessing as mp
import time

# UNCOMMENT IF RUNNING FROM RASPI:
import RPi.GPIO as GPIO

########################################################################################################################
#
# SET UP APP
#
########################################################################################################################

app = Flask(__name__)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'

########################################################################################################################
#
# STATUS VARIABLES
#
########################################################################################################################

READY = False
ERROR = False
BASE_VALUE = 0
INSERTED = False

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

# TODO PRIO1 measure the capacity of our pumps, save it here
# extraction capacity of pumps in ml per second
extraction_cap_ml_s = {
        "pump_1":   1,
        "pump_2":   1,
        "pump_3":   1,
        "pump_4":   5,
        "pump_5":   10,
        "valve":    20
}

# TODO PRIO1 measure the ansaug times for the different pumps
ansaug_times = {
        "pump_1":   10,
        "pump_2":   10,
        "pump_3":   10,
        "pump_4":   10,
        "pump_5":   10,
        "valve":    10
}


########################################################################################################################
#
# GPIO CONFIGURATION
#
########################################################################################################################

# GPIO-Settings:
# TODO PRIO1 set the right GPIOS

gpio_settings = {
        "pump_1":       26,
        "pump_2":       16,
        "pump_3":       12,
        "pump_4":       0,
        "pump_5":       0,
        "valve":        21,
        "scale_out":    0,
        "scale_in_DT":  5,
        "scale_in_SCK": 6,
        "distance1":    0,
        "distance2":    0,
        "distance3":    0,
        "rgb1":         0,
        "rgb2":         0,
        "rgb3":         0
        }

# Setup and stuff:

GPIO.cleanup()
time.sleep(1)
GPIO.setmode(GPIO.BCM)

for key, value in gpio_settings.items():
    if re.match('^pump', key) or re.match('^valve', key) or re.match('^rgb', key): 
        if value != 0: 
            GPIO.setup(value, GPIO.OUT, initial=GPIO.LOW)
            #GPIO.output( value, GPIO.LOW )
print('i did set up the gpios')

# scale - configure the scale environment
# TODO PRIO2 check if this works on the raspberry pi
# TODO PRIO2 add the files needed to make the scale work to my git, referencing to the guy who posted them
EMULATE_HX711=False
if not EMULATE_HX711:
    # uncomment line below when running from raspi
    from hx711 import HX711
    print('hello form hx711')
else:
    print('sounds nice doesnt work')
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(491)



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

# important function - handles the robots boot process
@app.route('/', methods=['GET', 'POST'])
def index():
    global READY, beverages, gpio_settings

    if READY and request.method == 'GET':
        # ansaugen all the set beverages
        # pouring_operations.ansaugen_all_tubes(gpio_settings, beverages, ansaug_times)
        # pouring_operations.initiate_hardware()
        return redirect('/drinks')
    elif request.method == 'GET':
        return render_template('/admin/conf_robot.html', options=db_operations.get_all_liquids_db())
    else:
        beverages = db_operations.set_current_tube_conf(request, beverages)
        READY = True
        return redirect('/')

# allows for post-boot-changes to the robot drink configuration
@app.route('/admin/robot_configuration', methods=['GET', 'POST'])
def robot_conf():
    global READY
    if request.method == 'GET':
        return render_template('/admin/conf_robot_edit.html', options=db_operations.get_all_liquids_db(), beverages=beverages)
    else:
        # can't remember what my logic was when writing this:
        READY = False
        return redirect('/')

# --- DRINKS ---

# displays the available drinks
@app.route('/drinks')
def drinks():
    all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
    doable_drinks = db_operations.get_drinks_doable(beverages, all_recipes, all_liquids)
    return render_template('drinks.html'
                            ,drinks=doable_drinks 
                            ,recipes=all_recipes)

# displays the admin view on available drinks, including the ability to add new drinks to the database
@app.route('/admin/add_drink', methods=['GET', 'POST'])
def add_drink():
    all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
    if request.method == 'POST':
        drink_title = request.form['title']
        drink_description = request.form['description']
        duplicate = db_operations.check_drink_duplicates(drink_title)
        
        if not duplicate:
            drink_id = db_operations.add_drink_to_db(db, drink_title, drink_description)
            keys = list(request.form.keys())
            success_code = db_operations.add_recipe_to_db(db, keys, request, drink_id)
            all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
            return render_template('/admin/add_drink.html', status_code=success_code, options=db_operations.get_all_liquids_db(),
                    drinks=all_drinks, recipes=all_recipes)
        else:
            error_code = "Drink with this title already exists. Be creative"
            # TODO PRIO2 Keep the drink I was trying to add. This is a nice to have. No Priority.
            return render_template('/admin/add_drink.html',
                    status_code=error_code, options=db_operations.get_all_liquids_db(),
                    drinks=all_drinks, recipes=all_recipes)
    else:
        all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
        return render_template('/admin/add_drink.html', options=db_operations.get_all_liquids_db(),
                    drinks=all_drinks, recipes=all_recipes)

# handles the deletion of a drink (drink row + recipe rows!)
# TODO PRIO2 Fix problems so i can do this with db_operations
@app.route('/admin/drinks/delete/<int:id>')
def delete(id):
    recipe = Recipe.query.filter_by(id_drink=id).all()    
    drink = Drink.query.get_or_404(id)
    for rec in recipe:
        db.session.delete(rec)
    db.session.delete(drink)
    db.session.commit()
    return redirect('/admin/add_drink')

# allows to edit an existing drink
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
            db.session.delete(rec)
        db.session.commit()
        # generate new recipe for the drink
        db_operations.add_recipe_to_db(db, keys, request, drink.id)
        return redirect('/admin/add_drink')
    else:
        return render_template('/admin/edit_drink.html', drink=drink, recipe=recipe, all_liquids=all_liquids, options=db_operations.get_all_liquids_db())

# --- LIQUIDS ---
# admin-liquid site. Allows to add new liquids, and displays all already existing liquids.
@app.route('/admin/add_liquid', methods=['GET', 'POST'])
def add_liquid():
    if request.method == 'POST':
        db_operations.add_liquid_to_db(db, request)
        all_liquids = Liquid.query.all()  
        return redirect('/admin/add_liquid')
    else:
        all_liquids = Liquid.query.all()
        return render_template('/admin/add_liquid.html', liquids=all_liquids)

# distplays all existing liquids. No admin rights or something like that
@app.route('/liquids')
def show_liquids():
    all_liquids = Liquid.query.all()
    return render_template('liquids.html', liquids=all_liquids)
   
# handles the deltion of a liquid
# TODO solve sessions problems so the code can be outsourced to db_operations.py
@app.route('/admin/liquid/delete/<int:id>')
def delete_liquid(id):
    liquid = Liquid.query.get_or_404(id)
    db.session.delete(liquid)
    db.session.commit()
    return redirect('/admin/add_liquid')

# handles the editing of a drink
@app.route('/admin/liquid/edit/<int:id>', methods=['GET', 'POST'])
def edit_liquid(id):
    liquid = Liquid.query.get_or_404(id)
    if request.method == 'POST':
        db_operations.edit_liquid_in_db(liquid, request, db)
        return redirect('/admin/add_liquid')
    else:
        return render_template('/admin/edit_liquid.html', liquid=liquid)


# --- DRINK MAKING PROCESS

# takes the drink it is supposed to make, and initiates its pouring process
@app.route('/serving/initiate/select_drink/<int:id>', methods=['GET', 'POST'])
def start_pouring_process(id):
    recipe = db_operations.get_recipe_for_drink(id)
    session['wants_drink_id'] = id
    if request.method == 'GET':
        # TODO PRIO2 implement option to change drink strength if time is left
        return render_template('/serving/initiation.html', id_drink=id, recipe=recipe)
    else:
        return redirect('/serving/initiate/check_glass')

# checks if glass was placed, and handles the whole pouring process. Should be renamed.
@app.route('/serving/initiate/check_glass', methods=['GET', 'POST'])
def check_glass_placement():
    global INSERTED, gpio_settings, beverages, extraction_cap_ml_s

    id = session['wants_drink_id']
    recipe = db_operations.get_recipe_for_drink(id)
    liquids = 0 #get_all_liquids()

    if request.method == 'GET':
        if not INSERTED:
            return render_template('/serving/glass_check.html')
        else:
            return render_template('/serving/pouring_process.html')
    else:
        if request.form['continue_button'] == 'Continue':
            print('checking distance sensor...')
            INSERTED = pouring_operations.check_glass_inserted()

            if INSERTED:
                # it probably doesn't make much sense to keep track of this here, if i am controlling the pouring process in
                # another function alltogether:
                LIQUID_RAN_OUT = False
                pouring_operations.tare_scale()
                try:
                    pouring_operations.control_pouring_process(session,gpio_settings, beverages, extraction_cap_ml_s)
                                                                
                    # TODO PRIO2 Ajax and JS to handle pouring process
                    # I need to update the page instead to redirecting to a new one. Is there a way to do that?
                    # Apparently, I need to use ajax for this, and need to have two divs, where i show one and hide the other, and
                    # vice versa. Keep on googling.
                    
                    # TODO handle successful completion of the pouring process
                    # if finishes successfully, needs to go load the next page or whatever, maybe just show a third div that was
                    # hidden until now.
                except Exception as e:
                    print(e)
                    # if it fails, the user needs to be notified about the failed status.
                    # it should change into debug mode, where the user is asked a series of questions. If all of those fail, 
                    # the robot should stay in hibernation until restarted. 

                    # TODO implement a working redirection to a working debugging system 

                    return redirect('debugging process')
            else:
                print('insert the fucking glass you donkey')
            
            return render_template('/serving/glass_check.html')


########################################################################################################################
#
# FUNCTIONS JINJA
#
########################################################################################################################

# everythin here works so far. Just leave it alone until there are no other bugs to solve. 

# available form html files. feeds jinja data
def get_recipes_for_drink(id_drink_req:int, all_recipes):
    try:
        all_recipes = Recipe.query.filter_by(id_drink=id_drink_req).all()
    except:
        all_recipes = []
    return all_recipes

# available from the html files. feeds jinja data.
def get_liquid_by_id(id_liquid_req:int, all_liquids):
    liquid = Liquid.query.filter_by(id=id_liquid_req).first().name
    return liquid

# make the functions available for jinja, so they can be called from the html-file.
app.jinja_env.globals.update(get_recipes_for_drink=get_recipes_for_drink)
app.jinja_env.globals.update(get_liquid_by_id=get_liquid_by_id)


########################################################################################################################
#
# Pumping
#
########################################################################################################################

# checks if glass was placed, and handles the whole pouring process. Should be renamed.
@app.route('/admin/pump_action', methods=['GET'])
def pump_action1():
    global gpio_settings, beverages, extraction_cap_ml_s

    if request.method == 'GET':
        return render_template('/admin/pump_action.html', gpio_settings=gpio_settings)


# checks if glass was placed, and handles the whole pouring process. Should be renamed.
@app.route('/admin/pump_action/<gpio>', methods=['GET', 'POST'])
def pump_action2(gpio):
    global gpio_settings, beverages, extraction_cap_ml_s

    if request.method == 'GET':
        return render_template('/admin/pump_action.html', gpio_settings=gpio_settings)
    else:
        print('hello, THIS IS PUMP ACTION')
        print(request.form)
        if request.form['button'] == "Start":
            # turn gpio on
            print('Start: ' + str(gpio))
            GPIO.output( gpio_settings[str(gpio)], GPIO.HIGH )
            pass
        if request.form['button'] == "Stop":
            print('Stop: ' + str(gpio))
            GPIO.output( gpio_settings[str(gpio)], GPIO.LOW )
            # turn gpio off
            pass
        return render_template('/admin/pump_action.html', gpio_settings=gpio_settings)
            


########################################################################################################################
#
# MAIN
#
########################################################################################################################

if __name__== '__main__':
    app.run(debug=True, port=5000 
            # ,host='192.168.1.141'
            #,host='192.168.223.176'
            #,host='192.168.223.211'
            ,host='192.168.68.176'
            )


