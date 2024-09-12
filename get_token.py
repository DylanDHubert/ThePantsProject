import os
from dropbox import DropboxOAuth2FlowNoRedirect

APP_KEY = 'ccuo0hm05rxkxu4'
APP_SECRET = 'biqx8pl2m05paq6'

auth_flow = DropboxOAuth2FlowNoRedirect(
    APP_KEY, 
    APP_SECRET,
    token_access_type='offline'  # This is crucial for getting a refresh token
)

authorize_url = auth_flow.start()
print("1. Go to: " + authorize_url)
print("2. Click \"Allow\" (you might have to log in first)")
print("3. Copy the authorization code.")
auth_code = input("Enter the authorization code here: ").strip()

try:
    oauth_result = auth_flow.finish(auth_code)
    print("Access Token:", oauth_result.access_token)
    print("Refresh Token:", oauth_result.refresh_token)
    print("Expiration:", oauth_result.expires_at)
    
    with open('.env', 'a') as f:
        f.write(f"\nDROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}")
        f.write(f"\nDROPBOX_APP_KEY={APP_KEY}")
    print("Tokens have been appended to your .env file")
except Exception as e:
    print('Error: %s' % (str(e),))