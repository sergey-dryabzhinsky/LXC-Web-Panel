'''
Functions for work with LVM2
'''

import subprocess
import os
import stat


def _run(cmd, output=False):
    '''
    To run command easier
    '''
    if output:
        try:
            out = subprocess.check_output('{}'.format(cmd), shell=True)
        except subprocess.CalledProcessError:
            out = False
        return out
    return subprocess.check_call('{}'.format(cmd), shell=True) # returns 0 for True


def is_lvm(blkdev):
    '''
    Check block device - maybe it is logical volume
    '''
    if (os.path.exists(blkdev) and not os.path.isdir(blkdev)):
        if stat.S_ISBLK( os.lstat(blkdev).st_mode ):
            return True
    return False
