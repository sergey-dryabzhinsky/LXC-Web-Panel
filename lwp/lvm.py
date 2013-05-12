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
        if stat.S_ISBLK( os.stat(blkdev).st_mode ):
            return True
    return False


def get_host_usage(vgname = None):
    '''
    Get host machine LVM2 volume groups usage

    @param vgname: LVM2 volume group name
    @type vgname: str

    @return: list - [ {
                        'total': (int) Mb
                        'used': (int) Mb
                        'free': (int) Mb
                        'percent': (int) % of used vg
                    },  ]
    '''
    out = _run("vgdisplay -C --units b", output=True)
    vgs = []
    if out:
        for line in out.split("\n"):
            if line.find("VG") != -1 and line.find("VSize") != -1:
                continue
            sline = line.strip().split()

            if vgname and sline[0] != vgname:
                continue

            item = {
                'name': sline[0],
                'total': int(sline[5].strip("B")) / 1024 / 1024,
                'free': int(sline[6].strip("B")) / 1024 / 1024,
                'percent': 0,
                'used': 0,
                'unit': 'Mb'
            }
            item['used'] = item['total'] - item['free']
            if item['total']:
                item['percent'] = item['used'] * 100 / item['total']

            # Format size
            for unit in ("GB", "TB"):
                if item['used'] > 1000:
                    item["used"] /= 1024
                    item["total"] /= 1024
                    item["free"] /= 1024
                    item["unit"] = unit
                else:
                    break

            vgs.append(item)

    return vgs
