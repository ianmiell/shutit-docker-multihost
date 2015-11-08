"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docker_multihost(ShutItModule):


	def build(self, shutit):
		# Some useful API calls for reference. See shutit's docs for more info and options:
		#
		# ISSUING BASH COMMANDS
		# shutit.send(send,expect=<default>) - Send a command, wait for expect (string or compiled regexp)
		#                                      to be seen before continuing. By default this is managed
		#                                      by ShutIt with shell prompts.
		# shutit.multisend(send,send_dict)   - Send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.send_and_get_output(send)   - Returns the output of the sent command
		# shutit.send_and_match_output(send, matches)
		#                                    - Returns True if any lines in output match any of
		#                                      the regexp strings in the matches list
		# shutit.send_until(send,regexps)    - Send command over and over until one of the regexps seen in the output.
		# shutit.run_script(script)          - Run the passed-in string as a script
		# shutit.install(package)            - Install a package
		# shutit.remove(package)             - Remove a package
		# shutit.login(user='root', command='su -')
		#                                    - Log user in with given command, and set up prompt and expects.
		#                                      Use this if your env (or more specifically, prompt) changes at all,
		#                                      eg reboot, bash, ssh
		# shutit.logout(command='exit')      - Clean up from a login.
		#
		# COMMAND HELPER FUNCTIONS
		# shutit.add_to_bashrc(line)         - Add a line to bashrc
		# shutit.get_url(fname, locations)   - Get a file via url from locations specified in a list
		# shutit.get_ip_address()            - Returns the ip address of the target
		# shutit.command_available(command)  - Returns true if the command is available to run
		#
		# LOGGING AND DEBUG
		# shutit.log(msg,add_final_message=False) -
		#                                      Send a message to the log. add_final_message adds message to
		#                                      output at end of build
		# shutit.pause_point(msg='')         - Give control of the terminal to the user
		# shutit.step_through(msg='')        - Give control to the user and allow them to step through commands
		#
		# SENDING FILES/TEXT
		# shutit.send_file(path, contents)   - Send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath)
		#                                    - Send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath)
		#                                    - Send directory and contents to path on the target
		# shutit.insert_text(text, fname, pattern)
		#                                    - Insert text into file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.delete_text(text, fname, pattern)
		#                                    - Delete text from file fname after the first occurrence of
		#                                      regexp pattern.
		# shutit.replace_text(text, fname, pattern)
		#                                    - Replace text from file fname after the first occurrence of
		#                                      regexp pattern.
		# ENVIRONMENT QUERYING
		# shutit.host_file_exists(filename, directory=False)
		#                                    - Returns True if file exists on host
		# shutit.file_exists(filename, directory=False)
		#                                    - Returns True if file exists on target
		# shutit.user_exists(user)           - Returns True if the user exists on the target
		# shutit.package_installed(package)  - Returns True if the package exists on the target
		# shutit.set_password(password, user='')
		#                                    - Set password for a given user on target
		#
		# USER INTERACTION
		# shutit.get_input(msg,default,valid[],boolean?,ispass?)
		#                                    - Get input from user and return output
		# shutit.fail(msg)                   - Fail the program and exit with status 1
		#
		shutit.send('mkdir -p /tmp/shutit-docker-multihost')
		shutit.send('rm -rf /tmp/shutit-docker-multihost')
		if shutit.send_and_get_output('vagrant box list 2>/dev/null | grep ubuntu/trusty64') == '':
		    shutit.send('vagrant box add https://atlas.hashicorp.com/ubuntu/boxes/trusty64',note='Download the trusty64 vagrant box')
		ip_base = '192.168.33'
		ip_list = []
		for num in range(1,4):
			if num == 1:
				master = True
			else:
				master = False
			shutit.send('mkdir -p /tmp/shutit-docker-multihost/dm-' + str(num) + ' && cd /tmp/shutit-docker-multihost/dm-' + str(num) + ' && vagrant init ubuntu/trusty64',note='Set up a trusty vm')
			shutit.send('cd /tmp/shutit-docker-multihost/dm-' + str(num))
			new_ip = ip_base + '.' + str(10 + num)
			ip_list = ip_list + [new_ip]
			shutit.insert_text('''    config.vm.network "private_network", ip: "''' + ip_base + '''.''' + str(10 + num) + '"','./Vagrantfile','.*ubuntu/trusty64.*')
			shutit.send('vagrant up')
			if master:
				shutit.login(command='vagrant ssh')
				shutit.login(command='sudo su -')
				shutit.send('apt-get update -y')
				shutit.install('build-essential fakeroot debhelper autoconf automake bzip2 libssl-dev openssl graphviz python-all procps python-qt4 python-zopeinterface python-twisted-conch libtool wget')
				# Fetch the latest archive
				shutit.send('wget -qO- http://openvswitch.org/releases/openvswitch-2.3.1.tar.gz | tar -zxvf -')
				shutit.send('cd openvswitch-2.3.1')
				# Build without check in parallel
				shutit.send("DEB_BUILD_OPTIONS='parallel=8 nocheck' fakeroot debian/rules binary")
				# Get the latest deb files and copy somewhere ...
				shutit.send('cd ..')
				shutit.send('cp *deb /vagrant')
				shutit.logout()
				shutit.logout()
				shutit.send('cp *deb /tmp/shutit-docker-multihost')
