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


print ("")
print ("Running automated script to create, launch and monitor web servers")
print ("")

# datetime object containing current date and time
now = datetime.now()
dt_string = now.strftime("d%Y-%m-%dt%H-%M-%S")
ec2_name = "ab-assignment-" + dt_string
print("ec2 name: " + ec2_name)

# random string to be used for bucket name
random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

s3_bucket_name = random_str + "-aballot"
print("s3 bucket name: " + s3_bucket_name)
print ("...")
print ("")

#create ec2 bucket
ec2 = boto3.resource('ec2')
new_instances = ec2.create_instances(
    ImageId='ami-0277155c3f0ab2930',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.nano',
    KeyName='abstudentkey',
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
        'httpssh',
    ],
    UserData="""#!/bin/bash
            yum install httpd -y
            systemctl enable httpd
            systemctl start httpd
            echo '<html>' > index.html
            echo 'Private IP address: ' >> index.html
            TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"`
            curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
            cp index.html /var/www/html/index.html"""
    )

#time.sleep(3) # Sleep for 3 seconds

print ("Created new EC2 instances:")
print ("ID: ", new_instances[0].id)
print ("Name: ", new_instances[0].tags[0]['Value'])
print ("...")
print ("")

new_instances[0].wait_until_running()
new_instances[0].reload() 
print ("Instance is running")

#print ("IP Address: ", new_instances[0].public_ip_address)

#for inst in ec2.instances.all():
#    print(inst.id, inst.state, inst.instance_type, inst.public_ip_address)


inst = ec2.Instance(new_instances[0].id)
print("TEST", inst.id, inst.state, inst.instance_type, inst.public_ip_address)
print("http://"+inst.public_ip_address)


#launching a browser
time.sleep(60)
new_instances[0].reload() 
ec2_url = "http://" + new_instances[0].public_ip_address
print (ec2_url)
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

bucket_website = s3.BucketWebsite(s3_bucket_name)   # replace with your bucket name or a string variable

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
    
#put image in object
object_name = "index.html"

html_data = f"""
	<!doctype html>
	<html>
	    <head>
		<meta charset="utf-8">
		<title>Test File</title>
	    </head>

	    <body>
		This is a test file!  If you can see this, your index.html is working!
		<img src=""" + image_name + """ alt="Assignment 1 Image">
	    </body>
	</html>
    """
    
    
try:
    #response = s3.Object(s3_bucket_name, object_name).put(Body=open(object_name, 'rb'))
    s3client.put_object(Bucket=s3_bucket_name, Key=object_name, Body=html_data.encode('utf-8'), ContentType='text/html')
    with open(image_name, 'rb') as file:
            s3client.put_object(Bucket=s3_bucket_name, Key=image_name, Body=file, ContentType='image/jpeg')
except Exception as error:
    print (error)    
    

print ("http://" + s3_bucket_name + ".s3-website-us-east-1.amazonaws.com/" + object_name)


