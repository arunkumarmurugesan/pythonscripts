import csv
import os, sys
import datetime
import argparse
import boto3
import re
import parser
import dateutil

# Defaults, can be modified
AWS_ACCESS_KEY = 'xxxx'
AWS_SECRET_KEY = 'xxxx'
AWS_REGIONS = u'us-east-1|us-west-1|us-west-2|eu-west-1|ap-southeast-1|ap-northeast-1|ap-southeast-2|sa-east-1|ap-south-1'
AWS_PROFILE = u'Dev_Developer|AWS_CoreEngineering'
#AWS_REGIONS = 'us-east-1'=
tag_list = [ 'ASV', 'CMDBEnvironment', 'OwnerContact']

def ec2_connect(region):
#def ec2_connect(region, profile):
    """
    Connects to ELB, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        #session = boto3.Session(region_name=region, profile_name=profile)
        conn = session.client('elb',region)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn = None
    return conn

def open_file(filepath,profile):
    try:
        filepath = filepath + "ELB_Report_" + profile + ".csv"
        f = file(filepath, 'wt')
        # Start write
        writer = csv.writer(f)
        writer.writerow(['Profile Name', 'LoadBalancerName', 'DNSName', 'OtherPolicies_name', 'ConnectionDrainingStatus',
                         'CrossZoneLoadBalancingStatus', 'AccessLogStatus', 'AWS Regoin', 'OwnerContact', 'CMDBEnvironment', 'ASV', 'Tag Status'])
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
        for region in region_list:
            print region
            # connects to ELB
            conn = ec2_connect (region)
            # conn = ec2_connect (region,profile)
            if not conn:
                sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
                continue
            # get all ELB Inventory
            try:
                loadbalancer = conn.describe_load_balancers().get('LoadBalancerDescriptions', [])
            except Exception, e:
                sys.stderr.write('Could not get rds details for region: %s. Skipping (problem: %s)\n' % (region, e.error_message))
                continue
            for load in loadbalancer:
                LoadBalancerName = load['LoadBalancerName']
                DNSName = load['DNSName']
                ListenerDescriptions = load['ListenerDescriptions']
                Policies = load['Policies']
                OtherPolicies = Policies['OtherPolicies']
                OtherPolicies_name = ','.join(OtherPolicies)
                load_balancer_attributes = conn.describe_load_balancer_attributes(LoadBalancerName=LoadBalancerName)
                LoadBalancerAttributes = load_balancer_attributes['LoadBalancerAttributes']
                ConnectionDraining = LoadBalancerAttributes['ConnectionDraining']
                ConnectionDrainingStatus = ConnectionDraining['Enabled']
                CrossZoneLoadBalancing = LoadBalancerAttributes['CrossZoneLoadBalancing']
                CrossZoneLoadBalancingStatus = CrossZoneLoadBalancing['Enabled']
                AccessLog = LoadBalancerAttributes['AccessLog']
                AccessLogStatus = AccessLog['Enabled']

                TagDescriptions = conn.describe_tags(LoadBalancerNames=[LoadBalancerName]).get('TagDescriptions')
                elb_asv = None
                elb_env = None
                elb_owner = None
                tag_set = True
                for t in TagDescriptions:
                    for tags in t.get('Tags'):
                        if tags['Key'] == 'ASV':
                            elb_asv = tags.get('Value', None)
                        elif tags['Key'] == 'CMDBEnvironment':
                            elb_env = tags.get('Value', None)
                        elif tags['Key'] == 'OwnerContact':
                            elb_owner = tags.get('Value', None)
                    if not elb_asv or not elb_env or not elb_owner:
                        tag_set = False
                    if tag_set:
                        tag_count = 1
                    else:
                        tag_count = 0
                    print LoadBalancerName, DNSName, OtherPolicies_name, ConnectionDrainingStatus, CrossZoneLoadBalancingStatus, AccessLogStatus, elb_asv, elb_env, elb_owner, tag_count
                    writer.writerow([profile, LoadBalancerName, DNSName, OtherPolicies_name, ConnectionDrainingStatus, CrossZoneLoadBalancingStatus, AccessLogStatus,
                         region,elb_owner, elb_env, elb_asv, tag_count])
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
