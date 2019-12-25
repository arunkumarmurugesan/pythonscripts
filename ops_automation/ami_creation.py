#!/usr/bin/python

import csv
import sys
import boto3
from datetime import datetime, timedelta, date
import re
import argparse
import re
from sys import argv


def ec2_connect_resource(region):
    """
    Connects to EC2, returns a connection object
    """
    try:
        ec = boto3.resource('ec2', region_name=region, aws_access_key_id='xxx',aws_secret_access_key='xx')
    except Exception, e:
        sys.stderr.write ('Could not connect to region: %s. Exception: %s\n' % (region, e))
        ec = None
    return ec


def ec2_connect_client(region):
    """
    Connects to EC2, returns a connection object
    """
    try:
        ec = boto3.client('ec2', region_name=region, aws_access_key_id='xxx',aws_secret_access_key='xxx')
    except Exception, e:
        sys.stderr.write ('Could not connect to region: %s. Exception: %s\n' % (region, e))
        ec = None
    return ec

def ami_creation(description):

    #Define the variables
    valid = {'yes':True, 'y':True,
                     'no':False, 'n':False}
    options = {'yes':True, 'y':True,
                     'no':False, 'n':False}
    goahead = False
    goahead1 = False
    retention_days = 7
    instance_name = []
    instance_id = []
    region = 'ap-southeast-1'

    #connect ec2 resouce using client method for AMI creation
    ec_client = ec2_connect_client (region)
    if  not ec_client:
        sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
        sys.exit (1)

    #connect ec2 resouce using resource method
    ec = ec2_connect_resource (region)
    if  not ec:
        sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
        sys.exit (1)

    #Instance name from user
    name_instance = sys.argv[2]
    #Get all the instance details and create a list which contains all instance names
    for instance in ec.instances.all():
         for tags in instance.tags:
            if tags['Key'] == 'Name':
                name = tags.get('Value')
                instance_name.append(name)
         id = instance.id
         instance_id.append(name +":"+ id)
    #Check the user entered name is in the instance list
    if  name_instance in instance_name:
        for name in instance_id:
            if re.match( name_instance, name, re.M|re.I):
                id = name.split(':')

        sys.stdout.write("Instance has been verified:- Name - %s, id - %s\n" % (name_instance, id[1]))
        #Get a confirmation from user to continue ami creation process
        choice = 'y'
        if choice in valid.keys ():
            if valid[choice]:
                goahead = True
        if  goahead:
        #Create a variable for AMI NAME
            date_obj = datetime.today()
            date_str = date_obj.strftime('%Y-%m-%d-%H-%M-%S')
            name = "Created for instance " + id[1] + " at " + date_str
            image = ec_client.create_image(InstanceId=id[1], Name=name, Description=description, NoReboot=True)
        else:
            sys.stdout.write("Selected option to discontinue the AMI creation process. Exit from script")
            sys.exit(0)
        image_id = str(image['ImageId'])
        sys.stdout.write("AMI Creation in progress, AMI ID - %s\nNote : Default retention period is 7 days\n"  %(image_id))
        ignore_retention = 'y'
        if ignore_retention in options.keys ():
            if not options[ignore_retention]:
                goahead1 = False
            if not goahead1:
                # get the date X days in the future
                delete_date = date.today()  + timedelta(days=retention_days)
                # format the date as YYYY-MM-DD
                delete_fmt = delete_date.strftime('%Y-%m-%d')
                reponse = ec.create_tags(
        Resources=[
        image_id,
    ],
        Tags=[
            {'Key': 'DeleteOn', 'Value': delete_fmt}, {'Key': 'Name', 'Value': name_instance},
        ]
    )
        print reponse
    else:
        sys.stdout.write("Instance verification has been failed. Please check the instance name is exists or not\n")
        sys.exit(0)
if __name__ == '__main__':
    # Define command line argument parser
    parser = argparse.ArgumentParser(description='Creates a AMI for manual operations.')
    parser.add_argument('--description', required=True, help='description of AMI')
    args = parser.parse_args ()
    ami_creation(args.description)