# Install some dependencies (needed for later) and install your packages
			else:
				shutit.send('cp ../*deb /tmp/shutit-docker-multihost/dm-' + str(num))
			shutit.login(command='vagrant ssh')
			shutit.login(command='sudo su -')
			shutit.send('apt-get install -y bridge-utils docker.io')
			shutit.send('dpkg -i /vagrant/openvswitch-common_2.3.1-1_amd64.deb /vagrant/openvswitch-switch_2.3.1-1_amd64.deb')
			shutit.logout()
			shutit.logout()
			shutit.send('cd')
		for num in range(1,4):
			shutit.send('cd /tmp/shutit-docker-multihost/dm-' + str(num))
			shutit.login(command='vagrant ssh')
			shutit.login(command='sudo su -')
			if num == 1:
				shutit.send('''cat >> /etc/network/interfaces << 'END'
# auto: to effectively starts it at boot
# br0=br0: to prevent finding the interface on `ifquery --list`
auto br0=br0
allow-ovs br0
iface br0 inet manual
    ovs_type OVSBridge
    ovs_ports gre1 gre2
    ovs_extra set bridge ${IFACE} stp_enable=true
    mtu 1462

allow-br0 gre1
iface gre1 inet manual
    ovs_type OVSPort
    ovs_bridge br0
    ovs_extra set interface ${IFACE} type=gre options:remote_ip=''' + ip_list[1] + '''

allow-br0 gre2
iface gre2 inet manual
    ovs_type OVSPort
    ovs_bridge br0
    ovs_extra set interface ${IFACE} type=gre options:remote_ip=''' + ip_list[2] + '''

# auto: create on start
# Define the docker0 that will be used by docker, and attached (when available) to
# the br0 bridge created by OpenVSwitch
# A different IP address need to be provided on each host (no conflict!)
auto docker0=docker0
iface docker0 inet static
    address 172.17.42.''' + str(num) + '''
    network 172.17.0.0
    netmask 255.255.0.0
    bridge_ports br0
    mtu 1462
END''')
			if num == 2:
				shutit.send('''cat >> /etc/network/interfaces << 'END'
# auto: to effectively starts it at boot
# br0=br0: to prevent finding the interface on `ifquery --list`
auto br0=br0
allow-ovs br0
iface br0 inet manual
    ovs_type OVSBridge
    ovs_ports gre1 gre3
    ovs_extra set bridge ${IFACE} stp_enable=true
    mtu 1462

allow-br0 gre1
iface gre1 inet manual
    ovs_type OVSPort
    ovs_bridge br0
    ovs_extra set interface ${IFACE} type=gre options:remote_ip=''' + ip_list[0] + '''

allow-br0 gre3
iface gre3 inet manual
    ovs_type OVSPort
    ovs_bridge br0
    ovs_extra set interface ${IFACE} type=gre options:remote_ip=''' + ip_list[2] + '''

# auto: create on start
# Define the docker0 that will be used by docker, and attached (when available) to
# the br0 bridge created by OpenVSwitch
# A different IP address need to be provided on each host (no conflict!)
auto docker0=docker0
iface docker0 inet static
    address 172.17.42.''' + str(num) + '''
    network 172.17.0.0
    netmask 255.255.0.0
    bridge_ports br0
    mtu 1462
END''')
			if num == 3:
				shutit.send('''cat >> /etc/network/interfaces << 'END'
# auto: to effectively starts it at boot
# br0=br0: to prevent finding the interface on `ifquery --list`
auto br0=br0
allow-ovs br0
iface br0 inet manual
    ovs_type OVSBridge
    ovs_ports gre2 gre3
    ovs_extra set bridge ${IFACE} stp_enable=true
    mtu 1462

allow-br0 gre2
iface gre1 inet manual
    ovs_type OVSPort
    ovs_bridge br0
    ovs_extra set interface ${IFACE} type=gre options:remote_ip=''' + ip_list[1] + '''

allow-br0 gre3
iface gre3 inet manual
    ovs_type OVSPort
    ovs_bridge br0
    ovs_extra set interface ${IFACE} type=gre options:remote_ip=''' + ip_list[2] + '''

# auto: create on start
# Define the docker0 that will be used by docker, and attached (when available) to
# the br0 bridge created by OpenVSwitch
# A different IP address need to be provided on each host (no conflict!)
auto docker0=docker0
iface docker0 inet static
    address 172.17.42.''' + str(num) + '''
    network 172.17.0.0
    netmask 255.255.0.0
    bridge_ports br0
    mtu 1462
END''')
			shutit.logout()
			shutit.logout()
		for num in range(1,4):
			shutit.send('cd /tmp/shutit-docker-multihost/dm-' + str(num))
			shutit.send('vagrant ssh -- sudo reboot')
		shutit.send('sleep 120')
		shutit.pause_point('')
		return True

	def get_config(self, shutit):
		# CONFIGURATION
		# shutit.get_config(module_id,option,default=None,boolean=False)
		#                                    - Get configuration value, boolean indicates whether the item is
		#                                      a boolean type, eg get the config with:
		# shutit.get_config(self.module_id, 'myconfig', default='a value')
		#                                      and reference in your code with:
		# shutit.cfg[self.module_id]['myconfig']
		return True

	def test(self, shutit):
		# For test cycle part of the ShutIt build.
		return True

	def finalize(self, shutit):
		# Any cleanup required at the end.
		return True
	
	def is_installed(self, shutit):
		return False


def module():
	return docker_multihost(
		'shutit.docker_multihost.docker_multihost.docker_multihost', 1772407079.00,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup']
	)

