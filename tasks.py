import boto3
import requests
import google.generativeai as genai
import constants

# AWS DynamoDB Configuration
aws_access_key_id = constants.Credentials.aws_access_key_id
aws_secret_access_key = constants.Credentials.aws_secret_access_key
region_name = constants.Credentials.region_name

# Generative AI Configuration
genai.configure(api_key=constants.Credentials.api_key)
model = genai.GenerativeModel('gemini-pro')

# Create DynamoDB resource and access table
dynamodb = boto3.resource('dynamodb', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key, region_name=region_name)
table = dynamodb.Table('ML_Hub_logs_LLM')

def generate_content_task(id: str):
    try:
        # Fetch the task details from DynamoDB
        task = fetch_data_from_database(id)
        
        if task:
            # Generate content
            status_update(id, status=constants.LogStatus.IN_PROGRESS)
            response = model.generate_content(task['Prompt'])
            
            # Update DynamoDB table with task completion status
            status_update(id, status=constants.LogStatus.COMPLETED)
            
            # Add the generated response to DynamoDB
            add_response(id, response.text)
            
            # Trigger the callback URL with relevant data
            post_response_to_callback(task['uID'], response.text, task['CallBackURL'])
        else:
            print(f"Task not found in DynamoDB: {id}")
            
    except Exception as e:
        # Handle errors and update status
        status_update(id, status=constants.LogStatus.FAILED)
        print(f"Error generating content: {str(e)}")

def post_response_to_callback(u_id, response_text, callback_url):
    try:
        # Make an HTTP POST request to the callback URL
        response = requests.post(callback_url, json={"tracking_id": u_id, "response": response_text})
        response.raise_for_status()
        print("Callback URL Triggered: ", callback_url)
        
    except requests.RequestException as e:
        print(f"Error posting response to callback URL: {str(e)}")
        # Log or handle the error as needed

def fetch_data_from_database(id: str):
    try:
        # Retrieve item from DynamoDB using TrackingID
        response = table.get_item(Key={'TrackingID': id})
        return response.get('Item', {})
        
    except Exception as e:
        print(f"Error fetching data from DynamoDB: {str(e)}")

def status_update(id: str, status: str):
    try:
        # Update the 'Status' attribute in DynamoDB for the specified TrackingID
        data = fetch_data_from_database(id)
        data['Status'] = status
        table.put_item(Item=data)
        
    except Exception as e:
        print(f"Error updating status in DynamoDB: {str(e)}")

def add_response(id: str, response: str):
    try:
        # Update the 'Response' attribute in DynamoDB for the specified TrackingID
        data = fetch_data_from_database(id)
        data['Response'] = response
        table.put_item(Item=data)
        
    except Exception as e:
        print(f"Error adding response to DynamoDB: {str(e)}")