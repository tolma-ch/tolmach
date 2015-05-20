# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "hashicorp/precise64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080

  config.vm.hostname = 'tolma.ch'
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.ip_resolver = proc do |vm, resolving_vm|
    if vm.id
      `VBoxManage guestproperty get #{vm.id} "/VirtualBox/GuestInfo/Net/1/V4/IP"`.split()[1]
    end
  end

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"
  config.vm.network "private_network", type: "dhcp"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
    vb.memory = "256"
    vb.name = "tolmach"
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end
  #config.vm.define "tolmach" do |tolmach|
  #end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    sudo -i
    apt-get update
    debconf-set-selections <<< 'mysql-server mysql-server/root_password password 123'
    debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password 123'
    apt-get install -y mysql-server
    apt-get install -y python-dev
    apt-get install -y python-pip
    apt-get install -y python-virtualenv
    apt-get install -y libmysqlclient-dev
    apt-get install -y gettext
    exit

    virtualenv tolmach
    source /home/vagrant/tolmach/bin/activate
    cd /vagrant
    pip install -r requirements.txt
    wget http://megavenik.ru/tolmach_dev.sql
    mysql -uroot -p123 -e "CREATE USER 'vagrant'@'localhost' IDENTIFIED BY '';"
    mysql -uroot -p123 -e "GRANT ALL PRIVILEGES ON * . * TO 'vagrant'@'localhost' WITH GRANT OPTION;"
    mysql -uroot -p123 -e "CREATE USER 'vagrant'@'%' IDENTIFIED BY '';"
    mysql -uroot -p123 -e "GRANT ALL PRIVILEGES ON * . * TO 'vagrant'@'%' WITH GRANT OPTION;"
    mysql -e "CREATE DATABASE tolmach CHARACTER SET utf8"
    mysql tolmach < tolmach_dev.sql
  SHELL
end
