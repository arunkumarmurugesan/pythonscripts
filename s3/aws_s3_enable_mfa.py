import boto3

AWS_ACCESS_KEY = 'xxx'
AWS_SECRET_KEY = 'xx+xxx/xx'

session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
#conn = session.client('iam')

# Place proper keys in boto configuration file /etc/boto.cfg
S3 = session.client('s3')

# Enter bucket name to which MFA delete has to be enabled
print("Enter bucket name to which MFA delete has to be enabled")
bucket_name = raw_input()
print ("Your bucket is : {}".format(bucket_name))


# bucket = s3.lookup(bucket_name)

# Checking vesioning and MfaDelete status
config = S3.get_bucket_versioning(Bucket=bucket_name)
print("Your bucket", bucket_name, "status is", config)

# Enter your 12-digits AWS Account ID
print("Enter your 12-digits Aws Account ID")
aws_account_id = raw_input()
print("Your account ID is", aws_account_id)

# Enter 6-digits Current MFA token from your MFA Device
print("Enter Current MFA token from your MFA device")
mfa_token = raw_input()
print("Provided/present MFA token is", mfa_token)

S3.put_bucket_versioning(
    Bucket=bucket_name,
    MFA='arn:aws:iam::%s:mfa/root-account-mfa-device %s' % (aws_account_id, mfa_token),
    VersioningConfiguration={
        'MFADelete': 'Enabled',
        'Status': 'Enabled'
    }
)

# After enabling, Checking vesioning and MfaDelete status, it will give an output in below format
# {'MfaDelete': 'Enabled', 'Versioning': 'Enabled'}
config1 = S3.get_bucket_versioning(Bucket=bucket_name)
print("Your bucket", bucket_name, "status is", config1)
# If you get versioning status output as {'MfaDelete': 'Enabled', 'Versioning': 'Enabled'}, then you are successful in enabling MFA delete on required bucket.
##NOTE: Don't forget to disable your root account access key after enabling MFA delete on all required buckets (mainly backups buckets).

