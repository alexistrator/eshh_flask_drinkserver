import re
import db_operations
import multiprocessing as mp
import time
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.orm.relationships import RelationshipProperty

RASPI = True
SCALE = True
#HOST = "127.0.0.1"
HOST = "192.168.15.203"

if RASPI:
    import RPi.GPIO as GPIO
    import pouring_operations
    from hx711 import HX711

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
CONTINUED = False

########################################################################################################################
#
# ROBOT CONFIGURATION
#
########################################################################################################################

beverages = {
        "pump_1":"",
        "pump_2":"",
        "pump_3":"",
        # "pump_4":"",
        # "pump_5":"",
        "valve":""
        }

# TODO PRIO1 measure the capacity of our pumps, save it here
# extraction capacity of pumps in ml per second
extraction_cap_ml_s = {
        "pump_1":   1,
        "pump_2":   1,
        "pump_3":   1,
        #"pump_4":   5,
        #"pump_5":   10,
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
gpio_settings = {
        "pump_1":       21,
        "pump_2":       20,
        "pump_3":       12,
        #"pump_4":       26,
        #"pump_5":       26,
        "valve":        26,
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
if RASPI:
    GPIO.cleanup()
    time.sleep(1)
    GPIO.setmode(GPIO.BCM)

    for key, value in gpio_settings.items():
        if re.match('^pump', key) or re.match('^valve', key) or re.match('^rgb', key): 
            if value != 0: 
                GPIO.setup(value, GPIO.OUT, initial=GPIO.HIGH)
    print('i did set up the gpios')

    if SCALE: 
        # scale - configure the scale environment
        # TODO PRIO2 check if this works on the raspberry pi
        # TODO PRIO2 add the files needed to make the scale work to my git, referencing to the guy who posted them
        hx = HX711(5, 6)
        hx.set_reading_format("MSB", "MSB")
        hx.set_reference_unit(491)
        print("I did set up the scale")



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
    """
    Important function. Handles boot process, with ansaugen.

    Returns:
        redirect : if READY and GET, go to the drinks menue
        template : if not READY and GET, return html template to configure robot
    """
    global READY, beverages, gpio_settings

    if READY and request.method == 'GET':
        # ansaugen all the set beverages
        # pouring_operations.ansaugen_all_tubes(gpio_settings, beverages, ansaug_times)
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
        # READY set to false so the ansaugen can be done for the tube
        READY = False
        return redirect('/')

# --- DRINKS ---

    
@app.route('/drinks')
def drinks():
    """
    Shows all available drinks

    Returns:
        template: html-template with the available drinks
    """
    all_drinks, all_recipes, all_liquids = db_operations.get_data_for_drinks()
    doable_drinks = db_operations.get_drinks_doable(beverages, all_recipes, all_liquids)
    return render_template('drinks.html'
                            ,drinks=doable_drinks 
                            ,recipes=all_recipes)

@app.route('/admin/add_drink', methods=['GET', 'POST'])
def add_drink():
    """
    Is accessible from admin mode. Makes it possible to add new drink recipes to the database, and to delete or edit them.

    Returns:
        template: html template
    """
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

# TODO PRIO2 Fix problems so i can do this with db_operations
@app.route('/admin/drinks/delete/<int:id>')
def delete(id):
    """
    Deletes everything related to a certain drink ID (drink + recipe)

    Args:
        id (int): id of the drinks that needs to be deleted

    Returns:
        redirect: back to the drink admin site
    """
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
    """
    Allows to edit a drink element as well as its corresponding recipes.

    Args:
        id (int): id of the drink that has to be edited

    Returns:
        template: html-template to drink editing menu if GET
        redirect: redirect to drink admin menu if POST
    """
    drink = Drink.query.get_or_404(id)
    recipe = Recipe.query.filter_by(id_drink=drink.id).all()
    all_liquids = Liquid.query.all()
    if request.method == 'GET':
        return render_template('/admin/edit_drink.html', drink=drink, recipe=recipe, all_liquids=all_liquids, options=db_operations.get_all_liquids_db())
    # TODO Prio2 outsource the code below to db_operations
    else:
        # edit the drink element
        drink.title = request.form['title']
        drink.description = request.form['description']
        db.session.commit()
        # delete the current recipes available for the drink
        for rec in recipe:
            db.session.delete(rec)
        db.session.commit()
        # generate new recipe for the drink
        keys = list(request.form.keys())
        db_operations.add_recipe_to_db(db, keys, request, drink.id)
        return redirect('/admin/add_drink')

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
    global INSERTED, gpio_settings, beverages, extraction_cap_ml_s, hx, READY, CONTINUED

    if request.method == 'GET':
        if not INSERTED:
            return render_template('/serving/glass_check.html')
        else:
            return render_template('/serving/pouring_process.html')
    else:
        if request.form['continue_button'] == 'Continue':
            print('checking distance sensor...')
            if RASPI:
                INSERTED = pouring_operations.check_glass_inserted()
            else:
                INSERTED = True

            if INSERTED:                
                if RASPI:
                    try:
                        hx.tare()
                        pouring_operations.control_pouring_process(session,gpio_settings, beverages, extraction_cap_ml_s, hx)

                        # TODO PRIO2 Ajax and JS to handle pouring process
                        # I need to update the page instead to redirecting to a new one. Is there a way to do that?
                        # Apparently, I need to use ajax for this, and need to have two divs, where i show one and hide the other, and
                        # vice versa. Keep on googling.
                        
                        # TODO handle successful completion of the pouring process
                        # if finishes successfully, needs to go load the next page or whatever, maybe just show a third div that was
                        # hidden until now.
                        INSERTED = False
                        return redirect('/')
                    except Exception as e:
                        print(e)
                        # if it fails, the user needs to be notified about the failed status.
                        # it should change into debug mode, where the user is asked a series of questions. If all of those fail, 
                        # the robot should stay in hibernation until restarted. 

                        # TODO implement a working redirection to a working debugging system 

                        return redirect('debugging process')
                else:
                    # mock serving (say "pouring liquid XYZ, pouring next, ..." etc.)
                    return redirect('/')
            else:
                print('insert the fucking glass you donkey')
            
            return render_template('/serving/glass_check.html')


########################################################################################################################
#
# FUNCTIONS JINJA
#
########################################################################################################################

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
# PUMP TESTING
#
########################################################################################################################

@app.route('/admin/pump_action', methods=['GET'])
def pump_action1():
    """
    Opens a menu to test the function of all the pumps. They can be turned on and off without having to go through the 
    drinks selection.

    Returns:
        template : html-template with the option to turn on and off certain gpio pins
    """
    global gpio_settings, beverages, extraction_cap_ml_s
    if request.method == 'GET':
        return render_template('/admin/pump_action.html', gpio_settings=gpio_settings)


@app.route('/admin/pump_action/<gpio>', methods=['GET', 'POST'])
def pump_action2(gpio):
    """
    Handles the POSTs from the pump testing site. Turns GPIOs on and off. 

    Args:
        gpio (int): GPIO pin that is being activated/deactivated

    Returns:
        template: html-template where the different pumps can be tested
    """
    global gpio_settings, beverages, extraction_cap_ml_s

    if request.method == 'GET':
        return render_template('/admin/pump_action.html', gpio_settings=gpio_settings)
    else:
        if request.form['button'] == "Start":
            print('Start: ' + str(gpio))
            GPIO.output( gpio_settings[str(gpio)], GPIO.LOW )
            pass
        if request.form['button'] == "Stop":
            print('Stop: ' + str(gpio))
            GPIO.output( gpio_settings[str(gpio)], GPIO.HIGH )
            pass
        return render_template('/admin/pump_action.html', gpio_settings=gpio_settings)
            


########################################################################################################################
#
# MAIN
#
########################################################################################################################

if __name__== '__main__':
    app.run(debug=True, port=5000, host=HOST
            )


