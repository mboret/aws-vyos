"""

    Create a bash script to configure a vyos EC2 instance for an AWS inter region VPN.
    The input format for the VPN must be vyatta.

    Argument1: Full path to the dowloaded VPN configuration file(/tmp/vpn-a99c83b.txt)
    Argument2: The private IP of the Vyos instance(ex: 10.0.1.100)
    Argument3: The CIDR of the VPC on the Vyos side(ex: 10.0.0.0/16)
    Argument4: The local gateway of the Vyos instance(ex: 10.0.0.1)

    Think to execute the script output as root on the Vyos instance.

"""
#!/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

def read_config(config_file):
    """ Return the entire config file as a list.

        :param  config_file: string  The path of the downloaded config file from AWS.
    """
    with open(config_file, 'r') as f:
        return f.readlines()

def remove_comment(config):
    """Return the config without comment.

      :param  config_file: list
    """
    new_content = []
    for line in config:
        if not line.startswith('!') and line != '\n':
            new_content.append(line)
    return new_content


def create_script_file(config, local_IP, local_cidr, local_gateway):
    """ Create a bash script for vyos configuration.

        :param config: list The VPN configuration.
        :param local_ip: string The local IP of the Vyos instance.
        :param local_cidr: string The CIDR of the entire VPC on the Vyos instance side.
        :param local_gateway: string The default gateway of the Vyos instance.
    """
    bgp = [i for i in config if re.search(r'soft-reconfiguration',i)][0]
    bgp = re.search(r'bgp (.*) neighbor', bgp).group(1)
    f = open('/tmp/vyos_config.sh', 'w')
    f.write('#!/bin/vbash\nsource /opt/vyatta/etc/functions/script-template\n')
    f.write('echo "Vyos-1.1.7" |run add system image http://packages.vyos.net/iso/release/1.1.7/vyos-1.1.7-amd64.iso\nconfigure\n')
    for line in config:
        if re.search(r'local-address', line):
            f.write(line.split('local-address')[0] + 'local-address ' + local_IP + '\n')
        elif not re.search(r'0.0.0.0/0',line):
            f.write(line)
    f.write('set protocols static route {0} next-hop {1} distance 10\n' .format(local_cidr, local_gateway))
    f.write('set protocols bgp {0} network {1}\n' .format(bgp, local_cidr))
    f.write('set vpn ipsec nat-traversal enable\ncommit\nsave\nexit\necho "Yes" |run reboot\nexit')
    f.close()

if __name__ == '__main__':
    conf = remove_comment(read_config(sys.argv[1]))
    create_script_file(conf, sys.argv[2], sys.argv[3], sys.argv[4])
    print("The configuration has been created: /tmp/vyos_config.sh")



