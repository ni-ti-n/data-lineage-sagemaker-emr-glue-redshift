from pyspark.sql import SparkSession
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark import SparkContext
from pyspark.sql import SparkSession
import sys
import logging


spark = SparkSession.builder.appName("lineageglue").enableHiveSupport().getOrCreate()
 
connection_details = glueContext.extract_jdbc_conf(connection_name="connectionname")

employee_df = spark.read.format("jdbc").option("url", "jdbc:MySQL://dbhost:3306/database_name").option("dbtable", "employee").option("user", connection_details['user']).option("password", connection_details['password']).load()

s3_paths = {
'absent_data': 's3://bucketname-{account_id}/csv/attendance.csv'
}
absent_df = spark.read.csv(s3_paths['absent_data'], header=True, inferSchema=True)

joined_df = employee_df.join(absent_df, on="EmployeeID", how="inner")

joined_df.write.mode("overwrite").format("parquet").option("path", "s3://datazone-{account_id}/attendanceparquet/").saveAsTable("gluedbname.tablename")
