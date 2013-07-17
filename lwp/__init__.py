import sys
sys.path.append('../')
from lxclite import exists, stopped, ContainerDoesntExists
import subprocess
import os
import platform
import time
import urllib2
import ConfigParser
import re


class CalledProcessError(Exception):
    pass

cgroup = {}
cgroup['type'] = 'lxc.network.type'
cgroup['link'] = 'lxc.network.link'
cgroup['flags'] = 'lxc.network.flags'
cgroup['hwaddr'] = 'lxc.network.hwaddr'
cgroup['rootfs'] = 'lxc.rootfs'
cgroup['utsname'] = 'lxc.utsname'
cgroup['arch'] = 'lxc.arch'
cgroup['ipv4'] = 'lxc.network.ipv4'
cgroup['memlimit'] = 'lxc.cgroup.memory.limit_in_bytes'
cgroup['swlimit'] = 'lxc.cgroup.memory.memsw.limit_in_bytes'
cgroup['cpus'] = 'lxc.cgroup.cpuset.cpus'
cgroup['shares'] = 'lxc.cgroup.cpu.shares'
cgroup['deny'] = 'lxc.cgroup.devices.deny'
cgroup['allow'] = 'lxc.cgroup.devices.allow'

class FakeSection(object):
    
    def __init__(self, fp):
        self.fp = fp
        self.sechead = '[DEFAULT]\n'

    def readline(self):
        if self.sechead:
            try:
                return self.sechead
            finally:
                self.sechead = None
        else:
            return self.fp.readline()

def DelSection(filename=None):
    if filename:
        load = open(filename, 'r')
        read = load.readlines()
        load.close()
        i = 0
        while i < len(read):
            if '[DEFAULT]' in read[i]:
                del read[i]
                break
        load = open(filename, 'w')
        load.writelines(read) 
        load.close()

def file_exist(filename):
    '''
    checks if a given file exist or not
    '''
    try:
        with open(filename) as f:
            f.close()
            return True
    except IOError:
        return False


def ls_auto():
    '''
    returns a list of autostart containers
    '''
    try:
        auto_list = os.listdir('/etc/lxc/auto/')
        auto_list.sort()
    except OSError:
        auto_list = []

    prio_list = {}
    for name in auto_list:
        dig = name.split("-")[0]
        if dig.isdigit():
            prio = int(dig)
            name = "-".join(name.split("-")[1:])
            name = name.replace(".conf", "")
        else:
            prio = ''
        prio_list[ name ] = prio
    return prio_list


def memory_usage(name):
    '''
    returns memory usage in MB
    '''
    if not exists(name):
        raise ContainerDoesntExists("The container (%s) does not exist!" % name)
    if name in stopped():
        return 0
    cmd = ['lxc-cgroup -n %s memory.usage_in_bytes' % name]
    try:
        out = subprocess.check_output(cmd, shell=True).splitlines()
    except:
        return 0
    return int(out[0])/1024/1024


def memory_usage_cgroup(name):
    '''
    returns memory usage in MB
    use cgroup sys fs files
    '''
    cont_usage_file = "/sys/fs/cgroup/memory/lxc/%s/memory.usage_in_bytes" % name
    if not os.path.isfile(cont_usage_file):
        return 0

    f = open(cont_usage_file, 'r')
    usage = f.readline().strip()
    f.close()

    return int(usage)/1024/1024


def max_memory_usage(name):
    if not exists(name):
        raise ContainerDoesntExists("The container (%s) does not exist!" % name)
    if name in stopped():
        return 0
    cmd = ['lxc-cgroup -n %s memory.limit_in_bytes' % name]
    try:
        out = subprocess.check_output(cmd, shell=True).splitlines()
    except:
        return 0
    host = host_memory_usage()
    limit = int(out[0])/1024/1024
    if limit > host["total"]:
        limit = host["total"]
    return limit


def max_memory_usage_cgroup(name):
    '''
    returns memory usage in MB
    use cgroup sys fs files
    '''
    cont_usage_file = "/sys/fs/cgroup/memory/lxc/%s/memory.limit_in_bytes" % name
    if not os.path.isfile(cont_usage_file):
        return 0

    f = open(cont_usage_file, 'r')
    usage = f.readline().strip()
    f.close()

    host = host_memory_usage()
    limit = int(usage)/1024/1024
    if limit > host["total"]:
        limit = host["total"]
    return limit


