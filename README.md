# AWS QuickSight Dashboard Management Toolkit

A comprehensive Python-based toolkit for managing Amazon QuickSight dashboards across AWS accounts. This toolkit enables automated creation, export, and cross-account deployment of QuickSight dashboards using templates.

The toolkit provides a streamlined workflow for creating, saving, and deploying QuickSight dashboards, making it easier to maintain consistency across multiple AWS accounts and environments. It leverages AWS SDK for Python (Boto3) to interact with QuickSight services and handles complex cross-account permissions and template management.

Key features include:
- Template creation from existing QuickSight analyses
- Cross-account dashboard deployment
- Template export and local storage
- Automated dataset mapping and permissions management
- Configurable dashboard publishing options

## Repository Structure
```
.
├── QScreateAnewDashboard.py    # Creates new dashboards from templates with dataset mapping
├── QScreateDiffAccountDash.py  # Handles cross-account dashboard deployment with role assumption
├── QSsaveTemplate.py           # Exports QuickSight templates to local JSON files
├── QStemplateExport.py         # Creates templates from existing QuickSight analyses
└── template.json               # Example template structure with schema definitions
```

## Usage Instructions
### Prerequisites
- Python 3.x
- AWS CLI configured with appropriate credentials
- Boto3 Python package
- AWS IAM permissions for QuickSight operations
- AWS account with QuickSight Enterprise edition enabled

### Installation
```bash
# Clone the repository
git clone <repository-url>

# Install required dependencies
pip install boto3

# Configure AWS credentials
aws configure
```

### Quick Start
1. Export an existing QuickSight analysis as a template:
```bash
export AWS_ACCOUNT_ID="your-account-id"
export ANALYSIS_ID="your-analysis-id"
python QStemplateExport.py
```

2. Save the template locally:
```bash
export AWS_ACCOUNT_ID="your-account-id"
export AWS_REGION="your-region"
export TEMPLATE_ID="your-template-id"
python QSsaveTemplate.py
```

3. Create a new dashboard from the template:
```bash
export AWS_ACCOUNT_ID="your-account-id"
export TEMPLATE_ID="your-template-id"
export DATASET_ID="your-dataset-id"
python QScreateAnewDashboard.py
```

### More Detailed Examples
#### Cross-Account Dashboard Deployment
```bash
# Set required environment variables
export AWS_ACCOUNT_ID="source-account-id"
export TEMPLATE_ID="template-id"
export TARGET_ACCOUNT_ID="target-account-id"
export TARGET_DATASET_ID="target-dataset-id"
export TARGET_ROLE_ARN="target-role-arn"
export TARGET_REGION="target-region"

# Run the cross-account deployment script
python QScreateDiffAccountDash.py
```

### Troubleshooting
#### Common Issues
1. Permission Errors
   - Error: "AccessDeniedException"
   - Solution: Verify IAM permissions include necessary QuickSight actions
   - Required permissions: quicksight:CreateTemplate, quicksight:DescribeTemplate, quicksight:CreateDashboard

2. Missing Environment Variables
   - Error: "Missing required environment variables"
   - Solution: Ensure all required environment variables are set before running scripts
   - Use `export` command to set variables

3. Cross-Account Access Issues
   - Error: "Unable to assume role"
   - Solution: Verify trust relationship in IAM role
   - Check if source account has permission to assume the target role

## Data Flow
The toolkit processes QuickSight resources through a template-based workflow, transforming analyses into reusable templates and deploying them as dashboards.

```ascii
[Analysis] -> [Template] -> [Dashboard]
     |            |             |
     v            v             v
[Source Account] -> [Template Storage] -> [Target Account]
```

Component Interactions:
- QuickSight analysis is exported as a template preserving visualizations and configurations
- Templates store dataset schemas and visualization layouts
- Dashboard creation maps template dataset placeholders to actual datasets
- Cross-account deployment handles permissions and role assumptions
- Template storage provides version control and reusability