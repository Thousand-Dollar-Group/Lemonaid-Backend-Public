import jwt
from fastapi import HTTPException, Cookie
from src.core.config import COGNITO_DOMAIN
from src.shared.DB_utils import insert_user, get_user_by_id, update_user_username

def get_cognito_urls() -> dict:
    """Constructs the necessary Cognito OAuth2 URLs."""
    return {
        "token_url": f"{COGNITO_DOMAIN}/oauth2/token",
        "userdebug_url": f"{COGNITO_DOMAIN}/oauth2/userInfo",
    }

def decode_id_token(id_token: str) -> dict:
    try:

        claims = jwt.decode(id_token, options={"verify_signature": False})
        return claims
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=500, detail=f"Failed to decode id_token: {str(e)}")
    

def register_user_with_id_token(id_token: str):
    """
    Registers a new user into the database using the provided id_token.
    This function decodes the given JWT `id_token` to extract user claims,
    retrieves the required fields (sub, name, email), and inserts the user
    into the 'users' table of the database if they do not already exist.
    Args:
        id_token (str): A JWT id_token obtained from Cognito or another identity provider.
    Returns:
        tuple[str, str, str]: A tuple containing (user_id, username, email).
    """
    try:
        claims = decode_id_token(id_token)

        user_id = claims.get("sub")
        username = claims.get("name")
        email = claims.get("email")
        picture = claims.get("picture")

        if not user_id or not username or not email:
            raise ValueError("Missing required claims: sub, name, or email")

        user_info = get_user_by_id(user_id)
        if user_info:
            if user_info["username"] != username:
                new_username = update_user_username(user_id, username)
                return {
                    "user_id": user_info['user_id'], 
                    "username": new_username if new_username else username, 
                    "email": user_info['email'], 
                    "picture": picture
                }
            else: 
                return {
                    "user_id": user_info['user_id'], 
                    "username": user_info['username'], 
                    "email": user_info['email'], 
                    "picture": picture
                }
        ret = insert_user(user_id, username, email)
        if ret != user_id:
            raise ValueError("Failed to insert or retrieve user from database")

        return {
            "user_id": user_id, 
            "username": username, 
            "email": email, 
            "picture": picture
        }
    except Exception as e:
        raise