def real_ipv4_container(name):
    if name in stopped():
        return ''
    cmd = ["lxc-attach --name %s -- ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'" % name]
    try:
        out = subprocess.check_output(cmd, shell=True)
    except:
        return ''
    return out


def container_cpu_percent(name):
    '''
    returns CPU usage in percent
    '''
    if name in stopped():
        return '0'

    cmd = ["lxc-ps --name %s -- u | awk 'BEGIN{s=0.0}{s+=$4}END{print s}'" % name]
    try:
        out = subprocess.check_output(cmd, shell=True).strip()
    except:
        return '0'
    return out

def container_cpu_percent_cgroup(name):
    '''
    returns CPU usage in percent
    '''
    cont_usage_file = "/sys/fs/cgroup/cpuacct/lxc/%s/cpuacct.usage" % name
    if not os.path.isfile(cont_usage_file):
        return '-1'

    f = open(cont_usage_file, 'r')
    line = f.readline().strip()
    prev_cont_usage_ns = float(line) * 10**-9
    f.close()

    time.sleep(0.1)

    f = open(cont_usage_file, 'r')
    line = f.readline().strip()
    current_cont_usage_ns = float(line) * 10**-9
    f.close()

    percent = 100 * (current_cont_usage_ns - prev_cont_usage_ns) / 0.1
    return str('%.1f' % percent)


def containers_cpu_percent_cgroup(containers):
    '''
    returns CPU usage in percent for all cantainers
    '''

    prev_usage = {}

    result = {}

    for name in containers:
        name = name.replace(' (auto)', '')

        cont_usage_file = "/sys/fs/cgroup/cpuacct/lxc/%s/cpuacct.usage" % name
        if not os.path.isfile(cont_usage_file):
            prev_usage[ name ] = (0, time.time(),)
            continue

        f = open(cont_usage_file, 'r')
        line = f.readline().strip()
        prev_usage[ name ] = (float(line) * 10**-9, time.time(),)
        f.close()

    time.sleep(0.1)

    for name in containers:
        name = name.replace(' (auto)', '')

        cont_usage_file = "/sys/fs/cgroup/cpuacct/lxc/%s/cpuacct.usage" % name
        if not os.path.isfile(cont_usage_file):
            result[name] = {
                "name": name,
                "cpu": "0"
            }
            continue

        f = open(cont_usage_file, 'r')
        line = f.readline().strip()
        current_usage_ns = float(line) * 10**-9
        f.close()

        current_time = time.time()

        prev_usage_ns, prev_time = prev_usage[ name ]

        percent = 100 * (current_usage_ns - prev_usage_ns) / (current_time - prev_time)

        result[name] = {
            "name": name,
            "cpu": "%0.1f" % percent
        }

    return result


def get_template_help(name):
    cmd = ["lxc-create -t %s -h" % name]
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return out
    except Exception as e:
        return unicode(e.output)


def host_memory_usage():
    '''
    returns a dict of host memory usage values
                    {'percent': int((used/total)*100),
                    'percent_cached':int((cached/total)*100),
                    'swap': int(swap/1024),
                    'used': int(used/1024),
                    'total': int(total/1024)}
    '''
    out = open('/proc/meminfo')
    total = free = buffers = cached = swap = 0
    for line in out:
        if 'MemTotal:' == line.split()[0]:
            split = line.split()
            total = float(split[1])
        if 'MemFree:' == line.split()[0]:
            split = line.split()
            free = float(split[1])
        if 'Buffers:' == line.split()[0]:
            split = line.split()
            buffers = float(split[1])
        if 'Cached:' == line.split()[0]:
            split = line.split()
            cached = float(split[1])
        if 'SwapTotal:' == line.split()[0]:
            split = line.split()
            swap = float(split[1])
    out.close()
    used = (total - (free + buffers + cached))
    return {'percent': int(used*100/total),
            'percent_cached': int(cached*100/total),
            'swap': int(swap/1024),
            'used': int(used/1024),
            'total': int(total/1024)}


