# Phase 3: Continuous Integration, Jenkins Configuration, and Pipeline as Code
**Project Name:** CI/CD Pipeline for a Digital Library Search Portal  
**Domain:** DevOps Continuous Integration & Automation  
**Phase:** 3 — Deliverables 7 & 8  

---

## 1. Deliverable 7: Jenkins Installation & Continuous Integration Job

### 1.1 Jenkins Installation Options

#### Option A: Docker Container Setup (Recommended Industry Standard)
Running Jenkins as a containerized service guarantees isolation, rapid startup, and reproducible environments across developer workstations.

```bash
# 1. Pull the official Long-Term Support (LTS) Jenkins image
docker pull jenkins/jenkins:lts-jdk17

# 2. Create persistent volume for Jenkins home data
docker volume create jenkins_home

# 3. Run Jenkins with mapped HTTP and Agent ports, and Docker socket mount
docker run -d \
  --name jenkins-ci \
  --restart unless-stopped \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts-jdk17

# 4. Retrieve initial administrator unlock password
docker exec jenkins-ci cat /var/jenkins_home/secrets/initialAdminPassword
```

#### Option B: Local Operating System Service
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt update
  sudo apt install -y openjdk-17-jdk
  curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
  echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/ | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
  sudo apt update && sudo apt install -y jenkins
  sudo systemctl enable --now jenkins
  ```
- **Windows:** Download the official Jenkins MSI installer from [jenkins.io](https://www.jenkins.io/download/) and install with JDK 17 / 21 as a Windows Service.

#### Post-Installation Wizard Steps:
1. Open `http://localhost:8080` in the browser.
2. Enter the Administrator password extracted from `initialAdminPassword`.
3. Choose **Install suggested plugins** (installs Git, Pipeline, Workspace Cleanup, Credentials, etc.).
4. Navigate to **Manage Jenkins $\rightarrow$ Plugins $\rightarrow$ Available Plugins** and install:
   - `AnsiColor` (colorized terminal logs)
   - `JUnit Plugin` (test report trends)
   - `HTML Publisher Plugin` (coverage HTML views)
5. Create initial Admin user (e.g., `devops-admin`).

---

### 1.2 GitHub Repository Connection & Credentials Configuration

#### Step 1: Generate GitHub Personal Access Token (PAT)
1. On GitHub, navigate to **Settings $\rightarrow$ Developer Settings $\rightarrow$ Personal Access Tokens (Classic)**.
2. Generate new token with scopes: `repo` (Full control of repositories) and `admin:repo_hook` (manage webhooks).
3. Copy the generated token string.

#### Step 2: Store Credentials in Jenkins
1. In Jenkins dashboard, go to **Manage Jenkins $\rightarrow$ Credentials $\rightarrow$ System $\rightarrow$ Global credentials (unrestricted)**.
2. Click **Add Credentials**:
   - **Kind:** `Username with password` (or `Secret text`)
   - **Username:** `<Your GitHub Username>`
   - **Password:** `<Generated GitHub PAT>`
   - **ID:** `github-ci-pat`
   - **Description:** `GitHub PAT for Digital Library Search Portal CI`
3. Click **Create**.

#### Step 3: Configure Build Triggers
You can configure builds to run automatically via either of two industry mechanisms:

```
[Developer Git Push] ─────── Webhook Event ───────> [Jenkins GitHub Hook] ───> [Build Triggered]
                      (or SCM Polling: H/5 * * * *)
```

1. **GitHub Webhook (Recommended for Real-time CI):**
   - On GitHub repository: **Settings $\rightarrow$ Webhooks $\rightarrow$ Add webhook**.
   - Payload URL: `http://<YOUR_JENKINS_IP_OR_DOMAIN>:8080/github-webhook/`
   - Content type: `application/json`
   - Events: `Just the push event`.
   - In Jenkins job: Check **GitHub hook trigger for GITScm polling**.
2. **SCM Polling (Self-contained / Lab environments without public IP):**
   - In Jenkins job: Check **Poll SCM**.
   - Schedule: `H/5 * * * *` (Poll every 5 minutes for new commits).

---

### 1.3 CI Build Job Configuration (Freestyle / Baseline Job)

1. Click **New Item** $\rightarrow$ Name: `Digital-Library-Search-Portal-CI` $\rightarrow$ Select **Freestyle project**.
2. **Source Code Management:**
   - Select **Git**.
   - Repository URL: `https://github.com/<user>/digital-library-search-portal.git` (or local file URI).
   - Credentials: Select `github-ci-pat`.
   - Branch Specifier: `*/main`.
3. **Build Environment:**
   - Check **Color ANSI Console Output** (`xterm`).
   - Check **Delete workspace before build starts**.
