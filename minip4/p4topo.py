import sys
import yaml
import os
import subprocess
import socket
import argparse
import re

from time import sleep

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI

from p4_mininet import P4Switch, P4Host


def convert_mac_to_int(mac):
    """ returns a mac address as an int

    Args:
        mac (str): mac address. Format, FF:FF:FF:FF:FF:FF
    """
    return int('0x' + mac.replace(':', ''), 16)


def convert_int_to_mac(mac):
    """ returns a mac address in int as str. Converts to FF:FF:FF:FF:FF:FF format

    Args:
        mac (str): integer
    """
    mac_to_hex = str(hex(int(mac)))[2:].zfill(12)
    blocks = [mac_to_hex[x:x + 2] for x in xrange(0, len(mac_to_hex), 2)]
    return ':'.join(blocks)

_HOSTS_LIST = [int(0)]


def get_mac(name):
    """ returns the mac address base of the host name. It uses all digits
        inside the host name if exists.

    Args:
        name (str): host name
    """
    id = get_device_id(name)
    if id is None or int(id) in _HOSTS_LIST:
        id = max(_HOSTS_LIST) + 1
    _HOSTS_LIST.append(int(id))

    return convert_int_to_mac(id)


_DEVICE_LIST = [int(0)]


def get_switch_id(name):
    """ returns the switch id base of the host name. It uses all digits
        inside the host name if exists.

    Args:
        name (str): device name
    """
    id = get_device_id(name)
    if id is None or int(id) in _DEVICE_LIST:
        id = max(_DEVICE_LIST) + 1
    _DEVICE_LIST.append(int(id))
    return id


def get_device_id(name):
    """ returns the number using all the digits in the name.

    Args:
        name (str): device name
    """
    value = None
    for s in name:
        if s.isdigit():
            if value is None:
                value = '' + s
            else:
                value = value + s

    return value


def wait_for_port(port, retries=10):
    """ wait until given port is available locally
        for a maximum of given retries (10 by default).

    Args:
        port (int): port number

    Kwargs:
        retries (str): maximum number of retries
    """

    result = -1
    while (result != 0 and retries > 0):
        # test local given port using sockets
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', int(port)))

        # decrement retries and sleep in case of error
        retries = retries - 1
        if result != 0 and retries > 0:
            sleep(1)


