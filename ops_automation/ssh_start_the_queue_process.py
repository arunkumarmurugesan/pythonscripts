import subprocess
import json
import re
import boto3
import paramiko
from subprocess import *
import time
import logging


def queue_start_stop():
    ec2 = boto3.resource('ec2', region_name='ap-south-1')  # call ec2 recourse to perform further actions
    response = ec2.instances.filter(
    Filters=[{'Name': 'tag:module', 'Values': ['qworker']}, {'Name': 'instance-state-name', 'Values': ['running']}])
#  Get information for all running instances
    for instance in response:
        q_ip = instance.private_ip_address
        try:
            q_ip = instance.private_ip_address
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(hostname=q_ip, username="ubuntu")
        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials: %s")
        except paramiko.SSHException as sshException:
            print("Unable to establish SSH connection: %s" % sshException)
        except paramiko.BadHostKeyException as badHostKeyException:
            print("Unable to verify server's host key: %s" % badHostKeyException)
        except Exception as e:
            print(e.args)
        try:
            cmd = "sudo supervisorctl status | grep -i 'DEV' | awk '{print $1}'"
            stdin, stdout, stderr = c.exec_command(cmd)
            output = stdout.read()
        except Exception as e:
            print("Unable to get the supervisorctl status for DEV queue: %s", e)
        try:
            if output:
                output = "'{}'".format(output)
                stdin, stdout, stderr = c.exec_command("sudo supervisorctl status " + output)
                q_status=stdout.read()
                state = str(state)
                #Stop the DEV queue if it's in RUNNING state
                if state in str(q_status) and state == "RUNNING":
                    #cmd = "sudo supervisorctl stop DEVQueue_bbasync:*"
                    # #stdin, stdout, stderr = c.exec_command(cmd)
                    stdin, stdout, stderr = c.exec_command("sudo supervisorctl status " + output)
                    j = stdout.read()
                    print("Found the DEV Queue on the Qworker - {} and stopped DEV Queue - {}".format(q_ip, j))
                elif state == "RUNNING":
                    print("Found the DEV Queue on the Qworker - {} and and its already in STOPPED state".format(q_ip))
                if state in str(q_status) and state == "STOPPED":
                    #cmd = "sudo supervisorctl start DEVQueue_bbasync:*"
                    #stdin, stdout, stderr = c.exec_command(cmd)
                    stdin, stdout, stderr = c.exec_command("sudo supervisorctl status " + output)
                    j = stdout.read()
                    print("Found the DEV Queue on the Qworker - {} and starting  DEV Queue - {}".format(q_ip, j))
                elif state == "STOPPED":
                    print("Found the DEV Queue on the Qworker - {} and and its already in RUNNING state".format(q_ip))
        except Exception as e:
            print("Unable to check status for DEV queue: %s", e)

    else:
        print("DEV Queue not Found on the Server: %s" % (q_ip))
if __name__ == '__main__':
    queue_start_stop()