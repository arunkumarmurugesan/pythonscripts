import json
import boto3

from collections import defaultdict
result = defaultdict(list)
port=[]
cidr=[]
result = {}
change = { "AuthorizeSecurityGroupIngress" : "addition of  inbound" , "RevokeSecurityGroupIngress" : "removal of inbound", "AuthorizeSecurityGroupEgress" :  "addition of  inbound", "RevokeSecurityGroupEgress" : "removal of outbound"   }

def evaluate_rules(event):
    if  event["detail"]["userIdentity"]["type"] == "AssumedRole":
        user_name = event["detail"]["userIdentity"]["principalId"].split(":")[1]
        group_id = event["detail"]["requestParameters"]["groupId"]
        change_type = event["detail"]["eventName"]
        for items in event["detail"]["requestParameters"]["ipPermissions"]["items"]:
            Toport = items['fromPort']
            Fromport =  items['toPort']
            if  items['ipRanges']:
                for cidr in items['ipRanges']['items']:
                    cidr_ip = cidr['cidrIp']
                    result[cidr_ip] = str(Toport) + "-" + str(Fromport)
            if  items['groups']:
                for sg in items['groups']['items']:
                    sg_id = sg['groupId']
                    result[sg_id] = str(Toport) + "-" + str(Fromport)

        text = "The user %s has modified the secuirty group - %s. The action %s has resulted in %s rules %s to the security group." %(user_name,group_id,change_type,change[change_type],result.items())

    elif event["detail"]["userIdentity"]["type"] == "IAMUser":
        user_name = event["detail"]["userIdentity"]["userName"]
        group_id = event["detail"]["requestParameters"]["groupId"]
        change_type = event["detail"]["eventName"]
        for items in event["detail"]["requestParameters"]["ipPermissions"]["items"]:
            Toport = items['fromPort']
            Fromport =  items['toPort']
            if  items['ipRanges']:
                for cidr in items['ipRanges']['items']:
                    cidr_ip = cidr['cidrIp']
                    result[cidr_ip] = str(Toport) + "-" + str(Fromport)
            if  items['groups']:
                for sg in items['groups']['items']:
                    sg_id = sg['groupId']
                    result[sg_id] = str(Toport) + "-" + str(Fromport)
        text = "The user %s has modified the secuirty group - %s. The action %s has resulted in %s rules %s to the security group." %(user_name,group_id,change_type,change[change_type],result.items())
    return text

def sns_topic(text):
    topicArn = 'arn:aws:sns:us-west-2:xxxx:notification'
    sns = boto3.client(service_name="sns") 
    sns.publish(
        TopicArn = topicArn,
        Message = text
    )
 
    return

        
# This is the main handle for the Lambda function.  AWS Lambda passes the function an event and a context.

def lambda_handler(event, context):
    print("event: ", json.dumps(event))
    text = evaluate_rules(event)
    sns_topic(text)
