import numpy as np
from matplotlib import pyplot
import h5py 
import os 
import sys 
from Tools import Coordinates

# 1) Function that opens the level 1 file
# 2) Function that contains the pointing model 
# 3) Check if pixel_pointing exists in the level 1 file, if so rename it to pixel_pointing_191101
# 4) Create a new pixel_pointing group in the level 1 file
# 5) Apply correction to old az/el data and write to the new pixel_pointing group
# 6) Calculate updated ra/dec coordinates and write to the new pixel_pointing group
# 7) Add an attribute to pixel_pointing group of: .attrs['azel\_pointing_model\_YYMMDD'] = [$A$, $B$,...]

# A,B,C,D,E,a,b
PARAMS_20230814 = [-0.04008, 0.00845, 0.03503, -0.00592, -0.00960,0.00655,-0.01208]
DATESTR_20230814 = '20230814'

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


def update_level1_file(filename, datestr, params=PARAMS_20230814,old_prefix='_191101'):
    """
    filename : str - name of the level 1 file
    datestr : str - date of the observation in YYMMDD format
    params : list - list of parameters for the pointing model
    """

    pointing_model = PointingModel()

    h = h5py.File(filename, 'r+')

    grp = h['spectrometer'] 
    # Read in az/el/mjd 
    az = grp['pixel_pointing/pixel_az'][...]
    el = grp['pixel_pointing/pixel_el'][...]
    mjd = grp['MJD'][:]

    # Apply pointing model to az/el
    for i in range(az.shape[0]):
        model_az, model_el = pointing_model(az[i], el[i], *params)
        el[i] = el[i] + model_el
        az[i] = az[i] + model_az/np.cos(el[i]*np.pi/180.) 

    # Update RA/Dec 
    ra = np.zeros(az.shape)
    dec = np.zeros(az.shape)
    for i in range(az.shape[0]):
        ra[i],dec[i] = Coordinates.h2e_full(az[i],el[i], mjd, Coordinates.comap_longitude, Coordinates.comap_latitude)

    # Check if the pixel_pointing group exists
    if 'pixel_pointing' in grp:
        # Rename the group to pixel_pointing_191101
        grp.move('pixel_pointing', f'pixel_pointing_191101')

    # Create a new pixel_pointing group
    grp.create_group('pixel_pointing')

    # Now update the pointing data
    grp.create_dataset('pixel_pointing/pixel_az', data=az)
    grp.create_dataset('pixel_pointing/pixel_el', data=el)
    grp.create_dataset('pixel_pointing/pixel_ra', data=ra)
    grp.create_dataset('pixel_pointing/pixel_dec', data=dec)
    if 'pixel_pointing_191101/pixel_xoffset' in grp:
        grp.create_dataset('pixel_pointing/pixel_xoffset', data=grp['pixel_pointing_191101/pixel_xoffset'][...])
        grp.create_dataset('pixel_pointing/pixel_yoffset', data=grp['pixel_pointing_191101/pixel_yoffset'][...])

    grp['pixel_pointing'].attrs['azel_pointing_model_'+datestr] = params

    h.close()

def reverse_update_level1_file(filename, old_prefix='_191101'):
    h = h5py.File(filename, 'r+')
    grp = h['spectrometer']
    if f'pixel_pointing{old_prefix}' in grp:
        del grp[f'pixel_pointing']
        grp.move(f'pixel_pointing{old_prefix}', 'pixel_pointing')
    h.close()

if __name__ == "__main__":
    reverse_update_level1_file(sys.argv[1])
    update_level1_file(sys.argv[1], DATESTR_20230814)