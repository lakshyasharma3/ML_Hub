# tasks.py
from celery import Celery
from datetime import datetime
import boto3
import requests
import google.generativeai as genai

celery = Celery(
    "tasks",
    broker="pyamqp://guest@localhost//",
    include=["tasks"]
)

# Configure DynamoDB
aws_access_key_id = 'AKIA2WBXJS74AID2255N'
aws_secret_access_key = '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'
region_name = 'ap-south-1'

# Create DynamoDB resource
dynamodb = boto3.resource('dynamodb', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key, region_name=region_name)

# Access DynamoDB table
table = dynamodb.Table('ML_Hub_logs_LLM')

# Configure Generative AI
genai.configure(api_key="AIzaSyCv1C_gOBfyahXvj4ujp7oBHA4c9ha1aIg")
model = genai.GenerativeModel('gemini-pro')


@celery.task
def generate_content_task(prompt, call_back_url,u_id):
    try:

        response = model.generate_content(prompt)

        update_database(id, status="success")
        # You can add additional logic here to handle the callback URL or any other post-processing tasks.
        post_response_to_callback(u_id,response.text, call_back_url)

    except Exception as e:
        update_database(id, status="error")
        print(f"Error generating content: {str(e)}")
        # Log or handle the error as needed


def post_response_to_callback(u_id,response_text, callback_url):
    try:
        # Make an HTTP POST request to the callback URL
        response = requests.post(callback_url, json={"tracking_id":u_id,"response": response_text})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error posting response to callback URL: {str(e)}")
        # Log or handle the error as needed


def update_database(id: str, status: str, last_updated: str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")):
    try:
        table.put_item(Item={
            'TrackingID': id,
            'LastUpdated': last_updated,
            'Status': status,
        })
    except Exception as e:
        print(f"Error logging to DynamoDB: {str(e)}")
