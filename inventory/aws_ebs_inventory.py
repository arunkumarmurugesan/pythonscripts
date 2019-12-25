import csv
import os, sys
import datetime
import argparse
import boto3
import re
import parser
import dateutil

# Defaults, can be modified
AWS_ACCESS_KEY = 'xxx'
AWS_SECRET_KEY = 'xxx'
AWS_REGIONS = u'us-east-1|us-west-1|us-west-2|eu-west-1|ap-southeast-1|ap-northeast-1|ap-southeast-2|sa-east-1'
tag_list = [ 'ASV', 'CMDBEnvironment', 'OwnerContact']


def ec2_connect(region):
    """
    Connects to EC2, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        conn = session.resource('ec2',region)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn = None
    return conn
def open_file (filepath):
    try:
        f = file(filepath, 'wt')
    except Exception, e:
        f = None
        sys.stderr.write ('Could not open file %s. reason: %s\n' % (filepath, e))
    return f

def create_ebs_report (regions, filepath):
    print regions
    # opens file
    f = open_file(filepath)
    if not f:
        return False
    # Start write
    writer = csv.writer(f)
    writer.writerow (['Volume ID', 'Volume Region', 'Volume encryption', 'OwnerContact', 'CMDBEnvironment', 'ASV', 'Tag Status'])

    region_list = regions.split('|')
    print region_list
    # go over all regions in list
    for region in region_list:
        # connects to ec2
        conn = ec2_connect (region)
        if not conn:
            sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
            continue
        # get all EBS Inventory
        for ec2_volume in conn.volumes.all():
            tag_set = True
            volume_id = ec2_volume.id
            volume_encryption = ec2_volume.encrypted
            if  ec2_volume.tags is not None:
                volume_asv = None
                volume_env = None
                volume_owner = None
                for tags in ec2_volume.tags:
                    if tags['Key'] == 'ASV':
                        volume_asv = tags.get('Value', None)
                    elif tags['Key'] == 'CMDBEnvironment':
                        volume_env = tags.get('Value', None)
                    elif tags['Key'] == 'OwnerContact':
                        volume_owner = tags.get('Value', None)
                if not volume_env or not volume_asv or not volume_owner:
                        tag_set = False
                if tag_set:
                    tag_count = 1
                else:
                    tag_count = 0
            writer.writerow([volume_id, region, volume_encryption, volume_env, volume_owner, volume_asv,tag_count])
    f.close()
if __name__ == '__main__':
    # Define command line argument parser
    parser = argparse.ArgumentParser(description='Creates a CSV report about EBS volumes and tracks snapshots on them.')
    parser.add_argument('--regions', default = AWS_REGIONS, help='AWS regions to create the report on, can add multiple with | as separator. Default will assume all regions')
    parser.add_argument('--file', required=True, help='Path for output CSV file')
    args = parser.parse_args()
    # creates the report
    retval = create_ebs_report(args.regions, args.file)
    if retval:
        sys.exit (0)
    else:
        sys.exit (1)
