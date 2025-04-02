#!/usr/bin/env python3
import boto3, os, json
from botocore.exceptions import ClientError
from datetime import datetime

def get_template_details(client, account_id, template_id):
    try:
        template_obj = client.describe_template(
            AwsAccountId=account_id,
            TemplateId=template_id
        )
        print("Template Details:")
        print(json.dumps(template_obj, default=str, indent=2))
        return template_obj
    except ClientError as e:
        print(f"Error getting template details: {e.response['Error']['Message']}")
        raise e

def create_dashboard(client, account_id, dashboard_name, template_obj):
    try:
        # Generate a unique dashboard ID
        dashboard_id = f"dashboard-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Add permissions for namespace with only the valid permission sets
        permissions = [
            {
                'Principal': f"arn:aws:quicksight:{os.environ.get('AWS_REGION', 'us-east-1')}:{account_id}:namespace/default",
                'Actions': [
                    'quicksight:DescribeDashboard',
                    'quicksight:QueryDashboard',
                    'quicksight:ListDashboardVersions'
                ]
            }
        ]

        # Get dataset references from the template
        dataset_references = []
        if 'Version' in template_obj['Template'] and 'DataSetConfigurations' in template_obj['Template']['Version']:
            for dataset_config in template_obj['Template']['Version']['DataSetConfigurations']:
                dataset_references.append({
                    'DataSetPlaceholder': dataset_config['Placeholder'],
                    'DataSetArn': f"arn:aws:quicksight:{os.environ.get('AWS_REGION', 'us-east-1')}:{account_id}:dataset/{os.environ['DATASET_ID']}"
                })
        
        if not dataset_references:
            raise ValueError("No dataset references found in template")

        print(f"\nCreating dashboard with ID: {dashboard_id}")
        print(f"Dataset References: {json.dumps(dataset_references, indent=2)}")

        response = client.create_dashboard(
            # AWS Account ID is required
            AwsAccountId=account_id,
            # Dashboard ID and Name
            DashboardId=dashboard_id,
            Name=dashboard_name,
            # Permissions
            Permissions=permissions,
            # Source Template configuration
            SourceEntity={
                'SourceTemplate': {
                    'Arn': template_obj['Template']['Arn'],
                    'DataSetReferences': dataset_references
                }
            },
            # Dashboard publish options
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
            # Version description
            VersionDescription='Initial version'
        )
        
        # Print the dashboard URL
        dashboard_url = f"https://{os.environ.get('AWS_REGION', 'us-east-1')}.quicksight.aws.amazon.com/sn/dashboards/{dashboard_id}"
        print(f"\nDashboard created successfully!")
        print(f"Dashboard URL: {dashboard_url}")
        
        return response
    except ClientError as e:
        print(f"Error creating dashboard: {e.response['Error']['Message']}")
        raise e

def list_quicksight_groups(client, account_id):
    try:
        response = client.list_groups(
            AwsAccountId=account_id,
            Namespace='default'
        )
        print("\nAvailable QuickSight Groups:")
        print(json.dumps(response, default=str, indent=2))
        return response
    except ClientError as e:
        print(f"Error listing groups: {e.response['Error']['Message']}")
        return None

try:
    # Validate required environment variables
    required_vars = ['AWS_ACCOUNT_ID', 'TEMPLATE_ID', 'DATASET_ID']
    missing_vars = [var for var in required_vars if var not in os.environ]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Create service client
    client = boto3.client('quicksight', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
    account_id = os.environ['AWS_ACCOUNT_ID']
    template_id = os.environ['TEMPLATE_ID']
    dashboard_name = 'New Dashboard'
    
    # List available QuickSight groups
    groups = list_quicksight_groups(client, account_id)
    
    # Get template details
    template_obj = get_template_details(client, account_id, template_id)
    
    # Create the dashboard
    response = create_dashboard(client, account_id, dashboard_name, template_obj)
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
