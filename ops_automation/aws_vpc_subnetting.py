#!/usr/bin/python
#title           : aws_vpc_subnetting.py
#author          : Arunkumar M
#date            : 20/06/2019
#usage           : python aws_vpc_subnetting.py
#Detailed Doc    : url.....
#==============================================================================

from netaddr import *
import boto3

AWS_ACCESS_KEY_ID='xxxx'
AWS_SECRET_ACCESS_KEY='xxxx'

REGION="us-west-2"

# Connect to AWS boto3 Client
def aws_connect_client(service,REGION):
    try:
        # Gaining API session
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        # Connect the client
        conn_client = session.client(service, REGION)
    except Exception as e:
        # logger.error('Could not connect to region: %s and resources: %s , Exception: %s\n' % (REGION, service, e))
        raise e
        conn_client = None
    return conn_client

# Connect to AWS boto3 Resource
def aws_connect_resource(service,REGION):
    try:
        # Gaining API session
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        # Connect the resource
        conn_resource = session.resource(service, REGION)
    except Exception as e:
        # logger.error('Could not connect to region: %s and resources: %s , Exception: %s\n' % (REGION, service, e))
        raise e
        conn_resource = None
    return conn_resource


mytags = [{
    "Key" : "Name",
       "Value" : "FlashService"
    },
    {
       "Key" : "flash",
       "Value" : "true"
    },
    {
       "Key" : "Project",
       "Value" : "iotu2"
    }]


ec2 = aws_connect_resource('ec2',REGION)
subnet_blacks=[]
ip = IPNetwork('172.24.0.0/16')
subnets = list(ip.subnet(17))
subnet_blacks = [i for i in list(ip.subnet(17))]

print(subnet_blacks)
print(len(IPNetwork(subnet_blacks[0])))

new=[]

new = [i for i in list(subnet_blacks[0].subnet(27))]
print(new)
print(len(new))

# for i in new:
#     print("{}/27".format(i.ip))

vpc = ec2.create_vpc(CidrBlock='172.24.0.0/16')
vpc.create_tags(Tags=mytags)
vpc.wait_until_available()
print(vpc.id)
vpc_conn = aws_connect_client("ec2",REGION)
response = vpc_conn.modify_vpc_attribute(
    EnableDnsHostnames={'Value': True},
    VpcId=vpc.id
)
if response['ResponseMetadata']['HTTPStatusCode'] == 200:
    print('DNS Hostname Enabled')

response1 = vpc_conn.modify_vpc_attribute(
    EnableDnsSupport={'Value': True},
    VpcId=vpc.id
)
if response1['ResponseMetadata']['HTTPStatusCode'] == 200:
    print('DNS Hostname Enabled')
# create then attach internet gateway
ig = ec2.create_internet_gateway()
vpc.attach_internet_gateway(InternetGatewayId=ig.id)
ig.create_tags(Tags=mytags)
print(ig.id)

# create a route table and a public route
route_table = vpc.create_route_table()
route = route_table.create_route(
    DestinationCidrBlock='0.0.0.0/0',
    GatewayId=ig.id
)
route_table.create_tags(Tags=mytags)
print(route_table.id)

j = 1
# create subnet
for i in new:
    mytags = [{
        "Key": "Name",
        "Value": "Service-Zone2A-Subnet-{}".format(j)
    },
        {
            "Key": "flash",
            "Value": "true"
        },
        {
            "Key": "Project",
            "Value": "iotu2"
        }]
    print("{}/27".format(i.ip))
    sub_ip='{}/27'.format(i.ip)
    subnet = ec2.create_subnet(CidrBlock=sub_ip, VpcId=vpc.id, AvailabilityZone='us-west-2a')
    subnet.create_tags(Tags=mytags)
    route_table.associate_with_subnet(SubnetId=subnet.id)
    print(subnet.id)
    j += 1