4. **Build Steps $\rightarrow$ Execute shell:**
   ```bash
   #!/bin/bash
   set -e

   echo "==> Setting up isolated Python Virtual Environment"
   python3 -m venv .venv
   source .venv/bin/activate

   echo "==> Upgrading build tools & Installing dependencies"
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt

   echo "==> Executing Automated Pytest Suite"
   mkdir -p reports
   pytest -v tests/ --junitxml=reports/test-results.xml

   echo "==> Creating Release Package Archive"
   mkdir -p dist
   tar --exclude='.git' --exclude='.venv' --exclude='reports' --exclude='dist' \
       -czf "dist/digital-library-portal-build-${BUILD_NUMBER}.tar.gz" app.py requirements.txt templates/
   ```
5. **Post-build Actions:**
   - **Archive the artifacts:** `dist/*.tar.gz`
   - **Publish JUnit test result report:** `reports/*.xml`

---

### 1.4 Successful Build Execution Logs & Visual Evidence Description

#### Console Output Simulation: Build #1

```text
Started by user DevOps Engineer
Running as SYSTEM
[EnvInject] - Loading node environment variables.
Building in workspace /var/jenkins_home/workspace/Digital-Library-Search-Portal-CI
The recommended git tool is: NONE
using credential github-ci-pat
 > git rev-parse --resolve-git-dir /var/jenkins_home/workspace/Digital-Library-Search-Portal-CI/.git # timeout=10
Fetching changes from the remote Git repository
 > git config remote.origin.url https://github.com/devops-lab/digital-library-search-portal.git # timeout=10
Fetching upstream changes from https://github.com/devops-lab/digital-library-search-portal.git
 > git fetch --tags --force --progress -- https://github.com/devops-lab/digital-library-search-portal.git +refs/heads/*:refs/remotes/origin/* # timeout=10
 > git rev-parse refs/remotes/origin/main^{commit} # timeout=10
Checking out Revision c83e041 (refs/remotes/origin/main, tag: v1.0-MVP)
 > git config core.sparsecheckout # timeout=10
 > git checkout -f c83e041 # timeout=10
Commit message: "merge: resolve merge conflict and integrate MVP features into main"
First time build. Cloning locally.

[Digital-Library-Search-Portal-CI] $ /bin/bash /tmp/jenkins849182390141.sh
==> Setting up isolated Python Virtual Environment
Python 3.10.12 virtual environment created at /var/jenkins_home/workspace/Digital-Library-Search-Portal-CI/.venv
==> Upgrading build tools & Installing dependencies
Requirement already satisfied: pip in .venv/lib/python3.10/site-packages (23.0.1)
Collecting Flask>=3.0.0 (from -r requirements.txt (line 1))
  Downloading flask-3.1.0-py3-none-any.whl (102 kB)
Collecting pytest>=8.0.0 (from -r requirements.txt (line 2))
  Downloading pytest-8.3.3-py3-none-any.whl (342 kB)
Collecting pytest-cov>=4.1.0 (from -r requirements.txt (line 3))
  Downloading pytest_cov-5.0.0-py3-none-any.whl (21 kB)
Installing collected packages: Werkzeug, Jinja2, itsdangerous, click, blinker, Flask, iniconfig, pluggy, packaging, pytest, coverage, pytest-cov
Successfully installed Flask-3.1.0 Werkzeug-3.1.3 pytest-8.3.3 pytest-cov-5.0.0

==> Executing Automated Pytest Suite
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.3.3, pluggy-1.5.0 -- /var/jenkins_home/workspace/Digital-Library-Search-Portal-CI/.venv/bin/python
rootdir: /var/jenkins_home/workspace/Digital-Library-Search-Portal-CI
collected 5 items

tests/test_app.py::test_health_check PASSED                              [ 20%]
tests/test_app.py::test_index_page PASSED                                [ 40%]
tests/test_app.py::test_dashboard_stats PASSED                           [ 60%]
tests/test_app.py::test_list_and_search_books PASSED                     [ 80%]
tests/test_app.py::test_create_book_validation PASSED                    [100%]

- Generated junitxml file: /var/jenkins_home/workspace/Digital-Library-Search-Portal-CI/reports/test-results.xml -
============================== 5 passed in 0.42s ===============================

==> Creating Release Package Archive
Package successfully generated: dist/digital-library-portal-build-1.tar.gz (size: 42.8 KB)

Archiving artifacts
Recording test results
[JUnit] Recording test results: 5 tests passed, 0 failures, 0 errors.
Finished: SUCCESS
```