def host_cpu_percent():
    '''
    returns CPU usage in percent
    '''
    f = open('/proc/stat', 'r')
    line = f.readlines()[0]
    data = line.split()
    previdle = float(data[4])
    prevtotal = float(data[1]) + float(data[2]) + float(data[3]) + float(data[4])
    f.close()
    time.sleep(0.1)
    f = open('/proc/stat', 'r')
    line = f.readlines()[0]
    data = line.split()
    idle = float(data[4])
    total = float(data[1]) + float(data[2]) + float(data[3]) + float(data[4])
    f.close()
    intervaltotal = total - prevtotal
    percent = 100 * (intervaltotal - (idle - previdle)) / intervaltotal
    return str('%.1f' % percent)


def host_disk_usage(partition=None):
    '''
    returns a dict of disk usage values
                    {'total': usage[1],
                    'used': usage[2],
                    'free': usage[3],
                    'percent': usage[4]}
    '''
    if not partition:
        partition = '/'
    usage = subprocess.check_output(['df -h %s' % partition], shell=True).split('\n')[1].split()
    return {'total': usage[1],
            'used': usage[2],
            'free': usage[3],
            'percent': usage[4]}


def host_lvm_usage(vgname=None):
    '''
    returns a list or dict of lvm usage values
                    [{'total': usage[1],
                    'used': usage[2],
                    'free': usage[3],
                    'percent': usage[4],
                    'unit': Mb
                    },]
    '''
    import lvm
    return {'vgs':lvm.get_host_usage(vgname)}


def host_uptime():
    '''
    returns a dict of the system uptime
            {'day': days,
            'time': '%d:%02d' % (hours,minutes)}
    '''
    f = open('/proc/uptime')
    uptime = int(f.readlines()[0].split('.')[0])
    minutes = uptime / 60 % 60
    hours = uptime / 60 / 60 % 24
    days = uptime / 60 / 60 / 24
    f.close()
    return {'day': days,
            'time': '%d:%02d' % (hours, minutes)}


def check_ubuntu():
    '''
    return the System version
    '''
    dist = '%s %s' % (platform.linux_distribution()[0], platform.linux_distribution()[1])
    if dist == 'Ubuntu 12.04':
        return dist
    elif dist == 'Ubuntu 12.10':
        return dist
    elif dist == 'Ubuntu 13.04':
        return dist
    return 'unknown'


def get_templates_list():
    '''
    returns a sorted lxc templates list
    '''
    templates = []
    path = None

    templates_path = '/usr/share/lxc/templates'
    if os.path.exists(templates_path) and os.path.isdir(templates_path):
        path = os.listdir(templates_path)
    else:
        templates_path = '/usr/lib/lxc/templates'
        if os.path.exists(templates_path) and os.path.isdir(templates_path):
            path = os.listdir(templates_path)

    if path:
        for line in path:
                templates.append(line.replace('lxc-', ''))

    return sorted(templates)


def check_version(url=None):
    '''
    returns latest LWP version (dict with current and latest)
    '''
    f = open('version')
    current = f.read()
    f.close()
    if not url:
        url = 'http://lxc-webpanel.github.com/version'
    latest = urllib2.urlopen(url).read()
    return {'current': current,
            'latest': latest}


def get_net_settings():
    '''
    returns a dict of all known settings for LXC networking
    '''
    filename = '/etc/default/lxc'
    if not file_exist(filename):
        return False
    config = ConfigParser.SafeConfigParser()
    cfg = {}
    config.readfp(FakeSection(open(filename)))
    cfg['use'] = config.get('DEFAULT', 'USE_LXC_BRIDGE').strip('"')
    cfg['bridge'] = config.get('DEFAULT', 'LXC_BRIDGE').strip('"')
    cfg['address'] = config.get('DEFAULT', 'LXC_ADDR').strip('"')
    cfg['netmask'] = config.get('DEFAULT', 'LXC_NETMASK').strip('"')
    cfg['network'] = config.get('DEFAULT', 'LXC_NETWORK').strip('"')
    cfg['range'] = config.get('DEFAULT', 'LXC_DHCP_RANGE').strip('"')
    cfg['max'] = config.get('DEFAULT', 'LXC_DHCP_MAX').strip('"')
    return cfg


