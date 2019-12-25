#!/bin/python
import boto3
import time
client = boto3.client('codedeploy', region_name='ap-south-1', aws_access_key_id='xxx', aws_secret_access_key='xxxx')
# The time revision will take for deployment in seconds.
time.sleep(120)
response5 = client.list_deployments( applicationName='uat-deploy', deploymentGroupName='uat-deploy', includeOnlyStatuses=[ 'Created', 'Queued', 'InProgress', 'Succeeded', 'Failed', 'Stopped', ], )
print response5['deployments'][0]
last_success_Id = response5['deployments'][0]
response3 = client.get_deployment( deploymentId=last_success_Id )
print response3['deploymentInfo']['status']
Status = response3['deploymentInfo']['status']
if (Status == 'Failed'):
    response4 = client.create_deployment( applicationName=response3['deploymentInfo']['applicationName'], deploymentGroupName=response3['deploymentInfo']['deploymentGroupName'], revision={ 'revisionType': response3['deploymentInfo']['revision']['revisionType'], 's3Location': { 'bucket': response3['deploymentInfo']['revision']['s3Location']['bucket'], 'key': response3['deploymentInfo']['revision']['s3Location']['key'], 'bundleType': response3['deploymentInfo']['revision']['s3Location']['bundleType'], 'eTag': response3['deploymentInfo']['revision']['s3Location']['eTag'] }, }, deploymentConfigName=response3['deploymentInfo']['deploymentConfigName'], ignoreApplicationStopFailures=response3['deploymentInfo']['ignoreApplicationStopFailures'] )
    print response4['deploymentId']
