# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/xenial64"

  config.vm.communicator = "ssh"
  config.ssh.username = "ubuntu"
  config.ssh.insert_key = true

  config.vm.network "forwarded_port", guest: 5672, host: 5672   # rabbitmq
  config.vm.network "forwarded_port", guest: 15672, host: 15672 # rabbitmq-mgmt
  config.vm.network "forwarded_port", guest: 27017, host: 27017 # mongodb

  config.vm.provider "virtualbox" do |vb|
    vb.name = "thugd"
    vb.memory = "4096"
    vb.cpus = "2"
    vb.gui = false
  end

  config.vm.provision "shell",
    inline: "sudo apt-get -y install aptitude python"

  config.vm.provision "ansible" do |ansible|
    ansible.playbook = "vagrant.yml"
    ansible.verbose = false
    ansible.sudo = true
  end

  config.vm.synced_folder ".", "/home/ubuntu/data"
end
