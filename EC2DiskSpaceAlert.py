#!/usr/bin/python
# ********************************************************************************************************
#    Python Script for sending out alerts when specified disk is utilized more than 80%
#    ----------------------------------
#
#    Notes:
#
#    1. The script runs following command and captures the result returned.
#       df -H /mnt/data --output=pcent
#    2. The above script returns the percent of the disk utilized for /mnt/data drive in EC2.
#       Replace /mnt/data with / in above command to find the percentage utilization of root drive.
#    3. Once we have the utilization percentage, we check if it crosses the THRESHOLD value. If it does, then
#       we send out notifications via SNS.
#
#     How SNS works:
#       1. We create a SNS topic.
#       2. Enter the email addresses which would listen to contents that gets published to this SNS topic.
#       3.We publish the the alert message to a SNS topic and the message will be sent out to entities
#         listening to that particular topic. 
# ********************************************************************************************************

import os
import sys
import json
import boto3
import traceback
import subprocess
from pprint import pprint

Region = xx-xxxxxxxx-2

# these are the paths and names of the drives in EC2
# you can simply add drives here as list of dicts
DRIVE_PATHS = [
    {'drive_name': 'MNT DATA DRIVE',
     'drive_path': '/mnt/data'},
    {'drive_name': 'ROOT DRIVE',
     'drive_path': '/'}
]

# change this value if you want some other threshold
THRESHOLD = 80

# this function returns the utilized disk percent for the drives
def run_command(drive_path):
    try:
        # command we're running via subprocess: df -H /mnt/data --output=pcent
        # this command captures the percentage of disk space currently being used
        p = subprocess.Popen(['df', '-H', drive_path, '--output=pcent'], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        print(out)
        # the response of the above command is string and its always same. 6th and 7th position gives the utilized disk %
        used_percent = int(out[6] + out[7])
        if used_percent > THRESHOLD:
            print(">> WARNING::: Disk usage at above 80% of the total storage!")
        else:
            print('>> Disk usage at below 80% of the total storage. No need to worry!')
        return used_percent
    except Exception as e:
        pprint('>> Error encountered while running disk usage command! \n Error:::: %s ' % e)
        type_, value_, traceback_ = sys.exc_info()
        pprint(traceback.format_tb(traceback_))
        pprint(type_, value_)
        sys.exit(1)


# this function sends the Alert messages to subscribed emails via AWS SNS
def notify_via_sns(msg):
    try:
        print('>> Sending notification via SNS................')
        message = {"message": msg}
        client = boto3.client('sns', region)
        response = client.publish(
            TargetArn='arn:aws:sns:ap-southeast-2:959060754311:EC2-Ubuntu-EBS-Space',
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )
        print('>> Notification successfully sent!')
    except Exception as e:
        pprint('>>> Error while sending notification via SNS! \n Error:::: %s ' % e)
        type_, value_, traceback_ = sys.exc_info()
        pprint(traceback.format_tb(traceback_))
        pprint(type_, value_)
        sys.exit(1)


def main():
    try:
        for each_drive in DRIVE_PATHS:
            drive_path = each_drive['drive_path']
            drive_name = each_drive['drive_name']
            print('>> Evaluating Disk Usage for - {}'.format(drive_name))
            used_percent = run_command(drive_path)
            # used_percent = 82
            message = """Hello, The disk usage for EC2 drive - ({} - '{}') has exceeded 80% of the total available space, with {}% being used currently. Please, free up the space to ensure uninterrupted operation on all sides.""" \
                .format(drive_name, drive_path, used_percent)
            if used_percent > THRESHOLD:
                notify_via_sns(message)
            print("-------------------------------------------------------------------------------------------------\n")
    except Exception as e:
        pprint('>>> Error in the main function! \n Error:::: %s ' % e)
        type_, value_, traceback_ = sys.exc_info()
        pprint(traceback.format_tb(traceback_))
        pprint(type_, value_)
        sys.exit(1)


if __name__ == '__main__':
    main()