import time
import sys
from math import isclose
import db_operations
import distance as d
import RPi.GPIO as GPIO
from hx711 import HX711


########################################################################################################################
#
# HARDWARE SETUP
#
########################################################################################################################

# set the usual value read from the distance sensor. If the distance is significantly different, we can assume that a glass
# has been inserted.
standard_value_distance_sens = 16.5


#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)
 
#set GPIO Pins
GPIO_TRIGGER = 25
GPIO_ECHO = 26
 
#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)
########################################################################################################################
#
# RGB Controls
#
########################################################################################################################
# TODO Prio1 set the gpio colors
def set_rgb_color(color:str):
    if color == 'red':
        # set to red
        print('red')
    elif color == 'yellow':
        # set color to yellow
        print('yellow')
    elif color == 'green':
        print('green')
    return True

########################################################################################################################
#
# DISTANCE SENSOR
#
########################################################################################################################
# TODO Prio1
# Get the distance sensor value in order to evaluate whether a glass has been placed in the automat or not
def get_distance_sensor_val():
    sensor_value = d.distance()
    return sensor_value

# tells us whether a glass was inserted or not, based on the distance sensor values
def check_glass_inserted():
    global standard_value
    current_value = get_distance_sensor_val()
    print("disance: " + str(current_value))
    if isclose(current_value, standard_value_distance_sens, abs_tol=4):
        return False
    else:
        return True

########################################################################################################################
#
# SCALE
#
########################################################################################################################
def cleanAndExit():
    print("Cleaning...")
    GPIO.cleanup()   
    print("Bye!")
    sys.exit()

# TODO Prio2
# This would offer a way to calibrate the scale via the robot gui. Not necessary for now.
def calibrate(): 
    return True

def get_scale_value(gpio_settings, hx):
    scale_value = 0
    try:
        scale_value = hx.get_weight()
        #hx.power_down()
        #hx.power_up()
        time.sleep(0.01)
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
    return round(scale_value, 0)

########################################################################################################################
#
# INITIATION PROCESS
#
########################################################################################################################

# TODO Prio1 - Get a working version of this method. It shall be executed upon the start of the great awakening of the drink
# robot.
def ansaugen_all_tubes(gpio_settings:dict, beverages:dict, ansaug_times:dict):
    pins_ansaugen=[]
    #TODO Prio2 Group the ansaug times in 2D array, start with the longest, end with the shortest. Based on the ansaug-times
    ansaug_time = 5
    for key, value in beverages.items():
        if value != "":
            pins_ansaugen.append(gpio_settings[key])
    
    for pin in pins_ansaugen:
        # turn on pump
        next
    print('turned on pump(s)')

    time.sleep(ansaug_time)

    for pin in pins_ansaugen:
        # turn off pump
        next
    print('turned off pumps')
    return True

########################################################################################################################
#
# POURING PROCESS
#
########################################################################################################################

def pour_liquid(liquid_id:int, outlet, amount_ml:int, gpio_pin:int, 
                extraction_cap:int, gpio_settings:dict, hx:HX711, liquid_name:str):

    keep_going = True
    current_state={
        'poured_time':0,
        'beverage': liquid_id,
        'outlet': outlet,
        'gpio_pin':gpio_pin
    }

    # gpio_pin start pouring
    time.sleep(1)
    GPIO.output( gpio_settings[outlet], GPIO.LOW )
    scale = 0
    old_scale = 0
    overflow_counter = 0
    start_time = time.time
    print(start_time)

    if outlet == 'valve':
        while scale <= amount_ml-30 and overflow_counter < 5:
            scale = get_scale_value(gpio_settings, hx)
            if scale == -0.0:
                scale = 0.0
            if old_scale == scale and time.time > start_time + 2:
                print(time.time)
                overflow_counter += 1
            old_scale = scale

            print(scale)
            time.sleep(0.3)
    else:
        while scale <= amount_ml and overflow_counter < 5:
            scale = get_scale_value(gpio_settings, hx)
            if scale == -0.0:
                scale = 0.0
            if old_scale == scale and time.time > start_time + 2:
                overflow_counter += 1
            old_scale = scale

            print(scale)
            time.sleep(0.3)
    GPIO.output( gpio_settings[outlet], GPIO.HIGH )
    print('finished pouring: ' + liquid_name)
    time.sleep(4)
        




def control_pouring_process(session:dict, gpio_settings:dict, beverages:dict, extraction_cap_ml_s:dict, hx:HX711):
    # at this point, selection was confirmed and glass has been inserted 
    # now, the pouring process just does its job, which i need to configure here.
    drink_id = session['wants_drink_id']
    recipes = db_operations.get_recipe_for_drink(drink_id)
    hx.reset()
    hx.tare()
    print("Tare done! Add weight now...")

    for recipe in recipes:
        try:
            liquid_id = recipe.id_liquid
            liquid_name = db_operations.get_liduid_by_id(liquid_id)
            amount_ml = recipe.ml_liquid
            outlet = next(key for key, value in beverages.items() if value == liquid_name)
            extraction_cap = extraction_cap_ml_s[outlet]
            gpio_pin = gpio_settings[outlet]
            print('pouring: ' + liquid_name)
            pour_liquid(liquid_id, outlet, amount_ml, gpio_pin, extraction_cap, gpio_settings , hx, liquid_name)
            hx.tare() # important
        except Exception as e: 
            print(e)

    print('terminated pouring process')
    return True


########################################################################################################################
#
# CLEANING PROCESS
#
########################################################################################################################

# TODO Prio2
# Cleaning is important, but not vital, to our demonstration

def clean(gpio_settings):
    # cleans the tubes. Similar to ansaugen, should make sure that i don't end up with massive code duplication
    # 0) blocks everything else and turns rgbs red
    # 1) asks you to fill a box with cleaning agent
    # 2) asks you to put all tubes in that box
    # 3) asks you to confirm that you have placed a recipient able to absorb all the liquid
    # 4) starts first round of cleaning with water with cleaning agent
    # 5) asks you to replace water-cleaning agent with pure water
    # 6) pumps through a set amount of water to make sure that there is no cleaning agent in the tubes
    # 7) finishes cleaning process
    return True