def get_container_settings(name):
    '''
    returns a dict of all utils settings for a container
    '''
    filename = '/var/lib/lxc/%s/config' % name
    if not file_exist(filename):
        return False
    config = ConfigParser.SafeConfigParser()
    cfg = {}
    config.readfp(FakeSection(open(filename)))
    try:
        cfg['type'] = config.get('DEFAULT', cgroup['type'])
    except ConfigParser.NoOptionError:
        cfg['type'] = ''
    try:
        cfg['link'] = config.get('DEFAULT', cgroup['link'])
    except ConfigParser.NoOptionError:
        cfg['link'] = ''
    try:
        cfg['flags'] = config.get('DEFAULT', cgroup['flags'])
    except ConfigParser.NoOptionError:
        cfg['flags'] = ''
    try:
        cfg['hwaddr'] = config.get('DEFAULT', cgroup['hwaddr'])
    except ConfigParser.NoOptionError:
        cfg['hwaddr'] = ''
    try:
        cfg['rootfs'] = config.get('DEFAULT', cgroup['rootfs'])
    except ConfigParser.NoOptionError:
        cfg['rootfs'] = ''
    try:
        cfg['utsname'] = config.get('DEFAULT', cgroup['utsname'])
    except ConfigParser.NoOptionError:
        cfg['utsname'] = ''
    try:
        cfg['arch'] = config.get('DEFAULT', cgroup['arch'])
    except ConfigParser.NoOptionError:
        cfg['arch'] = ''
    try:
        cfg['ipv4_real'] = False
        cfg['ipv4'] = config.get('DEFAULT', cgroup['ipv4'])
    except ConfigParser.NoOptionError:
        cfg['ipv4'] = real_ipv4_container(name)
        cfg['ipv4_real'] = True
    try:
        value = config.get('DEFAULT', cgroup['memlimit'])
        cfg['memlimit'] = re.sub(r'[a-zA-Z]', '', config.get('DEFAULT', cgroup['memlimit']))
        if value.find("M") == -1 and value.isdigit():
            cfg['memlimit'] = int(cfg['memlimit'])
            cfg['memlimit'] /= 1024*1024
    except ConfigParser.NoOptionError:
        cfg['memlimit'] = ''
    try:
        value = config.get('DEFAULT', cgroup['swlimit'])
        cfg['swlimit'] = re.sub(r'[a-zA-Z]', '', config.get('DEFAULT', cgroup['swlimit']))
        if value.find("M") == -1 and value.isdigit():
            cfg['swlimit'] = int(cfg['swlimit'])
            cfg['swlimit'] /= 1024*1024
    except ConfigParser.NoOptionError:
        cfg['swlimit'] = ''
    try:
        cfg['cpus'] = config.get('DEFAULT', cgroup['cpus'])
    except ConfigParser.NoOptionError:
        cfg['cpus'] = ''
    try:
        cfg['shares'] = config.get('DEFAULT', cgroup['shares'])
    except ConfigParser.NoOptionError:
        cfg['shares'] = ''

    auto_list = ls_auto()
    if name in auto_list:
        cfg['auto'] = True
        cfg['priority'] = auto_list[ name ]
    else:
        cfg['auto'] = False
        cfg['priority'] = ''

    return cfg


def push_net_value(key, value, filename='/etc/default/lxc'):
    '''
    replace a var in the lxc-net config file
    '''
    if filename:
        config = ConfigParser.RawConfigParser()
        config.readfp(FakeSection(open(filename)))
        if not value:
            config.remove_option('DEFAULT', key)
        else:
            config.set('DEFAULT', key, value)

        with open(filename, 'wb') as configfile:
            config.write(configfile)

        DelSection(filename=filename)

        load = open(filename, 'r')
        read = load.readlines()
        load.close()
        i = 0
        while i < len(read):
            if ' = ' in read[i]:
                split = read[i].split(' = ')
                split[1] = split[1].strip('\n')
                if '\"' in split[1]:
                    read[i] = '%s=%s\n' % (split[0].upper(), split[1])
                else:
                    read[i] = '%s=\"%s\"\n' % (split[0].upper(), split[1])
            i += 1
        load = open(filename, 'w')
        load.writelines(read)
        load.close()


