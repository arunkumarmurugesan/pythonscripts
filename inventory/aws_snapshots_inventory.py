import csv
import os, sys
import datetime
from datetime import datetime, timedelta, date
import argparse
import boto3
import re
import parser
import dateutil
import pytz

# Defaults, can be modified
AWS_ACCESS_KEY = 'xxx'
AWS_SECRET_KEY = 'xxx'
AWS_REGIONS = u'us-east-1|us-west-1|us-west-2|eu-west-1|ap-southeast-1|ap-northeast-1|ap-southeast-2|sa-east-1|ap-south-1'
AWS_PROFILE = u'AWS_Techops_Dev_Developer|PROD_AWS_CoreEngineering'
#AWS_REGIONS = 'us-east-1'
tag_list = [ 'ASV', 'CMDBEnvironment', 'OwnerContact']

def ec2_connect(region):
#def ec2_connect(region, profile):
    """
    Connects to EC2, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        #session = boto3.Session(region_name=region, profile_name=profile)
        conn = session.resource('ec2', region)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn = None
    return conn

def open_file (filepath,profile):
    try:
        filepath = filepath + "Snapshot_Report_" + profile + ".csv"
        f = file(filepath, 'wt')
    except Exception, e:
        f = None
        sys.stderr.write ('Could not open file %s. reason: %s\n' % (filepath, e))
    return f

def create_rds_report (regions, profile, filepath):

    region_list = regions.split('|')
    profile_list = profile.split('|')
    for profile in profile_list:
        # go over all regions in list
        for region in region_list:
            print region
            f = open_file(filepath,profile)
            if not f:
                return False
            # Start write
            writer = csv.writer(f)
            writer.writerow(['Profile Name', 'Snapshots ID', ' Snapshots Age ', ' Snapshot Encrytion', 'AWS Region', 'OwnerContact', ' CMDBEnvironment', 'ASV', 'Tag Status'])

            conn = ec2_connect (region)
            if not conn:
                sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
                continue
            # get all Snapshot Inventory
            try:
                reservation = conn.snapshots.filter(OwnerIds=[AWS_ACCOUNT_ID])
            except Exception, e:
                sys.stderr.write('Could not get snapshots details for region: %s. Skipping (problem: %s)\n' % (region, e.error_message))
                continue

            for snap in reservation:
                tag_set = True
                snap_time = str(snap.start_time)
                snap_creation_time = created_date = datetime.strptime(snap_time, "%Y-%m-%d %H:%M:%S+00:00").replace(
                    tzinfo=pytz.UTC)
                today_date = datetime.now()
                today_converted_date = today_date.replace(tzinfo=pytz.UTC)
                snap_days = today_converted_date - snap_creation_time
                snapshot_id = snap.snapshot_id
                snapshot_encryption = snap.encrypted
                if snap_days.days >= 21:
                    snapshot_age = snap_days.days
                    writer.writerow([profile, snapshot_id, snapshot_age, snapshot_encryption, region])
        f.close()
if __name__ == '__main__':
    # Define command line argument parser
    parser = argparse.ArgumentParser(description='Creates a CSV report about EBS volumes and tracks snapshots on them.')
    parser.add_argument('--regions', default = AWS_REGIONS, help='AWS regions to create the report on, can add multiple with | as separator. Default will assume all regions')
    parser.add_argument('--profile', default=AWS_PROFILE,
                        help='AWS profile to create the report on, can add multiple with | as separator. Default will assume all profile')
    parser.add_argument('--file', required=True, help='Path for output CSV file')
    args = parser.parse_args()
    # creates the report
    retval = create_rds_report (args.regions, args.profile, args.file)
    if retval:
        sys.exit (0)
    else:
        sys.exit (1)

