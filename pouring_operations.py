import time
import sys

########################################################################################################################
#
# GPIO SETUP
#
########################################################################################################################



########################################################################################################################
#
# HARDWARE SWETUP
#
########################################################################################################################
# scale
EMULATE_HX711=False
referenceUnit = 1
if not EMULATE_HX711:
    # uncomment line below when running from raspi
    # import RPi.GPIO as GPIO
    # from hx711 import HX711
    print('hello')
else:
    #from emulated_hx711 import HX711
    print('hello')
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)


########################################################################################################################
#
# RGB Controls
#
########################################################################################################################
def set_rgb_color(color:str):
    if color == 'red':
        # set to red
        print('yo')
    elif color == 'yellow':
        # set color to yellow
        print('yo')
    elif color == 'red':
        print('yo')
    return True

########################################################################################################################
#
# DISTANCE SENSOR
#
########################################################################################################################
def get_distance_sensor_val():
    # 1 - start the distance sensor
    # 2 - read the current value
    # 3 - turn it back off
    # 4 - return value
    sensor_value = 0
    return sensor_value

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

def calibrate(): # THIS IS PRIO 2!!
        # 0 - make sure that I am importing everythin that is needed here
    # 1 - redirect to calibraiton window
    # 2 - give calibration instructions: how much weight, etc.
    # 3 - guide through calibration process
    # 4 - store the calibration values in the corresponding global variable in this file
    return True

def tare_scale():
    # 1 -  Unncessecary, I think: Read in the previous valid value, probably stored in this file as global variable
    # 2 - read in the current value
    # 3 - set the current value as the new current value, or just return it, and it will be set in the function that called
    #     called this function
    return True

def get_scale_value():
    # 1 - start up scale
    # 2 - read in current value
    # 3 - return that value
    scale_value = 0

    try:
        # These three lines are usefull to debug wether to use MSB or LSB in the reading formats
        # for the first parameter of "hx.set_reading_format("LSB", "MSB")".
        # Comment the two lines "val = hx.get_weight(5)" and "print val" and uncomment these three lines to see what it prints.
        
        # np_arr8_string = hx.get_np_arr8_string()
        # binary_string = hx.get_binary_string()
        # print binary_string + " " + np_arr8_string
        
        # Prints the weight. Comment if you're debbuging the MSB and LSB issue.
        val = hx.get_weight(5)
        print(val)

        # To get weight from both channels (if you have load cells hooked up 
        # to both channel A and B), do something like this
        #val_A = hx.get_weight_A(5)
        #val_B = hx.get_weight_B(5)
        #print "A: %s  B: %s" % ( val_A, val_B )

        hx.power_down()
        hx.power_up()
        time.sleep(0.1)

    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()
    return scale_value


########################################################################################################################
#
# INITIATION PROCESS
#
########################################################################################################################

# check if I can condense the ansaug-functions into one function, and just give it a one-element list if i only want to do one
# tube. Seems more simple to me. 
def ansaugen_all_tubes():
    #ansaugs all the tubes for a set period of time, which is configured to surely fill them with liquid
    # 0 - asks you if you have connected all the tubes
    # 1 - when confirmed, blocks everything else
    # 2 - starts chugging away until the tubes have been filled
    # 3 - unblocks everyhting, changes led color back to green, and leads you back to main page
    return True

def ansaugen_single_tube():
    # can be used to ansaugen  a single tube, when a single bottle was changed, and we don't want to waste alcohol or drink 
    # disgusting mixes

    # 0 - asks you if the tube is in the liquid
    # 1 - when confirmed, blocks everytihng else
    # 2 - starts chugging away until the tubes have been filled
    # 3 - unblocks everything, changes led color back to green, and leads you back to main page
    return True


########################################################################################################################
#
# POURING PROCESS
#
########################################################################################################################

def pour_liquid(liquid:str, amount:int, bev_config:dict):
    return True

def conf_glass_tare_scale():
    distance = get_distance_sensor_val()

    return True

def control_pouring_process():
    # at this point, selection was confirmed and glass has been 
    return True


########################################################################################################################
#
# CLEANING PROCESS
#
########################################################################################################################

def clean():
    # cleans the tubes.
    # 0) blocks everything else and turns rgbs red
    # 1) asks you to fill a box with cleaning agent
    # 2) asks you to put all tubes in that box
    # 3) asks you to confirm that you have placed a recipient able to absorb all the liquid
    # 4) starts first round of cleaning with water with cleaning agent
    # 5) asks you to replace water-cleaning agent with pure water
    # 6) pumps through a set amount of water to make sure that there is no cleaning agent in the tubes
    # 7) finishes cleaning process
    return True