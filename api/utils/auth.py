import os
from fastapi import HTTPException, Query, status

def validate_api_key(api_key: str = Query(...)):
    print(api_key, os.getenv("API_KEY"))
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )