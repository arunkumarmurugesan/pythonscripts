#!/usr/bin/python
#title           : aws_security_and_compliance_fix
#author          : Arunkumar M 
#date            : 20190824
#usage           : python aws-security-fix.py -r us-west-2 -s3 devopslogs -e arunkumar.murugesan@gmail.com -k <all|k8s>
#==============================================================================

import boto3
import json, time, argparse, logging, sys
import datetime

# Credentials
AWS_ACCESS_KEY_ID='xxxx'
AWS_SECRET_ACCESS_KEY='xxxx'
#REGION = "ap-south-1"
FAILED_EXIT_CODE = 1
TODAY=datetime.datetime.now().strftime("%Y%m%d-%H%M")

# Enable the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S %Z')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Access the environment constants
try:
    ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
except KeyError:
    logger.error("Please set the environment variable AWS_ACCESS_KEY_ID")
    sys.exit(FAILED_EXIT_CODE)
try:
    SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
except KeyError:
    logger.error("Please set the environment variable AWS_SECRET_ACCESS_KEY")
    sys.exit(FAILED_EXIT_CODE)


# Connect to AWS boto3 Client
def aws_connect_client(service,REGION):
    try:
        # Gaining API session
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        # Connect the client
        conn_client = session.client(service, REGION)
    except Exception as e:
        logger.error('Could not connect to region: %s and resources: %s , Exception: %s\n' % (REGION, service, e))
        conn_client = None
    return conn_client

# Connect to AWS boto3 Resource
def aws_connect_resource(service,REGION):
    try:
        # Gaining API session
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        # Connect the resource
        conn_resource = session.resource(service, REGION)
    except Exception as e:
        logger.error('Could not connect to region: %s and resources: %s , Exception: %s\n' % (REGION, service, e))
        conn_resource = None
    return conn_resource

# Return AWS Account ID
def get_aws_account_id(REGION):
    return aws_connect_resource('iam', REGION).CurrentUser().arn.split(':')[4]

# Enable Termination protection for EC2
    # 1. List ASG instances
def enable_termination_protection(KEY, VALUE, REGION):
    ec2_client = aws_connect_client('ec2',REGION)
    try:
        response = ec2_client.describe_tags(
            Filters=[
                {
                    'Name': KEY,
                    'Values': [VALUE]
                }
             ] )
        tag_list = response['Tags']
        asg_instance_list = []
        for item in reversed(tag_list):
            asg_instance_ids = item['ResourceId']
            # Appending the asg instances in a list
            asg_instance_list.append(asg_instance_ids)
