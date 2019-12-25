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
AWS_REGIONS = 'ap-southeast-1'


def ec2_connect(AWS_REGIONS):
#def ec2_connect(region, profile):
    """
    Connects to EC2, returns a connection object
    """
    try:
        session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
        #session = boto3.Session(region_name=region, profile_name=profile)
        conn = session.client('elbv2',AWS_REGIONS)
    except Exception, e:
        sys.stderr.write('Could not connect to region: %s. Exception: %s\n' % (AWS_REGIONS, e))
        conn = None
    return conn

def alb_add(Loadbalancer,TargetGroup,RulePath,Priority):
    # connects to ec2
    conn = ec2_connect(AWS_REGIONS)
    # conn = ec2_connect (region,profile)
    if not conn:
        sys.stderr.write('Could not connect to region: %s. Skipping\n' % AWS_REGIONS)
        exit(0)
    try:
        loadbalancer = conn.describe_load_balancers().get('LoadBalancers', [])
    except Exception, e:
        sys.stderr.write('Could not get ALB details from region: %s. Skipping (problem: %s)\n' % (loadbalancer, e.error_message))
        exit(0)

    for load in loadbalancer:
        lb_arn = load["LoadBalancerArn"]
        alb_name = load['LoadBalancerName']
        response = conn.describe_listeners(LoadBalancerArn=lb_arn)
        if alb_name == Loadbalancer:
            for i in response['Listeners']:
                DefaultActions = i['DefaultActions']
                response1 = conn.describe_target_groups(LoadBalancerArn=lb_arn)
                TargetGroups_list = response1['TargetGroups']
                for j in TargetGroups_list:
                    targetgroup_name = j['TargetGroupName']
                    if targetgroup_name == TargetGroup:
                        targetgroup_arn = j['TargetGroupArn']
                        ListenerArn = i['ListenerArn']
                        response = conn.create_rule(
                                Actions=[
                                {
                                    'TargetGroupArn': targetgroup_arn,
                                    'Type': 'forward',
                                },
                                ],
                                Conditions=[
                                {
                                    'Field': 'path-pattern',
                                    'Values': [
                                                RulePath,
                                            ],
                                        },
                                    ],
                                ListenerArn=ListenerArn,
                                Priority=int(Priority),
                                )
                        print response

if __name__ == '__main__':
    # Define command line argument parser
    parser = argparse.ArgumentParser(description='Add the Rules in Application Loadbalancer')
    parser.add_argument('--Loadbalancer', required=True, help='Specify the Loadbalancer Name')
    parser.add_argument('--TargetGroup', required=True, help='Specify the TargetGroup Name')
    parser.add_argument('--RulePath', required=True, help='Please specify the Rules Path that has to be add in ALB')
    parser.add_argument('--Priority', required=True, help='Specify the Priority. It must be integer value')

    args = parser.parse_args()
    # creates the report
    retval = alb_add (args.Loadbalancer, args.TargetGroup, args.RulePath, args.Priority)
    if retval:
        sys.exit (0)
    else:
        sys.exit (1)


