# !/usr/bin/python
import csv
import sys
import boto3
from datetime import datetime, timedelta, date
import pytz
import re
from collections import defaultdict
import argparse
import botocore
import parser

# Defaults, can be modified
AWS_ACCESS_KEY = 'AKIAJ3DNNCL6WSDOO4DQ'
AWS_SECRET_KEY = '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'
AWS_REGIONS = u'us-east-1|us-west-2'
AWS_PROFILE = u'DEV_AWS_CoreEngineering|AWS_CoreEngineering'
profile_dict = {'DEV_AWS_CoreEngineering': 'CLOUD-ENGINEERING', 'PROD_AWS_CoreEngineering': 'Innovation-PROD'}

def ec2_connect(region):
#def ec2_connect_resource(region, profile):
    """
    Connects to EC2, returns a connection object
    """
    try:
        # session = boto3.Session(region_name=region, profile_name=profile)
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
        ec = session.client('redshift', region)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        ec = None
    return ec

def open_file (filepath,profile):
    try:
        filepath = filepath + "RedShift_Report_" + profile + ".csv"
        f = file(filepath, 'wt')
        #Start write
        writer = csv.writer (f)
        writer.writerow (['Profile Name','ClusterIdentifier','Endpoint_Name','Encrypted','PubliclyAccessible','LoggingEnabled','region'])
    except Exception, e:
        f = None
        sys.stderr.write ('Could not open file %s. reason: %s\n' % (filepath, e))
    return f

def create_ec2_report (regions, profile, filepath):
    region_list = regions.split('|')
    profile_list = profile.split('|')
    # go over all the profile's
    for profile in profile_list:
        print profile
        try:
            profile_name = profile_dict[profile]
        except Exception,e:
            sys.stderr.write('Could not find the profile name from the dictionary: %s. Exception: %s\n' % (profile, e))

        # open the csv file
        f = open_file(filepath, profile)
        writer = csv.writer(f)
        if not f:
            return False
        # go over all regions in list
        for region in region_list:
            print region
            # connect ec2 resouce using resource method
            ec = ec2_connect(region)
            if not ec:
                sys.stderr.write('Could not connect to region: %s. Skipping\n' % region)
                continue
            response = ec.describe_clusters()
            clusters = response['Clusters']
            for redshift in clusters:
                ClusterIdentifier = redshift['ClusterIdentifier']
                Endpoint = redshift['Endpoint']
                Endpoint_Name = Endpoint['Address']
                Encrypted = redshift['Encrypted']
                PubliclyAccessible = redshift['PubliclyAccessible']
                logging = ec.describe_logging_status(ClusterIdentifier=ClusterIdentifier)
                LoggingEnabled = logging['LoggingEnabled']
                print ClusterIdentifier, Endpoint_Name, Encrypted, PubliclyAccessible, LoggingEnabled
                writer.writerow ([profile_name,ClusterIdentifier,Endpoint_Name,Encrypted,PubliclyAccessible,LoggingEnabled,region])
        f.close ()
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates a CSV report about EC2 Inventory')
    parser.add_argument('--regions', default = AWS_REGIONS, help='AWS regions to create the report on, can add multiple with | as separator. Default will assume all regions')
    parser.add_argument('--profile', default=AWS_PROFILE,
                        help='AWS profile to create the report on, can add multiple with | as separator. Default will assume all profile')
    parser.add_argument('--file', required=True, help='Path for output CSV file')
    args = parser.parse_args()
    # creates the report
    retval = create_ec2_report(args.regions, args.profile, args.file)
    if retval:
        sys.exit (0)
    else:
        sys.exit (1)