#        logger.info("Able to list all the ASG Servers")
    except Exception as e:
        logger.error('Not able to list the ASG servers, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # 2. List all EC2 instances
    try:
        ec2_instance_list = []
        response = ec2_client.describe_instances()
        for vm in response["Reservations"]:
            for instance in vm["Instances"]:
                # This will print the output value of the Dictionary key 'InstanceId'
                # Appending all ec2 instances in a list
                ec2_instances_ids = instance["InstanceId"]
                ec2_instance_list.append(ec2_instances_ids)
        if ec2_instance_list:
            logger.info("Able to fetch the list of all servers")
    except Exception as e:
        logger.error("Not able to fetch all the servers list, Exception: {}".format(e))
        sys.exit(FAILED_EXIT_CODE)

    # 3. Filter only the standalone EC2 machines (not ASG's)
    try:
        standalone = list(set(ec2_instance_list) - set(asg_instance_list))
        if standalone == []:
            logger.info("There is no Standalone servers in {}".format(REGION))
        #  Enabling "Termination protection" for standalone EC2 instance
        else:
            for ec2_ids in standalone:
                response = ec2_client.modify_instance_attribute(DisableApiTermination={'Value': True},InstanceId=ec2_ids)
                if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                    logger.info("Termination protection enabled for {}".format(ec2_ids))
    except Exception as e:
        logger.error("Failed to enable termination protection, Exception: {}".format(e))
        sys.exit(FAILED_EXIT_CODE)

# Create S3 bucket function
def s3_bucket_creation(BUCKETNAME,REGION):
    # Create S3 bucket
    logger.info("Specified S3Bucket doesn't exist, hence creating")
    s3_client = aws_connect_client('s3', REGION)
    try:
        s3_bucket_create = s3_client.create_bucket(ACL='authenticated-read', Bucket=BUCKETNAME, CreateBucketConfiguration={'LocationConstraint': REGION})
        response = s3_client.put_bucket_versioning(
            Bucket=BUCKETNAME,
            VersioningConfiguration={
                'Status': 'Enabled'
            }
        )
        response = s3_client.put_bucket_encryption(
            Bucket=BUCKETNAME,
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256',
                        }
                    },
                ]
            }
        )
        if s3_bucket_create['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info('S3Bucket created: {} and Enabled the Versioning and Enabled ServerSideEncryption'.format(BUCKETNAME))
    except Exception as e:
        logger.error("Failed to create a s3 bucket {}, Exception: {}".format(BUCKETNAME,e))
        sys.exit(FAILED_EXIT_CODE)

    return BUCKETNAME


# Create S3 bucket Call
def s3_bucket(BUCKETNAME,REGION):
    try:
        bucket_list = [bucket['Name'] for bucket in aws_connect_client('s3', REGION).list_buckets()['Buckets']]
        if bucket_list:
            if BUCKETNAME in bucket_list:
                pass
                #logger.info('Specified bucket already exists: {}'.format(BUCKETNAME))
            else:
                s3_bucket_creation(BUCKETNAME, REGION)
        else:
            s3_bucket_creation(BUCKETNAME, REGION)
    except Exception as e:
        logger.error('Error with Bucket: {}, Exception: {}'.format(BUCKETNAME,e))
        #s3_name = None
        sys.exit(FAILED_EXIT_CODE)
    return BUCKETNAME

# Enable Config for all regions

def enable_awsconfig(BUCKETNAME,EMAILID, REGION):

    try:
        # Create SNS topic
        email_list = EMAILID.split(',')
        region_list = [region['RegionName'] for region in aws_connect_client('ec2',REGION).describe_regions()['Regions']]

        for region in reversed(region_list):
            snstopic = aws_connect_client('sns', region)
            logger.info('Creating SNS in {}'.format(region))
            topic = snstopic.create_topic(Name='notification')
            snsname = (topic['TopicArn'].split(':')[5])
            snsregion = "arn:aws:sns:%s:%s:%s" % (region, get_aws_account_id(REGION), snsname)

            # Create Subscriptions (e-mail) for the topic
            for id in email_list:
                snsemail = snstopic.subscribe(TopicArn=snsregion, Protocol='email', Endpoint=id)
        if (topic['ResponseMetadata']['HTTPStatusCode'] == 200 and snsemail['ResponseMetadata'][
            'HTTPStatusCode'] == 200):
            logger.info('SNS Topic created in all regions with the name: {}'.format(snsname))
            logger.info('Email subscription(s) created for topic "{}" in all regions'.format(snsname))

    except Exception as e:
        logger.error('Not able to create Email Subscription or Topic, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # Create SNS policy
    sns_arn_list = []
    for region in reversed(region_list):
        sns_arn = "arn:aws:sns:%s:%s:%s" % (region, get_aws_account_id(REGION), snsname)
        sns_arn_list.append(sns_arn)
        SNS_POLICY = \
        {
        "Version": "2012-10-17",
        "Statement":
            [
                {
                    "Effect": "Allow",
                    "Action": "sns:Publish",
                    "Resource": sns_arn_list
                }
            ]
        }

    # Trust relationship policy
    TRUST_POLICY = \
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
        "Service": "config.amazonaws.com"
                    },
        "Action": "sts:AssumeRole"
        }
    ]
    }

    try:
        # Create IAM Roles
        logger.info('Creating IAM Role')
        iam_client = aws_connect_client('iam', REGION)

        primary_role = iam_client.create_role( Path='/service-role/', RoleName='AWSConfig-{}'.format(TODAY),
        AssumeRolePolicyDocument=json.dumps(TRUST_POLICY),
        Description='Allows Config to call AWS services and collect resource configurations on your behalf')
        primary_role_arn = (primary_role['Role']['Arn'])
        logger.info('IAM Role created: ' + str(primary_role_arn))

    except Exception as e:
        logger.error('Not able to create IAM Role, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # S3 Policy
    S3_POLICY = \
    {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketAcl*"
            ],
            "Resource": "arn:aws:s3:::%s" % BUCKETNAME
        },{
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject*"
            ],
            "Resource": "arn:aws:s3:::%s/AWSLogs/%s/*" % (BUCKETNAME, get_aws_account_id(REGION)),
            "Condition": {
                "StringLike": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        }
        ]
    }


