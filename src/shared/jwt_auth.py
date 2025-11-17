import logging
import jwt
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException
from src.core.config import COGNITO_REGION, COGNITO_CLIENT_ID, USER_POOL_ID


COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

_jwks_cache: Optional[Dict] = None
_jwks_cache_time: Optional[datetime] = None
JWKS_CACHE_DURATION = timedelta(hours=24)


def get_jwks() -> Dict:
  global _jwks_cache, _jwks_cache_time

  now = datetime.now()

  if _jwks_cache and _jwks_cache_time:
    if now - _jwks_cache_time < JWKS_CACHE_DURATION:
      return _jwks_cache

  try:
    response = requests.get(JWKS_URL, timeout=10)
    response.raise_for_status()
    _jwks_cache = response.json()
    _jwks_cache_time = now
    return _jwks_cache
  except requests.RequestException as e:
    if _jwks_cache:
      return _jwks_cache
    raise HTTPException(status_code=500, detail=f"Failed to fetch JWKS: {str(e)}")


def get_public_key(token: str) -> str:
  try:
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")

    if not kid:
      raise HTTPException(status_code=401, detail="Token header missing 'kid'")

    jwks = get_jwks()

    for key in jwks.get("keys", []):
      if key.get("kid") == kid:
        return RSAAlgorithm.from_jwk(key)

    raise HTTPException(status_code=401, detail="Public key not found in JWKS")

  except jwt.DecodeError as e:
    raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")


def verify_session_token(access_token: str) -> Dict:
  try:
    public_key = get_public_key(access_token)

    decoded = jwt.decode(
      access_token,
      public_key,
      algorithms=["RS256"],
      issuer=COGNITO_ISSUER,
      options={
        "verify_signature": True,
        "verify_exp": True,
        "verify_iss": True,
        "require": ["exp", "iss", "token_use", "sub"],
      },
    )

    if decoded.get("token_use") != "access":
      raise HTTPException(status_code=401, detail="Token is not an access token")

    if COGNITO_CLIENT_ID and decoded.get("client_id") != COGNITO_CLIENT_ID:
      raise HTTPException(status_code=401, detail="Invalid client_id in token")

    logging.info(decoded)
    return decoded

  except jwt.ExpiredSignatureError:
    raise HTTPException(status_code=401, detail="Token has expired")
  except jwt.InvalidIssuerError:
    raise HTTPException(status_code=401, detail="Invalid token issuer")
  except jwt.InvalidTokenError as e:
    raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
  except jwt.PyJWTError as e:
    raise HTTPException(
      status_code=500, detail=f"Failed to decode access_token: {str(e)}"
    )
