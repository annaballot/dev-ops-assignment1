#!/usr/bin/env python3
import boto3
import webbrowser
import sys
import time
from datetime import datetime, timedelta
import time
import json
import random
import string
import requests
from PIL import Image 
import os
import subprocess

#############################################################################################

#	Set Variables - 1: NEED TO BE UPDATED BY EACH NEW USER

#############################################################################################

ec2_key_name = 'abstudentkey' #name of key pair for EC2 bucket, update this
ec2_security_group = "httpssh" #allowing http + ssh


#############################################################################################

#	Set Variables - 2: these do not need to be updated

#############################################################################################

s3_file_upload = "index.html" #name of file to upload to S3 bucket
url_image = "http://devops.witdemo.net/logo.jpg" #url of image to download
image_name = "logo.jpg" #used to name the downloaded file from above url
user_name = "aballot" #used to name the S3 bucket

# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("d%Y-%m-%dt%H-%M-%S")

# random string to be used for bucket name (https://docs.python.org/3/library/random.html)
random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

ec2_name = user_name + "-" + dt_string
s3_bucket_name = random_str + "-" + user_name

#create user data script for EC2 Website
user_data_script = ""
user_data_script = """#!/bin/bash
            yum install httpd -y
            systemctl enable httpd
            systemctl start httpd
            TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
            echo '<html>' > index.html
            echo '<head> <meta charset="utf-8"> <title>EC2 Site</title>  </head>' >> index.html
            echo '<b>Instance ID: </b>' >> index.html
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id >> index.html
            echo '<br> <b>Instance Type: </b>' >> index.html
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-type >> index.html
            echo '<br> <b>Availability Zone:</b> ' >> index.html
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html
            echo '<br> <b>Private IP address: </b>' >> index.html
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
            echo '<br> <b>Security Groups: </b>' >> index.html
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/security-groups >> index.html
            echo '<br><br>Heres an image about S3 Buckets from the amazon website: <br>' >> index.html
            echo '<img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQWYcZPhTkco_M0M2sko4U4-eq-dUlL0XZmOF4UQqdgEA&s" alt="Amazon Image about S3"><br>' >> index.html
            echo 'Hopefully it still exists on their site by the time Im finished this project!<br>' >> index.html
            cp index.html /var/www/html/index.html"""


#Printing variable information
print ("")
print("---------------------------------------------------------------------------------")
print ("Running automated script to create, launch and monitor web servers")
print ("")
print("---------------------------------------------------------------------------------")
print("ec2 name: " + ec2_name)
print("s3 bucket name: " + s3_bucket_name)


#############################################################################################

#	create ec2 bucket

#############################################################################################
          
ec2 = boto3.resource('ec2')
try:
        new_instances = ec2.create_instances(
        ImageId='ami-0440d3b780d96b29d',
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.nano',
        KeyName=ec2_key_name,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags' : [
                    {
                    'Key': 'Name',
                    'Value': ec2_name
                    },
                ]
            },
        ],
        SecurityGroups=[
            ec2_security_group,
        ],
        UserData=user_data_script
        )
except:
        print("Instance creation error")
        exit()

print ("")
print("---------------------------------------------------------------------------------")
print ("Created new EC2 instances:")
print ("Name: ", new_instances[0].tags[0]['Value'])
print ("ID: ", new_instances[0].id)

#Wait until the instance is running
try:
   new_instances[0].wait_until_running()
   new_instances[0].reload() 
except:
    print("Error with EC2 Instance")
    exit()   
   
time.sleep(60) #delay to make sure the server is up and running. 60 seconds has worked for all of my testing
inst = ec2.Instance(new_instances[0].id)
inst_id = inst.id
ec2_public_ip_address = inst.public_ip_address

print ("")
print("---------------------------------------------------------------------------------")
print ("Instance is running")
print("Instance ID: ", inst_id)
print("Instance State",inst.state)
print("Instance Type", inst.instance_type)
print("Instance Public IP Address", inst.public_ip_address)
print("http://"+inst.public_ip_address)


#############################################################################################

#	creating an S3 bucket

#############################################################################################

s3 = boto3.resource("s3")
try:
    s3.create_bucket(Bucket=s3_bucket_name) 
except:
    print("s3 bucket creation error")
    exit()

#s3 bucket permissions
s3client = boto3.client("s3")
s3client.delete_public_access_block(Bucket=s3_bucket_name)

bucket_policy = {
 "Version": "2012-10-17",
 "Statement": [
{
 "Sid": "PublicReadGetObject",
"Effect": "Allow",
"Principal": "*",
"Action": ["s3:GetObject"],
"Resource": f"arn:aws:s3:::{s3_bucket_name}/*"
 }
]
}
s3.Bucket(s3_bucket_name).Policy().put(Policy=json.dumps(bucket_policy))

