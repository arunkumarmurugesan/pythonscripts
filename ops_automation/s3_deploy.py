#!/usr/bin/python -w

import argparse
import os
import boto3
import logging
import sys
import time

#set the  variables
count = 1
extensions = ['.jpg', '.png' , '.gif' , '.png' , '.tiff', '.ico' , '.css' , '.js' ]
exists = True

#set the log file name
timestr = time.strftime("%Y%m%d-%H%M%S")
log = "s3_deploy-"+timestr+".log"



# create logger
logger = logging.getLogger("s3_deploy")
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


def s3_connect_resource():
    """
    Connects to S3, returns a connection object
    """
    try:
        s3_resource = boto3.resource('s3')

    except Exception, e:
        sys.stderr.write ('Could not connect to S3. Exception: %s\n' % (e))
        s3_resource = None
    return s3_resource


def s3_connect_client():
    """
    Connects to S3, returns a connection object
    """
    try:
        s3_client = boto3.client('s3')

    except Exception, e:
        sys.stderr.write('Could not connect to S3. Exception: %s\n' % (e))
        s3_client = None
    return s3_client

def check_bucket(bucket):
    s3 = s3_connect_resource()
    result = s3.Bucket(bucket) in s3.buckets.all()
    if not result:
    	logger.error("The bucket : %s doesn't exists " % bucket )
	sys.exit(1)


def metadata_config(extension):
    if extension in extensions and extension == '.css':
        # set the expiration for 1 month expiry
        contentType = 'text/css'
        CacheControl = 'max-age=2592000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }
    elif extension in extensions and extension == '.js':
        # set the expiration for 1 week of expiry
        contentType = 'application/javascript'
        CacheControl = 'max-age=604800'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }

    elif extension in extensions and extension == '.jpg':
        # set the expiration for 1 year of expiry
        contentType = 'image/jpeg'
        CacheControl = 'max-age=31536000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }
    elif extension in extensions and extension == '.png':
        contentType = 'image/png'
        CacheControl = 'max-age=31536000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }
    elif extension in extensions and extension == '.gif':
        contentType = 'image/gif'
        CacheControl = 'max-age=31536000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }

    elif extension in extensions and extension == '.mp4':
        contentType = 'video/mp4'
        CacheControl = 'max-age=31536000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }

    elif extension in extensions and extension == '.mpeg':
        contentType = 'video/mpeg'
        CacheControl = 'max-age=31536000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }

    else:
        contentType = 'application/octet-stream'
        CacheControl = 'max-age=31536000'
        metadata = {
            'ContentType': contentType,
            'CacheControl': CacheControl
        }
    return metadata,contentType,CacheControl

def file_upload(src_source ,bucket, s3_folder, dry):
    global count
    s3_client = s3_connect_client()
    head, tail = os.path.split(src_source)
    extension = os.path.splitext(tail)[1]
    metadata, contentType, CacheControl = metadata_config(extension)
    if not dry:
        logger.info("uploading %s ..." % (src_source))
        try:

            if s3_folder:
                s3_client.upload_file(src_source, bucket, s3_folder + '/' + tail, metadata)
            else:
                s3_client.upload_file(src_source, bucket, tail, metadata)
        except Exception, e:

            logger.error("Unable to upload the %s file to bukcet %s. Error - %s" % (src_source, bucket, e))

        else:

            if s3_folder:

                logger.info("File uploaded : %d. File_name - %s, Content-Type - %s, Max-age - %s" % (count, s3_folder + '/' + tail, contentType, CacheControl))
            else:

                logger.info("File uploaded : %d. File_name - %s, Content-Type - %s, Max-age - %s" % (count, tail, contentType, CacheControl))
    else:
        if s3_folder:
            logger.info("%d. File_name - %s, Content-Type - %s, Max-age - %s" % (count, s3_folder + '/' + tail, contentType, CacheControl))
        else:
            logger.info("%d. File_name - %s, Content-Type - %s, Max-age - %s" % (count, tail, contentType, CacheControl))

    count += 1


def folder_upload(src_source, bucket, s3_folder, dry):
    global count
    s3_client = s3_connect_client()
    for root, sub_folders, files in os.walk(src_source):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, src_source)
            extension = os.path.splitext(abs_path)[1]
            metadata, contentType, CacheControl = metadata_config(extension)
            if not dry:
                logger.info("uploading %s ..." % (abs_path))
                try:

                    if s3_folder:
                        s3_client.upload_file(abs_path, bucket, s3_folder + '/' + rel_path, metadata)
                    else:
                        s3_client.upload_file(abs_path, bucket, rel_path, metadata)
                except Exception, e:

                    logger.error("Unable to upload the %s file to bukcet %s. Error - %s" % (abs_path, bucket, e))

                else:

                    if s3_folder:

                        logger.info("File uploaded : %d. File_name - %s, Content-Type - %s, Max-age - %s" % (count, s3_folder + '/' + rel_path, contentType, CacheControl))
                    else:

                        logger.info("File uploaded : %d. File_name - %s, Content-Type - %s, Max-age - %s" % (count, rel_path, contentType, CacheControl))
		    count += 1
            else:
                if s3_folder:
                    logger.info("%d. File_name - %s, Content-Type - %s, Max-age - %s" % (
                    count, s3_folder + '/' + rel_path, contentType, CacheControl))
                else:
                    logger.info("%d. File_name - %s, Content-Type - %s, Max-age - %s" % (
                    count, rel_path, contentType, CacheControl))
	        count += 1



def check_source(src_source, bucket, s3_folder, dry):
    if os.path.isdir(src_source):
        exists = True
        folder_upload(src_source, bucket, s3_folder, dry)
    else:
        ERROR = "The source : %s is doesn't exists"
    if os.path.isfile(src_source):
        exists = True
        file_upload(src_source, bucket, s3_folder, dry)
    else:
        ERROR = "The file : %s is doesn't exists"
    if not exists:
        logger.error(ERROR  % src_source)
        sys.exit(1)

def main():
    #get arguments
    arg_parser = argparse.ArgumentParser(description='Deploy indiatv static web resources to an S3 bucket')
    arg_parser.add_argument('-s','--source', help='The source source containing your static website files', required=True)
    arg_parser.add_argument('-b','--bucket', help='The name of the bucket you wish to copy files to, the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables are used for your credentials', required=True)
    arg_parser.add_argument('-d', '--s3_folder', dest='s3_folder', help='The  source location in S3 store you want to upload the static resources. If it is not specified, the static resources will uploaded to root source of the bucket')
    arg_parser.add_argument('-n', '--dry-run', action='store_true', dest='dry', help='run without uploading any files')
    args = arg_parser.parse_args()

    #connect to S3
    target_bucket = args.bucket
    source_source = args.source
    dry = args.dry
    s3_folder = args.s3_folder

    check_bucket(target_bucket)
    check_source(source_source, target_bucket, s3_folder, dry)

if __name__ == '__main__':
    main()


