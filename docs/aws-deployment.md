# AWS Deployment Guide

This document records how the Investment Research Analyst was deployed to AWS
in `eu-west-2` and explains the purpose of every service used.

> Never commit API keys, passwords, AWS credentials, or secret values.

## Architecture

```text
Internet user
    |
Application Load Balancer (public subnets, port 80)
    |
ECS Fargate task (private subnets)
    |-- Streamlit frontend (8501)
    `-- FastAPI backend (8000)
          |-- RDS PostgreSQL (5432)
          |-- OpenSearch (HTTPS 443)
          |-- Azure OpenAI (through NAT)
          `-- Alpha Vantage (through NAT)
```

The frontend and backend run in the same ECS task, so the frontend reaches the
backend at `http://127.0.0.1:8000`.

## 1. Docker images

**What:** A Docker image is a packaged blueprint containing the code, runtime,
dependencies, and startup instructions. A container is a running instance of
that image.

**What we did:** Built and tested separate frontend and backend images:

```powershell
docker compose build backend frontend
docker compose up -d
docker compose ps
```

## 2. Amazon ECR

**What:** Private storage for Docker images. ECS downloads images from ECR when
starting containers.

**Created:**

- `yaj-investment-research-backend`
- `yaj-investment-research-frontend`

**Steps:**

1. Create both private repositories.
2. Confirm the AWS CLI identity and region:

   ```powershell
   aws sts get-caller-identity
   aws configure get region
   ```

3. Authenticate Docker using ECR's **View push commands** instructions.
4. Tag each local image with its full ECR URI and a version such as `v4`.
5. Push the images and verify their tags and digests in ECR.

Use the existing repositories for later releases; push a new image tag rather
than creating another repository.

## 3. VPC and subnets

**What:** A VPC is the private AWS network connecting the application
resources. It provides networking but does not run the application.

**Created:**

- VPC: `yaj-investment-vpc`
- CIDR: `10.0.0.0/16`
- Two public subnets in `eu-west-2a` and `eu-west-2b`
- Two private subnets in `eu-west-2a` and `eu-west-2b`
- DNS hostnames and DNS resolution enabled

**Purpose:** The public subnets contain the load balancer. The private subnets
contain ECS, RDS, and OpenSearch so users cannot connect to them directly.

## 4. Internet Gateway and NAT Gateway

**Internet Gateway:** Connects the public subnets to the internet. The public
route table sends `0.0.0.0/0` to `yaj-investment-igw`. This lets users reach the
public load balancer.

**NAT Gateway:** Lets resources in private subnets initiate outbound internet
connections without accepting inbound internet connections. ECS uses it to
call Azure OpenAI and Alpha Vantage.

## 5. Security groups

**What:** Virtual firewalls specifying which traffic may reach a resource.

| Security group | Inbound rule | Purpose |
|---|---|---|
| `yaj-investment-alb-sg` | TCP 80 from `0.0.0.0/0` | Public access to the load balancer. |
| `yaj-investment-ecs-sg` | TCP 8501 from the ALB group | Only the ALB can reach Streamlit. |
| `yaj-investment-rds-sg` | TCP 5432 from the ECS group | Only ECS can reach PostgreSQL. |
| `yaj-investment-opensearch-sg` | TCP 443 from the ECS group | Only ECS can reach OpenSearch. |

Referencing another security group is safer than permitting a broad IP range.

## 6. Amazon RDS for PostgreSQL

**What:** An AWS-managed relational database storing structured data in tables.
It replaces the local PostgreSQL Docker container.

**Created:**

- Instance: `yaj-investment-postgres`
- Engine: PostgreSQL 16
- Database: `investment_agent`
- Username: `postgres`
- Port: `5432`
- DB subnet group: `yaj-investment-db-subnet-group`
- Public access: No
- Security group: `yaj-investment-rds-sg`

The ECS backend needs the RDS endpoint, database name, port and username. The
password comes from the RDS master-credentials secret, not plain text.

## 7. Amazon OpenSearch Service

**What:** A managed search engine. It stores document chunks and their vector
embeddings. The backend searches it for relevant evidence before the AI creates
an answer; this is the retrieval part of RAG.

