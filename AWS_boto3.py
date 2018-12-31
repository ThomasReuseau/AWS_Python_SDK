# -*- coding: utf-8 -*-
"""
Created on Sat Dec 29 16:57:18 2018

@author: Thomas
"""

import boto3
from platform import system as system_name
from subprocess import call as system_call

ec2 = boto3.resource('ec2', aws_access_key_id='AWS_ACCESS_KEY',
                     aws_secret_access_key='AWS_SECRET_KEY',
                     region_name='eu-west-1')

# create VPC
vpc = ec2.create_vpc(CidrBlock='30.0.0.0/24')
vpc.create_tags(Tags=[{"Key": "Name", "Value": "My_VPC"}])
vpc.wait_until_available()
print("VPC with Cidr Block '30.0.0.0/25' has been created under the the id :", vpc.id)

# create Gateway
gateway = ec2.create_internet_gateway()
gateway.create_tags(Tags=[{"Key": "Name", "Value": "My_VPC_gateway"}])
vpc.attach_internet_gateway(InternetGatewayId=gateway.id)
print("Internet gateway has been created under the id :", gateway.id)

# create Route Table & Public Route
route_table = vpc.create_route_table()
route_table.create_tags(Tags=[{"Key": "Name", "Value": "My_VPC_RTB"}])
route = route_table.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=gateway.id)
print("Route table & public route have been created !")

# create Subnet
subnet = vpc.create_subnet(CidrBlock='30.0.0.0/25')
subnet.create_tags(Resources=[subnet.id], Tags=[{'Key':'Name', 'Value':'My_VPC_subnet'}])
route_table.associate_with_subnet(SubnetId=subnet.id)
print("Subnet with Cidr Block '30.0.0.0/25' has been created under the id :", subnet.id)

# Create Security Group allowing ICMP protocol
sec_group = ec2.create_security_group(
    GroupName='slice_0', Description='slice_0 sec group', VpcId=vpc.id)
sec_group.authorize_ingress(
    CidrIp='0.0.0.0/0',
    IpProtocol='icmp',
    FromPort=-1,
    ToPort=-1)
print("Security group :", sec_group.id, "allowing ICMP protocol has been created !")

# Create Instance
instances = ec2.create_instances(
    ImageId='ami-09693313102a30b2c', InstanceType='t2.micro', MaxCount=1, MinCount=1,
    NetworkInterfaces=[{'SubnetId': subnet.id, 'DeviceIndex': 0, 'AssociatePublicIpAddress': True, 'Groups': [sec_group.group_id]}])
instances[0].wait_until_running()
print("Instance has been created & is now running !")

# Get instance public IP
instance_1 = ec2.Instance(instances[0].id)
instance_public_IP = instance_1.public_ip_address

def ping(host):
    """Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid."""
    param = '-n' if system_name().lower()=='windows' else '-c'
    command = ['ping', param, '1', host]
    return system_call(command) == 0

Ping_request = ping(instance_public_IP)

if Ping_request == True:
    print("Host:", instance_public_IP, "is up !")
else:
    print("Host:", instance_public_IP, "is down or disallow ICMP protocol.")