#static website hosting
website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
}

bucket_website = s3.BucketWebsite(s3_bucket_name)
response = bucket_website.put(WebsiteConfiguration=website_configuration)

print(" ")
print("---------------------------------------------------------------------------------")
print("S3 bucket has been created: " + s3_bucket_name)


#############################################################################################

#	download image

#############################################################################################

response = requests.get(url_image)
if response.status_code == 200:
    with open(image_name, 'wb') as file:
        file.write(response.content)
    print("Image downloaded successfully")
else:
    print(f"Failed to download image from {image_url}. Status code: {response.status_code}")
    
#create html file for s3 bucket
html_data = f"""
	<!doctype html>
	<html>
	    <head>
		<meta charset="utf-8">
		<title>S3 Bucket</title>
	    </head>

	    <body>
		Welcome to your S3 bucket! <br>
		Enjoy the below image which has been downloaded from """ + url_image + """and uploaded here.
	    </body>
	    <body>
	        <img src=""" + image_name + """ alt="Logo Image Assignment 1">
	    </body>
	</html>
    """
    
#upload html file + image to s3 bucket 
#reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html   
try:
    s3client.put_object(Bucket=s3_bucket_name, Key=s3_file_upload, Body=html_data.encode('utf-8'), ContentType='text/html')
    with open(image_name, 'rb') as file:
            s3client.put_object(Bucket=s3_bucket_name, Key=image_name, Body=file, ContentType='image/jpeg')
except Exception as error:
    print("Error downloading the image")
    print (error)    
    exit()

#############################################################################################

#	Launch Browsers

#############################################################################################

#create file
#reference: https://ioflood.com/blog/python-create-file/
try:
    file = open(user_name + '_websites.txt', 'w')
    file.write("EC2 URL: http://" + s3_bucket_name + ".s3-website-us-east-1.amazonaws.com/")
    file.write("S3 Bucket URL: http://" + ec2_public_ip_address)
except FileNotFoundError as e:
    print(f'An error occurred writing to the file: {e}')

file.close()

#launching EC2 browser
try:
    webbrowser.open_new_tab("http://" + ec2_public_ip_address)
except:
    print ("Error opening: http://" + ec2_public_ip_address)
        
#launching S3 Bucket browser
try:
    webbrowser.open_new_tab("http://" + s3_bucket_name + ".s3-website-us-east-1.amazonaws.com/")
except:
    print ("Error opening: http://" + s3_bucket_name + ".s3-website-us-east-1.amazonaws.com/")


print ("")
print("---------------------------------------------------------------------------------")
print ("Opening browser to URLs specified")


#############################################################################################

#	Monitoring

#############################################################################################

print ("")
print ("---------------------------------------------------------------------------------")
print ("Monitoring:")

# Wait 6 minutes to ensure we have some data for monitoring + cloudwatch
time.sleep(360)    

#copy monitoring script to ec2 instance
result = subprocess.run(["scp", "-i", ec2_key_name +".pem", "-o", "StrictHostKeyChecking=no", "monitoring.sh", "ec2-user@" + ec2_public_ip_address + ":."])
print ("Command Run: ", result.args)

result = subprocess.run(["ssh", "-i", ec2_key_name + ".pem", "ec2-user@" + ec2_public_ip_address, "chmod 700 monitoring.sh"])
print ("Command Run: ", result.args)

result = subprocess.run(["ssh", "-i", ec2_key_name + ".pem", "ec2-user@" + ec2_public_ip_address, "./monitoring.sh"])
print ("Command Run: ", result.args)


#############################################################################################

#	Cloudwatch

#############################################################################################

cloudwatch = boto3.resource('cloudwatch')
ec2 = boto3.resource('ec2')

instance = ec2.Instance(inst_id)

try:
    instance.monitor()  # Enables detailed monitoring on instance (1-minute intervals)

    metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                                MetricName='CPUUtilization',
                                                Dimensions=[{'Name':'InstanceId', 'Value': inst_id}])

    metric = list(metric_iterator)[0]    # extract first (only) element

    response = metric.get_statistics(StartTime = datetime.utcnow() - timedelta(minutes=5),   # 5 minutes ago
                                     EndTime=datetime.utcnow(),                              # now
                                     Period=300,                                             # 5 min intervals
                                     Statistics=['Average'])
except:
    print ("Error opening accessing cloudwatch data")
    
print ("")
print("---------------------------------------------------------------------------------")
print("Cloud Watch Stats: ")
print ("Average CPU utilisation:", response['Datapoints'][0]['Average'], response['Datapoints'][0]['Unit'])


