from flask import Flask
from RPi import GPIO


# Conf the pins:

OUTPUT = 2
OUTPUTTER = 3

GPIO.setmode(GPIO.BCM)
GPIO.setup(OUTPUT, GPIO.OUT) 
GPIO.setup(OUTPUTTER, GPIO.OUT)

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world'

@app.route('/led_on')
def fanOn(): 
    GPIO.output(OUTPUT, 1)
    GPIO.output(OUTPUTTER, 1)
    return '<h1>LED should be be shinig bright like a diamond in the sky</h1>'

@app.route('/led_off')
def fanOff():
    
    GPIO.output(OUTPUT, 0)
    GPIO.output(OUTPUTTER, 0)
    return '<h1>LED should be fucking dead</h1>'


if __name__== '__main__':
    app.run(debug=True, port=5000, host='192.168.26.176')
