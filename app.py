from flask import Flask, render_template, request, redirect
from RPi import GPIO
from flask_sqlalchemy import SQLAlchemy


########################################################################################################################
#
# STATUS VARIABLES
#
########################################################################################################################

READY = False
ERROR = False


########################################################################################################################
#
# ROBOT CONFIGURATION
#
########################################################################################################################

beverages = {
        pump_1:"",
        pump_2:"",
        pump_3:"",
        pump_4:"",
        pump_5:"",
        valve:""
        }


########################################################################################################################
#
# GPIO CONFIGURATION
#
########################################################################################################################

# Pins for the pumps:

#pump1
#pump2
#pump3

# Pins for the scale:

#scale_out
#scale_in1
#scale_in2

# Pins for the distance sensor:

#distance1
#distance2
#distance3

# Pins for the LED Stripes

# rgb1
# rgb2
# rgb3

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

@app.route('/', methods=['GET', 'POST'])
def index():
    if READY and request.method == 'GET':
        return render_template('index.html')
    else:
        if request.method == 'GET':
            return render_template('configure_robot.html')
        else:
            # handle the input
            # configure robot variables
            # when all is done, change READY to True, or keep it false, if the input is not correct
            # redirect to /


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
    
    if request.method == 'POST':
        
        # Create new drink row:
        drink_title = request.form['title']
        drink_description = request.form['description']
        new_drink = Drink(title=drink_title, description=drink_description)
        db.session.add(new_drink)
        db.session.commit()
       

        # Create drink rows and add them to the db
        drink_id = Drink.query.filter_by(title=drink_title, description=drink_description)[0].id
        liquids = {
             Liquid.query.filter_by(name=request.form['liquid_1']).first().id : request.form['ml_liquid_1'],
             Liquid.query.filter_by(name=request.form['liquid_2']).first().id : request.form['ml_liquid_2'],
             Liquid.query.filter_by(name=request.form['liquid_3']).first().id : request.form['ml_liquid_3'],
             Liquid.query.filter_by(name=request.form['liquid_4']).first().id : request.form['ml_liquid_4'],
             Liquid.query.filter_by(name=request.form['liquid_5']).first().id : request.form['ml_liquid_5'], 
        }
        
        for key in liquids:
            liquid_id = key
            liquid_amount = liquids[key]
            new_recipe = Recipe(id_drink= drink_id, id_liquid= liquid_id, ml_liquid=liquid_amount)
            db.session.add(new_recipe)
            db.session.commit()
    
        return redirect('/admin/add_drink')
    
    else:
        return render_template('/admin/add_drink.html')

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

        return redirect('/admin/add_liquid')
    
    else:
        return render_template('/admin/add_liquid.html')


@app.route('/liquids')
def show_liquids():
    all_liquids = Liquid.query.all()
    return render_template('liquids.html', liquids=all_liquids)
   
@app.route('/admin/configure_liquids', methods=['GET', 'POST'])
def configure_liquids():
    if request.method == 'POST':
        return redirect('/admin/configure_liquids')
    else:
        all_liquids = Liquid.query.all()  
        return render_template('/admin/configure_liquids.html', all_liquids)

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



########################################################################################################################
#
# FUNCTIONS JINJA
#
########################################################################################################################

def get_recipes_for_drink(id_drink_req:int, all_recipes):
    all_recipes = Recipe.query.filter_by(id_drink=id_drink_req).all()
    return all_recipes

def get_liquid_by_id(id_liquid_req:int, all_liquids):
    liquid = Liquid,quer.filter_by(id=id_liquid_req).first()
    return liquid

# TODO write a function to get the available drinks with the given bottle configuration

def set_robot_configuration(conf_array):
    return

# make the functions available for jinja, so they can be called from the html-file.
app.jinja_env.globals.update(get_recipes_for_drink=get_recipes_for_drink)
app.jinja_env.globals.update(get_liquid_by_id=get_liquid_by_id)

if __name__== '__main__':
    app.run(debug=True, port=5000, host='192.168.1.141')
    print_hello()
