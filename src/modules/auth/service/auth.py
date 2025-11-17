import base64
from typing import Optional
import httpx
from fastapi import Request, HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from src.core.config import COGNITO_CLIENT_ID, COGNITO_CLIENT_SECRET, APP_FRONTEND_URL
from src.modules.auth.lib.cognito_utils import get_cognito_urls, register_user_with_id_token


async def auth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    """
    Handles the redirect from Cognito after a user logs in.
    It exchanges the authorization code for JWT tokens.
    """
    if error:
        # If Cognito returns an error (e.g., user cancels login)
        raise HTTPException(status_code=400, detail=f"Cognito error: {error}")

    if not code:
        # If 'code' is not in the query parameters, something went wrong.
        raise HTTPException(status_code=400, detail="Authorization code not found in callback.")

    # 1. Prepare to exchange the authorization code for tokens
    cognito_urls = get_cognito_urls()
    token_url = cognito_urls["token_url"]
    redirect_uri = str(request.url).split('?')[0] # The base URL of this callback endpoint

    # 2. Encode Client ID and Client Secret for the Authorization header
    auth_str = f"{COGNITO_CLIENT_ID}:{COGNITO_CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_b64}'
    }

    # 3. Define the payload for the token request
    payload = {
        'grant_type': 'authorization_code',
        'client_id': COGNITO_CLIENT_ID,
        'code': code,
        'redirect_uri': redirect_uri
    }

    # 4. Make the POST request to Cognito's token endpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
            tokens = response.json()

            # Define the URL to redirect to after successful login
            redirect_url = f"{APP_FRONTEND_URL}" # make this as an environment variable

            # Create a redirect response
            response = RedirectResponse(url=redirect_url)

            # Set the tokens in secure, HttpOnly cookies
            # HttpOnly=True means JavaScript can't access the cookie, which is crucial for security!
            response.set_cookie(
                key="access_token",
                value=tokens['access_token'],
                httponly=True,
                secure=False,       # Only send over HTTPS
                samesite='lax'     # Helps prevent CSRF attacks
            )
            response.set_cookie(
                key="id_token",
                value=tokens['id_token'],
                httponly=True,
                secure=False,
                samesite='lax'
            )

            response.set_cookie(
                key="refresh_token",
                value=tokens['refresh_token'],
                httponly=True,
                secure=False,
                samesite='lax'
            )

            return response # Send the redirect response to the browser
            

    except httpx.HTTPStatusError as e:
        # Log the error and response for debugging
        print(f"Error exchanging code for tokens: {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to exchange authorization code for tokens. Cognito responded with: {e.response.text}"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

async def auth_post_user(request: Request):
    """
    Register a user using the id_token stored in cookies.
    """
    try:
        # print("Headers:", request.headers)
        # print("Cookies received:", request.cookies)
        id_token = request.cookies.get("id_token")
        # print(id_token)
        if not id_token:
            raise HTTPException(status_code=401, detail="id_token not found in cookies")

        resp = register_user_with_id_token(id_token)
        return resp
    except Exception as e:
        raise e 

async def auth_logout():
    """
    Logout the user by clearing authentication cookies.
    """
    response = JSONResponse(content={"message": "Logged out successfully."})

    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="id_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")

    return response