
import boto3
import datetime
from botocore.exceptions import ClientError
import sys

# Update your Access/Secret Key
AWS_ACCESS_KEY = '*********************'
AWS_SECRET_KEY = '*********************'
AWS_REGIONS = 'ap-south-1'
try:
    session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    client = session.client('s3', AWS_REGIONS, config=boto3.session.Config(signature_version='s3v4'))
except ClientError as e:
    print e.message
    sys.exit(0)

try:
    # Enable the versioning to bucket
    response = client.put_bucket_versioning(Bucket='arun-test01', VersioningConfiguration={'Status': 'Enabled'})
except ClientError as e:
    print e.message
    sys.exit(0)

try:
    # Suspend the versioning to bucket
    response = client.put_bucket_versioning(Bucket='arun-test01', VersioningConfiguration={'Status': 'Suspended'})
except ClientError as e:
    print e.message
    sys.exit(0)

try:
    # Set lifecycle policy to transition to galicer after 30 days and expire the objects afters 35th days
    response = client.put_bucket_lifecycle_configuration(Bucket='arun-test02', LifecycleConfiguration={'Rules': [
        {'ID': 'id1', 'Prefix': 'arun-test02/', 'Status': 'Enabled',
         'Transitions': [{'Days': 30, 'StorageClass': 'GLACIER'}], 'Expiration': {'Days': 35}}]})
except ClientError as e:
    print e.message
    sys.exit(0)

try:
    # Expire 3 days after the object's creation date
    response = client.put_bucket_lifecycle_configuration(Bucket='arun-test02', LifecycleConfiguration={
        'Rules': [{'ID': 'id2', 'Prefix': 'arun-test02/', 'Status': 'Enabled', 'Expiration': {'Days': 3}}]})
except ClientError as e:
    print e.message
    sys.exit(0)

try:
    # List the all the buckets
    response = client.list_buckets()
except ClientError as e:
    print e.message
    sys.exit(0)
for bucket in response['Buckets']:
    print bucket['Name']
