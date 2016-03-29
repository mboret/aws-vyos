# aws-vyos
Configuration to create an AWS inter region VPN

### Description 

An easy way to create a VPN connection between two AWS Region. 

This repository describes how to configure the AWS VPN service on the first region and a Vyos instance on the second region.

# Use case example

For this how to we will used the region us-east-1 and eu-west-1.
The goal is to authorize instances in the VPC-EU to communicate with the instances in the VPC-US and vice versa.

```  
                      US-EAST-1                                                        EU-WEST-1                 
-------------------           ------------------                      ---------------------       ---------------------
| VPC-US 10.10.0.0/16 | <===> | AWS VPN Service| <===> INTERNET <===> | EC2-Vyos-Instance | <===> | VPC-EU 10.0.0.0/16 |
-------------------           ------------------                      ---------------------       ---------------------
```

# Requirement

In the EU-WEST-1 region, go to EC2, Elastic IPs and click on "Allocate New Address" and keep it on aside.
 
# 1. Create the VPN in US-EAST-1

In your AWS console, select the region US-EAST-1 and the VPC service.
 
1.1 - Create the Customer Gateway:

- Click on "Create Customer Gateway"
    - "Name Tag" -> The name of the Customer Gateway(ex: CG-EU-US-PROD).
    - "Routing"  -> Choose dynamic.
    - "IP address" -> The EIP create in the eu-west-1 region.
    - "BGP ASN" -> Put a value for the BGP ASN(ex: 65000).

1.2 - Create the Virtual Private Gateway:

- Click on "Create Virtual Private Gateway"
    - "Name Tag" -> The name of the private gateway(ex: PG-EU-US-PROD)
    -  Select the VPG previously create and click on "attach to VPC"
    -  Choose the VPC which will accessible through the VPN(in our example: VPC-US).
 
1.3 - Configure the VPN connection:

- Click on "Create VPN Connection":

    - "Name Tag" -> The name of the VPN connection(ex: VPN-EU-US-PROD)
    - "Virtual Private Gateway" -> Select the Virtual Gateway create at the step 1.2
    - "Customer Gateway" -> Select the Customer Gateway create at the step 1.1
    - "Routing Options" -> Select "Dynamic"

1.4 - Download the VPN configuration:

Select your new VPN connection and click on "Download the configuration". Select "Vyatta" as the configuration type.

On the VPN connection, click on the "Tunnel Details" tab and keep the two Public IPs on aside.


# 2. Create and configure the Vyos instance

In your AWS console, select the region EU-WEST-1 and the EC2 Service.

2.1 -  Create the Vyos EC2 instance.

- Click on  "launch instance":

    - Select "AWS Marketplace" et search "vyos"
    - Choose the instance type.
    - Choose the VPC and the subnet(only Public!!!) where the Vyos instance will be started(ex: VPC-EU)
    - Create a new security group and add rules for the two Public IPs of the US VPN(step 1.4) and authorize them on the ports UDP/500, TCP/179 and UDP/123.
    - Finish the setup process as usual.

When the instance is ready, select it, right click -> networking -> source dest/check and click on disabled.

2.2 - Configuration of the EC2 Vyos instance.

- Execute the script: vyos_config.py: 
*python vyos_config.py vpn_config_path    vyos_ip     cidr_vpc_vyos    local_gateway*

Parameters:
 
    - vpn_config_path: Full path of the VPN configuration downloaded at the end of the step 1.4(ex: /tmp/vpn-aa99ezv1.txt)
    - vyos_ip: The private IP of the Vyos instance(ex: 10.0.1.100)
    - cidr_vpc_vyos: The VPC CIDR of the Vyos instance(ex: 10.0.0.0/16)
    - local_gateway: The local gateway of the Vyos instance, you can found it when you are connected on Vyos with the command "show ip route"(take the gateway for the route "0.0.0.0/0"). (ex: 10.0.1.1)

Example:

*python vyos_config.py /tmp/vpn-aa99ezv1.txt 10.0.1.100 10.0.0.0/16 10.0.1.1*

- Connect on your Vyos EC2 instance(user: vyos):

    - Import the bash script create at the previous step.
    - Make the script executable:
	*chmod +x vyos_config.sh*
    - Change the vyos user to root:
	*sudo su*
    - Execute the script: 
        *vbash vyos_config.sh*

### The instance will reboot automatically. Don't panic :)


# 3. Update the route tables 

 
3.1 -  In US-EAST-1:

- Select the VPC service -> route tables -> select the route tables attached to your VPC subnets which you want to give the VPN access. 
- Select the "route propagation" tab and set to "Yes" the value of  "propagate"(Normally, now you have a new route in the "routes table").
 
3.2 - In EU-WEST-1:

- Select the VPC -> route tables -> select the route tables attached to the subnets which you want to give the VPN access through the Vyos instance.
- Select the tab "routes", click on  "add". In "destination" enter the network CIDR of the US-EAST-1(ex: 10.10.0.0/16) and in "target", choose the instance Vyos.


# Conclusion

Normally, now you have a working VPN connection between two AWS regions and the other EC2 instances can communicate through it(if they are in the VPC-US or in the VPC-EU).


# Vyos debug commands

- show ip route
- show vpn ipsec sa
- show bgp 

# Debug steps

- Try to ping your Vyos instance from another local instance(same VPC).
- Launch a tcpdump on the Vyos instance(cpdump -f "icmp" -i eth0) when you are trying to ping instances over the VPN. 
- Try to ping your Vyos instance from a remote instance(the other side of your VPN).

