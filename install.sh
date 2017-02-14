sudo apt-get update
type git || sudo apt-get install git -y
type python || sudo apt-get install python python-dev python-setuptools -y
type pip || sudo apt-get install python-pip -y

cd ~

type mn
if [ $? -ne 0 ]
then
  rm -rf mininet
  git clone https://github.com/mininet/mininet.git
  cd mininet
  sudo python setup.py install
  git checkout tags/2.2.1
  cd ..
  sed -i 's/git:\/\/openflowswitch.org\/openflow.git/https:\/\/github.com\/mininet\/openflow.git/g' mininet/util/install.sh
  sed -i 's/git:\/\/gitosis.stanford.edu\/oflops.git/https:\/\/github.com\/mininet\/oflops.git/g' mininet/util/install.sh
  # Mininet is installed with -n to avoid installing unnecessary openflow dependencies
  mininet/util/install.sh -n
fi

type p4c-bmv2
if [ $? -ne 0 ]
then
  rm -rf p4c-bm
  git clone https://github.com/p4lang/p4c-bm.git
  cd p4c-bm
  sudo pip install -r requirements.txt
  sudo python setup.py install
  cd ..
fi

type simple_switch
if [ $? -ne 0 ]
then
  rm -rf behavioral-model
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
fi
