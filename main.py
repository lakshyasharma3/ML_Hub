from fastapi import FastAPI, HTTPException
import uuid
from tasks import generate_content_task
import constants as constants
from datetime import datetime
import boto3

# Configure AWS credentials and DynamoDB region
aws_access_key_id = constants.Credentials.aws_access_key_id
aws_secret_access_key = constants.Credentials.aws_secret_access_key
region_name = constants.Credentials.region_name

# Create DynamoDB resource
dynamodb = boto3.resource('dynamodb', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key, region_name=region_name)

# Access DynamoDB table
table = dynamodb.Table('ML_Hub_logs_LLM')

app = FastAPI()

@app.get("/")
def read_root():
    """
    Endpoint to get a welcome message.
    """
    return {"message": "Welcome to the Generative AI. Use POST method with a prompt to get a response."}

@app.post("/")
async def generate_content(payload: dict):
    """
    Endpoint to generate content based on the provided prompt.

    Args:
        payload (dict): Request payload containing 'prompt', 'call_back_url', and 'id'.

    Returns:
        dict: Status message indicating if the task is scheduled for processing.
    """
    try:
        prompt = payload.get("prompt")
        call_back_url = payload.get("call_back_url")
        universal_id = payload.get("id")

        # Validate payload
        if not prompt or not call_back_url or not universal_id:
            raise HTTPException(status_code=422, detail="Missing required fields in the request payload")

        # Generate unique ID for tracking
        id = str(uuid.uuid1())

        # Create an entry in DynamoDB with PENDING status
        database_create(id, payload, status=constants.LogStatus.PENDING)

        # Schedule content generation task
        generate_content_task(id)

        return {"status": "Task scheduled for processing"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

def database_create(id: str, payload: dict, status: str, last_updated: str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")):
    """
    Function to create an entry in DynamoDB.

    Args:
        id (str): Tracking ID.
        payload (dict): Request payload.
        status (str): Status of the entry.
        last_updated (str): Last updated timestamp (default is the current timestamp).

    Returns:
        None
    """
    try:
        table.put_item(Item={
            'TrackingID': id,
            'LastUpdated': last_updated,
            'Status': status,
            'Prompt': payload.get("prompt"),
            'CallBackURL': payload.get("call_back_url"),
            'uID': payload.get("id"),
            'Response': ""
        })
    except Exception as e:
        print(f"Error logging to DynamoDB: {str(e)}")
