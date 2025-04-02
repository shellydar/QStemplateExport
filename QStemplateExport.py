#!/usr/bin/env python3
import boto3, os, json
from botocore.exceptions import ClientError
from datetime import datetime

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def create_quicksight_template(analysis_id):
    # Get the current region from the session
    quicksight = boto3.client('quicksight')
    session = boto3.session.Session()
    current_region = session.region_name
    
    try:
        # First, get the analysis details to get dataset references
        analysis = quicksight.describe_analysis(
            AwsAccountId=os.environ['AWS_ACCOUNT_ID'],
            AnalysisId=analysis_id
        )
        
        # Get the dataset references from the analysis
        dataset_references = []
        for dataset in analysis['Analysis']['DataSetArns']:
            dataset_name = dataset.split('/')[-1]  # Extract dataset name from ARN
            dataset_references.append({
                'DataSetPlaceholder': dataset_name,
                'DataSetArn': dataset
            })

        # Create a template from an analysis
        response = quicksight.create_template(
            AwsAccountId=os.environ['AWS_ACCOUNT_ID'],
            TemplateId=analysis_id,
            Name=analysis_id,
            SourceEntity={
                'SourceAnalysis': {
                    'Arn': f"arn:aws:quicksight:{current_region}:{os.environ['AWS_ACCOUNT_ID']}:analysis/{analysis_id}",
                    'DataSetReferences': dataset_references
                }
            },
            VersionDescription='Created from analysis'
        )
        
        # Return the template description
        return quicksight.describe_template(
            AwsAccountId=os.environ['AWS_ACCOUNT_ID'],
            TemplateId=analysis_id
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'ResourceNotFoundException':
            print(f"Analysis with ID {analysis_id} does not exist in region {current_region}")
        
        print(f"Error Code: {error_code}")
        print(f"Error Message: {error_message}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise

try:
    analysis_id = os.environ['ANALYSIS_ID']  # Make sure to set this environment variable
    quicksight_template = create_quicksight_template(analysis_id)
    # Use the custom encoder when dumping to JSON
    print(json.dumps(quicksight_template, indent=2, cls=DateTimeEncoder))
except Exception as e:
    print(f"Failed to create template: {str(e)}")