# Create Policies
    try:
        logger.info('Creating policies for S3 and SNS ')

        s3policycreate = iam_client.create_policy(PolicyName='S3Policy-AWSConfig-{}'.format(TODAY),PolicyDocument=json.dumps(S3_POLICY),Description='S3 POLICY')
        s3_policy_arn = (s3policycreate['Policy']['Arn'])
        logger.info('S3 Policy created: ' + str(s3_policy_arn))

        snspolicycreate = iam_client.create_policy(PolicyName='SNSPolicy-Config-{}'.format(TODAY),PolicyDocument=json.dumps(SNS_POLICY),Description='SNS POLICY')
        sns_policy_arn = (snspolicycreate['Policy']['Arn'])
        logger.info('SNS Policy created: ' + str(sns_policy_arn))

    except Exception as e:
        logger.error('Not able to create Policies, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # Attach Policies to Roles
    try:
        logger.info('Attaching S3, SNS & AWS Config Policies to IAM Roles')

        configpolicyattach = iam_client.attach_role_policy(RoleName=primary_role_arn,PolicyArn='arn:aws:iam::aws:policy/service-role/AWSConfigRole')
        s3policyattach = iam_client.attach_role_policy(RoleName='AWSConfigPrimary',PolicyArn=s3_policy_arn)
        snspolicyattach = iam_client.attach_role_policy(RoleName='AWSConfigPrimary',PolicyArn=sns_policy_arn)

        if (s3policyattach['ResponseMetadata']['HTTPStatusCode'] == 200 and snspolicyattach['ResponseMetadata']['HTTPStatusCode'] == 200 and
            configpolicyattach['ResponseMetadata']['HTTPStatusCode'] == 200):
            logger.info('S3, SNS, Config Policies attached to Roles')
            # Sleep 30 seconds
            logger.info('Waiting 30 seconds for the IAM Roles to get updated')
            time.sleep(30)
    except Exception as e:
        logger.error('Not able to attach Policies to Roles, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # Calling function
    config_func(snsname,BUCKETNAME,primary_role_arn, REGION)

# Create Config for all regions
def config_func(SNSNAME, BUCKETNAME, PRIMARY_ROLE_ARN, REGION):
    # Calling S3 function
    s3_bucket_name = s3_bucket(BUCKETNAME, REGION)
    # Get Regions
    region_lists = [region['RegionName'] for region in aws_connect_client('ec2', REGION).describe_regions()['Regions']]
    try:
        logger.info('Enabling AWS Config')
        for region in region_lists:
            sns_arn = "arn:aws:sns:%s:%s:%s" % (region, get_aws_account_id(REGION), SNSNAME)
            config_conn = aws_connect_client('config', region)
            # Check for existing recorders
            config_recorder = config_conn.describe_configuration_recorders()
            if config_recorder['ConfigurationRecorders'] == []:
                # Create Config Recorder
                recordfirst = config_conn.put_configuration_recorder(
                    ConfigurationRecorder={
                        'name': 'recorder-{}'.format(region),
                        'roleARN': '{}'.format(PRIMARY_ROLE_ARN),
                        'recordingGroup': {
                        'allSupported': True,
                        'includeGlobalResourceTypes': True }})
            else:
                logger.info("Yay! AWSConfig 'Recorder' already exists in {}".format(region))

            # Check for existing channels
            delivery_channel = config_conn.describe_delivery_channels()
            if delivery_channel['DeliveryChannels'] == []:
                # Create Config Channel
                channelfirst = config_conn.put_delivery_channel(
                    DeliveryChannel={
                        'name': 'channel-{}'.format(region),
                        's3BucketName': '{}'.format(s3_bucket_name),
                        'snsTopicARN': '{}'.format(sns_arn),
                        'configSnapshotDeliveryProperties': {'deliveryFrequency': 'Six_Hours'}})

                # Start AWS Config Service
                config_activate = config_conn.start_configuration_recorder(ConfigurationRecorderName='recorder-{}'.format(region))

                if (recordfirst['ResponseMetadata']['HTTPStatusCode'] == 200 and config_activate['ResponseMetadata']['HTTPStatusCode'] == 200 and
                        channelfirst['ResponseMetadata']['HTTPStatusCode'] == 200):
                    logger.info('AWS Config enabled in {}'.format(region))
            else:
                logger.info("Yay! AWSConfig 'DeliveryChannel' already exists in {}".format(region))

    except Exception as e:
        logger.error('AWS Config not enabled, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

# ---------------

# Enable VPC Endpoint and Flow logs, DNS hostname

def enable_vpc_endpoint(REGION):
    iam_client = aws_connect_client('iam', REGION)
    ec2_client = aws_connect_client('ec2', REGION)
    logs_client = aws_connect_client('logs', REGION)

    # Flow log Policy
    VPC_FLOW_POLICY = \
    {
    "Version": "2012-10-17",
    "Statement": [
        {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Effect": "Allow",
      "Resource": "*"
        }
      ]
    }

# Trust relationship policy
    TRUST_FLOW_POLICY = \
        {
    "Version": "2012-10-17",
    "Statement": [
        {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "vpc-flow-logs.amazonaws.com"
        },
      "Action": "sts:AssumeRole"
        }
      ]
    }
    # Creating CloudWatch Log group
    try:
        # Check vpc's for flowlogs
        flow_list = [flow ['ResourceId'] for flow in ec2_client.describe_flow_logs()['FlowLogs']]
        vpc_list = [vpcl['VpcId'] for vpcl in ec2_client.describe_vpcs()['Vpcs']]
        flowlog_not_enabled = list(set(vpc_list) - set(flow_list))
        if flowlog_not_enabled == []:
            logger.info("Wow! Flowlogs enabled for all VPC's already")
        else:
            # Create Policy
            try:
                logger.info('Creating FlowLogs policy ')
                flowpolicycreate = iam_client.create_policy(PolicyName='VPCFlowlogspolicy-{}'.format(TODAY),
                                                            PolicyDocument=json.dumps(VPC_FLOW_POLICY),
                                                            Description='VPC FLOWLOGS POLICY')
                flowpolname = (flowpolicycreate['Policy']['Arn'])
                logger.info('Flow log policy created: {}'.format(flowpolname))
            except Exception as e:
                logger.error('Not able to create Flow log Policy , Exception: {}'.format(e))
                sys.exit(FAILED_EXIT_CODE)

            # Create IAM Role
            try:
                logger.info('Creating IAM Role for FlowLogs')
                role = iam_client.create_role(Path='/service-role/', RoleName='VPCFlowLogs-{}'.format(TODAY),
                                              AssumeRolePolicyDocument=json.dumps(TRUST_FLOW_POLICY),
                                              Description='Allows VPC flowlogs to call AWS services and collect resource configurations on your behalf')
                rolearn = (role['Role']['Arn'])
                logger.info('Flow logs Role created: {}'.format(rolearn))
            except Exception as e:
                logger.error('Not able to create Flow logs Role, Exception: {}'.format(e))
                sys.exit(FAILED_EXIT_CODE)

            # Attach Policy to Role:
            try:
                time.sleep(10)
                flowpolicyattach = iam_client.attach_role_policy(RoleName='VPCFlowLogs-{}'.format(TODAY), PolicyArn=flowpolname)
                if (flowpolicyattach['ResponseMetadata']['HTTPStatusCode'] == 200):
                    logger.info('Flow logs Policy attached to Role')
            except Exception as e:
                logger.error('Not able to attach Policy to Role, Exception: {}'.format(e))
                sys.exit(FAILED_EXIT_CODE)

            logger.info('Creating CloudWatch Log group')
            loggroup_lists = [group['logGroupName'] for group in logs_client.describe_log_groups()['logGroups']]
            loggroup_not_enabled = list(set(vpc_list) - set(loggroup_lists))
            for vpcid in reversed(loggroup_not_enabled):
                if loggroup_not_enabled == []:
                    logger.info("CloudWatch Loggroup is already created for all VPC")
                else:
                    response = logs_client.create_log_group(logGroupName=vpcid, tags={'Name': 'Logs-{}'.format(vpcid)})
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                      logger.info("CloudWatch Loggroup created for VPC: {}".format(vpcid))
    except Exception as e:
        logger.error('Error while creating CloudWatch Loggroup, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

# Endpoint policy
    ENDPOINT_POLICY = \
    {
    "Statement": [
            {
            "Action": "*",
            "Effect": "Allow",
            "Resource": "*",
            "Principal": "*"
            }
        ]
    }


    try:
        # Check all VPC for endpoint
        endpoint_list = [end['VpcId'] for end in ec2_client.describe_vpc_endpoints()['VpcEndpoints']]
        vpc_list = [vpcl['VpcId'] for vpcl in ec2_client.describe_vpcs()['Vpcs']]
        endpoint_not_enabled = list(set(vpc_list) - set(endpoint_list))
        if endpoint_not_enabled == []:
            logger.info("Hurray! Endpoint enabled for all VPC's already")
        else:
            #Creating VPC Endpoint
            dict = {}
            logger.info('Enabling VPC Endpoint')
            ec2_resource = aws_connect_resource('ec2', REGION)
            for vpcid in reversed(endpoint_not_enabled):
                routelist = []
                filters = [{'Name':'vpc-id', 'Values':[vpcid]}]
                routes = list(ec2_resource.route_tables.filter(Filters=filters))
                for eachroute in routes:
                    routelist.append(eachroute.id)
                dict[vpcid] = routelist
                resp = ec2_client.create_vpc_endpoint(VpcId=vpcid, ServiceName='com.amazonaws.{}.s3'.format(REGION),
                                                      PolicyDocument=json.dumps(ENDPOINT_POLICY),RouteTableIds=dict[(vpcid)])
                if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                    logger.info("VPCEndpoint enabled for {} with ID: {}".format(vpcid, resp['VpcEndpoint']['VpcEndpointId']))
    except Exception as e:
        logger.error('Execution Failed while creating VPCEndpoint, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # Enable DNS Hostname
    try:
        logger.info('Enabling DNS Hostname')
        for vpcid in reversed(vpc_list):
            dns = ec2_client.modify_vpc_attribute(EnableDnsHostnames={'Value': True}, VpcId=vpcid)
        if dns['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info('DNS Hostname Enabled' )
    except Exception as e:
        logger.error('Error while enabling DNS Hostname, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

    # Enable VPC FLowlogs
    try:
        logger.info('Enabling VPC Flow logs')
        if flowlog_not_enabled == []:
            logger.info("Hurray! Flowlogs already enabled for all VPC's")
        else:
            for vpcid in reversed(flowlog_not_enabled):
                responses = ec2_client.create_flow_logs(DeliverLogsPermissionArn=rolearn,LogGroupName=vpcid,
                                                        ResourceIds=[vpcid],ResourceType='VPC',TrafficType='ALL')
                if responses['ResponseMetadata']['HTTPStatusCode'] == 200:
                    logger.info('VPC Flow logs Enabled: {}'.format(responses['FlowLogIds']))
    except Exception as e:
        logger.error('Error while enabling VPC FLowLogs, Exception: {}'.format(e))
        sys.exit(FAILED_EXIT_CODE)

def append_policy(policy):
    s3_bucket_policies = {
        "Version": "2012-10-17",
        "Statement": policy
    }
    return s3_bucket_policies

def enable_cloudtrail(BUCKETNAME,REGION, ACCOUNT):
    BUCKETNAME="{}-cloudtrail-bucket".format(ACCOUNT)
    s3_conn = aws_connect_client('s3', REGION)
    ct_conn = aws_connect_client('cloudtrail', REGION)

    # Create the bucket policy
    cloudtrail_bucket_policy = [
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AWSCloudTrailAclCheck20150319",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": "s3:GetBucketAcl",
                    "Resource": "arn:aws:s3:::{}".format(BUCKETNAME)
                },
                {
                    "Sid": "AWSCloudTrailWrite20150319",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": "s3:PutObject",
                    "Resource": "arn:aws:s3:::{}/AWSLogs/{}/*".format(BUCKETNAME,get_aws_account_id(REGION)),
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-acl": "bucket-owner-full-control"
                        }
                    }
                }
            ]
        }
    ]

    s3_bucket(BUCKETNAME, REGION)

    try:
        # Get bucket policy for the given Bucket
        policy = s3_conn.get_bucket_policy(Bucket=BUCKETNAME)
        bucket_policy = eval(policy['Policy'])
        bucket_policy_n = bucket_policy["Statement"]
        bucket_policy_new = bucket_policy_n + cloudtrail_bucket_policy
        trail_bucket_policy = append_policy(bucket_policy_new)
    except Exception as e:
        logger.error("Unable to get the bucket policy. Exception: {}".format(e))

    try:
        # Set the new policy on the given bucket
        resp = s3_conn.put_bucket_policy(Bucket=s3_bucket(BUCKETNAME,REGION), Policy=json.dumps(trail_bucket_policy, indent=4, sort_keys=True))
        if resp['ResponseMetadata']['HTTPStatusCode'] == 204:
            logger.info("The s3 bucket {} is updated with cloudtrail policy".format(BUCKETNAME))
    except Exception as e:
        logger.error("The s3 bucket {} is not updated with cloudtrail policy - Exception: {}".format(BUCKETNAME,e))
        raise e

    try:
        # Calling S3 function
        s3_bucket_name = s3_bucket(BUCKETNAME, REGION)
        cloudtrail_name = 'prod-all-region-trail'

        # Check for existing Multiregion enabled Trails
        cloudtrail_list = [trail['IsMultiRegionTrail'] for trail in ct_conn.describe_trails()['trailList']]
        if False in cloudtrail_list:
            response = ct_conn.create_trail(Name=cloudtrail_name,S3BucketName=s3_bucket_name,S3KeyPrefix="cloudtrail-logs",
                                            IncludeGlobalServiceEvents=True,IsMultiRegionTrail=True,EnableLogFileValidation=True)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                logger.info("Cloudtrail enabled for all regions")
            responses = ct_conn.start_logging(Name=cloudtrail_name)
            if responses['ResponseMetadata']['HTTPStatusCode'] == 200:
                logger.info("Cloudtrail started trailing in all the regions")
        else:
            logger.info("Yay! Cloudtrail enabled for all regions already")
    except Exception as e:
        logger.error("Unable to activate Cloudtrail for all regions - Exception: {}".format(e))
        sys.exit(FAILED_EXIT_CODE)

def enable_elb_connection_draining_crosszone_logging(BUCKETNAME, REGION):

    elb_account_id = {
        "us-east-1": "127311923021",
        "us-east-2": "033677994240",
        "us-west-1": "027434742980",
        "us-west-2": "797873946194",
        "ca-central-1": "985666609251",
        "eu-central-1": "054676820928",
        "eu-west-1": "156460612806",
        "eu-west-2": "652711504416",
        "eu-west-3": "009996457667",
        "ap-northeast-1": "582318560864",
        "ap-northeast-2": "600734575887",
        "ap-northeast-3": "83597477331",
        "ap-southeast-1": "114774131450",
        "ap-southeast-2": "783225319266",
        "ap-south-1": "718504428378",
        "sa-east-1": "507241528517",
        "us-gov-west-1": "048591011584",
        "cn-north-1": "638102146993",
        "cn-northwest-1": "037604701340"
    }

    # S3 Policy for ELB
    user_policy = \
    {
            "Version": "2012-10-17",
            "Statement": [{
        "Sid": "Stmt1429136633762",
          "Action": [
            "s3:PutObject"
          ],
          "Effect": "Allow",
          "Resource": "arn:aws:s3:::%s/*" % BUCKETNAME,
          "Principal": {
            "AWS": [elb_account_id[str(REGION)]]
          }
        }]
    }

    try:
        # Calling S3 function
        s3_bucket_name = s3_bucket(BUCKETNAME, REGION)

        elb_conn = aws_connect_client("elb", REGION)
        s3_conn = aws_connect_client("s3", REGION)
        resp = s3_conn.put_bucket_policy(Bucket=s3_bucket_name, Policy=json.dumps(user_policy,indent=4, sort_keys=True))
        if resp['ResponseMetadata']['HTTPStatusCode'] == 204:
            logger.info("The s3 bucket {} is updated with elb policy".format(BUCKETNAME))
    except Exception as e:
        logger.error("The s3 bucket {} is not updated with elb policy. Exception: {} ".format(BUCKETNAME,e))

    try:
        elb_list = [lb['LoadBalancerName'] for lb in elb_conn.describe_load_balancers()['LoadBalancerDescriptions']]


        for elbname in reversed(elb_list):
            elb_attributes = elb_conn.describe_load_balancer_attributes(LoadBalancerName=elbname)
            access_log = elb_attributes['LoadBalancerAttributes']['AccessLog']['Enabled']
            conn_drain = elb_attributes['LoadBalancerAttributes']['ConnectionDraining']['Enabled']
            cross_zone = elb_attributes['LoadBalancerAttributes']['CrossZoneLoadBalancing']['Enabled']
            conn_timeout = elb_attributes['LoadBalancerAttributes']['ConnectionSettings']['IdleTimeout']
            if conn_drain == False or cross_zone == False or conn_timeout != 300 or access_log == False:
                if access_log == False:
                    response = elb_conn.modify_load_balancer_attributes(LoadBalancerName=elbname,LoadBalancerAttributes={
                            'AccessLog': { 'Enabled': True,'S3BucketName': BUCKETNAME,'EmitInterval': 60,'S3BucketPrefix': 'ELB-logs/%s' % elbname}})
                    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                        logger.info("Enabled AccessLogs for {}".format(elbname))
                else:
                    logger.info("The access logs is already enabled for - {}".format(elbname))
                if conn_drain == False or cross_zone == False or conn_timeout != 300:
                    responses = elb_conn.modify_load_balancer_attributes( LoadBalancerName=elbname,
                                                          LoadBalancerAttributes={
                                                         'CrossZoneLoadBalancing': {'Enabled': True},
                                                         'ConnectionDraining': {'Enabled': True,'Timeout': 300},
                                                         'ConnectionSettings': {'IdleTimeout': 300}
                                                          } )
                    if responses['ResponseMetadata']['HTTPStatusCode'] == 200:
                        logger.info("Enabled Connection Draning: 300sec , CrossZoneLoadBalancing & IdleTimeout: 300sec for {}".format(elbname))

                else:
                    logger.info("The CrossZoneLoadBalancing,ConnectionDraining and ConnectionSettings is already enabled for - {}".format(elbname))
            else:
                logger.info(
                    "The AccessLogs (s3 bucket:- {}),CrossZoneLoadBalancing,ConnectionDraining and ConnectionSettings is already enabled for - {}".format(
                        s3_bucket_name,elbname))

    except Exception as e:
        logger.error("Failed bcoz not able to enable the ELB attributes. Exception: {}".format(e))
        sys.exit(FAILED_EXIT_CODE)

def update_iam_password_policy(REGION):
    iam_conn = aws_connect_client('iam',REGION)
    if not iam_conn:
        logger.error("Not able to connect to the IAM")
    try:
        response = iam_conn.update_account_password_policy(MinimumPasswordLength=12,RequireSymbols=True,
                                                           RequireNumbers=True,RequireUppercaseCharacters=True,
                                                           RequireLowercaseCharacters=True,AllowUsersToChangePassword=True,
                                                           MaxPasswordAge=90,PasswordReusePrevention=3)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info("The IAM password policy has been updated.")
    except Exception as e:
        logger.error("Execution Failed - Could not able to update the IAM policy. Exception: {}".format(e))
        sys.exit(FAILED_EXIT_CODE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AWS Initialization Script')
    parser.add_argument('--region', '-r', required=True, help='Specify the region.',type=str.lower)
    parser.add_argument('--s3name', '-s3', required=True, help='Specify the S3 Bucket Name, It should be unique',type=str.lower)
    parser.add_argument('--email', '-e', required=True, help="Specify the MailID's for SNS Topic, you can add multiple IDs with comma separated values (ex: suresh@gmail.com,mathan@outlook.com) without spaces",type=str.lower)
    parser.add_argument('--kind', '-k', required=True, help="Provide 'k8s' to configure the k8s security stuff related to aws resources like elb and vpc. Else, Provide 'all' to enable basic AWS Security recommendations",type=str.lower)
    parser.add_argument('--account', '-a', required=True, help="Provide the Environment like sherlock-prod,sherlock-stage or sherlock-dev",type=str.lower)

    args = parser.parse_args()
    s3_bucket(args.s3name, args.region)
    # Calling all the main functions
    if args.kind == 'k8s':
        logger.info("****** 1. Enabling the VPCEndpoint and Flowlogs ****** ")
        enable_vpc_endpoint(args.region)
        logger.info("****** 2. Enabling the TerminationProtection for all EC2 machines except ASG's if at all there is any Standalone server ******")
        enable_termination_protection('key', 'aws:autoscaling:groupName', args.region)
        logger.info("****** 3. Enabling the ELB Attributes ******")
        enable_elb_connection_draining_crosszone_logging(args.s3name, args.region)
    elif args.kind == 'all':
         logger.info("****** 1. Enabling the VPCEndpoint and Flowlogs ******")
         enable_vpc_endpoint(args.region.lower())
         logger.info("****** 2. Enabling the TerminationProtection for all EC2 machines except ASG's if at all there is any Standalone server ******")
         enable_termination_protection('key', 'aws:autoscaling:groupName', args.region.lower())
         logger.info("****** 3. Enabling the ELB Attributes ******")
         enable_elb_connection_draining_crosszone_logging(args.s3name, args.region)
         logger.info("****** 4. Enabling the AWSConfig for all the regions with SNS Topic and Notifications ******")
         enable_awsconfig(args.s3name.lower(),args.email.lower(), args.region.lower())
         logger.info("****** 5. Enabling the CloudTrail logs for all regions ****** ")
         enable_cloudtrail(args.s3name,args.region,args.account)
         logger.info("****** 6. Enabling the IAM Password Policy ******")
         update_iam_password_policy(args.region)