class P4Topo(object):
    """ Mininet network based on P4 switches """

    def __init__(self, file, p4src=None):
        """ create Mininet P4 topology base on given topology yaml file

        Args:
            file (str): file path

        Kwargs:
            p4src (str): default p4 source file
        """

        self.p4src = p4src

        # create default variables
        self.hosts = {}
        self.switches = {}
        self.links = []
        self.portmap = {}
        self.host_connected_switch = {}
        self.p4_src_json = {}

        # read given yaml file
        self.props = None
        if (os.path.isfile(file)):
            with open(file, 'r') as f:
                self.props = yaml.load(f)

        if self.props is None:
            raise ValueError("cannot load given topology file {}".format(file))

        # get defaults properties
        self.defaults = self.props['defaults'] if 'defaults' in self.props else None

        # load host/switches/links
        self.__load_hosts()
        self.__load_switches()
        self.__load_links()

    def __load_hosts(self):

        # if hosts are given append to the topology
        if 'host' not in self.props or self.props['host'] is None:
            return

        macs = []

        # calculate host defaults parameters
        host_defaults = {}
        if 'host' in self.defaults:
            host_defaults = self.defaults['host']

        default_gw = None
        default_cmds = []

        if 'gw' in host_defaults:
            default_gw = host_defaults['gw']

        if 'command' in host_defaults:
            default_cmds = host_defaults['command']

        for host in self.props['host']:
            host_name = host['name']
            self.hosts[host_name] = host

            if 'gw' not in host:
                host['gw'] = default_gw
            if 'command' not in host:
                host['command'] = default_cmds
            if 'mac' not in host:
                host['mac'] = get_mac(host_name)
            if host['mac'] is None or convert_mac_to_int(host['mac']) in macs:
                if len(macs) == 0:
                    mac = 1
                else:
                    mac = max(macs) + 1
                host['mac'] = convert_int_to_mac(mac)

    def __load_switches(self):

        # if switches are given append to the topology
        if 'switch' not in self.props or self.props['switch'] is None:
            raise ValueError("switches not found in the topology")

        # calculate switch defaults parameters
        sw_defaults = {}
        if 'switch' in self.defaults:
            sw_defaults = self.defaults['switch']

        default_p4src = self.p4src
        default_dump = True
        default_port = 22222
        default_verbose = 'info'
        default_commands = None

        if default_p4src is None and 'p4src' in sw_defaults:
            default_p4src = sw_defaults['p4src']

        if 'dump' in sw_defaults:
            default_dump = sw_defaults['dump']

        if 'port' in sw_defaults:
            default_port = sw_defaults['port']

        if 'commands' in sw_defaults:
            default_commands = sw_defaults['commands']

        if 'verbose' in sw_defaults:
            default_verbose = sw_defaults['verbose']

        for switch in self.props['switch']:
            name = switch['name']
            self.switches[name] = switch

            if 'sw_path' not in switch:
                switch['sw_path'] = 'simple_switch'

            if 'cli' not in switch:
                switch['cli'] = 'runtime_CLI.py'

            if 'compiler' not in switch:
                switch['compiler'] = 'p4c-bmv2'

            if 'p4src' not in switch:
                switch['p4src'] = default_p4src
            switch['p4json'] = switch['p4src'] + '.json'

            if 'port' not in switch:
                switch['port'] = default_port

            if 'dump' not in switch:
                switch['dump'] = default_dump

            if 'commands' not in switch:
                commands = 'commands-{}.txt'.format(name)
                switch['commands'] = commands if os.path.isfile(commands) else default_commands

            if 'verbose' not in switch:
                switch['verbose'] = default_verbose

            if 'id' not in switch:
                switch['id'] = get_switch_id(name)

            default_port = default_port + 1

    def __load_links(self):
        if 'link' not in self.props or self.props['link'] is None:
            return

        self.links = self.props['link']

        ports = {}

        for link in self.links:
            src = link['source']
            if src not in ports:
                ports[src] = 1
            src_port = ports[src]
            ports[src] = ports[src] + 1

            dst = link['destination']
            if dst not in ports:
                ports[dst] = 1
            dst_port = ports[dst]
            ports[dst] = ports[dst] + 1

            if src not in self.portmap:
                self.portmap[src] = {}
            self.portmap[src][dst] = src_port

            if dst not in self.portmap:
                self.portmap[dst] = {}
            self.portmap[dst][src] = dst_port

            # skip connections between hosts
            if src in self.hosts and dst in self.hosts:
                continue

            # save the connected switch by host
            if (src in self.hosts and dst in self.switches):
                self.host_connected_switch[src] = dst
            elif (dst in self.hosts and src in self.switches):
                self.host_connected_switch[dst] = src

    def start(self):

        # ensure all path exists
        for name in self.switches:
            switch = self.switches[name]

            p4src = switch['p4src']
            sw_path = switch['sw_path']
            compiler = switch['compiler']
            cli = switch['cli']
            commands = switch['commands']

            # ensure all paths exit
            if p4src is None:
                raise ValueError("p4 source file for switch {} not provided".format(name))
            if not os.path.isfile(p4src):
                raise ValueError("p4 source file {} for switch {} not found".format(p4src, name))
            if not which(cli):
                raise ValueError("cli command {} for switch {} not found".format(cli, name))
            if commands is not None and not os.path.isfile(commands):
                raise ValueError("commands file {} for switch {} not found ".format(commands, name))
            if not which(sw_path):
                raise ValueError("switch path {} for switch {} not found ".format(sw_path, name))

            if p4src not in self.p4_src_json:
                print "compiling source {}".format(p4src)
                cmd = [switch['compiler'], p4src, "--json", switch['p4json']]
                print ' '.join(cmd)
                self.p4_src_json[p4src] = switch['p4json']
                try:
                    output = subprocess.check_output(cmd)
                    print output
                except subprocess.CalledProcessError as e:
                    print e
                    print e.output
                    raise e

        # create repo
        topo = Topo()

        for name in self.hosts:
            host = self.hosts[name]
            default_route = None
            if host['gw'] is not None:
                default_route = 'via ' + host['gw']
            topo.addHost(
                name,
                ip=host['ip'],
                mac=host['mac'],
                defaultRoute=default_route)

        for name in self.switches:
            switch = self.switches[name]
            topo.addSwitch(
                name,
                sw_path=switch['sw_path'],
                json_path=switch['p4json'],
                thrift_port=switch['port'],
                verbose=switch['verbose'],
                pcap_dump=switch['dump'],
                device_id=int(switch['id']))

        for link in self.links:
            topo.addLink(link['source'], link['destination'])

        net = Mininet(topo=topo,
                      host=P4Host,
                      switch=P4Switch,
                      controller=None)

        net.start()

        # execute host command parameters
        for name in self.hosts:
            host = self.hosts[name]

            # p4_mininet P4Host rename the interface to eth0
            # see: self.defaultIntf().rename("eth0") on P4Host
            # The host lost the gw after the interface is renamed
            # so we execute following command to ensure provided
            # gw is configured in the host
            if 'gw' in host:
                net.get(name).cmd("route add default gw {}".format(host['gw']))

            if 'command' not in host:
                continue
            for cmd in host['command']:
                print "host ({}) executing {}".format(name, cmd)
                net.get(name).cmd(cmd)

        # execute switch command parameters
        for name in self.switches:
            switch = self.switches[name]
            if switch['commands'] is None:
                continue
            cmd = [switch['cli'],
                   "--json", switch['p4json'],
                   "--thrift-port", str(switch['port'])]
            print ' '.join(cmd)
            with open(switch['commands'], "r") as f:
                wait_for_port(switch['port'])
                try:
                    output = subprocess.check_output(cmd, stdin=f)
                    print output
                except subprocess.CalledProcessError as e:
                    print e
                    print e.output

        CLI(net)
        net.stop()



# check if executable exits
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None
