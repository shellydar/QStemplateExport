#!/usr/bin/env python3
import boto3
import os
import json
from botocore.exceptions import ClientError
from datetime import datetime

def assume_target_role(target_role_arn):
    """Assume role in target account directly"""
    try:
        sts_client = boto3.client('sts')
        assumed_role = sts_client.assume_role(
            RoleArn=target_role_arn,
            RoleSessionName="QuickSightSession"
        )
        
        print(f"\nSuccessfully assumed role in target account: {target_role_arn}")
        
        return boto3.Session(
            aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
            aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
            aws_session_token=assumed_role['Credentials']['SessionToken'],
            region_name=os.environ.get('TARGET_REGION', os.environ.get('AWS_REGION', 'us-east-1'))
        )
    except Exception as e:
        print(f"Error assuming role: {str(e)}")
        raise
def update_template_permissions(client, account_id, template_id, target_account_id):
    """Update template permissions to allow access from target account"""
    try:
        print(f"\nUpdating template permissions for template: {template_id}")
        response = client.update_template_permissions(
            AwsAccountId=account_id,
            TemplateId=template_id,
            GrantPermissions=[
                {
                    'Principal': f'arn:aws:iam::{target_account_id}:root',
                    'Actions': [
                        'quicksight:DescribeTemplate',
                        'quicksight:ListTemplateVersions',
                        'quicksight:UpdateTemplatePermissions'
                    ]
                }
            ]
        )
        print("Template permissions updated successfully")
        return response
    except ClientError as e:
        print(f"Error updating template permissions: {e.response['Error']['Message']}")
        raise

