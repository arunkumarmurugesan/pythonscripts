# !/usr/bin/python

import csv
import sys
import boto3
from datetime import datetime, timedelta, date
import pytz
import re
from collections import defaultdict
import argparse
filepath = "Ec2-report.csv"
region = 'us-east-1'
tag_list = ['DevOwner', 'Name', 'SprtOwner', 'OwnerContact', 'ENV', 'ASV']
tag_set = True

AWS_ACCESS_KEY_ID = "***************"
AWS_SECRET_ACCESS_KEY = "*****************"

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def ec2_connect_resource(region):
    """
    Connects to EC2, returns a connection object
    """
    try:
        ec = session.resource('ec2', region_name=region)
        print ec
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        ec = None
    return ec

def open_file (filepath):
    try:
        f = file(filepath, 'wt')
    except Exception, e:
        f = None
        sys.stderr.write ('Could not open file %s. reason: %s\n' % (filepath, e))
    return f

def tag_check():
    # opens file
    f = open_file (filepath)
    if not f:
        return False
    #Start write
    writer = csv.writer (f)
    writer.writerow (['Instance Name','Instance ID','DevOwner','SprtOwner','OwnerContact',' ENV', 'ASV', 'Tag Status'])

    # connect ec2 resouce using resource method
    ec = ec2_connect_resource(region)
    if not ec:
        sys.stderr.write('Could not connect to region: %s. Skipping\n' % region)
        sys.exit(1)
    for instance in ec.instances.all():
        instance_id = instance.id
        tag_set = True
        tag_name = [tags.get('Key') for tags in instance.tags]
        instance_name = None
        instance_asv = None 
        instance_env = None
        instance_owner = None
        instance_dev = None
        instance_sport = None
        for tags in instance.tags:
            if tags['Key'] == 'Name':
                instance_name = tags.get('Value',None)
            elif tags['Key'] == 'ASV':
                instance_asv  = tags.get('Value',None)
            elif tags['Key'] == 'ENV':
                instance_env =  tags.get('Value',None)
            elif tags['Key'] == 'OwnerContact':
                instance_owner = tags.get('Value',None)
            elif  tags['Key'] == 'DevOwner':
                instance_dev = tags.get('Value',None)
            elif tags['Key'] == 'SprtOwner':
                instance_sport = tags.get('Value',None)
        if not instance_env or not instance_sport or not instance_name or not instance_asv or not instance_owner or not instance_dev:
            tag_set = False
        for tag_key in tag_list:
            if tag_key not in tag_name:
                tag_set = False
                break
        if tag_set:
            tag_count = 1
        else:
            tag_count = 0
        writer.writerow ([instance_name,instance_id,instance_dev,instance_sport,instance_owner,instance_env,instance_asv,tag_count])
    f.close ()
if __name__ == '__main__':
    tag_check()