**Created:**

- Domain: `yaj-investment-opensearch`
- VPC-only access in private subnets
- IPv4 and HTTPS port `443`
- Instance: `t3.small.search`
- Security group: `yaj-investment-opensearch-sg`
- Application index: `investment-research`
- Fine-grained access with the ECS task role as IAM master

The domain policy allows the task role to make the required `es:ESHttp*`
requests against the domain resources ending in `/*`.

IPv4 was required because the subnets had no IPv6 CIDR blocks; selecting dual
stack caused the original domain validation failure.

## 8. AWS Secrets Manager

**What:** Secure runtime storage for passwords and API keys.

**Used:**

- RDS master-credentials secret: PostgreSQL username and password.
- Application secret: `AZURE_API_KEY` and `ALPHA_VANTAGE_API_KEY`.

Only secret ARNs are referenced by IAM and ECS. Actual values must not appear
in Docker images, documentation, task-definition plain-text values, or Git.

## 9. IAM roles and policies

**What:** IAM controls which AWS actions identities and resources may perform.

**Execution role — `yaj-investment-ecs-task-execution-role`:** Used by ECS while
starting the task. It pulls ECR images, sends logs to CloudWatch, and reads the
specific Secrets Manager values.

**Task role — `yaj-investment-ecs-task-role`:** Used by the running application.
It authorises the backend's signed OpenSearch requests.

In short: the execution role starts the containers; the task role is used by
the code after it starts.

## 10. Amazon CloudWatch

**What:** Stores logs and operational information from AWS resources.

**Created:**

- `/ecs/yaj-investment-backend`
- `/ecs/yaj-investment-frontend`

These contain startup messages, Python output, errors, tracebacks, and output
from one-time initialisation tasks.

## 11. ECS cluster and Fargate

**ECS:** Manages container workloads. The cluster
`yaj-investment-cluster` logically organises the service and tasks.

**Fargate:** Supplies and manages the computers that run the containers. No EC2
virtual machine had to be created or maintained manually.

## 12. ECS task definition

**What:** The blueprint ECS follows to start the application. It specifies
images, ports, environment values, secrets, roles, CPU, memory, and logging.

**Created:** Family `yaj-investment-app`, containing two containers.

### Backend container

- Backend ECR image and port `8000`.
- RDS environment:

  ```text
  POSTGRES_HOST=<RDS endpoint without :5432>
  POSTGRES_PORT=5432
  POSTGRES_DB=investment_agent
  POSTGRES_USER=postgres
  ```

- OpenSearch environment:

  ```text
  VECTOR_STORE=opensearch
  OPENSEARCH_ENDPOINT=<OpenSearch VPC endpoint>
  OPENSEARCH_INDEX=investment-research
  OPENSEARCH_SERVICE=es
  OPENSEARCH_TIMEOUT_SECONDS=60
  AWS_REGION=eu-west-2
  ```

- Azure settings: `AZURE_ENDPOINT`, `EMBED_DEPLOYMENT`,
  `EMBED_API_VERSION`, `CHAT_DEPLOYMENT`, and `CHAT_API_VERSION`.
- Secret references: `POSTGRES_PASSWORD`, `AZURE_API_KEY`, and
  `ALPHA_VANTAGE_API_KEY`.
- CloudWatch group: `/ecs/yaj-investment-backend`.

### Frontend container

- Frontend ECR image and port `8501`.
- `BACKEND_URL=http://127.0.0.1:8000`.
- `BACKEND_TIMEOUT_SECONDS=90`.
- CloudWatch group: `/ecs/yaj-investment-frontend`.

## 13. Target group and Application Load Balancer

**Target group:** Tells the load balancer where to forward requests and how to
test target health.

- `yaj-investment-frontend-tg`
- Target type: IP
- HTTP port `8501`
- Health path: `/_stcore/health`

ECS registers task IP addresses automatically; no IP is added manually.

**Application Load Balancer:** The application's public entrance.

- `yaj-investment-alb`
- Internet-facing in both public subnets
- Security group: `yaj-investment-alb-sg`
- Listener: HTTP port `80`
- Forwards to `yaj-investment-frontend-tg`