try:
    # Validate required environment variables
    required_vars = [
        'AWS_ACCOUNT_ID',
        'TEMPLATE_ID',
        'TARGET_ACCOUNT_ID',
        'TARGET_DATASET_ID',
        'TARGET_ROLE_ARN'
    ]
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create source client using current credentials
    source_client = boto3.client('quicksight', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    # Update template permissions first
    update_template_permissions(
        source_client,
        os.environ['AWS_ACCOUNT_ID'],
        os.environ['TEMPLATE_ID'],
        os.environ['TARGET_ACCOUNT_ID']
    )
    
    # Assume role in target account
    target_session = assume_target_role(os.environ['TARGET_ROLE_ARN'])
    target_client = target_session.client('quicksight')
    
    # Get template details from source account
    template_obj = get_template_details(
        source_client, 
        os.environ['AWS_ACCOUNT_ID'], 
        os.environ['TEMPLATE_ID']
    )
    
    # Create the dashboard in target account
    dashboard_name = f"Imported Dashboard {datetime.now().strftime('%Y%m%d%H%M%S')}"
    response = create_dashboard(
        target_client,
        os.environ['TARGET_ACCOUNT_ID'],
        dashboard_name,
        template_obj,
        os.environ['TARGET_DATASET_ID']
    )
    
    print("\nDashboard Creation Response:")
    print(json.dumps(response, default=str, indent=2))

except ClientError as e:
    print(f"AWS Error: {e.response['Error']['Message']}")
except KeyError as e:
    print(f"Missing environment variable: {str(e)}")
except ValueError as e:
    print(f"Configuration error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")

def get_template_details(client, account_id, template_id):
    """Get template details from source account"""
    try:
        template_obj = client.describe_template(
            AwsAccountId=account_id,
            TemplateId=template_id
        )
        print("\nTemplate Details:")
        print(json.dumps(template_obj, default=str, indent=2))
        return template_obj
    except ClientError as e:
        print(f"Error getting template details: {e.response['Error']['Message']}")
        raise

def create_dashboard(client, account_id, dashboard_name, template_obj, dataset_id):
    """Create dashboard in target account using target account's dataset"""
    try:
        dashboard_id = f"dashboard-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Get dataset references from template and map to target dataset
        dataset_references = []
        if 'Version' in template_obj['Template'] and 'DataSetConfigurations' in template_obj['Template']['Version']:
            for dataset_config in template_obj['Template']['Version']['DataSetConfigurations']:
                print(f"\nMapping dataset placeholder '{dataset_config['Placeholder']}' to target dataset: {dataset_id}")
                dataset_references.append({
                    'DataSetPlaceholder': dataset_config['Placeholder'],
                    'DataSetArn': f"arn:aws:quicksight:{os.environ.get('TARGET_REGION', 'us-east-1')}:{account_id}:dataset/{dataset_id}"
                })
        
        print(f"\nCreating dashboard with ID: {dashboard_id}")
        print(f"Dataset References: {json.dumps(dataset_references, indent=2)}")
        
        response = client.create_dashboard(
            AwsAccountId=account_id,
            DashboardId=dashboard_id,
            Name=dashboard_name,
            Permissions=[
                {
                    'Principal': f"arn:aws:quicksight:{os.environ.get('TARGET_REGION', 'us-east-1')}:{account_id}:namespace/default",
                    'Actions': [
                        'quicksight:DescribeDashboard',
                        'quicksight:QueryDashboard',
                        'quicksight:ListDashboardVersions'
                    ]
                }
            ],
            SourceEntity={
                'SourceTemplate': {
                    'Arn': template_obj['Template']['Arn'],
                    'DataSetReferences': dataset_references
                }
            },
            DashboardPublishOptions={
                'AdHocFilteringOption': {
                    'AvailabilityStatus': 'ENABLED'
                },
                'ExportToCSVOption': {
                    'AvailabilityStatus': 'ENABLED'
                },
                'SheetControlsOption': {
                    'VisibilityState': 'EXPANDED'
                }
            },
            VersionDescription='Initial version'
        )
        
        dashboard_url = f"https://{os.environ.get('TARGET_REGION', 'us-east-1')}.quicksight.aws.amazon.com/sn/dashboards/{dashboard_id}"
        print(f"\nDashboard created successfully!")
        print(f"Dashboard URL: {dashboard_url}")
        
        return response
    except ClientError as e:
        print(f"Error creating dashboard: {e.response['Error']['Message']}")
        raise

try:
    # Validate required environment variables
    required_vars = [
        'AWS_ACCOUNT_ID',
        'TEMPLATE_ID',
        'TARGET_ACCOUNT_ID',
        'TARGET_DATASET_ID',
        'TARGET_ROLE_ARN'
    ]
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create source client using current credentials
    source_client = boto3.client('quicksight', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    # Update template permissions first
    update_template_permissions(
        source_client,
        os.environ['AWS_ACCOUNT_ID'],
        os.environ['TEMPLATE_ID'],
        os.environ['TARGET_ACCOUNT_ID']
    )
    
    # Assume role in target account
    target_session = assume_target_role(os.environ['TARGET_ROLE_ARN'])
    target_client = target_session.client('quicksight')
    
    # Get template details from source account
    template_obj = get_template_details(
        source_client, 
        os.environ['AWS_ACCOUNT_ID'], 
        os.environ['TEMPLATE_ID']
    )
    
    # Print dataset configurations from template for debugging
    if 'Version' in template_obj['Template'] and 'DataSetConfigurations' in template_obj['Template']['Version']:
        print("\nTemplate Dataset Configurations:")
        for dataset_config in template_obj['Template']['Version']['DataSetConfigurations']:
            print(f"Placeholder: {dataset_config['Placeholder']}")
            print(f"Column Configuration Count: {len(dataset_config.get('ColumnConfigurations', []))}")
    
    # Create the dashboard in target account
    dashboard_name = f"Imported Dashboard {datetime.now().strftime('%Y%m%d%H%M%S')}"
    response = create_dashboard(
        target_client,
        os.environ['TARGET_ACCOUNT_ID'],
        dashboard_name,
        template_obj,
        os.environ['TARGET_DATASET_ID']
    )
    
    print("\nDashboard Creation Response:")
    print(json.dumps(response, default=str, indent=2))

except ClientError as e:
    print(f"AWS Error: {e.response['Error']['Message']}")
except KeyError as e:
    print(f"Missing environment variable: {str(e)}")
except ValueError as e:
    print(f"Configuration error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")


try:
    # Validate required environment variables
    required_vars = [
        'AWS_ACCOUNT_ID',
        'TEMPLATE_ID',
        'TARGET_ACCOUNT_ID',
        'TARGET_DATASET_ID',
        'TARGET_ROLE_ARN'
    ]
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create source client using current credentials
    source_client = boto3.client('quicksight', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    
    # Assume role in target account
    target_session = assume_target_role(os.environ['TARGET_ROLE_ARN'])
    target_client = target_session.client('quicksight')
    
    # Get template details from source account
    template_obj = get_template_details(
        source_client, 
        os.environ['AWS_ACCOUNT_ID'], 
        os.environ['TEMPLATE_ID']
    )
    
    # Create the dashboard in target account
    dashboard_name = f"Imported Dashboard {datetime.now().strftime('%Y%m%d%H%M%S')}"
    response = create_dashboard(
        target_client,
        os.environ['TARGET_ACCOUNT_ID'],
        dashboard_name,
        template_obj,
        os.environ['TARGET_DATASET_ID']
    )
    
    print("\nDashboard Creation Response:")
    print(json.dumps(response, default=str, indent=2))

except ClientError as e:
    print(f"AWS Error: {e.response['Error']['Message']}")
except KeyError as e:
    print(f"Missing environment variable: {str(e)}")
except ValueError as e:
    print(f"Configuration error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
