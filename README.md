# 🚀 FastAPI Deployment Guide (with Docker on AWS EC2)

This guide walks you through setting up and deploying your Dockerized FastAPI app on an AWS EC2 instance for local testing or lightweight production use.

---

## 📦 Local Setup (Optional)

To test the service locally using Docker Compose:

```bash
docker compose up -d
```

To view logs:

```bash
docker compose logs -f
```

To stop:

```bash
docker compose down
```

---

## 🔑 Using .env for Secret Keys

To securely manage secrets like API keys, create a `.env` file in your project root:

### Example `.env` file:

```env
API_KEY=your-super-secret-api-key
APP_ENV=production
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
```

Add the `.env` file to your `.gitignore` to prevent accidental commits:

```bash
echo ".env" >> .gitignore
```

In your FastAPI app, load the environment variables using `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
```

Docker Compose will automatically load variables from the `.env` file if specified using the `env_file` option in your `docker-compose.yml`:

```yaml
env_file:
  - .env
```

---

## ☁️ AWS Security Group Configuration

Before deploying to EC2, configure your **security group** to allow necessary traffic:

### Steps (via AWS Console):

1. Go to [EC2 Dashboard](https://console.aws.amazon.com/ec2)
2. Click **"Security Groups"** in the sidebar
3. Select your security group
4. Click **"Edit inbound rules"**
5. Add the following rules:

| Type       | Protocol | Port Range | Source                  | Description        |
| ---------- | -------- | ---------- | ----------------------- | ------------------ |
| SSH        | TCP      | 22         | Your IP or `0.0.0.0/0`¹ | Remote login (SSH) |
| HTTP       | TCP      | 80         | `0.0.0.0/0`             | Web (Nginx)        |
| HTTPS      | TCP      | 443        | `0.0.0.0/0`             | Secure Web         |
| Custom TCP | TCP      | 8000       | `0.0.0.0/0`             | FastAPI (dev/test) |

¹ Replace `0.0.0.0/0` with your IP address for SSH to improve security.

6. Click **Save rules**

---

## 🚀 Deploying to EC2

### 1. Launch Your EC2 Instance

* Go to the [EC2 Console](https://console.aws.amazon.com/ec2)
* Launch a new instance:

  * OS: **Ubuntu 22.04 LTS**
  * Instance type: **t3.micro** (free tier eligible)
* Configure the security group as shown above
* Download your **`.pem` key file** and move it to your project root

---

### 2. SSH into Your Instance & Install Docker

```bash
ssh -i my-key.pem ubuntu@<your-ec2-public-ip>
```

Inside the instance:

```bash
sudo apt update && sudo apt install docker.io -y
sudo apt install docker-compose -y
sudo usermod -aG docker $USER
newgrp docker  # Apply group change without reboot
```

Then exit the instance:

```bash
exit
```

Or press `Ctrl + D`

---

### 3. Upload Your FastAPI Project to EC2

From your local machine:

```bash
scp -i my-key.pem -r ./your-fastapi-app ubuntu@<your-ec2-ip>:/home/ubuntu/
```

---

### 4. SSH Back and Run the App

```bash
ssh -i my-key.pem ubuntu@<your-ec2-public-ip>
```

Inside the EC2 instance:

```bash
cd your-fastapi-app
docker compose up -d
```

---

## 🔍 Monitoring and Managing the App

* View logs:

  ```bash
  docker compose logs -f
  ```

* Stop the service:

  ```bash
  docker compose down
  ```

---

## 🧠 Notes

* Make sure your `.pem` file has correct permissions:

  ```bash
  chmod 400 my-key.pem
  ```

* Access your FastAPI app at:

  ```
  http://<your-ec2-public-ip>:8000/
  ```

---

## ✅ What's Next?

* Add Nginx + HTTPS support for production
* Configure environment variables with `.env`
* Automate deployment with GitHub Actions or Ansible

---
