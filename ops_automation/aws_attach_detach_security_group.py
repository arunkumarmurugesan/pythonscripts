import boto3
import os, sys
import argparse
from botocore.exceptions import ClientError

AWS_ACCESS_KEY = 'xxx'
AWS_SECRET_KEY = 'xxx'
AWS_REGIONS = 'ap-southeast-1'

filters = [{
    'Name': 'tag:Name',
    'Values': ['Mediawiki', 'arun-delete']
    }]
sg_name=["sg-xxxx","sg-xxx","sg-xxx"]

# instance_list = list(ec2.instances.filter(Filters=filters))
# action="detach"
def connect_region():
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
        conn = session.client('ec2', AWS_REGIONS)
    except ClientError as e:
        print "Unable to attach the Connect Region From Client API : %s" % e
    return conn

def connect_region_source():
    try:
        ec2 = boto3.resource('ec2', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,
                         region_name=AWS_REGIONS)
    except ClientError as e:
        print "Unable to attach the Connect Region From Resource API : %s" % e
    return ec2

def sg_attach_detach(actions):
    conn = connect_region()
    ec2 = connect_region_source()
    if not conn:
        sys.stderr.write('Could not connect to region: %s. Skipping\n' % AWS_REGIONS)
        exit(0)
    instance_list = list(ec2.instances.filter(Filters=filters))

    for i in instance_list:
        ins= i.id
        # conn = session.client('ec2',AWS_REGIONS)
        response = conn.describe_instances()
        list_sg=[]
        for reservation in (response["Reservations"]):
            for instance in reservation["Instances"]:
                if "attach" == actions:
                    if ins == instance['InstanceId']:
                        for sg in instance.get('SecurityGroups', []):
                            list_sg.append(sg['GroupId'])
                        all_sg_list=list_sg+sg_name
                    try:
                        if ins == instance['InstanceId']:
                            reps=conn.modify_instance_attribute(InstanceId=ins,Groups=all_sg_list)
                            if reps['ResponseMetadata']['HTTPStatusCode'] == 200:
                                print ("Successfully Added the Security Groups: %s to the Instance: %s" % (all_sg_list,ins))
                    except ClientError as e:
                        print "Unable to attach the Secuirty Groups : %s" % e
                elif "detach" == actions:
                    if ins == instance['InstanceId']:
                        for sg in instance.get('SecurityGroups', []):
                            list_sg.append(sg['GroupId'])
                        all_sg_list=list_sg
                        new_list=[]
                        for e in all_sg_list:
                            if e not in sg_name:
                                new_list.append(e)
                        all_sg_list= new_list
                        try:
                            if ins == instance['InstanceId']:
                                reps = conn.modify_instance_attribute(InstanceId=ins, Groups=all_sg_list)
                                if reps['ResponseMetadata']['HTTPStatusCode'] == 200:
                                    print (
                                    "Successfully Removed the Security Groups: %s from the Instance: %s" % (sg_name, ins))
                        except ClientError as e:
                            print "Unable to attach the Secuirty Groups : %s" % e


if __name__ == '__main__':
    # Define command line argument parser
    parser = argparse.ArgumentParser(description='Add the Rules in Application Loadbalancer')
    parser.add_argument('--Action', required=True, help='Specify the Action. i.e "attach" or "detach"')

    args = parser.parse_args()
    retval = sg_attach_detach (args.Action)
    if retval:
        sys.exit (0)
    else:
        sys.exit (1)

    # sg_attach_detach()