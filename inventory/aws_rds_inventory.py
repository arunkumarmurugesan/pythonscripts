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
AWS_REGIONS = u'us-east-1|us-west-1|us-west-2|eu-west-1|ap-southeast-1|ap-northeast-1|ap-southeast-2|sa-east-1|ap-south-1'
tag_list = [ 'ASV', 'CMDBEnvironment', 'OwnerContact']
AWS_PROFILE = u'DEV_AWS_CoreEngineering|PROD_AWS_CoreEngineerings'
profile_dict = {'DEV_AWS_CoreEngineering': 'CLOUD-ENGINEERING', 'DEV_AWS_CoreEngineering': 'Innovation-PROD'}

def ec2_connect(region):
#def ec2_connect(region, profile):
    """
    Connects to EC2, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        #session = boto3.Session(region_name=region, profile_name=profile)
        conn = session.client('rds',region)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn = None
    return conn
def open_file (filepath,profile):
    try:
        filepath = filepath + "RDS_Report_" + profile + ".csv"
        f = file(filepath, 'wt')
        # Start write
        writer = csv.writer(f)
        writer.writerow(['Profile Name', 'DBInstanceIdentifier', 'DB Endpoint', 'DBInstanceClass', 'DBName',
                         'DB PubliclyAccessible', 'AWS Region', 'StorageEncrypted', 'BackupRetentionPeriod',
                         'OwnerContact', ' CMDBEnvironment', 'ASV', 'Tag Status'])
    except Exception, e:
        f = None
        sys.stderr.write ('Could not open file %s. reason: %s\n' % (filepath, e))
    return f

def create_rds_report (regions, profile, filepath):
    region_list = regions.split('|')
    profile_list = profile.split('|')
    for profile in profile_list:
        # go over all regions in list
        f = open_file(filepath, profile)
        writer = csv.writer(f)
        print f
        if not f:
            return False
            ####get the profile name####
        try:
            profile_name = profile_dict[profile]
        except Exception, e:
            sys.stderr.write('Could not find the profile name from the dictionary: %s. Exception: %s\n' % (profile, e))
        for region in region_list:
            print region


            # connects to ec2
            conn = ec2_connect (region)
            # conn = ec2_connect (region,profile)
            if not conn:
                sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
                continue
            # get all RDS Inventory
            try:
                rdb = conn.describe_db_instances().get('DBInstances', [])
            except Exception, e:
                sys.stderr.write('Could not get rds details for region: %s. Skipping (problem: %s)\n' % (region, e.error_message))
                continue

            for dbinstance in rdb:
                tag_set = True
                DBInstanceIdentifier = dbinstance['DBInstanceIdentifier']
                DBInstanceClass = dbinstance['DBInstanceClass']
                DBInstanceStatus = dbinstance['DBInstanceClass']
                DBName = dbinstance['DBName']
                DBEndpoint = dbinstance['Endpoint']
                DBHost = DBEndpoint['Address']
                DBPubliclyAccessible = dbinstance['PubliclyAccessible']
                StorageEncrypted = dbinstance ['StorageEncrypted']
                BackupRetentionPeriod = dbinstance ['BackupRetentionPeriod']
                arn = 'arn:aws:rds:%s:%s:db:%s' % (region, account_number, DBInstanceIdentifier)
                rdstags = conn.list_tags_for_resource(ResourceName=arn)
                rds_asv = None
                rds_env = None
                rds_owner = None

                for tags in rdstags['TagList']:
                    if tags['Key'] == 'ASV':
                        rds_asv = tags.get('Value', None)
                    elif tags['Key'] == 'CMDBEnvironment':
                        rds_env = tags.get('Value', None)
                    elif tags['Key'] == 'OwnerContact':
                        rds_owner = tags.get('Value', None)
                if not rds_asv or not rds_env or not rds_owner:
                    tag_set = False
                if tag_set:
                    tag_count = 1
                else:
                    tag_count = 0
                writer.writerow([profile_name, DBInstanceIdentifier, DBHost, DBInstanceClass, DBName, DBPubliclyAccessible, region, StorageEncrypted,
                                     BackupRetentionPeriod, rds_owner, rds_env, rds_asv, tag_count])
                print profile, DBInstanceIdentifier, DBHost, DBInstanceClass, DBName, DBPubliclyAccessible, region, StorageEncrypted, BackupRetentionPeriod, rds_owner, rds_env, rds_asv, tag_count

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
