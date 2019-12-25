import os, sys
import boto3
import json
import string
import csv

profile=""
filepath = "iam-role-report.csv"

#session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_KEY)
session = boto3.Session(profile_name=profile)
conn = session.client('iam')

f = file(filepath, 'wt')
writer = csv.writer (f)
writer.writerow (['RoleName','RoleArn','AssumeRolePolicyDocument','ManagedPolicyName','ManagedPolicyARN','InlinePolicyName','InlineJson'])

with open('C:/Users/arunkumar/Desktop/text.txt', "r") as f:
    for line in f:
        roles = line.rstrip('\n')

        ManagedPolicyARN = None
        ManagedPolicyName = None
        AttachedPolicies = None
        InlinePolicyNames = None
        InlinePolicyJson = None

        roles_des = conn.get_role(RoleName=roles)
        role_list = roles_des['Role']
        policy_arn = role_list['Arn']
        role_name = role_list['RoleName']
        AssumeRolePolicyDocument = role_list["AssumeRolePolicyDocument"]
        json_pre = json.dumps(AssumeRolePolicyDocument)
        json_pos = json_pre.translate(None, string.whitespace)
        AssumeRolePolicyDocument = json_pos

        list_attached_policies = conn.list_attached_role_policies(RoleName=role_name)
        AttachedPolicies = list_attached_policies['AttachedPolicies']
        ManagedPN= []
        ManagedPARN= []
        if AttachedPolicies is not None:
            for list in AttachedPolicies:
                ManagedPolicyName=list["PolicyName"]
                ManagedPolicyName= ''.join(ManagedPolicyName)
                ManagedPolicyARN=list["PolicyArn"]
                ManagedPN.append(ManagedPolicyName)
                ManagedPARN.append(ManagedPolicyARN)

        list_inline_policies = conn.list_role_policies(RoleName=role_name)
        InlinePolicyNames = list_inline_policies['PolicyNames']
        InlinePolicyJson= []
        InlinePN= []
        if InlinePolicyNames is not None:
            for list_policy in InlinePolicyNames:
                InlinePN.append(list_policy)
                response1 = conn.get_role_policy(RoleName=role_name, PolicyName=list_policy)
                data = response1['PolicyDocument']
                json_pre = json.dumps(data)
                json_pos = json_pre.translate(None, string.whitespace)
                InlinePolicyJson.append(json_pos)

        print role_name,policy_arn,AssumeRolePolicyDocument,ManagedPN,ManagedPARN,InlinePN,InlinePolicyJson
        # print ManagedPolicyName
        writer.writerow([role_name, policy_arn, AssumeRolePolicyDocument,ManagedPN, ManagedPARN, InlinePN, InlinePolicyJson])
    f.close()
f.close()
