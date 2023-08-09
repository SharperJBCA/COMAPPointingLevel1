import numpy as np
from matplotlib import pyplot
import h5py 
import os 
import sys 

# 1) Function that opens the level 1 file
# 2) Function that contains the pointing model 
# 3) Check if pixel_pointing exists in the level 1 file, if so rename it to pixel_pointing_191101
# 4) Create a new pixel_pointing group in the level 1 file
# 5) Apply correction to old az/el data and write to the new pixel_pointing group
# 6) Calculate updated ra/dec coordinates and write to the new pixel_pointing group
# 7) Add an attribute to pixel_pointing group of: .attrs['azel\_pointing_model\_YYMMDD'] = [$A$, $B$,...]

class PointingModel:
    def __init__(self, az_functions=['function_A', 'function_B','function_C','function_D','function_E'], el_functions=['function_a', 'function_b','function_c']):
        # Define possible functions and their parameters inside the class
        self.available_functions = {'Az':{
            'function_A': {
                'func': lambda az, el, A: A*np.ones(az.size),
                'params': ['A']
            },
            'function_B': {
                'func': lambda az, el, B: B*np.cos(el),
                'params': ['B']
            },
            'function_C': {
                'func': lambda az, el, C: C*np.sin(el),
                'params': ['C']
            },
            'function_D': {
                'func': lambda az, el, D: -D*np.sin(az)*np.sin(el),
                'params': ['D']
            },
            'function_E': {
                'func': lambda az, el, E: -E*np.cos(az)*np.sin(el),
                'params': ['E']
            }},'El':{
            'function_a': {
                'func': lambda az, el, a: a*np.ones(az.size),
                'params': ['a']
            },
            'function_b': {
                'func': lambda az, el, b: b*np.cos(el),
                'params': ['b']
            },
            'function_c': {
                'func': lambda az, el, D: -D*np.cos(az),
                'params': ['D']
            },
            'function_d': {
                'func': lambda az, el, E: E*np.sin(az),
                'params': ['E']
            }}

        }
        
        self.selected_functions = {
            'Az': [self.available_functions['Az'][func_name] for func_name in az_functions],
            'El': [self.available_functions['El'][func_name] for func_name in el_functions]
        }

        self.unique_params = self.get_unique_params()

    def get_unique_params(self):
        unique_az_params = list(set(p for func in self.selected_functions['Az'] for p in func['params']))
        unique_el_params = list(set(p for func in self.selected_functions['El'] for p in func['params']))
        return np.sort(list(set(unique_az_params + unique_el_params)))

    @property
    def nparams(self):
        return len(self.unique_params)
    
    def model_components(self, azimuth, elevation, *params):
        param_dict = dict(zip(self.unique_params, params))

        model_az = sum(func['func'](azimuth, elevation, *[param_dict[p] for p in func['params']])
                       for func in self.selected_functions['Az'])

        model_el = sum(func['func'](azimuth, elevation, *[param_dict[p] for p in func['params']])
                       for func in self.selected_functions['El'])

        return model_az, model_el

    def __call__(self, azimuth, elevation, *params):
        model_az, model_el = self.model_components(azimuth, elevation, *params)
        return model_az, model_el


def update_level1_file(filename, datestr):
    """
    filename : str - name of the level 1 file
    datestr : str - date of the observation in YYMMDD format
    """

    pointing_model = PointingModel()
