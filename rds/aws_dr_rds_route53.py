import os, sys, time
import boto3
import argparse

# Defaults, can be modified
AWS_ACCESS_KEY = 'xxxx'
AWS_SECRET_KEY = 'xxxx'

AWS_REGION = 'ap-southeast-1'
AWS_PROFILE = u'xxx_CoreEngineering'


def aws_rds_connect(region):
    # def aws_rds_connect(region, profile):
    """
    Connects to RDS, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        #session = boto3.Session(region_name=region, profile_name=profile)
        # Connect the RDS
        conn_rds = session.client('rds', region)
        # Connect the Route53
        conn_r53 = session.client('route53')

    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (region, e))
        conn_rds = None
    return conn_rds


def aws_route53_connect(profile):
    # def aws_route53_connect(AWS_PROFILE):
    """
    Connects to Route53, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        #session = boto3.Session(profile_name=AWS_PROFILE)
        # Connect the Route53
        conn_r53 = session.client('route53')

    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (AWS_PROFILE, e))
        conn_r53 = None
    return conn_r53

def promote_rds_to_master(region,profile,DBInstance):
    # connects to ec2
    conn = aws_rds_connect(region)
    # conn = aws_rds_connect (region,profile)
    if not conn:
        sys.stderr.write('Could not connect to region: %s. Skipping\n' % region)

    # list all db instances
    rdb = conn.describe_db_instances().get('DBInstances', [])
    for dbinstance in rdb:
        start_time = time.time()
        # print dbinstance['DBInstanceIdentifier']
        DBInstanceIdentifier = dbinstance['DBInstanceIdentifier']
        DBEndpoint = dbinstance['Endpoint']
        status = dbinstance['DBInstanceStatus']
        Address = DBEndpoint['Address']
        if DBInstance == DBInstanceIdentifier:
            response = conn.promote_read_replica(DBInstanceIdentifier=DBInstanceIdentifier, BackupRetentionPeriod=2)
            time.sleep(10)
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                print "Successfully Promoted the RDS as Master : %s" %Address
            running = True
            while running:
                response = conn.describe_db_instances(DBInstanceIdentifier=DBInstanceIdentifier)
                db_instances = response['DBInstances']
                db_instance = db_instances[0]
                status = db_instance['DBInstanceStatus']
                time.sleep(10)
                print 'Last DB status: %s' % status
                if status == 'available':
                    print "DB instance ready : %s" %Address
                    running = False
                    end_time = time.time()
                    print "RDS Promote took {} minutes to execute.".format((end_time - start_time) / 60.)


def update_cname_route53(region,profile,HostedZoneId,SourceDomainName,ELBName):
    # connects to Route53
    conn = aws_route53_connect(region)
    # conn = aws_route53_connect (region,profile)
    if not conn:
        sys.stderr.write('Could not connect to region: %s. Skipping\n' % region)
    start_time = time.time()
    ### Can be modified as per need. Define the HostedZone ID, DomainName and TargetName (CNAME of ELB) #####

    try:
        response = conn.change_resource_record_sets(
                HostedZoneId=HostedZoneId,
                ChangeBatch={
                    'Comment': 'update elb name',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': SourceDomainName,
                                'Type': 'CNAME',
                                'TTL': 300,
                                'ResourceRecords': [{'Value': ELBName}]
                            }
                        }]
                })

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print "Successfully updated the CNAME : %s" %ELBName
    except Exception as e:
        print e
    end_time = time.time()
    print "Route53 update took {} minutes to execute.".format((end_time - start_time) / 60.)


if __name__ == '__main__':
    # Define command line argument parser
    parser = argparse.ArgumentParser(description='DR setup script. As first phase it will promote the read replica rds to master and will update the ELB name in Route53')
    parser.add_argument('--Region', required=True,help='AWS region required to promote the RDS as Master')
    parser.add_argument('--Profile', required=True,help='AWS profile required to promote the RDS as Master and route the traffic in Route53')
    parser.add_argument('--DBInstanceIdentifier', required=True, help='Specify the RDS DB Instance Name')
    parser.add_argument('--HostedZoneId', required=True, help='Specify the HostedZoneId of Domain. It will be in Route53')
    parser.add_argument('--SourceDomainName', required=True, help='Specify the Domain Name')
    parser.add_argument('--ELBName', required=True, help='Specify the ELB Name which is required to update the Route53')
    args = parser.parse_args()

    promote_rds_to_master (args.Region, args.Profile, args.DBInstanceIdentifier)
    time.sleep(5)
    update_cname_route53(args.Region, args.Profile, args.DBInstanceIdentifier, args.HostedZoneId, args.SourceDomainName, args.ELBName)

