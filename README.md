# **EZAI User Manual**

## **Table of Contents**
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Operation](#operation)
   - [Logging In](#logging-in)
   - [Registering Models](#registering-models)
   - [Deploying Models](#deploying-models)
   - [Managing Jobs](#managing-jobs)
6. [Troubleshooting](#troubleshooting)
7. [Security](#security)
8. [Support](#support)

---

## **Introduction**
**EZAI** is a tool designed to manage and deploy machine learning models with ease. It uses Celery workers, SageMaker, and a structured relational database to facilitate efficient model management, allowing users to register and deploy models, track job statuses, and manage model endpoints.

## **System Requirements**
- Python 3.8 or higher
- Redis and RabbitMQ for Celery
- AWS SageMaker with appropriate permissions
- PostgreSQL or MySQL database
- Docker (optional, for containerization)

## **Installation**

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-repo/HF-Clone.git
   cd HF-Clone
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration:**
   - Copy the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Update `.env` with your environment-specific variables, such as `DATABASE_URI`, `RABBITMQ_URI`, and AWS credentials for SageMaker.

4. **Database Setup:**
   - Set up the database schema by running:
     ```bash
     python -c "from app.models.models import Base, engine; Base.metadata.create_all(engine)"
     ```

5. **Start Redis and RabbitMQ Services:**
   - If you are using Docker, you can start these with:
     ```bash
     docker-compose up -d
     ```

## **Configuration**

1. **Environment Variables:**
   - Open `.env` and configure:
     - `DATABASE_URI`: The connection string for your database.
     - `RABBITMQ_URI`: The URI for your RabbitMQ instance.
     - `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`: Your AWS credentials.
     - `SECRET_KEY`: Your application's secret key for JWT.

2. **Celery Worker Configuration:**
   - Start a Celery worker using the configured broker:
     ```bash
     celery -A app.tasks worker --loglevel=info
     ```

## **Operation**

### **Logging In**
- Users authenticate via a token-based system. Provide a valid token for operations that require user-specific access.

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

For further support, please contact the development team or refer to the official documentation on GitHub at [GitHub Repository](https://github.com/your-repo/HF-Clone).
