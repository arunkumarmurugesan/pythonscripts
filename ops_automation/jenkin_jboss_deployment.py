#!/usr/bin/python
import sys
import urllib2  
import base64
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

def py_mail(SUBJECT, BODY, TO, FROM):
    """With this function we send out our html email"""
 
    # Create message container - the correct MIME type is multipart/alternative here!
    MESSAGE = MIMEMultipart('alternative')
    MESSAGE['subject'] = SUBJECT
    MESSAGE['To'] = ", ".join(TO)
    MESSAGE['From'] = FROM
    MESSAGE.preamble = """
Your mail reader does not support the report format.
Please visit us <a href="http://www.mysite.com">online</a>!"""
 
    # Record the MIME type text/html.
    HTML_BODY = MIMEText(BODY, 'html')
 
    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    MESSAGE.attach(HTML_BODY)
 
    # The actual sending of the e-mail
    server = smtplib.SMTP('10.xx.xx.xx:25')
 
    # Print debugging output when testing
    server.sendmail(FROM, TO, MESSAGE.as_string())
    server.quit()

def email_content(BUILD_STATUS,BUILD_APPLICATION,BUILD_TAG,SVN_FOLDER,BUILD_USER,TICKET_NUMBER,BUILD_NUMBER,ENV,color_code):
  email_content =  """<div style="background:#eee;border:1px solid #ccc;padding:5px 10px"><span style="font-size:14px"><strong><span style="text-decoration:underline">Build Result</span></strong></span></div>

<p><span style="font-size:10px;">ENVIRONMENT : ${ENV}</span></p>

<p><span style="font-size:10px;">SVN FOLDER : ${SVN_FOLDER}</span></p>

<p><span style="font-size:10px;">TAG NAME&nbsp;: ${BUILD_TAG}</span></p>

<p><span style="font-size:10px;">TICKET NUMBER&nbsp;: ${TICKET_NUMBER}</span></p>

<p><span style="font-size:10px;">MODULE&nbsp;: ${BUILD_APPLICATION}</span></p>

<p><span style="font-size:10px;">BUILD NUMBER&nbsp;: ${BUILD_NUMBER}</span></p>

<p><span style="font-size:10px;">BUILD TRIGGERED&nbsp;BY : ${BUILD_USER}</span></p>

<p><span style="font-size:10px;"><strong>STATUS</strong>&nbsp;: <font color="${color_code}">${BUILD_STATUS}</font></span></p>


"""
  s = Template(email_content).safe_substitute(BUILD_TAG=BUILD_TAG,TICKET_NUMBER=TICKET_NUMBER,BUILD_NUMBER=BUILD_NUMBER,BUILD_STATUS=BUILD_STATUS,BUILD_USER=BUILD_USER,SVN_FOLDER=SVN_FOLDER,ENV=ENV,BUILD_APPLICATION=BUILD_APPLICATION,color_code=color_code)
  FROM = 'arun@gmail.con'
  TO = ['arun@jar.com']
  py_mail("Project App01 - " + ENV + " | Build - " + BUILD_STATUS , s, TO, FROM)


def auth_headers(username, password):
  return 'Basic ' + base64.encodestring('%s:%s' % (username, password))[:-1]

def jenkins_url ():
  
  jenkins_user = "arun"
  jenkins_pwd = "arun"
  jenkinsUrl = "https://x.x.x.x/job"
  jobName = "/Prod_Build/job/project_sit_build"
  headers = {'Authorization': auth_headers(jenkins_user,jenkins_pwd)}  
  request = urllib2.Request(jenkinsUrl + jobName + "/lastBuild/api/json",None, headers)
  response = None
  
  try:
    response = urllib2.urlopen(request)
  except urllib2.URLError as uerr:
    print(uerr.msg)
    sys.exit(2)
  try:
    buildStatusJson = json.load(response)
  except:
    print "Failed to parse json"
    sys.exit(3)

  if buildStatusJson.has_key( "result" ):
    BUILD_STATUS = buildStatusJson["result"]
  if buildStatusJson.has_key("displayName"):
    BUILD_NUMBER = buildStatusJson["displayName"]
  if buildStatusJson.has_key( "actions" ):
    for content in buildStatusJson["actions"]:
      if 'parameters' in content:
        parm = content['parameters']
        for mode in parm:
          if mode['name'] == 'application':
            BUILD_APPLICATION = mode.get('value')
          if mode['name'] == 'svn_folder':
            SVN_FOLDER = mode.get('value')
          if mode['name'] == 'stream_name':
            BUILD_TAG = mode.get('tag')
	  if mode['name'] == 'environment':
            ENV = mode.get('value')
	  if mode['name'] == 'ticket_number':
            TICKET_NUMBER = mode.get('value')
      if 'causes' in  content:
        parm = content['causes']
        for mode in parm:
            BUILD_USER = mode.get('userName')
  if BUILD_STATUS == "FAILURE":
    color_code = "#ff0000"
  if BUILD_STATUS == "SUCCESS":
    color_code = "#00ff00"
  email_content(BUILD_STATUS,BUILD_APPLICATION,BUILD_TAG,SVN_FOLDER,BUILD_USER,TICKET_NUMBER,BUILD_NUMBER,ENV,color_code)
if __name__ == '__main__':
  jenkins_url ()

