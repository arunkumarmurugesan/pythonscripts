
Introduction:
This document is a short description of aws security and compliance fix in Sherlock Production Account and How to remediate the AWS security gaps. 

The script enables following:
1. VPCEndpoint and Flowlogs for all VPC's in a provided region. If there is any VPC already with endpoint or flowlogs enabled, it will skip the same.
2. Termination protection for all Standalone EC2 machines except Autoscaling
3. ELB attributes like Connection draining ,ELB Access logs (escapes the ELB which already has Logs enabled), Crosszone Loadbalancing,DNS Hostname
4. AWS Config to store events triggered by AWS Resources for all regions, ignores if already enabled.
5. CloudTrail to monitor, governance & auditing in all regions for the actions performed, flies to next function if already enabled. 
6. The IAM Password Policy to avoid attacks (MinPasswordLength, Lowercase and Uppercase, Password Expiry, Password Re-Use)

What is this script for?
Let's say you want to check the log events occured in AWS like user's login and other activities. To do that you need to enable AWS Cloudtrail. Similar way, there are basic settings and recommdantions which needs to be enabled to safeguard your AWS account. They are,

 VPC Endpoint and Flow Logs
 Termination protection for Standalone EC2 machines
 ELB attributes like
a. Connection draining
b. ELB Access logs
c. Crosszone Loadbalancing
d. DNS Hostname
AWS Config for all regions with SNS E-mail Notification
CloudTrail logs for all regions
IAM Password Policy


Pre-Requisites
1. Install/Import Packages mentioned below:

Python3
pip
boto3
time
datetime
argparse
logging
2. Authentication

 Use an AWS Access and Secret Key with admin privileges to execute this script 
> AWS_ACCESS_KEY_ID='XXXXXX' 
> AWS_SECRET_ACCESS_KEY='YYYYYY'
(or)
If you have the keys already configured in your host, you can comment out the Environment variables and comment the keys sections.
 #Access the environment constants 
 #try: 
 #ACCESS_KEY = os.environ["AWS_ACCESS_KEY_ID"] 
 #except KeyError: 
 #logger.error("Please set the environment variable AWS_ACCESS_KEY_ID") 
 #sys.exit(FAILED_EXIT_CODE) 
 #try: 
 #SECRET_KEY = os.environ["AWS_SECRET_ACCESS_KEY"] 
 #except KeyError: 
 #logger.error("Please set the environment variable AWS_SECRET_ACCESS_KEY") 
 #sys.exit(FAILED_EXIT_CODE)
