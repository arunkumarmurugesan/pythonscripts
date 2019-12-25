#!/usr/bin/python
#title           : aws_route53_update.py
#author          : Arunkumar M
#date            : 20180824
#usage           : python aws_route53_update.py -r us-west-2 -elb <elbname> -d arun.example.com -c example.com
#==============================================================================

import boto3
import json, time, argparse, logging, sys
import datetime
import os

# Credentials
#AWS_ACCESS_KEY_ID=''
#AWS_SECRET_ACCESS_KEY=''

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
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
except KeyError:
    logger.error("Please set the environment variable AWS_ACCESS_KEY_ID")
    sys.exit(FAILED_EXIT_CODE)
try:
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
except KeyError:
    logger.error("Please set the environment variable AWS_SECRET_ACCESS_KEY")
    sys.exit(FAILED_EXIT_CODE)

# Connect to AWS boto3 Client
def aws_connect_client(service,REGION):
    try:
        # Gaining API session
        #session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        session = boto3.Session()
        # Connect the client
        conn_client = session.client(service, REGION)
    except Exception as e:
        logger.error('Could not connect to region: %s and resources: %s , Exception: %s\n' % (REGION, service, e))
        conn_client = None
    return conn_client

def update_cname_route53(REGION,ELB,DOMAIN):
	# connects to Route53
    r53_client = aws_connect_client('route53', REGION)
    HOSTEDZONEID="none"
    try:
        response = r53_client.change_resource_record_sets(
            HostedZoneId=HOSTEDZONEID,
            ChangeBatch={
                'Comment': 'Create/Update ELB dns entry',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': '{}'.format(DOMAIN),
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': 'xxxxDJxxxx',
                                'DNSName': '{}'.format(ELB),
                                'EvaluateTargetHealth': False
                            }
                        }
                    },
                ]
            }
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info('Route53 Alias was created for given domain name: {}'.format(DOMAIN))
    except Exception as e:
        logger.error('Not able to create route53 alias entry for given domain : {}, Exception: {}'.format(DOMAIN,e))
        raise e
        sys.exit(FAILED_EXIT_CODE)

def updateRoute53(REGION,DOMAIN_NAME,CLUSTER_NAME):
    r53_client = aws_connect_client('route53', REGION)
    HOSTEDZONEID = listHostedZone(REGION, DOMAIN_NAME)
    ELB = getELB(REGION,CLUSTER_NAME)
    CLUSTER_NAME = "api.{}".format(CLUSTER_NAME)
    try:
        response = r53_client.change_resource_record_sets(
            HostedZoneId=HOSTEDZONEID,
            ChangeBatch={
                'Comment': 'add %s -> %s' % (ELB, CLUSTER_NAME),
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': CLUSTER_NAME,
                            'Type': 'CNAME',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': ELB}]
                        }
                    }]
            })
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            logger.info('Route53 record set was created for given domain name: {} ELB: {}'.format(CLUSTER_NAME,ELB))

    except Exception as e:
        logger.error('Not able to create route53 record set entry for given domain : {}, Exception: {}'.format(CLUSTER_NAME,e))
        raise e
        sys.exit(FAILED_EXIT_CODE)

def getELB(REGION,CLUSERNAME):
	# connects to Route53
    conn = aws_connect_client('elb', REGION)
    loadbalancer = conn.describe_load_balancers().get('LoadBalancerDescriptions', [])
    for load in loadbalancer:
        LoadBalancerName = load['LoadBalancerName']
        response = conn.describe_tags(LoadBalancerNames=[LoadBalancerName])
        for t in response['TagDescriptions']:
            for tags in t.get('Tags'):
                if tags['Key'] == 'Name':
                    DOMAINNAME="api.{}".format(CLUSERNAME)
                    if tags.get('Value') == DOMAINNAME:
                        ELB=load['DNSName']
    return ELB

def listHostedZone(REGION,DOMAINNAME):
    conn = aws_connect_client('route53', REGION)
    response = conn.list_hosted_zones()
    print(json.dumps(response, indent= 4))
    for i in response['HostedZones']:
        if i['Name'] == "{}.".format(DOMAINNAME) and i['Config']['PrivateZone'] == False:
            HOSTEDZONEID = str(i['Id']).split("/")[2]
    return HOSTEDZONEID

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AWS Route53 Record Creation Script')
    parser.add_argument('--region', '-r', required=True, help='Specify the region.',type=str.lower)
    parser.add_argument('--loadbalancer', '-elb', help='Specify the ELB Name, It should be unique',type=str.lower)
    parser.add_argument('--domain', '-d', required=True, help='Specify the Domain Name, It should be unique',type=str.lower)
    parser.add_argument('--clustername', '-c', required=True, help='Specify the cluster name', type=str.lower)
    args = parser.parse_args()
    updateRoute53(args.region,args.domain,args.clustername)

