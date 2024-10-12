# **EZAI User Manual**

## **Table of Contents**
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
5. [Operation](#operation)
   - [Website URL](#website-url)
   - [Registering Models](#registering-models)
   - [Deploying Models](#deploying-models)
   - [Managing Jobs](#managing-jobs)
7. [Troubleshooting](#troubleshooting)
8. [Security](#security)
9. [Support](#support)

---

## **Introduction**
**EZAI** is a tool designed to manage and deploy machine learning models with ease. It uses Celery workers, SageMaker, and a structured relational database to facilitate efficient model management, allowing users to register and deploy models, track job statuses, and manage model endpoints.

## **System Requirements**
- Python 3.9 or higher
- Redis and RabbitMQ for Celery
- AWS SageMaker with appropriate permissions
- PostgreSQL
- Docker (for containerization)

## **Installation**

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/fishpain/ezai.git
   cd ezai
   ```

2. **Environment Configuration:**
   - Copy the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Update `.env` with your environment-specific variables, such as `DATABASE_URI`, `RABBITMQ_URI`, and AWS credentials for SageMaker.
   > Note: Email 2302705 at sit.singaporetech.edu.sg for env file.


3. **Build Application, RabbitMQ, Database through:**
   ```bash
   cd hf_api/docker && docker compose -f docker-compose-local-x86.yml up -d
   ```
   > Note: Above command is to build for X86 platform, aka windows.
   > To build on ARM achitechture, you have to edit the `requirements.txt` file and choose `libs/h5py-3.9.0-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl` instead.
   > Then build the `docker-compose-local-arm.yml` instead.


## **Operation**

### **Website URL**
- Website URL available at `localhost:5051/`
- Swagger API Available at `localhost:5051/v1/docs/`
> Application supports Chrome and Safari. Not IE.

### **Logging In**
- Users authenticate via a token-based system. Provide a valid token for operations that require user-specific access.
> Note: Please enable cookie and javascript on your browser.

### **Registering Models**
- Call the `/register` endpoint or use the `register_model_worker` task to register a new model with SageMaker. This will:
  - Create an entry in the `MLModel` table.
  - Register the model version in `ModelRegistryModel`.
  - Deploy the model to an endpoint on SageMaker.

### **Deploying Models**
- Deploy registered models to SageMaker by triggering the `register_model_worker` task, which handles the creation and deployment to the appropriate endpoint.

### **Managing Jobs**
- Monitor job statuses via `JobsModel`. The system automatically updates job statuses as tasks progress.
- View contributions and model statistics via the `get_model_run_counts_with_details` function.

## **Troubleshooting**

- **Database Connection Issues:**
  Ensure that `DATABASE_URI` is correctly configured and that your database server is running.

- **Celery Worker Not Responding:**
  - Verify that RabbitMQ and Redis are accessible.
  - Check the worker logs for specific errors.

- **AWS SageMaker Permissions:**
  - Ensure your AWS role has sufficient permissions for deploying and managing models in SageMaker.

- **401 Unauthorized Error:**
  - Ensure you provide a valid JWT token in the `Authorization` header.

## **Security**

- **Database Access:**
  - Ensure that the worker user has restricted access to sensitive tables.
  - Use separate database users for different parts of the system for fine-grained access control.

- **Token Management:**
  - Store the `SECRET_KEY` securely.
  - Rotate the JWT secret regularly for enhanced security.

## **Support**

For further support, please contact the development team or refer to the official documentation on GitHub at [GitHub Repository](https://github.com/fishpain/ezai).
