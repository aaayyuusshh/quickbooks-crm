from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import requests
import base64
import uuid
from config import *

app = FastAPI()

state_token = str(uuid.uuid4())

# oauth login
@app.get("/login")
def login():
    auth_url = (
        f"{AUTH_BASE_URL}"
        f"?client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&scope=com.intuit.quickbooks.accounting"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state_token}"
    )
    return RedirectResponse(auth_url)

# oauth callback that gives us the access token required to make requests to quickbooks
@app.get("/callback")
def callback(request: Request):
    auth_code = request.query_params.get("code")
    realm_id = request.query_params.get("realmId")

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
    }

    token_response = requests.post(TOKEN_URL, headers=headers, data=data)
    token_json = token_response.json()

    return {"token_info": token_json, "realm_id": realm_id}
