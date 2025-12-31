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

# query helper
def quickbooks_query(access_token: str, realm_id: str, query: str):
    url = f"{API_BASE_URL}/v3/company/{realm_id}/query"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    response = requests.get(url, headers=headers, params={"query": query})
    if response.status_code == 200:
        return response.json().get("QueryResponse", {})
    else:
        return {"error": response.status_code, "message": response.text}

# endpoints
@app.get("/customers")
def get_customers(access_token: str, realm_id: str):
    query = "SELECT Id, DisplayName, PrimaryEmailAddr FROM Customer"
    return quickbooks_query(access_token, realm_id, query)

@app.get("/invoices")
def get_invoices(access_token: str, realm_id: str):
    query = "SELECT Id, DocNumber, CustomerRef, TotalAmt, Balance, TxnDate FROM Invoice"
    return quickbooks_query(access_token, realm_id, query)
