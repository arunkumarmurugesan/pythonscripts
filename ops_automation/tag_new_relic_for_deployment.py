#!/usr/bin/python
#__author__ = "Arun N"
#__version__ = "V2"
#__status__ = "Production Environment"

import sys
import requests
import json
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

name = raw_input("Who are you? (name): ")
Ticket_no = raw_input("Enter deployment description(Ticket no): ")
Revision_no = raw_input("Enter deploymnet revision (Revision no): ")
changelog = raw_input("Enter deployment changelog: ")

url= 'https://api.newrelic.com/v2/applications/xxxx/deployments.json'
payload  = {
"deployment":{
    "user": name,
    "revision":Ticket_no,
    "description":Revision_no,
    "changelog":changelog
  }
}

headers = {"X-Api-Key":"xxxxx","Content-Type":"application/json"}
r= requests.post(url, headers=headers, data=json.dumps(payload))
parsed = json.loads(r.text)
print json.dumps(parsed,indent=4, sort_keys=True)