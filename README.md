# Data Lineage Visualization with Amazon SageMaker Catalog

Comprehensive solution for visualizing and tracking data lineage across AWS analytics services using Amazon SageMaker Catalog. This implementation demonstrates automated lineage capture from AWS Glue, Amazon EMR Serverless, and Amazon Redshift with visualization through Amazon SageMaker Unified Studio.

[Visualize data lineage using Amazon SageMaker Catalog for Amazon EMR, AWS Glue, and Amazon Redshift](https://aws.amazon.com/blogs/big-data/visualize-data-lineage-using-amazon-sagemaker-catalog-for-amazon-emr-aws-glue-and-amazon-redshift/)


## Overview

This solution demonstrates end-to-end data lineage tracking and visualization across multiple AWS analytics services. It provides:

- Automated lineage capture from AWS Glue ETL jobs and notebooks
- Lineage tracking for Amazon EMR Serverless Spark applications
- Amazon Redshift query lineage visualization
- OpenLineage-compatible event capture and versioning
- Visual lineage graphs in Amazon SageMaker Unified Studio
- Complete data provenance and transformation history
- Cross-service data flow tracking

## Architecture

The solution captures lineage from multiple data processing services:

1. **AWS Glue**: ETL jobs and notebooks reading from RDS MySQL and S3, writing to Data Catalog
2. **Amazon Redshift**: SQL queries joining tables and creating new tables with CTAS operations
3. **Amazon EMR Serverless**: Spark applications reading from RDS MySQL and Redshift, writing to S3
4. **SageMaker Catalog**: Central lineage repository with visual graph representation
5. **SageMaker Unified Studio**: User interface for exploring and analyzing data lineage

## Key Features

### Automated Lineage Capture
- OpenLineage-compatible event capture from AWS analytics services
- Automatic metadata extraction from Spark, SQL, and ETL operations
- Version tracking for lineage events over time
- No code changes required for basic lineage capture

### Visual Lineage Graphs
- Interactive lineage visualization in SageMaker Unified Studio
- Column-level lineage tracking
- Upstream and downstream dependency mapping
- Historical lineage comparison

### Multi-Service Support
- AWS Glue ETL jobs and interactive notebooks
- Amazon EMR Serverless Spark applications
- Amazon Redshift SQL queries and CTAS operations
- Cross-service data flow tracking

### Governance Benefits
- Compliance and audit trail support
- Impact analysis for schema changes
- Data quality management
- Root cause analysis for data issues

## Prerequisites

- Active AWS account with billing enabled
- IAM user with administrator access or permissions to create:
  - VPC, subnets, security groups
  - NAT gateway, internet gateway
  - Amazon EC2, Amazon RDS for MySQL
  - Amazon SageMaker Unified Studio domain and projects
  - AWS Glue jobs, Data Catalog
  - Amazon EMR Serverless applications
  - Amazon Redshift Serverless
  - S3 buckets, IAM roles
- AWS IAM Identity Center enabled and configured
- At least one user added to Identity Center directory
- S3 bucket for data storage: `s3://datazone-{account_id}/`
- Sufficient VPC capacity in chosen AWS Region
- AWS Region: US West (Oregon) - `us-west-2` (recommended)

## Deployment

### Step 1: Deploy Infrastructure with CloudFormation

1. Launch the CloudFormation stack `vpc-analytics-lineage-sus.yaml`

2. Provide the following parameters:

| Parameter | Description | Sample Value |
|-----------|-------------|--------------|
| DatazoneS3Bucket | S3 bucket for SageMaker data | s3://datazone-{account_id}/ |
| DomainName | SageMaker Unified Studio domain name | dz-studio |
| EnvironmentName | Environment name prefix | sm-unifiedstudio |
| PrivateSubnet1CIDR | Private subnet AZ1 | 10.192.20.0/24 |
| PrivateSubnet2CIDR | Private subnet AZ2 | 10.192.21.0/24 |
| PrivateSubnet3CIDR | Private subnet AZ3 | 10.192.22.0/24 |
| ProjectName | SageMaker project name | sidproject |
| PublicSubnet1CIDR | Public subnet AZ1 | 10.192.10.0/24 |
| PublicSubnet2CIDR | Public subnet AZ2 | 10.192.11.0/24 |
| PublicSubnet3CIDR | Public subnet AZ3 | 10.192.12.0/24 |
| UsersList | IAM Identity Center user | analyst |
| VpcCIDR | IP range for VPC | 10.192.0.0/16 |

3. Wait approximately 20 minutes for stack creation to complete

4. Check the **Outputs** tab for:
   - DataZoneDomainid (format: `dzd_xxxxxxxx`)
   - RDS endpoint
   - Redshift Serverless workgroup name

### Step 2: Prepare Sample Data

1. Create two CSV files with sample employee and attendance data:

**attendance.csv**
```csv
EmployeeID,Date,ShiftStart,ShiftEnd,Absent,OvertimeHours
E1000,2024-01-01,2024-01-01 08:00:00,2024-01-01 16:22:00,False,3
E1001,2024-01-08,2024-01-08 08:00:00,2024-01-08 16:38:00,False,2
E1002,2024-01-23,2024-01-23 08:00:00,2024-01-23 16:24:00,False,3
```

**employees.csv**
```csv
EmployeeID,Name,Department,Role,HireDate,Salary,PerformanceRating,Shift,Location
E1000,Employee_0,Quality Control,Operator,2021-08-08,33002.0,1,Night,Plant C
E1001,Employee_1,Maintenance,Supervisor,2015-12-31,69813.76,5,Evening,Plant B
E1002,Employee_2,Production,Technician,2015-06-18,46753.32,1,Evening,Plant A
```

2. Upload files to S3: `s3://datazone-{account_id}/csv/`

### Step 3: Load Data into RDS MySQL

1. Connect to EC2 instance via AWS Systems Manager
2. Connect to RDS MySQL database:

```bash
mysql -u admin -h <rds-endpoint> -p
```

3. Create and populate employee table:

```sql
USE employeedb;

CREATE TABLE employee (
  EmployeeID longtext,
  Name longtext,
  Department longtext,
  Role longtext,
  HireDate longtext,
  Salary longtext,
  PerformanceRating longtext,
  Shift longtext,
  Location longtext
);

INSERT INTO employee VALUES 
('E1000', 'Employee_0', 'Quality Control', 'Operator', '2021-08-08', 33002.00, 1, 'Night', 'Plant C'),
('E1001', 'Employee_1', 'Maintenance', 'Supervisor', '2015-12-31', 69813.76, 5, 'Evening', 'Plant B'),
('E1002', 'Employee_2', 'Production', 'Technician', '2015-06-18', 46753.32, 1, 'Evening', 'Plant A');
```

## Lineage Capture Implementation

### Option 1: AWS Glue ETL Job Lineage

1. Create AWS Glue ETL job with version 5.0
2. Enable **Generate lineage events** in job settings
3. Provide SageMaker domain ID: `dzd_xxxxxxxx`
4. Use the following script template:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("lineageglue").enableHiveSupport().getOrCreate()

# Read from RDS MySQL
connection_details = glueContext.extract_jdbc_conf(connection_name="connectionname")
employee_df = spark.read.format("jdbc") \
    .option("url", "jdbc:mysql://dbhost:3306/database_name") \
    .option("dbtable", "employee") \
    .option("user", connection_details['user']) \
    .option("password", connection_details['password']) \
    .load()

# Read from S3
absent_df = spark.read.csv('s3://datazone-{account_id}/csv/attendance.csv', 
                           header=True, inferSchema=True)

# Join and write to Data Catalog
joined_df = employee_df.join(absent_df, on="EmployeeID", how="inner")
joined_df.write.mode("overwrite").format("parquet") \
    .option("path", "s3://datazone-{account_id}/attendanceparquet/") \
    .saveAsTable("gluedbname.attendance_with_emp1")
```

5. Run the job and verify in SageMaker Unified Studio
6. Navigate to **Assets** → select `attendance_with_emp1` → **LINEAGE** tab

### Option 2: AWS Glue Notebook Lineage

1. Create AWS Glue interactive notebook
2. Add Spark configuration for lineage:

```python
%%configure --name project.spark -f
{
"--conf":"spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener \
--conf spark.openlineage.transport.type=amazon_datazone_api \
--conf spark.openlineage.transport.domainId=dzd_xxxxxxxx \
--conf spark.glue.accountId={account_id} \
--conf spark.openlineage.facets.custom_environment_variables=[AWS_DEFAULT_REGION;GLUE_VERSION;] \
--conf spark.glue.JOB_NAME=lineagenotebook"
}
```

3. Execute data processing code
4. Lineage is automatically captured and sent to SageMaker Catalog

### Option 3: Amazon Redshift Lineage

1. Connect to Redshift Serverless via Query Editor v2
2. Create tables and load data:

```sql
-- Create tables
CREATE TABLE public.absent (
    employeeid VARCHAR(65535),
    date DATE,
    shiftstart TIMESTAMP,
    shiftend TIMESTAMP,
    absent BOOLEAN,
    overtimehours INTEGER
);

CREATE TABLE public.employee (
    employeeid VARCHAR(65535),
    name VARCHAR(65535),
    department VARCHAR(65535),
    role VARCHAR(65535),
    hiredate DATE,
    salary DOUBLE PRECISION,
    performancerating INTEGER,
    shift VARCHAR(65535),
    location VARCHAR(65535)
);

-- Load data from S3
COPY absent FROM 's3://datazone-{account_id}/csv/attendance.csv' 
IAM_ROLE 'arn:aws:iam::{account_id}:role/RedshiftAdmin'
CSV IGNOREHEADER 1;

COPY employee FROM 's3://datazone-{account_id}/csv/employees.csv' 
IAM_ROLE 'arn:aws:iam::{account_id}:role/RedshiftAdmin'
CSV IGNOREHEADER 1;

-- Create joined table with CTAS
CREATE TABLE public.employeewithabsent AS
SELECT e.*, a.absent, a.overtimehours
FROM public.employee e
INNER JOIN public.absent a ON e.EmployeeID = a.EmployeeID;
```

3. In SageMaker Unified Studio, edit Redshift data source
4. Enable **Import data lineage**
5. Set table selection criteria (use `*` for all tables)
6. Run data source to create asset and capture lineage

### Option 4: Amazon EMR Serverless Lineage

1. Create EMR Serverless Spark application (emr-7.8.0)
2. Enable interactive endpoint for EMR Studio
3. Add Iceberg configuration:

```json
[{
    "Classification": "iceberg-defaults",
    "Properties": {
        "iceberg.enabled": "true"
    }
}]
```

4. Upload Spark script and MySQL connector JAR to S3
5. Submit job with lineage configuration:

```bash
aws emr-serverless start-job-run \
  --application-id <app-id> \
  --execution-role-arn <role-arn> \
  --name "Spark-Lineage" \
  --job-driver '{
    "sparkSubmit": {
      "entryPoint": "s3://datazone-{account_id}/script/emrspark.py",
      "sparkSubmitParameters": "--conf spark.jars=/usr/share/aws/datazone-openlineage-spark/lib/DataZoneOpenLineageSpark-1.0.jar,s3://datazone-{account_id}/jars/mysql-connector-java-8.0.20.jar --conf spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener --conf spark.openlineage.transport.type=amazon_datazone_api --conf spark.openlineage.transport.domainId=dzd_xxxxxxxx --conf spark.glue.accountId={account_id}"
    }
  }'