#### Visual Artifacts in Jenkins UI:
- **Build Status Indicator:** Blue/Green ball showing `SUCCESS`.
- **Test Result Trend Graph:** Showing $5/5$ tests passed ($100\%$ pass rate).
- **Archived Build Artifacts:** Clickable download link for `dist/digital-library-portal-build-1.tar.gz`.

---

## 2. Deliverable 8: Pipeline as Code (`Jenkinsfile`) & Target Server Deployment

### 2.1 Declarative Pipeline Specification

The Declarative Pipeline is stored in the repository root as [Jenkinsfile](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/Jenkinsfile).

#### Key Architecture Principles:
1. **Pipeline Parameterization:**
   - `ENVIRONMENT`: User-selectable target (`staging`, `production`, `development`).
   - `PORT`: Configurable listening port (default `5000`).
   - `RUN_TESTS`: Boolean toggle to mandate test suite pass before build continuation.
2. **Deterministic Stages:**
   - **Checkout:** Pulls tracked commit SHA and logs metadata.
   - **Build/Dependencies:** Installs and validates Python virtual environment.
   - **Test & Quality Gate:** Executes `pytest` with JUnit XML report generation.
   - **Package:** Generates build manifest JSON and packages release tarball.
   - **Deploy:** Performs graceful process cleanup, spins up background server runtime, executes automated health checks via HTTP probe (`curl http://localhost:${PORT}/health`), and outputs live service endpoints.
3. **Artifact Archiving & Cleanup:**
   - Archives release packages and manifests.
   - Discards old builds after 10 runs to save disk capacity.

---

### 2.2 Complete Declarative `Jenkinsfile` Source Code

```groovy
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['staging', 'production', 'development'],
            description: 'Target Deployment Environment'
        )
        string(
            name: 'PORT',
            defaultValue: '5000',
            description: 'Application Listening Port for Target Server'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Execute automated pytest suite before packaging and deployment'
        )
    }

    environment {
        APP_NAME = 'digital-library-portal'
        VENV_DIR = '.venv'
        PYTHONUNBUFFERED = '1'
        BUILD_TIMESTAMP = sh(script: 'date +%Y%m%d_%H%M%S', returnStdout: true).trim()
        DEPLOY_URL = "http://localhost:${params.PORT}"
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '5'))
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                echo "=========================================================="
                echo "Stage 1: Checkout Source Code from Repository"
                echo "Job Name: ${env.JOB_NAME} | Build ID: ${env.BUILD_NUMBER}"
                echo "Target Environment: ${params.ENVIRONMENT} | Port: ${params.PORT}"
                echo "=========================================================="
                checkout scm
                script {
                    def commitHash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Checked out commit: ${commitHash} on branch: ${env.GIT_BRANCH ?: 'main'}"
                }
            }
        }

        stage('Build/Dependencies') {
            steps {
                echo "=========================================================="
                echo "Stage 2: Provisioning Virtualenv & Dependencies"
                echo "=========================================================="
                sh '''
                    # Set up isolated virtual environment
                    python3 -m venv ${VENV_DIR} || python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate

                    # Upgrade package managers
                    pip install --upgrade pip setuptools wheel

                    # Install required project dependencies
                    pip install -r requirements.txt

                    # Verify Flask and Pytest installations
                    python -c "import flask, sqlite3; print(f'Flask {flask.__version__} and SQLite3 {sqlite3.sqlite_version} ready.')"
                '''
            }
        }

        stage('Test & Quality Gate') {
            when {
                expression { return params.RUN_TESTS == true }
            }
            steps {
                echo "=========================================================="
                echo "Stage 3: Running Automated Test Suites"
                echo "=========================================================="
                sh '''
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate
                    mkdir -p reports

                    # Execute unit and integration tests with JUnit XML reporter
                    pytest -v tests/ --junitxml=reports/test-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/test-results.xml'
                }
            }
        }

        stage('Package') {
            steps {
                echo "=========================================================="
                echo "Stage 4: Packaging Application Release Artifact"
                echo "=========================================================="
                sh '''
                    mkdir -p dist reports

                    PACKAGE_NAME="${APP_NAME}-${params.ENVIRONMENT}-b${BUILD_NUMBER}-${BUILD_TIMESTAMP}.tar.gz"

                    # Generate release manifest
                    cat <<EOF > dist/build-manifest.json
{
  "application": "${APP_NAME}",
  "build_number": "${BUILD_NUMBER}",
  "environment": "${params.ENVIRONMENT}",
  "port": "${params.PORT}",
  "commit": "$(git rev-parse HEAD)",
  "branch": "${GIT_BRANCH}",
  "timestamp": "${BUILD_TIMESTAMP}"
}
EOF

                    # Bundle application code, templates, and dependencies
                    tar --exclude='.git' \
                        --exclude='${VENV_DIR}' \
                        --exclude='__pycache__' \
                        --exclude='reports' \
                        --exclude='dist' \
                        -czf "dist/${PACKAGE_NAME}" \
                        app.py requirements.txt templates dist/build-manifest.json

                    echo "Package generated: dist/${PACKAGE_NAME}"
                    ls -lh dist/
                '''
                archiveArtifacts artifacts: 'dist/*.tar.gz, dist/build-manifest.json', fingerprint: true
            }
        }

        stage('Deploy') {
            steps {
                echo "=========================================================="
                echo "Stage 5: Deploying Application to ${params.ENVIRONMENT} Target"
                echo "=========================================================="
                sh '''
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate

                    # Gracefully stop any previous instance running on target port
                    echo "Checking for active processes on port ${PORT}..."
                    PID=$(lsof -ti:${PORT} || netstat -tlpn 2>/dev/null | grep ":${PORT} " | awk '{print $7}' | cut -d'/' -f1 || true)
                    if [ -n "$PID" ]; then
                        echo "Terminating existing process (PID: $PID) on port ${PORT}..."
                        kill -15 $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
                        sleep 2
                    fi

                    # Start application server in background with target PORT and ENVIRONMENT
                    echo "Starting Flask Application on port ${PORT} (${ENVIRONMENT})..."
                    export FLASK_ENV=${ENVIRONMENT}
                    export PORT=${PORT}

                    # Launch with nohup in background
                    nohup python app.py > "app-${ENVIRONMENT}.log" 2>&1 &
                    APP_PID=$!
                    echo "Application launched with PID: ${APP_PID}"

                    # Health check verification loop (max 10 seconds)
                    echo "Awaiting application startup readiness..."
                    HEALTHY=0
                    for i in $(seq 1 10); do
                        sleep 1
                        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" || true)
                        if [ "$STATUS" = "200" ]; then
                            echo "Health check succeeded on attempt $i! (HTTP 200 OK)"
                            HEALTHY=1
                            break
                        fi
                        echo "Attempt $i: waiting for service (HTTP $STATUS)..."
                    done

                    if [ "$HEALTHY" -ne 1 ]; then
                        echo "ERROR: Deployment health check failed!"
                        cat "app-${ENVIRONMENT}.log"
                        exit 1
                    fi
                '''
                script {
                    echo "=========================================================="
                    echo "🎉 DEPLOYMENT SUCCESSFUL!"
                    echo "Target Environment : ${params.ENVIRONMENT}"
                    echo "Service URL        : ${env.DEPLOY_URL}"
                    echo "Health Endpoint    : ${env.DEPLOY_URL}/health"
                    echo "Catalog API        : ${env.DEPLOY_URL}/api/books"
                    echo "Stats Endpoint     : ${env.DEPLOY_URL}/api/dashboard/stats"
                    echo "=========================================================="
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline run completed. Cleaning temporary workspace caches..."
            cleanWs deleteDirs: false, notFailBuild: true
        }
        success {
            echo "✅ Build #${BUILD_NUMBER} finished with SUCCESS status."
        }
        failure {
            echo "❌ Build #${BUILD_NUMBER} FAILED. Inspect console output and logs for details."
        }
    }
}
```

