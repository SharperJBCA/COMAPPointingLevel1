#!
#=============#
# Description: Batch update COMAP Level 1 files using PointingCorrection.py #
# Author: SH #
# Date : 2023-08-14
#=============#

import os
import sys  
import numpy as np
from mpi4py import MPI

import PointingCorrection
from tqdm import tqdm 
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if __name__ == "__main__":

    filelist = np.loadtxt(sys.argv[1],dtype=str,ndmin=1)

    idx = np.sort(np.mod(np.arange(filelist.size),size))
    filelist = filelist[idx==rank]

    if rank == 0:
        _filelist = tqdm(filelist)
    else:
        _filelist = filelist

    for filename in _filelist:
        PointingCorrection.reverse_update_level1_file(filename,old_prefix='_191101')
        PointingCorrection.update_level1_file(filename, PointingCorrection.DATESTR_20230814, PointingCorrection.PARAMS_20230814, old_prefix='_191101')

