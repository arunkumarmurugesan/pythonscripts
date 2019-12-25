import paramiko
from subprocess import *
import subprocess
import boto3

def ssh_into_server_check_nrt_queue(q_ip):
     c = paramiko.SSHClient()
     c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
     c.connect(hostname=q_ip, username="ubuntu")
     print "ssh connected"
     cmd="sudo supervisorctl status | grep -i 'NRT' | awk '{print $1}'"
     stdin, stdout, stderr = c.exec_command(cmd)
     output = stdout.read()
     if output:
        output = "'{}'".format(output)
        print output
        stdin, stdout, stderr = c.exec_command("sudo supervisorctl status " + output)
        j=stdout.read()
        print "Queue Found on the Server: %s and Status of the Queue: %s" %(q_ip,j)
     else:
        print "Queue not Found on the Server: %s" %(q_ip)

def get_qworker_ip():
    ec2 = boto3.resource('ec2', region_name='ap-south-1')  # call ec2 recourse to perform further actions
    response = ec2.instances.filter(Filters=[{'Name': 'tag:module', 'Values': ['qworker']},{'Name': 'instance-state-name','Values': ['running']}])
    #   Get information for all running instances
    for instance in response:
        q_ip=instance.private_ip_address
        ssh_into_server_check_nrt_queue(q_ip)
if __name__ == '__main__':
    get_qworker_ip()
