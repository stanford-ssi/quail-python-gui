#############
''' Units Module :
The units module handles basic unit conversion by defining a set of unit conversion anonymous 
functions. The functions use numpy array-friendly operations to allow users to pass a value array in place
of a single value, should they wish.
'''
#############
import numpy as np

''' The unit lib stores conversion functions that take a value, x, from a given unit to the base unit. Metric modifiers on base units are 
    handled separately (made easy by the fact that all base units are the metric base units). 
    Ex:  unit_lib['m']['in'] is the equivalent of  0.0254 (m / in) 

    NOTE: The unit lib doesn't handle unit systems with different zero-reference points, e.g. temperature. The unit_offset structure holds
    offset values; if a unit is not found in the unit_offset library, it is assumed that reference points are the same.
'''
unit_lib = {
    "m" : { "m": 1, "in": 0.0254, "ft": 0.0254 * 12.0 } , # LINEAR DISTANCE (base: meter)
    "N" : { "N": 1, "lbf": 4.4482216 }, # FORCE (base: Newton)
    "g" : { "g": 1, "lb": 453.59237 , "slug": 14593.90}, # MASS (base: gram | lbf is included for imperial-minded folk)
    "pa" :{ "pa": 1, "psi": 6894.7572931783, "atm": 101325, "bar": 1e5 }, # PRESSURE (base: Pascal)
    "K" : { "K": 1, "R": 5.0/9.0, "C": 1, "F": 5.0/9.0 }, #TEMPERATURE (base: Kelvin)
    "unitless" : { "unitless": 1, "none": 1 } # UNITLESS
}
''' The unit_offset stores the offsets of a unit from the base unit's zero reference, in the base unit. If a unit is not found in the unit_offset
    structure, it is assumed that no reference-shift is necessary.
    Ex: to convert a temperature, T, in degC to degK
    degK = unit_lib['K']['C'] * T degC + unit_offset['K']['C'] degK 
'''
unit_offset = {
    "K" : {"C": 273.15 , "F": 273.15 - 32*5.0/9.0 }, #TEMPERATURE OFFSETS 
}

''' The metric mult stores the metric multipliers based on the shorthand prefixes. '''
metric_mult = {
    "k": 1000,
    "h": 100,
    "da": 10,
    "d": 0.1,
    "c": 0.01,
    "m": 1E-3,
    "n": 1E-9
}

def get_available_units():
    ''' Returns a list of all available units defined in the units lib '''
    unit_list = []
    for key in unit_lib:
        unit_list += list(unit_lib[key].keys())
    return unit_list

def get_compatible_units(unit):
    ''' Returns a list of units compatible with the given unit. 
        The returned list will contain the given unit, unless no other compatible units are found.
    '''  
    my_base_unit = None
    # Search for the from_unit in the unit lib
    for base_unit in unit_lib:
        for each_unit in unit_lib[base_unit]:
            if unit.casefold() == each_unit.casefold() :
                my_base_unit = base_unit
                break
    if my_base_unit is None: # If you don't find a base unit, return empty list
        return []
    else:
        return unit_lib[my_base_unit].keys() # return list of keys for that base unit

def validate_units(from_unit, to_unit): 
    ''' Returns true if from_unit can be converted to to_unit by this module. Otherwise returns false. '''
    my_base_unit = None
    # Search for the from_unit in the unit lib
    for base_unit in unit_lib:
        for unit in base_unit:
            if unit.casefold() == from_unit.casefold():
                my_base_unit = base_unit
                break
    # If didn't find it, check if the from_unit is a metric multiplier of the base unit. 
    # If so, remove the metric multiplier and validate the base unit
    if my_base_unit is None:
        for prefix in metric_mult:
            if from_unit[:len(prefix)] == prefix:
                my_base_unit = from_unit[len(prefix):]
                if not(my_base_unit in [key.casefold() for key in unit_lib.keys()]):
                    return False # if can't find the base unit
    # Confirm that the to_unit is a valid conversion based on the base unit.
    if to_unit in [key.casefold() for key in unit_lib[my_base_unit].keys()]:
        return True 
    else:
        return False

def convert(value, from_unit, to_unit):
    ''' Returns the conversion of a value in one unit to a compatible unit.
        value: the value to be converted (can also be a np array of values)
        from_unit: the units of value
        to_unit: the units to which value is converted 

        Raises a KeyError if the units passed are incompatible or invalid.
    '''
    my_base_unit = None
    # Search for the from_unit in the unit lib
    for base_unit in unit_lib:
        for unit in unit_lib[base_unit]:
            if unit.casefold() == from_unit.casefold() :
                my_base_unit = base_unit
                from_unit = unit
                break
    # If didn't find it, from_unit is a metric multiplier of the base unit. 
    # If so, adjust the value to get it in its base unit equivalent (e.g. take the km value to m)
    if my_base_unit is None:
        for prefix in metric_mult:
            if from_unit[:len(prefix)].casefold() == prefix.casefold():
                value = np.multiply(value, metric_mult[prefix] )
                return convert(value, from_unit[len(prefix):], to_unit) # having converted to a base unit and multiplied valued, recurse
    # Do the same as above for the to_unit, defining a multiplier thats applied on the value at end if to_unit is 
        # a metric multiplier of a base unit
    mult = 1 # by default, multiplier is 1
    flag = False
    for unit in unit_lib[my_base_unit]:
        if unit.casefold() == to_unit.casefold():
            to_unit = unit
            flag = True
    if flag is False: # If didn't find it, must be a metric multiplier of a base unit
            for prefix in metric_mult:
                if to_unit[:len(prefix)].casefold() == prefix.casefold():
                    mult = 1 / metric_mult[prefix]
                    to_unit = to_unit[len(prefix):]
                    for unit in unit_lib[my_base_unit]: # if found the metric multiplier, find the key that is the case-insensitive match
                        if unit.casefold() == to_unit.casefold():
                            to_unit = unit
                            break
                    break
    # Convert to base unit, checking to see if an offset exists 
    value = np.multiply(value, unit_lib[my_base_unit][from_unit] ) # value (from_unit) * # (base_unit/from_unit) = new value (base_unit)
    try:
        value = np.add(value, unit_offset[my_base_unit][from_unit])
    except KeyError:
        pass # KeyError indicates no offset exists for this unit pair
    # Convert to to_unit, checking to see if an offset exists
    try:
        value = np.subtract(value, unit_offset[my_base_unit][to_unit])
    except KeyError:
        pass # KeyError indicates no offset exists for this unit pair
    value = np.divide(value, unit_lib[my_base_unit][to_unit])
    
    return np.multiply(value, mult) # apply the multiplier and return


### FUNCTIONALITY TESTING ###
# print( 0 == convert(-273.15, 'C', 'K'))
# print( 2.54 == convert(1.0, 'in', 'cm'))
# print(1000/0.0254 == convert(1.0, 'km', 'in'))
# print(2.54e-5 == convert(1.0, 'in', 'km'))
# print(abs(1/2.21 - convert(1.0,'lb','kg')) <= 1E-2)
# print( [[1.0], [2.0], [3.0]] ==  np.divide(convert([[1],[2],[3]], 'km', 'in'), 1000/0.0254 ) )
