from flask import Flask, render_template, request, redirect
from RPi import GPIO
from flask_sqlalchemy import SQLAlchemy

# Conf the pins:

OUTPUT = 2
OUTPUTTER = 3

GPIO.setmode(GPIO.BCM)
GPIO.setup(OUTPUT, GPIO.OUT) 
GPIO.setup(OUTPUTTER, GPIO.OUT)

app = Flask(__name__)


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

# We're working with a simplified cocktail dataset, as well as a simplified model. I will not fully normalize the
# table, as I think it's not necessary in this example. 

class Liquid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    alc_category = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    alc_content = db.Column(db.Float, nullable=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # There's quite some work to do here, i need:
    id_drink = db.Column(db.Integer, nullable=False)
    id_liquid = db.Column(db.Integer, nullable=False)
    ml_liquid = db.Column(db.Integer, nullable=False)
    
    # 4) This would be fun: Amount of times that it was made. Each execution would be +1.


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/drinks')
def drinks():
    all_drinks = Drink.query.order_by(Drink.title).all()
    # TODO
    # we will need the recipes as well.
    all_recipes = Recipe.query.all()
    all_liquids = Liquid.query.all()
    # give that query result to the render template
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
        
        # Create the recipe rows:
        # get drink id and store it in order to also create the recipe
        drink_id = Drink.query.filter_by(title=drink_title, description=drink_description)[0].id

        # TODO
        # The rows below should be a dict, which will be used to create the recipe
        # The values in here can only be chosen from the existing list of drinks, so we can work with id's:
        # Get the respective IDs of the drink, map the amount, map the cocktail ID
        
        liquid_1 = request.form['liquid_1']
        ml_liquid_1 = request.form['ml_liquid_1']
        ml_liquid_1 = request.form['ml_liquid_1']
        liquid_2 = request.form['liquid_2']
        ml_liquid_2 = request.form['ml_liquid_2']
        liquid_3 = request.form['liquid_3']
        ml_liquid_3 = request.form['ml_liquid_3']
        liquid_4 = request.form['liquid_4']
        ml_liquid_4 = request.form['ml_liquid_4']
        liquid_5 = request.form['liquid_5']
        ml_liquid_5 = request.form['ml_liquid_5']
      
        print(liquid_1)

        
        # TODO - write the dictionary according to the line below, and test it.
        liquids = {
             Liquid.query.filter_by(name=request.form['liquid_1']).first().id : request.form['ml_liquid_1'],
             Liquid.query.filter_by(name=request.form['liquid_2']).first().id : request.form['ml_liquid_2'],
             Liquid.query.filter_by(name=request.form['liquid_3']).first().id : request.form['ml_liquid_3'],
             Liquid.query.filter_by(name=request.form['liquid_4']).first().id : request.form['ml_liquid_4'],
             Liquid.query.filter_by(name=request.form['liquid_5']).first().id : request.form['ml_liquid_5'], 
        }
        
       
        # TODO
        for key in liquids:
            liquid_id = key
            liquid_amount = liquids[key]
            new_recipe = Recipe(id_drink= drink_id, id_liquid= liquid_id, ml_liquid=liquid_amount)
            db.session.add(new_recipe)
            db.session.commit()
        return redirect('/admin/add_drink')
    else:
        return render_template('/admin/add_drink.html')

@app.route('/admin/add_liquid', methods=['GET', 'POST'])
# TODO write template for adding liquids, analogue to the one with the drinks
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
   
# TODO save the current tube configuration in some sort of global variable
@app.route('/admin/configure_liquids', methods=['GET', 'POST'])
def configure_liquids():
    if request.method == 'POST':
        return redirect('/admin/configure_liquids')
    else:
        #all_liquids =  
        return render_template('/admin/configure_liquids.html', all_liquids)

@app.route('/led_on')
def fanOn(): 
    GPIO.output(OUTPUT, 1)
    GPIO.output(OUTPUTTER, 1)
    return '<h1>Da LED should be be shinig bright like a diamond in the sky</h1>'

@app.route('/led_off')
def fanOff():
    
    GPIO.output(OUTPUT, 0)
    GPIO.output(OUTPUTTER, 0)
    return '<h1>LED should be fucking dead</h1>'



######## This part contains global functions that can be called by jinja ###########

def get_recipes_for_drink(id_drink_req:int, all_recipes):
    all_recipes = Recipe.query.filter_by(id_drink=id_drink_req).all()
    return all_recipes

def get_liquid_by_id(id_liquid_req:int, all_liquids):
    liquid = Liquid,quer.filter_by(id=id_liquid_req).first()
    return liquid



app.jinja_env.globals.update(get_recipes_for_drink=get_recipes_for_drink)
app.jinja_env.globals.update(get_liquid_by_id=get_liquid_by_id)

if __name__== '__main__':
    app.run(debug=True, port=5000, host='192.168.1.141')
