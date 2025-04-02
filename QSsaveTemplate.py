#!/usr/bin/env python3
# download a template from quicksight into a file

import boto3
import argparse
import os
import sys
import time
import json
import logging
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime
from dateutil.tz import tzlocal
from dateutil import parser

# set up logging
logging.basicConfig(level=logging.INFO)

# download a Quicksight template 
def download_template(aws_account_id, template_id, version_number, region, output_file):
    # create a session
    session = boto3.Session()
    # create a quicksight client
    quicksight = session.client('quicksight', region_name=region)
    # get the template
    response = quicksight.describe_template(
        AwsAccountId=aws_account_id,
        TemplateId=template_id,
        VersionNumber=int(version_number)
    )
    # write the template to a file
    with open(output_file, 'w') as f:
        f.write(json.dumps(response['Template'], indent=4, sort_keys=True, default=str))


AwsAccountId=os.environ['AWS_ACCOUNT_ID']
Region=os.environ['AWS_REGION']
TemplateId=os.environ['TEMPLATE_ID']
download_template(AwsAccountId, TemplateId, 1, Region, 'template.json')