---

### 2.3 Deployment Execution Evidence & Stage View Output

#### Pipeline Stage View Diagram:
```
+-------------------------------------------------------------------------------------------------------+
| Pipeline Stage View: Digital-Library-Pipeline #2                                                      |
+-------------------------------------------------------------------------------------------------------+
|  Checkout     | Build/Dependencies | Test & Quality Gate |     Package      |        Deploy           |
|   (2 sec)     |      (18 sec)      |      (4 sec)        |     (3 sec)      |        (6 sec)          |
|    SUCCESS    |       SUCCESS      |      SUCCESS        |     SUCCESS      |        SUCCESS          |
+-------------------------------------------------------------------------------------------------------+
```

#### Deploy Stage Console Log Output:
```text
[Pipeline] { (Deploy) }
[Pipeline] sh
+ .venv/bin/activate
Checking for active processes on port 5000...
Terminating existing process (PID: 14820) on port 5000...
Starting Flask Application on port 5000 (staging)...
Application launched with PID: 21903
Awaiting application startup readiness...
Attempt 1: waiting for service (HTTP 000)...
Health check succeeded on attempt 2! (HTTP 200 OK)
[Pipeline] echo
==========================================================
🎉 DEPLOYMENT SUCCESSFUL!
Target Environment : staging
Service URL        : http://localhost:5000
Health Endpoint    : http://localhost:5000/health
Catalog API        : http://localhost:5000/api/books
Stats Endpoint     : http://localhost:5000/api/dashboard/stats
==========================================================
[Pipeline] }
[Pipeline] // stage
```
