# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|


  config.vm.box = "ubuntu/trusty64"

  # No need to check for box updates
  config.vm.box_check_update = false

  config.vm.provider "virtualbox" do |vb|
     # Display the VirtualBox GUI when booting the machine
     vb.gui = false
     vb.name = "minip4"
     # 2GB and 1 cpus are required
     vb.memory = 4096
     vb.cpus = 2
  end

  config.vm.provider "libvirt" do |vb|
     # 2GB and 1 cpus are required
     vb.memory = 4096
     vb.cpus = 2
  end

  config.vm.provision :shell, :path => "install.sh", privileged: false

end
