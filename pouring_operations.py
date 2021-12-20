import time
import sys
from math import isclose
import db_operations



########################################################################################################################
#
# HARDWARE SETUP
#
########################################################################################################################

# moved everything to app.py

# distance sensor - configure the distance sensor environment
standard_value = 0



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
    # 1 - start the distance sensor
    # 2 - read the current value
    # 3 - turn it back off
    # 4 - return value
    sensor_value = 20
    return sensor_value

# tells us whether a glass was inserted or not, based on the distance sensor values
def check_glass_inserted():
    global standard_value
    current_value = get_distance_sensor_val()
    if isclose(current_value, standard_value, abs_tol=10):
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

    if not EMULATE_HX711:
        GPIO.cleanup()
        
    print("Bye!")
    sys.exit()

# TODO Prio2
# This would offer a way to calibrate the scale via the robot gui. Not necessary for now.
def calibrate(): 
    return True

# TODO Prio1
# This tares the scale value. Not sure if we even need it, I can just set it back to zero in the pouring loop as soon as the 
# glass was placed
def tare_scale():
    return True


# TODO Prio 1
# This will return the current scale value
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


def ansaugen_all_tubes(gpio_settings, beverages, ansaug_times):
    pins_ansaugen=[]
    #TODO Prio2 Group the ansaug times in 2D array, start with the longest, end with the shortest. Based on the ansaug-times
    ansaug_time = 5
    for key, value in beverages.items():
        if value != "":
            pins_ansaugen.append(gpio_settings[key])
    
    for pin in pins_ansaugen:
        # turn on pump
        print(pin)
    print('turned on pump')

    time.sleep(ansaug_time)

    for pin in pins_ansaugen:
        # turn off pump
        print(pin)
    print('ansaugen should be finished')
    return True

def ansaugen_single_tube(gpio_to_ansaug):
    # can be used to ansaugen  a single tube, when a single bottle was changed, and we don't want to waste alcohol or drink 
    # disgusting mixes

    return True


########################################################################################################################
#
# POURING PROCESS
#
########################################################################################################################

def pour_liquid(liquid_id, outlet, amount_ml, gpio_pin, extraction_cap, gpio_settings, hx):

    time_s = round(amount_ml/extraction_cap, 0)
    time_s = 20
    print(time_s)
    time_c = 0 
    keep_going = True
    current_state={
        'poured_time':0,
        'beverage': liquid_id,
        'outlet': outlet,
        'gpio_pin':gpio_pin
    }

    # gpio_pin start pouring
    print('going to sleep...')
    time.sleep(1)
    print('woke up')
    time_c += 1

    while time_c <= time_s:
        scale = get_scale_value(gpio_settings, hx)
        if scale == -0.0:
            scale = 0.0
        print(scale)
        time_c+=1
        # approximation with +/- 20% - let's try it like this
        """ if scale <= time_c*extraction_cap*1.2 and scale >= time_c*extraction_cap*0.8:
            keep_going = True
            # time.sleep(1)
            time_c += 1
            current_state['poured_time'] = time_c
            pass
        else:
            # interrupt pouring proces according to follwing scenarios:
            if scale > time_c*extraction_cap*1.2:
                print('seems like we re poruing too fast - stopping the process')
                #TODO PRIO1 - Handle this
                break
            if scale < time_c*extraction_cap*0.8:
                print('seems like pouring is obstructed or the bottle is empty - please refill and confirm')
                #TODO PRIO1 - Handle this

                break
            break """
        




def control_pouring_process(session, gpio_settings, beverages, extraction_cap_ml_s, hx):
    # at this point, selection was confirmed and glass has been inserted 
    # now, the pouring process just does its job, which i need to configure here.
    drink_id = session['wants_drink_id']
    recipes = db_operations.get_recipe_for_drink(drink_id)
    hx.reset()
    hx.tare()
    print("Tare done! Add weight now...")


    for recipe in recipes:
        liquid_id = recipe.id_liquid
        liquid_name = db_operations.get_liduid_by_id(liquid_id)
        amount_ml = recipe.ml_liquid
        outlet = next(key for key, value in beverages.items() if value == liquid_name)
        extraction_cap = extraction_cap_ml_s[outlet]
        gpio_pin = gpio_settings[outlet]
        print('about to pour first liquid...')
        pour_liquid(liquid_id, outlet, amount_ml, gpio_pin, extraction_cap, gpio_settings )


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
