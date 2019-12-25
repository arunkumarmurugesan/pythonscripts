import os, sys
import argparse
import re
import parser
import dateutil
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
import datetime
import pytz

# Defaults, can be modified
AWS_ACCESS_KEY = 'xx'
AWS_SECRET_KEY = 'xx'
AWS_REGIONS = 'us-east-1'

session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY,region_name=AWS_REGIONS)
print session
# session = boto3.Session(region_name=region, profile_name=profile)
# Get the service resource.
resource = boto3.resource('dynamodb', AWS_REGIONS)
client   = boto3.client('dynamodb', AWS_REGIONS)
print resource
print client

table_to_create = 'SampleTable'
print "Checking if table exists"
table_exists = False

try:
  tabledescription = client.describe_table(TableName=table_to_create)
  print "Table already exists"
  print "Table descriptiuon:"
  print tabledescription
  table_exists = True
except Exception as e:
    if "Requested resource not found: Table" in str(e):
        print "Table does not exist"
        print "Creating table"
        table = resource.create_table(
          TableName            =table_to_create,
          KeySchema            =[{'AttributeName': 'Company_Name'   ,'KeyType': 'HASH' },
                                 {'AttributeName': 'Department_Name','KeyType': 'RANGE'}
                                ],
          AttributeDefinitions =[{'AttributeName': 'Company_Name','AttributeType': 'S' },
                                 {'AttributeName': 'Department_Name','AttributeType': 'S'},
                                ],
          ProvisionedThroughput={'ReadCapacityUnits': 10,'WriteCapacityUnits': 10}
        )
table = resource.Table(table_to_create)
print table
response = table.scan()
print "\nCounting all records (using table scan)"
print "Real Item Count:" + str(response['Count'])

print "\nInserting Records"
print "looking up record : Employee table"
response = table.query(KeyConditionExpression=Key('Company_Name').eq('Capitalone') & Key('Department_Name').eq('Ops'))
if response[u'Count'] == 0:
  print "employee table record not found, inserting"
  table.put_item(Item={'Department_Name': 'Ops', 'Company_Name' : 'Capitalone', 'description' : 'Employee table', 'insert_timestamp': datetime.datetime.now(tz=pytz.utc).isoformat() })

print "looking up record : Employee table"
response = table.query(KeyConditionExpression=Key('Company_Name').eq('Capitalone') & Key('Department_Name').eq('Dev'))
if response[u'Count'] == 0:
  print "employee table record not found, inserting"
  table.put_item(Item={'Department_Name': 'Dev', 'Company_Name' : 'Capitalone', 'description' : 'Employee table', 'insert_timestamp': datetime.datetime.now(tz=pytz.utc).isoformat() })

print "looking up record : Development table"
response = table.query(KeyConditionExpression=Key('Company_Name').eq('Capitaltwo') & Key('Department_Name').eq('Ops'))
if response[u'Count'] == 0:
  print "employee table record not found, inserting"
  table.put_item(Item={'Department_Name': 'Ops', 'Company_Name' : 'Capitaltwo', 'description' : 'Development table', 'insert_timestamp': datetime.datetime.now(tz=pytz.utc).isoformat() })

print "looking up record : Development table"
response = table.query(KeyConditionExpression=Key('Company_Name').eq('Capitaltwo') & Key('Department_Name').eq('Dev'))
if response[u'Count'] == 0:
  print "employee table record not found, inserting"
  table.put_item(Item={'Department_Name': 'Dev', 'Company_Name' : 'Capitaltwo', 'description' : 'Development table', 'insert_timestamp': datetime.datetime.now(tz=pytz.utc).isoformat() })

print "\nscanning table (retrieving all records)"
response = table.scan()
i = 0
for item in response['Items']:
    i = i + 1
    print str(i), ":", item['Department_Name'], ":", item['Company_Name'], ":", item['description'], ":", item['insert_timestamp']



