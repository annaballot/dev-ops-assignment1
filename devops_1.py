#!/usr/bin/env python3
import boto3
import webbrowser
import sys
import time
from datetime import datetime
import json
import random
import string
import requests
from PIL import Image 
import os


#set variables
url_image = "http://devops.witdemo.net/logo.jpg" 
image_name = "logo.jpg"
user_name = "aballot"
ec2_key_name = 'abstudentkey'
s3_file_upload = "index.html"
ec2_security_group = "httpssh"

print ("""---------------------------------------------------------------------------------

Running automated script to create, launch and monitor web servers
...

""")

# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("d%Y-%m-%dt%H-%M-%S")

# random string to be used for bucket name (https://docs.python.org/3/library/random.html)
random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

#set ec3 + s3 names
ec2_name = user_name + "-" + dt_string
s3_bucket_name = random_str + "-" + user_name
print("---------------------------------------------------------------------------------")
print("ec2 name: " + ec2_name)
print("s3 bucket name: " + s3_bucket_name)
print ("...")
print ("")

user_data_script = ""
user_data_script = """#!/bin/bash
            yum install httpd -y
            systemctl enable httpd
            systemctl start httpd
            TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
            echo '<html>' > index.html
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
            
#create ec2 bucket
ec2 = boto3.resource('ec2')
new_instances = ec2.create_instances(
    ImageId='ami-0277155c3f0ab2930',
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

print("---------------------------------------------------------------------------------")
print ("Created new EC2 instances:")
print ("ID: ", new_instances[0].id)
print ("Name: ", new_instances[0].tags[0]['Value'])
print ("")

new_instances[0].wait_until_running()
new_instances[0].reload() 
inst = ec2.Instance(new_instances[0].id)

print("---------------------------------------------------------------------------------")
print ("Instance is running")
print("TEST", inst.id, inst.state, inst.instance_type, inst.public_ip_address)
print("http://"+inst.public_ip_address)


#launching a browser
time.sleep(60)
new_instances[0].reload() 
ec2_url = "http://" + new_instances[0].public_ip_address
print ("EC2 URL: " + ec2_url)

webbrowser.open_new_tab(ec2_url)


#creating an S3 bucket
s3 = boto3.resource("s3")
s3.create_bucket(Bucket=s3_bucket_name) 

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
print("s3 bucket name is " + s3_bucket_name)
print("Upload an index.html file to test it works!")

#download image
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
		<title>Test File</title>
	    </head>

	    <body>
		This is a test file!  If you can see this, your index.html is working!
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
    print (error)    
    
print ("http://" + s3_bucket_name + ".s3-website-us-east-1.amazonaws.com/" + s3_file_upload)

#launching a browser
webbrowser.open_new_tab("http://" + s3_bucket_name + ".s3-website-us-east-1.amazonaws.com/" + s3_file_upload)


