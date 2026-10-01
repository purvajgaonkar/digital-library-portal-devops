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
        DEPLOY_DIR = "/opt/${APP_NAME}/${params.ENVIRONMENT}"
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

                    # Launch with nohup or background process
                    nohup python app.py > "app-${ENVIRONMENT}.log" 2>&1 &
                    APP_PID=$!
                    echo "Application launched with PID: ${APP_PID}"

                    # Health check verification loop (max 15 seconds)
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
