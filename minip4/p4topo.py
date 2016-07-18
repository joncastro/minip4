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


_DEVICE_ID_PATTERN = re.compile('[^\d*](\d+).*')


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


def get_mac(name):
    """ returns the mac address base of the host name. It use the first number inside the host name

    Args:
        name (str): host name
    """
    id = get_device_id(name)
    if id is not None:
        return convert_int_to_mac(id)


def get_device_id(name):
    """ returns the number inside the given name if exists

    Args:
        name (str): device name
    """
    m = _DEVICE_ID_PATTERN.match(name)
    if m is not None:
        return m.group(1)
    return None


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

    def __init__(self, file, p4src=None, bmv2=None, p4c=None):
        """ create Mininet P4 topology base on given topology yaml file

        Args:
            file (str): file path

        Kwargs:
            p4src (str): default p4 source file
            bmv2 (str): bmv2 base path
            p4c (str): p4c base path
        """

        # create default variables
        self.hosts = {}
        self.switches = {}
        self.links = []
        self.portmap = {}
        self.host_connected_switch = {}
        self.p4_src_json = {}

        self.p4src = p4src
        self.bmv2 = bmv2
        self.p4c = p4c

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

        device_ids = []

        # calculate switch defaults parameters
        sw_defaults = {}
        if 'switch' in self.defaults:
            sw_defaults = self.defaults['switch']

        default_bmv2 = self.bmv2
        if default_bmv2 is None and 'BMV2_PATH' in os.environ:
            default_bmv2 = os.environ['BMV2_PATH']
        if default_bmv2 is None:
            default_bmv2 = '../bmv2'

        default_p4c = self.p4c
        if default_p4c is None and 'P4C_BM_PATH' in os.environ:
            default_p4c = os.environ['P4C_BM_PATH']
        if default_p4c is None:
            default_p4c = '../p4c-bmv2'

        default_p4src = self.p4src
        default_dump = True
        default_port = 22222
        default_verbose = 'info'
        default_commands = None

        if self.bmv2 is None and 'bmv2' in sw_defaults:
            default_bmv2 = sw_defaults['bmv2']

        if self.p4c is None and 'p4c' in sw_defaults:
            default_p4c = sw_defaults['p4c']

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

            if 'bmv2' not in switch:
                switch['bmv2'] = default_bmv2

            if 'sw_path' not in switch:
                switch['sw_path'] = switch['bmv2'] + '/targets/simple_switch/simple_switch'

            if 'cli' not in switch:
                switch['cli'] = switch['bmv2'] + '/tools/runtime_CLI.py'

            if 'p4c' not in switch:
                switch['p4c'] = default_p4c

            if 'compiler' not in switch:
                switch['compiler'] = switch['p4c'] + '/p4c_bm/__main__.py'

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

            if 'id' not in switch or switch['id'] in device_ids:
                device_id = get_device_id(name)
                if device_id is None or device_id in device_ids:
                    if len(device_ids) == 0:
                        device_id = 1
                    else:
                        device_id = max(device_ids) + 1
                    device_ids.append(device_id)
                switch['id'] = device_id

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
            if not os.path.isfile(cli):
                raise ValueError("cli file {} for switch {} not found".format(cli, name))
            if commands is not None and not os.path.isfile(commands):
                raise ValueError("commands file {} for switch {} not found ".format(commands, name))
            if not os.path.isfile(sw_path):
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
            if 'command' not in host:
                continue
            for cmd in host['command']:
                print "host ({}) executing {}".format(name, cmd)
                host.cmd(cmd)

        # execute switch command parameters
        for name in self.switches:
            switch = self.switches[name]
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
