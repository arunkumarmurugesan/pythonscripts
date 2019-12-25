#!/usr/bin/python -w

import argparse
import os
import boto3
import logging
import sys
import time
import datetime
from botocore.client import Config

#set the log file name
timestr = time.strftime("%Y%m%d-%H%M%S")

#Create a log directory
pwd_dir = os.getcwd()
log_dir = pwd_dir+'/log'
if not os.path.exists(log_dir):
    try:
        os.makedirs(log_dir)
    except Exception, e :
       print ('Could not create the directory: Exception: %s\n' % (e))
       sys.exit(1)

log = log_dir+"/"+"s3_set_expire-"+timestr+".log"
# create logger
logger = logging.getLogger("s3_set_expire")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)


#create file handler and set level to debug

handler = logging.FileHandler(log)
handler.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter to ch and handler
ch.setFormatter(formatter)
handler.setFormatter(formatter)

# add ch and handler  to logger
logger.addHandler(ch)
logger.addHandler(handler)

count = 1

def expire_cal(expire_sec):
    today_obj = datetime.datetime.now()
    delta_obj = datetime.timedelta(seconds=expire_sec)
    return(today_obj + delta_obj)


def check_bucket(source_bucket,dest_bucket):
    s3 = boto3.resource('s3')
    result = s3.Bucket(source_bucket) in s3.buckets.all()
    if not result:
        logger.error("The bucket : %s doesn't exists " % source_bucket )
        sys.exit(1)
    result = s3.Bucket(dest_bucket) in s3.buckets.all()
    if not result:
        logger.error("The bucket : %s doesn't exists " % dest_bucket)
        sys.exit(1)



def set_expire(source_bucket,dest_bucket, dry, folder):
    global count
    s3_resource = boto3.resource('s3')
    # Get a service client for Singapore region
    s3 = boto3.client('s3', 'ap-south-1', config=Config(signature_version='s3v4'))
    # Get a service client for the Mumbai region
    source_client = boto3.client('s3', 'ap-southeast-1', config=Config(signature_version='s3v4'))
    dest_resource = boto3.resource('s3', 'ap-south-1', config=Config(signature_version='s3v4'))
    # Copies object located in mybucket at mykey in ap-southeast-1 region
    # to the location otherbucket at otherkey in the ap-south-1 regio

    target_bucket = s3_resource.Bucket(source_bucket)
    if folder:
        condition = target_bucket.objects.filter(Prefix=folder)
    else:
        condition = target_bucket.objects.filter()
    for obj_new in condition:
        obj = obj_new.key
        if obj.endswith('.css'):
            contentType = 'text/css'
            CacheControl = 'max-age=2592000'
            expire_sec = 2592000
        elif obj.endswith('.CSS'):
            contentType = 'text/css'
            CacheControl = 'max-age=2592000'
            expire_sec = 2592000
        elif obj.endswith('.js'):
            #set the expiration for 1 week of expiry
            contentType = 'application/javascript'
            CacheControl = 'max-age=604800'
            expire_sec = 604800
        elif obj.endswith('.JS'):
            #set the expiration for 1 week of expiry
            contentType = 'application/javascript'
            CacheControl = 'max-age=604800'
            expire_sec = 604800
        elif obj.endswith('.jpg'):
            contentType = 'image/jpeg'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        elif obj.endswith('.JPG'):
            contentType = 'image/jpeg'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        elif obj.endswith('.png'):
            contentType = 'image/png'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        elif obj.endswith('.PNG'):
            contentType = 'image/png'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        elif obj.endswith('.gif'):
            contentType = 'image/gif'
            CacheControl = 'max-age=31536000'
            expire_sec =  31536000
        elif obj.endswith('.GIF'):
            contentType = 'image/gif'
            CacheControl = 'max-age=31536000'
            expire_sec =  31536000
        elif obj.endswith('.tiff'):
            contentType = 'image/tiff'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        elif obj.endswith('.ico'):
            contentType = 'image/x-icon'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        else:
            contentType = 'application/octet-stream'
            CacheControl = 'max-age=31536000'
            expire_sec = 31536000
        expire_date_obj = expire_cal(expire_sec)
        expire_date_obj_aware = datetime.datetime.strftime (expire_date_obj, '%Y-%m-%d %H:%M:%s')
        if not dry:
            logger.info("Updating cache headers of  object -  %s in bukcet %s " % (obj, source_bucket))
            try:
                copy_source = {
                'Bucket': source_bucket,
                'Key': obj
            }
                api_client = dest_resource.meta.client
                response = s3.copy(copy_source, dest_bucket, obj, SourceClient=source_client)
                response1 = api_client.copy_object(Bucket=dest_bucket, Key=obj, ContentType=contentType,   Expires=expire_date_obj,
                                                  CacheControl=CacheControl,
                                                  MetadataDirective="REPLACE", CopySource=dest_bucket + "/" + obj)
            except Exception as e:
                logger.error("Unable to set the cache headers of  object - %s in bukcet %s Error - %s=============\
                                =====================" % (obj, dest_bucket,e.message))
            else:
                logger.info("Completed  : %d. Src_bucket - %s, Dest_bucket - %s, Object  - %s, Content-Type - %s, Max-age - %s, Expire - %s\n==========================\n" % (count, source_bucket, dest_bucket, obj, contentType, CacheControl,expire_date_obj_aware))
        else:
            logger.info("%d. Src_bucket - %s, Dest_bucket - %s, Object  - %s, Content-Type - %s, Max-age - %s, Expire - %s\n===================================================\n" % (count, source_bucket, dest_bucket, obj, contentType, CacheControl,expire_date_obj_aware))
        count += 1


def main():
    # get arguments
    arg_parser = argparse.ArgumentParser(description='Set the content type for existing indiatv static web resources in an S3 bucket')
    arg_parser.add_argument('-sb', '--sourcebucket',
                            help='The name of the bucket you wish to copy files to, the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are used for your credentials',
                            required=True)
    arg_parser.add_argument('-db', '--destbucket',
                            help='The name of the bucket you wish to copy files to, the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are used for your credentials',
                            required=True)
    arg_parser.add_argument('-n', '--dry-run', action='store_true', dest='dry', help='run without uploading any files')
    arg_parser.add_argument('-f', '--folder', dest='folder', help='set the folder location, So the cache settings will apply only for these folder')
    args = arg_parser.parse_args()

    # connect to S3
    source_bucket = args.sourcebucket
    dest_bucket = args.destbucket
    dry = args.dry
    folder = args.folder
    check_bucket(source_bucket,dest_bucket)
    set_expire(source_bucket,dest_bucket, dry, folder)


if __name__ == '__main__':
    main()

