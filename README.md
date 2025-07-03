# Setup local testing

docker build -t fastapi-app .
docker run -d -p 8080:8080 fastapi-app
docker run -it --rm fastapi-app p 8080:8080 /bin/bash

uvicorn api.main:app --reload
# Visit http://localhost:8080


# Install and initialize gcloud SDK
gcloud init
gcloud auth application-default login

# Deploy
gcloud app deploy