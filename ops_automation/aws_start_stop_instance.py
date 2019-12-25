import boto.ec2
import sys
access_id='xxx'
secret__key='xxx'
region='us-east-1'


def print_usage(args):
  print 'Usage:', args[0], 'stop|start <instance name>'
  sys.exit(1)

def usage(args):
  arg1 = ['stop', 'start']
  if not len(args) == 3:
    print_usage(args)
  else:
    if not args[1] in arg1:
      print_usage(args)
    else:
      return args[2]


myinstance = usage(sys.argv)

conn = boto.ec2.connect_to_region(region, aws_access_key_id=access_id, aws_secret_access_key=secret__key)

if sys.argv[1] == 'start':
  try:
    inst = conn.get_all_instances(filters={'tag:Environment': myinstance})[0].instances[0]
  except IndexError:
    print 'Error:', myinstance, 'not found!'
    sys.exit(1)
  if not inst.state == 'running':
    print 'Starting', myinstance
    inst.start()
  else:
    print 'Error:', myinstance, 'already running or starting up!'
    print inst
    sys.exit(1)

if sys.argv[1] == 'stop':
  try:
    inst = conn.get_all_instances(filters={'tag:Environment': myinstance})[0].instances[0]
  except IndexError:
    print 'Error:', myinstance, 'not found!'
    sys.exit(1)
  if inst.state == 'running':
    print 'Stopping', myinstance
    inst.stop()
    print inst
  else:
    print 'Error:', myinstance, 'already stopped or stopping'
    sys.exit(1)