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

class Liquid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    alc_category = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    alc_content = db.Column(db.Float, nullable=True)

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # There's quite some work to do here, i need:
    # 1) pk from Drink
    # 2b) Drink.name in order to filter through this shit (or should I just build a dynamic query?)
    # 2) pk from Liquid
    # 3) amount of liquid
    # 4) This would be fun: Amount of times that it was made. Each execution would be +1.


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/drinks')
def drinks():
    all_drinks = Drink.query.order_by(Drink.title).all()
    return render_template('drinks.html', drinks=all_drinks)

@app.route('/admin/add_drink', methods=['GET', 'POST'])
def add_drink():
    if request.method == 'POST':
        drink_title = request.form['title']
        drink_description = request.form['description']
        # add for loop to add to the liquid-drink-table
        new_drink = Drink(title=drink_title, description=drink_description)
        db.session.add(new_drink)
        db.session.commit()
        return redirect('/admin/add_drink')
    else:
        return render_template('add_drink.html')


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


if __name__== '__main__':
    app.run(debug=True, port=5000, host='192.168.1.141')