The ALB DNS name is the URL users open.

## 14. ECS service

**What:** Keeps the requested number of application tasks running and replaces
a task if it crashes.

**Created:**

- Service: `yaj-investment-service`
- Cluster: `yaj-investment-cluster`
- Fargate with one desired task
- Both private subnets; public IP off
- Security group: `yaj-investment-ecs-sg`
- Frontend port `8501` attached to the target group
- Rolling updates with circuit breaker and rollback
- Health-check grace period: `120` seconds

A healthy deployment shows Active, desired 1, running 1, pending 0, successful
deployment, and a healthy load-balancer target.

## 15. Initialise the data

A one-time standalone ECS task used the backend container to seed PostgreSQL
and build the OpenSearch RAG index. Successful CloudWatch output showed:

```text
Seed rows 0
Indexed chunks 203
```

`Seed rows 0` meant the rows already existed. `Indexed chunks 203` confirmed
OpenSearch indexing. This temporary task should stop with exit code `0`; the
permanent ECS service task should remain running.

## 16. Verify the deployment

1. Confirm the ALB is **Active**.
2. Confirm ECS shows one running task and a successful deployment.
3. Confirm the target group has a healthy target.
4. Open the ALB DNS name with `http://`.
5. Test a structured-data question and a RAG/document question.
6. Inspect both CloudWatch log groups for errors.

The final test successfully returned an Apple-versus-Microsoft investment
comparison through the public Streamlit page.

## 17. What happens when a user asks a question

1. The browser sends a request to the ALB DNS name.
2. The Internet Gateway allows it to reach the public ALB.
3. The ALB forwards it to Streamlit on port `8501`.
4. Streamlit calls FastAPI at `127.0.0.1:8000` in the same task.
5. FastAPI may query PostgreSQL for structured data.
6. FastAPI may query OpenSearch for relevant document chunks.
7. FastAPI calls Azure OpenAI and, if needed, Alpha Vantage through NAT.
8. The response returns through Streamlit and the ALB to the browser.

## 18. Deploy a future code update

Do not recreate the VPC, RDS database, OpenSearch domain, ALB, or ECS cluster
for an ordinary application update.

1. Test the change locally.
2. Rebuild the affected Docker image.
3. Give it a new immutable tag, for example `v5`.
4. Authenticate Docker to ECR and push to the existing repository.
5. Create a new task-definition revision using the new image URI.
6. Update the ECS service to the new revision.
7. Wait for the rolling deployment and health checks.
8. Test the URL and inspect CloudWatch logs.

## 19. Troubleshooting lessons

- **Expired AWS session:** sign in to AWS SSO again.
- **Docker credential-helper error:** repair the Docker login or use the tested
  temporary Docker configuration.
- **OpenSearch creation failure:** choose IPv4 if the subnets have no IPv6.
- **OpenSearch 403:** check both the IAM task-role policy and domain access
  policy; an unconditional Deny overrides Allow.
- **OpenSearch timeout:** increase the timeout and enable retries.
- **OpenSearch 429:** reduce bulk batch size and use retry/backoff.
- **Standalone task exit 1:** open its backend container and CloudWatch stream
  to find the actual exception.

## 20. Security and cost reminders

- Keep `.env`, credentials, passwords, and API keys out of Git.
- Keep RDS and OpenSearch private.
- Permit RDS and OpenSearch from the ECS security group, not the internet.
- Add HTTPS with an ACM certificate before production use.
- NAT Gateway, ALB, RDS, OpenSearch, and Fargate generate ongoing costs.
- Configure AWS Budgets and delete unneeded training resources, taking a
  database snapshot first if its data must be preserved.

## Presentation summary

> I containerised the Streamlit frontend and FastAPI backend and stored their
> images in Amazon ECR. I created a VPC with public and private subnets. A public
> Application Load Balancer sends requests to an ECS Fargate service running
> both containers privately. Amazon RDS provides PostgreSQL, while OpenSearch
> stores and searches vector embeddings for RAG. Secrets Manager protects
> credentials, IAM controls AWS permissions, security groups restrict network
> traffic, and CloudWatch stores the application logs.