```

6. After job completion, update data source in SageMaker Unified Studio to import lineage

## Components

### Amazon SageMaker Unified Studio
- Unified environment for data and AI development
- Visual lineage graph interface
- Asset management and discovery
- Project and domain management

### Amazon SageMaker Catalog
- Central metadata repository
- OpenLineage-compatible event storage
- Version tracking for lineage events
- Cross-service lineage aggregation

### AWS Glue
- ETL jobs with automatic lineage capture
- Interactive notebooks with Spark lineage
- Data Catalog for table metadata
- Connection management for data sources

### Amazon EMR Serverless
- Serverless Spark application execution
- OpenLineage integration via DataZone library
- Automatic resource scaling
- No cluster management required

### Amazon Redshift Serverless
- Serverless data warehouse
- SQL query lineage tracking
- CTAS operation lineage
- Automatic lineage capture for table operations

### Amazon RDS for MySQL
- Source operational database
- Employee data storage
- JDBC connectivity for Spark and Glue

### Amazon S3
- Data lake storage
- CSV source files
- Parquet output files
- Script and JAR file storage

## Cleanup

To avoid ongoing charges, complete the following steps:

1. **Delete AWS Glue resources**:
   - Navigate to AWS Glue console
   - Delete ETL jobs and notebooks

2. **Delete EMR Serverless resources**:
   - Navigate to Amazon EMR console
   - Stop and delete EMR Serverless applications
   - Delete EMR Studio

3. **Delete CloudFormation stack**:
   - Navigate to CloudFormation console
   - Select stack `vpc-analytics-lineage-sus`
   - Click **Delete** and confirm

4. **Manual cleanup** (if needed):
   - Empty and delete S3 buckets
   - Delete SageMaker Unified Studio domain (if not deleted by stack)
   - Remove IAM Identity Center users (optional)

## Use Cases

### Compliance and Auditing
- Track complete data provenance for regulatory requirements
- Generate audit trails for data transformations
- Demonstrate data lineage for compliance reports
- Identify data sources for GDPR and privacy compliance

### Impact Analysis
- Assess impact of schema changes across pipelines
- Identify downstream dependencies before modifications
- Understand blast radius of data source changes
- Plan migration strategies with full dependency visibility

### Data Quality Management
- Trace data quality issues to source systems
- Identify transformation steps that introduce errors
- Monitor data flow for anomaly detection
- Validate data consistency across systems

## Additional Resources

### Sample Data Files

**attendance.csv**
```csv
EmployeeID,Date,ShiftStart,ShiftEnd,Absent,OvertimeHours
E1000,2024-01-01,2024-01-01 08:00:00,2024-01-01 16:22:00,False,3
E1001,2024-01-08,2024-01-08 08:00:00,2024-01-08 16:38:00,False,2
E1002,2024-01-23,2024-01-23 08:00:00,2024-01-23 16:24:00,False,3
E1003,2024-01-09,2024-01-09 10:00:00,2024-01-09 18:31:00,False,0
E1004,2024-01-15,2024-01-15 09:00:00,2024-01-15 17:48:00,False,1
```

**employees.csv**
```csv
EmployeeID,Name,Department,Role,HireDate,Salary,PerformanceRating,Shift,Location
E1000,Employee_0,Quality Control,Operator,2021-08-08,33002.0,1,Night,Plant C
E1001,Employee_1,Maintenance,Supervisor,2015-12-31,69813.76,5,Evening,Plant B
E1002,Employee_2,Production,Technician,2015-06-18,46753.32,1,Evening,Plant A
E1003,Employee_3,Admin,Supervisor,2020-10-13,52853.4,5,Night,Plant A
E1004,Employee_4,Quality Control,Manager,2023-09-21,55645.27,5,Evening,Plant A
```

### Key Configuration Parameters

**OpenLineage Spark Configuration**:
- `spark.extraListeners=io.openlineage.spark.agent.OpenLineageSparkListener`
- `spark.openlineage.transport.type=amazon_datazone_api`
- `spark.openlineage.transport.domainId=dzd_xxxxxxxx`
- `spark.glue.accountId={account_id}`

**AWS Glue Lineage Settings**:
- Enable "Generate lineage events" in job configuration
- Provide SageMaker domain ID
- Use AWS Glue version 5.0 or later

**Data Source Import Settings**:
- Enable "Import data lineage" in data source configuration
- Set table selection criteria (use `*` for all tables)
- Run data source import after job execution

## License

This solution is provided as-is for educational and demonstration purposes.
