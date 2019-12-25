import boto3
import re
import sys
import csv

AWS_ACCESS_KEY_ID = "***********"
AWS_SECRET_ACCESS_KEY = "**************"

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
region = 'us-east-1'
#ec = session.resource('ec2', region_name=region)
filepath = "report.csv"

def ec2_connect_resource(region):
    """
    Connects to EC2, returns a connection object
    """
    try:
        ec = session.resource('ec2', region_name=region)
        #print ec
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
    writer.writerow(['Instance ID', 'Private IP Address', 'Public IP Address' , 'Public IP Count'])
    # connect ec2 resouce using resource method
    ec = ec2_connect_resource(region)
    if not ec:
        sys.stderr.write('Could not connect to region: %s. Skipping\n' % region)
        sys.exit(1)

    for instance in ec.instances.all():
        instance_public_ip = instance.public_ip_address
        instance_private_ip = instance.private_ip_address
        instance_id = instance.id

        if instance_public_ip is None:
            tag_set=0
        else:
            tag_set=1
        writer.writerow([instance_id , instance_private_ip, instance_public_ip, tag_set])
    f.close()
if __name__ == '__main__':
    tag_check()

