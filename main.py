from fastapi import FastAPI, HTTPException
from tasks import generate_content_task
import uuid
import contants
from tasks import update_database

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Generative AI. Use post method with a prompt to get a response."}


@app.post("/")
async def generate_content(payload: dict):
    try:
        prompt = payload.get("prompt")
        call_back_url = payload.get("call_back_url")
        universal_id = payload.get("id")

        if not prompt:
            raise HTTPException(status_code=422, detail="Missing 'prompt' in request payload")
        if not call_back_url:
            raise HTTPException(status_code=422, detail="Missing 'call_back_url' in request payload")
        if not universal_id:
            raise HTTPException(status_code=422, detail="Missing 'universal_id' in request payload")

        id = str(uuid.uuid1())
        update_database(id, status=contants.LogStatus.PENDING)
        
        # generate_content_task.delay(prompt, call_back_url,universal_id,id)

        return {"status": "Task scheduled for processing"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")