def push_config_value(key, value, container=None):
    '''
    replace a var in a container config file
    '''

    def save_cgroup_devices(filename=None):
        '''
        returns multiple values (lxc.cgroup.devices.deny and lxc.cgroup.devices.allow) in a list.
        because ConfigParser cannot make this...
        '''
        if filename:
            values = []
            i = 0

            load = open(filename, 'r')
            read = load.readlines()
            load.close()

            while i < len(read):
                if not read[i].startswith('#') and re.match('lxc.cgroup.devices.deny|lxc.cgroup.devices.allow', read[i]):
                    values.append(read[i])
                i += 1
            return values

    if container:
        filename = '/var/lib/lxc/%s/config' % container
        save = save_cgroup_devices(filename=filename)

        config = ConfigParser.RawConfigParser()
        config.readfp(FakeSection(open(filename)))
        if not value:
            config.remove_option('DEFAULT', key)
        elif key == cgroup['memlimit'] or key == cgroup['swlimit'] and value != False:
            config.set('DEFAULT', key, '%sM' % value)
        else:
            config.set('DEFAULT', key, value)

        # Bugfix (can't duplicate keys with config parser)
        if config.has_option('DEFAULT', cgroup['deny']) or config.has_option('DEFAULT', cgroup['allow']):
            config.remove_option('DEFAULT', cgroup['deny'])
            config.remove_option('DEFAULT', cgroup['allow'])

        with open(filename, 'wb') as configfile:
            config.write(configfile)

        DelSection(filename=filename)

        with open(filename, "a") as configfile:
            configfile.writelines(save)


def net_restart():
    '''
    restarts LXC networking
    '''
    cmd = ['/usr/sbin/service lxc-net restart']
    try:
        subprocess.check_call(cmd, shell=True)
        return 0
    except CalledProcessError:
        return 1


def get_fake_filesystem_usage(container):
    '''
    Returns container root filesystem fake  usage
    '''
    result = {
        'total': 2,
        'used': 1,
        'free': 1,
        'unit' : 'MB',
        'percent': '50'
    }
    return result


def get_filesystem_usage(container, check_running=False):
    '''
    Returns container root filesystem current usage
    Only for running containers
    '''
    result = {
        'total': 0,
        'used': 0,
        'free': 0,
        'percent': '0'
    }
    if check_running and container in stopped():
        return result

    cmd = ["lxc-attach --name %s -- df -h /" % container]
    done = False
    try:
        usage = subprocess.check_output(cmd, shell=True).split('\n')[1].split()
        result = {'total': usage[1],
                'used': usage[2],
                'free': usage[3],
                'percent': usage[4].strip('%')}
        done = True
    except Exception as e:
        pass

    if not done:
        try:
            import lvm
            import fs

            filename = '/var/lib/lxc/%s/config' % container

            config = ConfigParser.RawConfigParser()
            config.readfp(FakeSection(open(filename)))

            try:
                rootfs = config.get('DEFAULT', cgroup['rootfs'])
            except ConfigParser.NoOptionError:
                rootfs = ''

            if rootfs:
                if lvm.is_lvm(rootfs):
                    result.update( fs.get_usage(rootfs) )
                else:
                    # Simulate lxc-attach is rootfs is directory
                    cmd = ["df -h %s" % rootfs]
                    usage = subprocess.check_output(cmd, shell=True).split('\n')[1].split()
                    result = {'total': usage[1],
                            'used': usage[2],
                            'free': usage[3],
                            'percent': usage[4].strip('%')}
        except Exception as e:
            pass

    return result


def get_template_options(template):
    '''
    Get lxc template options: arch & releases
    '''
    result = {
        "arch" : [],
        "releases" : [],
        "system" : {
            "arch" : platform.machine(),
            "release" : platform.linux_distribution()[2],
        }
    }

    # XXX: some distros arch not equal to system arch...
    # Dunno what to do, maybe aliases in templates.conf...
    if result["system"]["arch"] == "x86_64":
        if platform.linux_distribution()[0] in ('Debian', 'Ubuntu'):
            result["system"]["arch"] = 'amd64'

    if not os.path.isfile('templates.conf'):
        return result

    config = ConfigParser.SafeConfigParser(allow_no_value=True)
    config.readfp(open('templates.conf'))

    if config.has_section(template):
        if config.has_option(template, 'arch'):
            result['arch'].extend( config.get(template, 'arch').split(',') )
        if config.has_option(template, 'releases'):
            result['releases'].extend( config.get(template, 'releases').split(',') )
    elif config.has_section('default'):
        if config.has_option('default', 'arch'):
            result['arch'].extend( config.get('default', 'arch').split(',') )
        if config.has_option('default', 'releases'):
            result['releases'].extend( config.get('default', 'releases').split(',') )


    return result
