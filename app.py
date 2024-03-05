import re
from os import environ as env

from datetime import datetime

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, session, request
from fusionauth.fusionauth_client import FusionAuthClient


ENV_FILE = find_dotenv()
if ENV_FILE:
  load_dotenv(ENV_FILE)

app = Flask(__name__)  # default
app.secret_key = env.get("APP_SECRET_KEY")
app.fa_url = env.get("ISSUER")

fusionauth_api_client = FusionAuthClient(app.secret_key, app.fa_url)

# oauth = OAuth(app)

# oauth.register(
#   "FusionAuth",
#   client_id=env.get("CLIENT_ID"),
#   client_secret=env.get("CLIENT_SECRET"),
#   client_kwargs={
#     "scope": "openid offline_access",
#     'code_challenge_method': 'S256' # This enables PKCE
#   },
#   server_metadata_url=f'{env.get("ISSUER")}/.well-known/openid-configuration'
# )

# if __name__ == "__main__":
#   app.run(host="localhost", port=env.get("PORT", 8010))

@app.route("/")
def home():
    return "Hello Flask"

@app.route("/hello/<name>")
def hello_there(name):
    now = datetime.now()
    formatted_now = now.strftime("%A, %d %B, %Y at %X")

    # Filter the name argument to letters only using regular expressions. URL arguments
    # can contain arbitrary text, so we restrict to safe characters only.
    match_object = re.match("[a-zA-Z]+", name)

    if match_object:
        clean_name = match_object.group(0)
    else:
        clean_name = "Friend"

    content = "Hello there, " + clean_name + "! It's " + formatted_now
    return content

@app.route("/tenant/<tenant_name>", methods=["POST"])
def create_tenant(tenant_name: str):
  tenant_data = {
      'tenant' : {
          'name': tenant_name
      }
  }

  client_response = fusionauth_api_client.create_tenant(tenant_data)

  if client_response.was_successful():
    tenant_data = client_response.success_response['tenant']
    return tenant_data, 201
  else:
    return client_response.error_response, client_response.status
  
@app.route("/application/<application_name>/<tenant_id>", methods=["POST"])
def create_application(application_name: str, tenant_id: str):
   
  application_data = {
    'application' : {
      'name': application_name,
      'oauthConfiguration': {
        'authorizedRedirectURLs': [
          'https://fusionauth.io'
        ],
        'enabledGrants': [
          'authorization_code'
        ]
      }
    }
  }

  fusionauth_api_client.set_tenant_id(tenant_id)

  client_response = fusionauth_api_client.create_application(application_data)

  if client_response.was_successful():
    application_data = client_response.success_response['application']
    return application_data, 201
  else:
    return client_response.error_response, client_response.status

@app.route("/register/<username>/<application_id>", methods=["POST"])
def create_and_register_user(username: str, application_id: str):

    user_registration_data = {
      'registration' : {
          'applicationId': application_id
      },
      'user': {
          'email': username + "@fusionauth.io",
          'password': 'password',
          'username': username
      },
      'SetPasswordEmail': False,
      'skipVerification': False
    }
    
    client_response = fusionauth_api_client.register(user_registration_data)

    if client_response.was_successful():
      user_data = client_response.success_response['user']
      return user_data, 201
    else:
      return client_response.error_response, client_response.status
