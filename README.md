# TeamSPAM Data Engineering Project

**Team SPAM** — Sarah, Pawan, Ammad, Maryam 
*Data Engineering Bootcamp — Final Project*

---

## What This Project Does

This project builds an **automated data pipeline** for a coffee shop chain with two branches (Leeds and Chesterfield). Raw sales data — every coffee ordered, the price, how it was paid for — is automatically collected, cleaned, and stored in a database so the business can query it and visualise trends on a dashboard.

The pipeline exists in two forms:
- **Local** — runs on your own laptop for development and testing
- **Cloud (AWS)** — runs automatically on Amazon Web Services whenever new data arrives

---

## Table of Contents

1. [How the Data Flows](#how-the-data-flows)
2. [Project Structure](#project-structure)
3. [Local Pipeline](#local-pipeline)
4. [Data Sources](#data-sources)
5. [Cloud Pipeline (AWS)](#cloud-pipeline-aws)
6. [Infrastructure — What Runs in the Cloud](#infrastructure--what-runs-in-the-cloud)
7. [Deployment — How We Push Everything to AWS](#deployment--how-we-push-everything-to-aws)
8. [Visualisation — Grafana Dashboard](#visualisation--grafana-dashboard)
9. [Database Schema](#database-schema)
10. [Security & Privacy](#security--privacy)
11. [Testing](#testing)
12. [How to Run Locally](#how-to-run-locally)
13. [How to Deploy to AWS](#how-to-deploy-to-aws)

---

## How the Data Flows

There are two separate journeys the data takes — one for local development and one for the live cloud system.

### Local (Development)

```
CSV files on disk
    │
    ▼
Extract  →  Read the CSV files into memory
    │
    ▼
Transform  →  Clean & reshape the data
               (parse drink names, hash customer names, split items)
    │
    ▼
Load  →  Insert records into a local PostgreSQL database
    │
    ▼
Adminer (web UI)  →  Browse the database at http://localhost:8080 or your "IP Address":8080
```

### Cloud (Production)

```
CSV file uploaded to an S3 bucket ("raw data" bucket)
    │
    ▼  (S3 automatically triggers the next step)
AWS Lambda Function  →  Serverless code that wakes up, processes the file, then goes back to sleep
    │
    ▼
Transform  →  Same cleaning logic as local
    │
    ▼
Amazon Redshift  →  Cloud data warehouse
    │
    ▼
Grafana Dashboard  →  Charts & graphs built on top of the Redshift data
```

---

## Project Structure

```
TeamSPAM-DataEng-Project/
│
├── pipeline/                   Local ETL pipeline (Extract, Transform, Load)
│   ├── etl/
│   │   ├── run_pipeline.py     Main entry point — runs the whole local pipeline
│   │   ├── transform.py        Cleans and reshapes the raw data
│   │   └── load.py             Inserts cleaned data into PostgreSQL
│   └── ingestion/
│       ├── extract.py          Reads the CSV files
│       └── sources/            Raw CSV data files (Leeds & Chesterfield)
│
├── deployment/                 Everything needed to run on AWS
│   ├── src/
│   │   ├── etl_lambda.py       The Lambda function handler (cloud entry point)
│   │   ├── transform.py        Cloud version of the transform logic
│   │   └── utils/
│   │       ├── s3_utils.py     Downloads files from S3
│   │       ├── db_utils.py     Connects to Redshift, fetches credentials from SSM
│   │       └── sql_utils.py    Creates tables & inserts data in Redshift
│   ├── templates/
│   │   ├── etl-stack.yml               Main cloud infrastructure definition
│   │   └── deployment-bucket-stack.yml S3 bucket for deployment artefacts
│   ├── deploy.sh               Script to deploy everything to AWS
│   ├── teardown.sh             Script to tear down & clean up AWS resources
│   └── userdata                Startup script that installs Grafana on the EC2 server
│
├── warehouse/                  Database schema definitions
│   └── schema/
│       ├── postgrestable.py    Creates the tables in PostgreSQL
│       └── *.sql               SQL table definitions
│
├── tests/                      Automated tests
│   ├── local/                  Tests for the local pipeline
│   ├── deployment/             Tests for the AWS pipeline (using mocks)
│   └── scripts/                Tests for the deployment bash scripts
│
├── podman-compose.yml          Alternative local DB setup — not used (pre-existing Docker containers used instead)
├── requirements.txt            Python package dependencies
└── .env                        Local database credentials (not committed to git)
```

---

## Local Pipeline

The local pipeline is used during **development** — it lets the team test changes without touching any AWS services.

### How it works

**1. Extract** (`pipeline/ingestion/extract.py`)
Opens the CSV files and reads each row into memory as a list of records.

**2. Transform** (`pipeline/etl/transform.py`)
This is where the raw, messy data gets cleaned:
- Each row in the CSV has an `items` column like `"Large Chai latte - 2.60, Regular Latte - 2.00"` — the transform step splits this into individual drink items
- The customer name is replaced with an anonymous ID (see [Security & Privacy](#security--privacy))
- Duplicate items on the same order are collapsed into a quantity (e.g. 3x the same coffee = 1 row with `quantity = 3`)
- Date and time columns are merged into a single timestamp

**3. Load** (`pipeline/etl/load.py`)
Inserts all the cleaned records into a local PostgreSQL database, using `ON CONFLICT DO NOTHING` so running the pipeline twice doesn't create duplicate rows.

**Run the local pipeline:**
```bash
python -m pipeline.etl.run_pipeline
```

### Local Database (PostgreSQL + Adminer)

For the local database we used **existing Docker containers** that the team had already set up from earlier in the bootcamp — a PostgreSQL database and Adminer (a browser-based database viewer). These were already running locally, so we simply connected to them rather than spinning anything new up.

> **Note:** A `podman-compose.yml` file exists in the repository as a fallback option (Podman is an alternative to Docker), but the team never needed to use it — the pre-existing Docker containers worked throughout.

- **PostgreSQL** is available on port `5432`
- **Adminer** (database browser UI) is available at [http://localhost:8080](http://localhost:8080)

---

## Data Sources

The raw data comes from two coffee shop branches. Each CSV file contains one row per transaction with the following columns:

| Column | Example | Notes |
|---|---|---|
| `date` | `25/08/2021` | Date of the sale |
| `time` | `09:00` | Time of the sale |
| `location` | `Leeds` | Branch name |
| `customer_name` | `Jane Smith` | Hashed before storage |
| `items_total` | `Large Latte - 2.50` | Comma-separated drink list |
| `amount_paid` | `5.00` | Total charged |
| `payment_method` | `card` | `cash` or `card` |
| `card_number` | `1234...` | Dropped immediately, never stored |

**Source files:**

| File | Size | Description |
|---|---|---|
| `pipeline/ingestion/sources/leedsdata.csv` | 54 KB | Leeds branch sales |
| `pipeline/ingestion/sources/chesterfielddata.csv` | 47 KB | Chesterfield branch sales |

---

## Cloud Pipeline (AWS)

The cloud pipeline is the **production system** — it runs automatically without anyone needing to press a button.

### Step-by-step

**Step 1 — Upload a CSV to S3**
A CSV file of sales data is uploaded to a dedicated Amazon S3 bucket (think of S3 as a cloud file storage system). This bucket is named `<teamname>-raw-data` and is locked down so only authorised accounts can write to it.

**Step 2 — S3 triggers Lambda automatically**
The moment a file lands in the S3 bucket, Amazon automatically calls our Lambda function. Lambda is "serverless" — there is no permanent server running; the code only runs when it is needed, and you only pay for the seconds it is active.

**Step 3 — Lambda downloads and transforms the file**
The Lambda function (`deployment/src/etl_lambda.py`):
1. Reads the file name and bucket from the trigger event
2. Downloads the CSV file from S3
3. Runs the same Extract → Transform logic as the local pipeline
4. Fetches database credentials securely from AWS SSM Parameter Store (a secrets vault)
5. Connects to Redshift and loads the clean data

**Step 4 — Data lands in Redshift**
Amazon Redshift is a cloud data warehouse — a database built for running analytical queries across millions of rows quickly. The four tables (`sizes`, `flavours`, `orders`, `order_items`) are created automatically if they don't yet exist.

---

## Infrastructure — What Runs in the Cloud

All the cloud infrastructure is defined as code using **AWS CloudFormation** — meaning the entire setup (servers, buckets, functions, permissions) is described in YAML files and can be created or destroyed with a single command.

### Resources defined in `deployment/templates/etl-stack.yml`

| Resource | What it is | Purpose |
|---|---|---|
| **S3 Raw Data Bucket** | Cloud file storage | Receives the uploaded CSV files; triggers Lambda on upload |
| **Lambda Function** | Serverless compute | Wakes up, processes the CSV, loads data to Redshift, then stops |
| **EC2 Instance** | A virtual machine (server) | Hosts the Grafana dashboard (t2.micro — the smallest/cheapest size) |
| **IAM Roles & Permissions** | Access control | Grants Lambda permission to read from S3 and SSM; restricts everything else |
| **VPC Placement** | Network | Lambda is placed inside the same private network as Redshift for secure communication |

### Resources defined in `deployment/templates/deployment-bucket-stack.yml`

| Resource | What it is | Purpose |
|---|---|---|
| **S3 Deployment Bucket** | Cloud file storage | Holds the zipped Lambda code and packaged CloudFormation templates during deployment |

### CloudFormation Parameters

When deploying, you provide these values:

| Parameter | Example | Description |
|---|---|---|
| `YourName` | `spam` | Used as a prefix for all resource names |
| `NetworkStackName` | `de-nat4-network` | Name of the existing VPC/network stack |
| `EC2InstanceIngressIp` | `12.34.56.78/32` | Your laptop's IP — only this IP can access Grafana |
| `EC2UserData` | *(base64 script)* | The startup script for the EC2 server |

---

## Deployment — How We Push Everything to AWS

The team worked on a **CentOS virtual machine (VM)**. From there, we used the **AWS CLI** to authenticate with our AWS accounts and run all deployments — nothing was deployed directly from a personal laptop.

### The full deployment process

**1. Copy files to the VM**
All project files (Python scripts, CloudFormation YAML templates, `deploy.sh`, `userdata`) were copied onto the CentOS VM.

**2. Log in to AWS from the VM**
```bash
aws configure --profile data-course 
```
This stores an AWS Access Key, Secret Key, and region on the VM so subsequent commands authenticate automatically.

**3. Run the deployment script**
```bash
bash deploy.sh data-course spam <your-ip-address>  (data-course is the aws profile name different for each teamate)
```

The `deploy.sh` script (`deployment/deploy.sh`) does the following automatically:

| Step | What happens |
|---|---|
| **1** | Deploys the deployment bucket CloudFormation stack (creates the S3 bucket for artefacts) |
| **2** | Runs `pip install` to download Python dependencies into the `src/` folder (using Linux-compatible wheels so they work in Lambda) |
| **3** | Runs `aws cloudformation package` — zips up all the Lambda code and uploads it to the deployment S3 bucket |
| **4** | Deploys the main ETL CloudFormation stack — creates Lambda, the raw data S3 bucket, and the EC2 instance |

### Teardown

When the project is finished (to avoid AWS charges), the teardown script removes all resources:
```bash
bash teardown.sh
```

This empties the S3 buckets (they must be empty before deletion), then deletes both CloudFormation stacks and waits for confirmation that everything is gone.

---

## Visualisation — Grafana Dashboard

**Grafana** is an open-source tool for building charts and dashboards. In this project, Grafana is installed on the EC2 virtual machine and connected to Redshift so the business can visualise the sales data.

### How Grafana gets installed

The EC2 instance runs a startup script (`deployment/userdata`) the very first time it boots. This script:
1. Installs Docker on the server
2. Pulls the official Grafana Docker image
3. Launches Grafana as a container, accessible on port 80 (standard web traffic)

Once running, Grafana is accessible at the EC2 instance's public IP address in a browser. Only the IP address specified at deployment time can reach it (a firewall rule blocks everyone else).

### What you can visualise

By connecting Grafana to Redshift, the team can build dashboards showing:
- Sales volume by branch (Leeds vs Chesterfield)
- Most popular drinks and sizes
- Revenue by payment method (cash vs card)
- Sales trends over time (by hour, day, week)

---

## Database Schema

Data is stored across four tables in both the local PostgreSQL database and the cloud Redshift data warehouse. The structure is identical in both.

### `sizes` — lookup table

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Unique identifier |
| `name` | TEXT | `"Large"` or `"Regular"` |

### `flavours` — lookup table

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Unique identifier |
| `name` | TEXT | e.g. `"Hazelnut"`, `"Caramel"`, `"Vanilla"` |

### `orders` — one row per customer transaction

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Unique order identifier |
| `branch_name` | TEXT | `"Leeds"` or `"Chesterfield"` |
| `customer_id` | UUID | Anonymised customer reference (hashed) |
| `order_time` | TIMESTAMP | Date and time of purchase |
| `payment_method` | TEXT | `"cash"` or `"card"` |
| `total_amount` | DECIMAL | Total amount paid |

### `order_items` — one row per drink on an order

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Unique line-item identifier |
| `order_id` | UUID | Links back to the `orders` table |
| `item_name` | TEXT | Full drink name e.g. `"Large Chai Latte"` |
| `size_id` | UUID | Links to the `sizes` table |
| `flavour_id` | UUID | Links to the `flavours` table (null if no flavour) |
| `price` | DECIMAL | Price of a single unit |
| `quantity` | INTEGER | How many of this drink were ordered |

---

## Security & Privacy

### Customer Name Hashing (GDPR)
Customer names from the CSV are **never stored** in the database. Instead, the pipeline applies a SHA-256 cryptographic hash to the name, producing a consistent anonymous ID. The same customer always gets the same ID, so repeat visits can be tracked, but the actual name cannot be recovered from the database.

### Card Numbers
Card numbers present in the raw CSV are **dropped immediately** during the transform step and never written to any database or log.

### S3 Bucket Security
- Public access is blocked on all S3 buckets
- All data in transit must use HTTPS/SSL (HTTP requests are rejected)
- Server-side encryption is enabled

### Credentials Management
- Local development credentials live in `.env` (excluded from git via `.gitignore`)
- Production credentials (Redshift host, user, password) are stored in **AWS SSM Parameter Store** — a secure secrets vault — and fetched by Lambda at runtime. They are never hard-coded.

---

## Testing

The project has a suite of automated tests that run before any code is merged, catching bugs early.

```
tests/
├── local/              Tests for the local pipeline
│   ├── test_extract.py         Checks CSV files are read correctly
│   ├── test_transform.py       Checks item parsing, hashing, deduplication
│   └── test_data_quality.py    Runs the full pipeline against real CSV data
│
├── deployment/         Tests for the AWS Lambda pipeline (AWS services are mocked)
│   ├── test_transform.py       Cloud transform logic
│   ├── test_s3_utils.py        S3 event parsing & file download
│   └── test_sql_utils.py       Table creation & data insertion
│
└── scripts/            Tests for the deployment bash scripts
    └── test_bash_scripts.py    Checks scripts have correct arguments & safe flags
```

**Run all tests:**
```bash
pip install -r tests/requirements-test.txt
pytest tests/
```

---

## How to Run Locally

### Prerequisites
- Python 3.10+
- Docker (with PostgreSQL and Adminer containers already running from a previous setup)

### Steps

**1. Clone the repository**
```bash
git clone <repo-url>
cd TeamSPAM-DataEng-Project
```

**2. Install Python dependencies**
```bash
pip install -r requirements.txt
```

**3. Create a `.env` file** in the project root:
```
POSTGRES_HOST=localhost
POSTGRES_DB=teamspam
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_PORT=5432
```

**4. Ensure your Docker containers are running**
The team used pre-existing Docker containers with PostgreSQL and Adminer already configured. Make sure those containers are up and running before proceeding. A `podman-compose.yml` is included in the repo as a fallback if you need to spin up fresh containers, but it was not used during the project.

**5. Run the pipeline**
```bash
python -m pipeline.etl.run_pipeline
```

**6. View the data**
Open [http://localhost:8080](http://localhost:8080) in a browser and log in to Adminer with the credentials from your `.env` file.

---

## How to Deploy to AWS

### Prerequisites
- Access to a CentOS VM with AWS CLI installed
- AWS credentials (Access Key ID + Secret Access Key) for the `data-course` profile
- The project files copied onto the VM

### Steps

**1. Log in to AWS on the VM**
```bash
aws configure --profile "your_name/profile-name"
```

**2. Run the deployment script**
```bash
cd deployment
bash deploy.sh "your_name/profile-name" spam <your-public-ip>
```
Replace `spam` with your chosen team name and `<your-public-ip>` with your current IP address (used to restrict Grafana access).

**3. Upload a CSV to trigger the pipeline**
Once deployed, upload a CSV file to the S3 raw data bucket (`spam-raw-data`). Lambda will automatically process it within seconds.

**4. Open Grafana**
Find the EC2 instance's public IP in the AWS console and open it in a browser. Default Grafana credentials are `admin` / `admin` (change these immediately).

### Tear everything down
```bash
bash teardown.sh
```
This removes all AWS resources and stops any ongoing charges.

---
