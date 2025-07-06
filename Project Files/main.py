from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference
import os

# Load environment variables
load_dotenv()

API_KEY = os.getenv("IBM_API_KEY")
ENDPOINT = os.getenv("IBM_GRANITE_ENDPOINT")
MODEL_ID = os.getenv("IBM_MODEL_ID")
PROJECT_ID = os.getenv("IBM_PROJECT_ID")

# FastAPI setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Safely call model and return generated response
def query_model(prompt: str):
    try:
        model = ModelInference(
            model_id=MODEL_ID,
            project_id=PROJECT_ID,
            credentials={"apikey": API_KEY, "url": ENDPOINT}
        )
        response = model.generate_text(
            prompt=prompt,
            params={"max_new_tokens": 100, "decoding_method": "greedy"}
        )

        # If it's a string (correct format), return it
        if isinstance(response, str):
            return response

        # If it's a dict, try to extract result
        elif isinstance(response, dict) and "results" in response:
            return response["results"][0].get("generated_text", "No result found.")

        # Any other format
        else:
            return f"⚠️ Unexpected response format: {response}"
    except Exception as e:
        return f"⚠️ Error while generating response: {str(e)}"

# Routes

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/predict", response_class=JSONResponse)
async def predict(user_input: str = Form(...)):
    prompt = f"Symptoms: {user_input}\nWhat disease could it be? give 3 lines of explanation also in bullet points"
    result = query_model(prompt)
    # Format as bullet list
    fresult = "\n".join(f"👉 {item.strip()}" for item in result.split(".") if item.strip())

    return {"result": fresult}

@app.post("/remedies", response_class=JSONResponse)
async def remedies(user_input: str = Form(...)):
    prompt = f"Disease or Symptoms: {user_input}\nGive a list of natural remedies (max 6) give in points line by line."
    import re
    result = query_model(prompt)
    fresult= "\n".join(
    f" {item.strip()}"
    for item in re.split(r"\d+\.\s*", result)
    if item.strip()
)
    return {"result": fresult}

@app.get("/tips", response_class=JSONResponse)
async def tips():
    prompt = "Give 12 health tips"
    result = query_model(prompt)
    return {"result": result}
@app.post("/chat", response_class=JSONResponse)
async def chat(user_input: str = Form(...)):
    prompt = (
        f"You are a smart and helpful health assistant. "
        f"Respond to the user's health questions clearly and accurately.\n\n"
        f"User: {user_input}\n"
        f"Assistant:"
    )
    result = query_model(prompt)
    return {"result": result}
@app.post("/treatment", response_class=JSONResponse)
async def treatment(user_input: str = Form(...)):
    prompt = (
        f"Condition and patient details: {user_input}\n"
        f"Generate a concise treatment plan with exactly 3 points for each section:\n"
        f"1. Medications\n"
        f"2. Lifestyle changes\n"
        f"3. Follow-up care"
    )

    result = query_model(prompt)

    # Return plain text as result
    return {"plan": result.strip()}
@app.post("/ai-insights", response_class=JSONResponse)
async def ai_insights(
    heart_rate: str = Form(...),
    blood_pressure: str = Form(...),
    glucose: str = Form(...)
):
    # Combine into prompt
    user_data = (
        f"Heart Rate: {heart_rate}\n"
        f"Blood Pressure (systolic): {blood_pressure}\n"
        f"Blood Glucose: {glucose}"
    )

    prompt = (
        f"Analyze the following 7-day health data trends:\n{user_data}\n\n"
        f"Give 2 potential health insights and 3 improvement recommendations."
    )

    result = query_model(prompt)
    return {"result": result}


# Optional: Quick frontend test
@app.post("/chat-test", response_class=JSONResponse)
async def chat_test(user_input: str = Form(...)):
    return {"result": f"✅ Echo: {user_input}"}


