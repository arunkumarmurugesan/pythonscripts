import os
import boto
import datetime
import time

AWS_ACCESS_KEY_ID = '******'
AWS_ACCESS_KEY_SECRET = '******'
# hour, minute, second = time.strftime("%H:%M:%S").split(":")
# print hour, minute, second
#backup directories to s3
destdir = ""
sourcedir = " "
#specify bucket name or create a new bucket below
bucket = "prod-aerospike"
#destination directory name in s3
namespace = "prodenv"

def getbackup():
    curr_date = time.strftime("%d%m%Y")
    print curr_date

    # curr_time = time.strftime("%H_%M_%S")
    set_list = ""
    bin_list = ""
    # host = "" #host IP address
    port = "3000" #port number
    node_list = "127.0.0.1:3000" #node-list
    parallel = "1" #mention no of nodes to be backed up in parallel


    d = "/mnt/"
    directory = d + namespace +"_" + curr_date
    exec_comm = "asbackup --node-list %s --directory %s --namespace %s --set %s --bin-list %s >> /opt/logs/aerospike.log 2>&1" %(node_list, directory, namespace, set_list, bin_list)
    print exec_comm
    output = os.system(exec_comm)
    os.system('echo "\n" >> /opt/logs/aerospike.log')
    getOldDirs(sourcedir, 2)

# check for directories older than 5 days
def getOldDirs(dirPath, olderThanDays):
    print "getOldIdre"
    """ return a list of all subfolders under dirPath older than olderThanDays """
    olderThanDays *= 86400
    # convert days to seconds
    present = time.time()
    for root, dirs, files in os.walk(dirPath, topdown=False):
        for name in dirs:
            subDirPath = os.path.join(root, name)
            if (present - os.path.getmtime(subDirPath)) > olderThanDays:
                #print os.path.relpath(subDirPath)
                dir_to_backup = os.path.abspath(subDirPath)
                s3_backup(dir_to_backup)



def s3_backup(dir_name):
    print "s3_backup"
    uploadFiles = []
    conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY_SECRET)
    for path, subdirs, files in os.walk(dir_name):
        for name in files:
            uploadFiles.append(os.path.join(path, name))

    for files in uploadFiles:
        destpath = os.path.join(destdir, files)
        sourcepath = os.path.join(sourcedir, files)
        bucketobj = conn.get_bucket(bucket)
        k = boto.s3.key.Key(bucketobj)
        k.key = destpath
        print files
        k.set_contents_from_filename(k.key)
        f = open('/opt/logs/backup.log','a')
        timenow = datetime.datetime.now()
        f.write('Uploaded '+files+' to '+namespace+' at '+str(timenow)+'\n')

getbackup()

getOldDirs("/mnt/",0)
os.system('sudo find /mnt/* -mtime +5 -exec rm -rf {} \;')