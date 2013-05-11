'''
Functions for work with filesystems
'''

import subprocess
import os

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


def get_type(blkdev):
    '''
    Try to get filesystem type on block device
    '''
    fsType = None
    out = _run("blkid %s" % blkdev, output=True)
    if out:
        for chunk in out.split():
            if chunk.startswith("TYPE="):
                fsType = chunk.split("=").strip()
    return fsType


def get_usage_ext234(blkdev):
    '''
    Get filesystem usage in MB
    '''
    result = {
        'total': 0,
        'used': 0,
        'free': 0,
        'percent': 0
    }
    out = _run("tune2fs -l %s" % blkdev, output=True)
    if out:
        block_count = 0
        block_free = 0
        block_size = 0
        for line in out.split("\n"):
            if line.startswith("Block count:"):
                block_count = int(line.split(":")[1].strip())
            if line.startswith("Block size:"):
                block_size = int(line.split(":")[1].strip())
            if line.startswith("Free blocks:"):
                block_free = int(line.split(":")[1].strip())

        result['total'] = block_count * block_size / 1024 / 1024
        result['free'] = block_free * block_size / 1024 / 1024
        result['used'] = result['total'] - result['free']
        result['percent'] = result['used'] * 100 / result['total']
    return result


def get_usage(blkdev):
    result = {
        'total': 0,
        'used': 0,
        'free': 0,
        'percent': 0
    }
    fsType = get_type(blkdev)
    if fsType in ("ext2", "ext3", "ext4"):
        result = get_usage_ext234(blkdev)

    return result
