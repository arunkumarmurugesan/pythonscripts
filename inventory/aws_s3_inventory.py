import boto3
import dateutil
import pytz
import csv
from boto3.session import Session
import dateutil
import argparse
from boto3.session import Session
import os, sys
import parser


# Defaults, can be modified
AWS_ACCESS_KEY = 'xxx'
AWS_SECRET_KEY = 'xxx'
AWS_REGIONS = u'us-east-1|us-west-1|us-west-2|eu-west-1|ap-southeast-1|ap-northeast-1|ap-southeast-2|sa-east-1|ap-south-1'
AWS_PROFILE = u'AWS_Techops_Dev_Developer|DEV_AWS_CoreEngineering'
AWS_REGIONS = 'us-east-1'
tag_list = [ 'ASV', 'CMDBEnvironment', 'OwnerContact']

def ec2_connect(region):
#def ec2_connect(region, profile):
    """
    Connects to EC2, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        conn = session.resource('s3', config=boto3.session.Config(signature_version='s3v4'))
        #session = boto3.Session(region_name=region, profile_name=profile)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn = None
    return conn
def open_file (filepath,profile):
    try:
        filepath = filepath + "S3_Report_" + profile + ".csv"
        f = file(filepath, 'wt')
        # Start write
        writer = csv.writer(f)
        writer.writerow(['Profile Name', 'S3 BucketName', 'S3 Logging Status', 'S3 Versioning Status', 'S3 ACL Status', 'AWS Regoin', 'CMDBEnvironment', 'OwnerContact', 'ASV', 'Tag Status'])
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
            # connects to ec2
            conn = ec2_connect (region)
            # conn = ec2_connect (region,profile)
            if not conn:
                sys.stderr.write ('Could not connect to region: %s. Skipping\n' % region)
                continue
            # get all RDS Inventory
            try:
                s3buckets = conn.buckets.all()
            except Exception, e:
                sys.stderr.write('Could not get rds details for region: %s. Skipping (problem: %s)\n' % (region, e.error_message))
                continue
            for s3 in s3buckets:
                s3_bucket_name = s3.name
                bucket_logging = conn.BucketLogging(s3_bucket_name)
                logging_enabled = bucket_logging.logging_enabled
                if logging_enabled is not None:
                    logging_status = 1
                else:
                    logging_status = 0
                bucket_versioning = conn.BucketVersioning(s3_bucket_name)
                bucket_versioning_status = bucket_versioning.status
                if bucket_versioning_status is not None:
                    versioning_status = 1
                else:
                    versioning_status = 0
                tag_set = True
                bucket_acl = conn.BucketAcl(s3_bucket_name)
                for grant in bucket_acl.grants:
                    grantee = grant['Grantee']
                    # permission = grant['Permission']
                    uri = grantee.get('URI')
                    if uri is not None:
                        uri_list = uri
                        uri_str = 'AllUsers'
                        value = uri_str in uri_list
                        if value:
                            acl_value = 1
                        else:
                            acl_value = 0
                # for bucket in conn.buckets.all():
                # now we rule out if the ignore tag exists
                try:
                    t = conn.BucketTagging(s3_bucket_name)
                    tags = t.tag_set
                    s3_asv = None
                    s3_env = None
                    s3_owner = None
                    for tagslist in tags:
                        if tagslist['Key'] == 'ASV':
                            s3_asv = tagslist.get('Value', None)
                        elif tagslist['Key'] == 'CMDBEnvironment':
                            s3_env = tagslist.get('Value', None)
                        elif tagslist['Key'] == 'OwnerContact':
                            s3_owner = tagslist.get('Value', None)
                    if not s3_asv or not s3_env or not s3_owner:
                        tag_set = False
                    if tag_set:
                        tag_count = 1
                    else:
                        tag_count = 0
                except Exception as ex:
                        # print("No tags found for S3 bucket " + bucket.name)
                    f = None
                #print s3_bucket_name, logging_status, bucket_versioning_status, acl_value, s3_env, s3_owner, s3_asv, tag_count
                writer.writerow([profile, s3_bucket_name, logging_status, bucket_versioning_status, acl_value, region, s3_env, s3_owner, s3_asv, tag_count])
                print profile, s3_bucket_name, logging_status, bucket_versioning_status, acl_value, s3_owner, region, s3_env, s3_owner, s3_asv, tag_count
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

