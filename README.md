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
git checkout tags/2.2.1
cd ..
sed -i 's/git:\/\/openflowswitch.org\/openflow.git/https:\/\/github.com\/mininet\/openflow.git/g' mininet/util/install.sh
sed -i 's/git:\/\/gitosis.stanford.edu\/oflops.git/https:\/\/github.com\/mininet\/oflops.git/g' mininet/util/install.sh
mininet/util/install.sh
```

- [p4c-bm](https://github.com/p4lang/p4c-bm)

```
git clone https://github.com/p4lang/p4c-bm.git p4c-bmv2
cd p4c-bmv2
#git checkout 96b0fffafbeea4292063aed6e9a78d39621fdefd
sudo pip install -r requirements.txt
#sudo pip install -r requirements_v1_1.txt
sudo python setup.py install
cd ..
```

- [behavioral-model](https://github.com/p4lang/behavioral-model)

```
git clone https://github.com/p4lang/behavioral-model.git bmv2
cd bmv2
#git checkout 4553c1466c437bdd0b4e7bb35ed238cb5b39d7e7
./install_deps.sh
./autogen.sh
./configure --with-pdfixed
make
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
- `bmv2`: behavioral model base folder. Default, `BMV2_PATH` env variable or `../bmv2`
- `p4c` : p4 compiler base folder. Default, `P4C_BM_PATH` env variable or `../p4c-bmv2`
- `sw_path`: switch behavioral executable. Default, `bmv2` + `/targets/simple_switch/simple_switch`
- `cli`: p4 cli path. Default, `bmv2` + `/tools/runtime_CLI.py`
- `compiler`: p4 compiler path. Default, `p4c` + `/p4c_bm/__main__.py`

### Hosts

List of **host**

Mandatory parameters:

- `name`: host name
- `ip`: ip address

Optional parameters:

All default **host** parameters and following ones:

- `mac`: if not provided and the name contains a number, the number of the name will be used and converted to mac address. For example, if name is `h101` then mac address is `00:00:00:00:00:65`. Notice `65` is the hex representation of `101`.

### Switches

List of **switch**

Mandatory parameters:

- `name`: switch name (mandatory)

Optional parameters if provided on defaults:

All default **switch** parameters and following ones:

- `id`: if not provided and the name contains a number, the number of the name will be used. For example, if name is `s101`, 101 will be used as `id`
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
    bmv2: ../bmv2
    p4c: ../p4c-bmv2
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
