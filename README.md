# MiniP4

MiniP4 is a python utility to quickly create a Mininet network using [P4](https://github.com/p4lang) switches.

- [Install](#install)
- [Usage](#usage)
- [Topology YAML](#topology-yaml)

## Install

### From source

```
git clone https://github.com/p4kide/minip4
cd minip4
sudo python setup.py install
```

### Dependencies

The dependencies to run MiniP4 are

- [Mininet](https://github.com/mininet)

```
git clone https://github.com/mininet/mininet.git
cd mininet
sudo python setup.py install
git checkout tags/2.2.1
cd ..
sed -i 's/git:\/\/openflowswitch.org\/openflow.git/https:\/\/github.com\/mininet\/openflow.git/g' mininet/util/install.sh
sed -i 's/git:\/\/gitosis.stanford.edu\/oflops.git/https:\/\/github.com\/mininet\/oflops.git/g' mininet/util/install.sh
# Mininet is installed with -n to avoid installing unnecessary openflow dependencies
mininet/util/install.sh -n
```

- [p4c-bm](https://github.com/p4lang/p4c-bm)

```
git clone https://github.com/p4lang/p4c-bm.git
cd p4c-bm
sudo pip install -r requirements.txt
sudo python setup.py install
cd ..
```

- [behavioral-model](https://github.com/p4lang/behavioral-model)

```
git clone https://github.com/p4lang/behavioral-model.git
cd behavioral-model
./install_deps.sh
./autogen.sh
aclocal && automake --add-missing && autoconf && autoreconf -fi
./configure --with-pdfixed
#./configure
make
sudo ln -s ${PWD}/targets/simple_switch/simple_switch /usr/local/bin/simple_switch
sudo ln -s ${PWD}/tools/runtime_CLI.py /usr/local/bin/runtime_CLI.py
cd ..
```

## Usage

MiniP4 requires a topology file based in YAML to create a Mininet network using P4 switches. The topology file mainly contains the list of hots, switches and the links that connect them.

MiniP4 can be started executing `mnp4` command. By default `p4-topo.yml` topology file will be used if not provided.

## Topology YAML

The YAML file is composed on following sections.

### Defaults

Defaults parameters to be used by default for host and switches.

**hosts** default parameters:

- `gw` : default gateway
- `command`: a list of default commands to be executed

**switches** default parameters:

- `p4src`: p4 source file
- `dump`: dump packets into a pcap file per interface
- `port`: default port start number for thrift
- `commands`: default switch commands
- `verbose`: log level (`trace`,`debug`, `info`, `warn`, `error`, `off`). Default, `info`
- `sw_path`: switch behavioral executable. Default, `simple_switch`
- `cli`: p4 cli path. Default, `runtime_CLI.py`
- `compiler`: p4 compiler path. Default, `p4c-bmv2`

### Hosts

List of **host**

Mandatory parameters:

- `name`: host name
- `ip`: ip address

Optional parameters:

All default **host** parameters and following ones:

- `mac`: if not provided and the name contains a digits, the mac will use the number of concatenating all digits and converted to mac address. For example, if name is `h101c1` then mac address is `00:00:00:00:03:F3`. Notice `0x03:F3` is the hex representation of `1011`. If not, a random mac address will be calculated.

### Switches

List of **switch**

Mandatory parameters:

- `name`: switch name (mandatory)

Optional parameters if provided on defaults:

All default **switch** parameters and following ones:

- `id`: if not provided and the name contains a digits, the id will be the number of concatenating all digits. For example, if name is `s101c2`, 1012 will be used as `id`. If not, a random id will be calculated.
- `port`: thrift port

### Links

List of **link**

- `source`: source host or switch name
- `destination`: destination host or switch name

### Example

Example,

```
defaults:
  host:
    gw: 10.0.0.1
    command:
    - route add 8.8.8.0 dev eth0

  switch:
    sw_path: simple_switch
    compiler: p4c-bmv2
    cli: runtime_CLI.py
    p4src : p4src/vpc.p4
    dump: true
    port: 22222
    commands: commands.txt

host:
- ip: 10.0.1.1/16
  name: h101
- ip: 10.0.1.2/16
  name: h102
- ip: 10.0.1.3/16
  name: h103

switch:
- name: s101
- name: s102
- name: s103

link:
- source: h101
  destination: s101
- source: h102
  destination: s102
- source: h103
  destination: s103
- source: s101
  destination: s102
- source: s101
  destination: s103
- source: s102
  destination: s103
```
