import subprocess
import os

# LXC Python Library
# for compatibility with LXC 1.0+
# on Ubuntu 15.10/16.04/+ Debian 8+ / Proxmox 4

# Author: Sergey Dryabzhinsky
# Contact: sergey.dryabzhinsky@gmail.com

# Orignika work LXC Lite for 0.9
# Author: Elie Deloumeau
# Contact: elie@deloumeau.fr

# The MIT License (MIT)
# Copyright (c) 2013 Elie Deloumeau
# Copyright (c) 2016 Sergey Dryabzhinsky

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

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

class ContainerAlreadyExists(Exception): pass
class ContainerDoesntExists(Exception): pass
class ContainerAlreadyRunning(Exception): pass
class ContainerNotRunning(Exception): pass


def version():
    command = 'lxc-info --version'
    raw = _run(command, True)
    v = [ int(d) for d in raw.split('.') ]
    return v


def exists(container):
    '''
    Check if container exists
    '''
    if container in ls(): return True
    return False


def create(container, template='ubuntu', storage=None, xargs=None):
    '''
    Create a container (without all options)
    Default template: Ubuntu
    '''
    if exists(container): raise ContainerAlreadyExists('Container {} already created!'.format(container))

    command = 'lxc-create -n {}'.format(container)
    command += ' -t {}'.format(template)
    if storage: command += ' -B {}'.format(storage)
    if xargs: command += ' -- {}'.format(xargs)
    return _run(command)

def cgroup(container, key, value):
    if not exists(container): raise ContainerDoesntExists('Container {} does not exist!'.format(container))
    key = key.replace('lxc.cgroup.', '')
    command = 'lxc-cgroup -n {} {} {}'.format(container, key, value)
    return _run(command)


def clone(orig=None, new=None, snapshot=False, storage=None):
    '''
    Clone a container (without all options)
    '''
    if orig and new:
        if exists(new): raise ContainerAlreadyExists('Container {} already exist!'.format(new))

        command = 'lxc-clone -o {} -n {}'.format(orig, new)
        if snapshot: command += ' -s'
        if storage: command += ' -B {}'.format(storage)
        return _run(command)


def info(container):
    '''
    Output changed
    Name: <name>
    STATE: <state>
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exist!'.format(container))

    result = {'state':'Unknown','pid':-1,'ip':'0.0.0.0'}

    output = _run('lxc-info -s -n {}'.format(container), output=True)
    if output:
        output = output.splitlines()
        result['state'] = output[0].split()[1]

    output = _run('lxc-info -p -n {}'.format(container), output=True)
    if output:
        output = output.splitlines()
        result['pid'] = output[0].split()[1]

    output = _run('lxc-info -i -n {}'.format(container), output=True)
    if output:
        output = output.splitlines()
        result['ip'] = output[0].split()[1]

    return result


def ls():
    '''
    List containers directory

    Note: Directory mode for Ubuntu 12/13 compatibility
    '''
    try: ct_list = os.listdir('/var/lib/lxc/')
    except OSError: ct_list = []
    return sorted(ct_list)


def listx():
    '''
    List all containers with status (Running, Frozen or Stopped) in a dict
    Same as lxc-list or lxc-ls --fancy (0.9)
    '''
    stopped = []
    frozen = []
    running = []

    vms = ls()

    for vm in vms:

        i = info(vm)

        if i['state'] == 'RUNNING':
            running.append(vm)
        elif i['state'] == 'FROZEN':
            frozen.append(vm)
        elif i['state'] == 'STOPPED':
            stopped.append(vm)

    return {'RUNNING': running,
            'FROZEN': frozen,
            'STOPPED': stopped}


def running():
    return listx()['RUNNING']


def frozen():
    return listx()['FROZEN']


def stopped():
    return listx()['STOPPED']


def start(container):
    '''
    Starts a container
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exists!'.format(container))
    if container in running(): raise ContainerAlreadyRunning('Container {} is already running!'.format(container))
    return _run('lxc-start -dn {}'.format(container))


def stop(container):
    '''
    Stops a container
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exists!'.format(container))
    if container in stopped(): raise ContainerNotRunning('Container {} is not running!'.format(container))
    return _run('lxc-stop -n {}'.format(container))


def shutdown(container):
    '''
    Stops a container nicely
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exists!'.format(container))
    if container in stopped(): raise ContainerNotRunning('Container {} is not running!'.format(container))
    return _run('lxc-shutdown -n {}'.format(container))


def freeze(container):
    '''
    Freezes a container
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exists!'.format(container))
    if not container in running(): raise ContainerNotRunning('Container {} is not running!'.format(container))
    return _run('lxc-freeze -n {}'.format(container))


def unfreeze(container):
    '''
    Unfreezes a container
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exists!'.format(container))
    if not container in frozen(): raise ContainerNotRunning('Container {} is not frozen!'.format(container))
    return _run('lxc-unfreeze -n {}'.format(container))


def destroy(container):
    '''
    Destroys a container
    '''
    if not exists(container): raise ContainerDoesntExists('Container {} does not exists!'.format(container))
    return _run('lxc-destroy -n {}'.format(container))


def checkconfig():
    '''
    Returns the output of lxc-checkconfig (colors cleared)
    '''
    out = _run('lxc-checkconfig', output=True)
    if out: return out.replace('[1;32m', '').replace('[1;33m', '').replace('[0;39m', '').replace('[1;32m', '').replace('\x1b', '').replace(': ', ':').split('\n')
    return out
