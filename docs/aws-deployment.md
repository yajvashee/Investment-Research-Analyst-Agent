# AWS Deployment Guide

## Current status

The local Docker deployment is verified. AWS deployment was not executed from this machine because the AWS CLI has no configured profile, credentials, or default region. No AWS resources, charges, or deployment claims have been made.

## Recommended training-project architecture

For the simplest reproducible deployment, use one small EC2 instance running the same Docker Compose stack:

```text
Browser
  -> EC2 public IP or DNS name
  -> Streamlit container
  -> FastAPI container
  -> PostgreSQL container
```

This is simpler than ECS/RDS/S3 for a short training project because it reuses the already-tested Docker Compose configuration. It is not the recommended design for a large production system; a production version would normally use managed RDS PostgreSQL and external document storage.

## Before deployment

1. Obtain an AWS account, an IAM user or role with permission to launch an EC2 instance, and a chosen region.
2. Configure the AWS CLI locally without committing credentials:

   ```powershell
   aws configure
   aws sts get-caller-identity
   ```

3. Create a security group that allows:

   - TCP 22 from your own IP address only, for SSH;
   - TCP 8501 from your demonstrator/tester IP range, for Streamlit.

4. Create an Ubuntu EC2 instance large enough for Docker, Python dependencies, and the local Chroma index.

## EC2 deployment steps

On the EC2 instance:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
```

Sign out and back in, then copy or clone the project to the instance. Create `.env` only on the instance and add the required PostgreSQL, Azure OpenAI, and Alpha Vantage settings. Do not upload `.env` to Git.

Copy the active RAG documents and `data/chroma` index to the same relative paths. Then run:

```bash
docker compose up -d --build
docker compose ps
```

Open:

```text
http://<EC2-public-DNS-or-IP>:8501
```

## Optional ECR image registry

ECR is optional for the simple EC2 approach. If a course requires images to be stored in ECR, create backend and frontend repositories, authenticate Docker, tag the locally built images, and push them. The EC2 instance can then pull the images before running Compose.

Do not create ECR repositories or push images until AWS credentials and a billing owner are confirmed.

## Production configuration values

| Setting | Local Docker Compose | EC2 Docker Compose | Managed-service alternative |
|---|---|---|---|
| `BACKEND_URL` | `http://backend:8000` inside frontend | `http://backend:8000` inside frontend | deployed backend URL/load balancer |
| `POSTGRES_HOST` | `postgres` inside backend | `postgres` inside backend | RDS endpoint |
| RAG documents/index | bind mounts | bind mounts or copied project files | S3/EFS/object storage |

## Verification after deployment

1. Open the Streamlit page.
2. Ask `How has Microsoft's revenue changed?` to verify PostgreSQL.
3. Ask `What are Microsoft's main business risks?` to verify RAG.
4. Run `docker compose logs -f backend` if a request fails.

## Security notes

- Keep `.env` only on the deployed host or use a managed secret store.
- Do not expose PostgreSQL port 5432 publicly in a real deployment.
- Restrict the Streamlit security-group rule to the smallest practical IP range.
- Stop or terminate the EC2 instance after the presentation to avoid ongoing charges.
