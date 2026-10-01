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
            name: 'RUN_UNIT_TESTS',
            defaultValue: true,
            description: 'Execute unit and integration test suite'
        )
        booleanParam(
            name: 'RUN_UI_TESTS',
            defaultValue: true,
            description: 'Execute automated Headless Selenium UI regression test suite'
        )
    }

    environment {
        APP_NAME = 'digital-library-portal'
        VENV_DIR = '.venv'
        PYTHONUNBUFFERED = '1'
        BASE_URL = "http://127.0.0.1:${params.PORT}"
        BUILD_TIMESTAMP = sh(script: 'date +%Y%m%d_%H%M%S', returnStdout: true).trim()
        DEPLOY_URL = "http://localhost:${params.PORT}"
    }

    options {
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '15', artifactNumToKeepStr: '10'))
        ansiColor('xterm')
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                echo "=========================================================="
                echo "Stage 1: Checkout Source Code"
                echo "Job: ${env.JOB_NAME} | Build: #${env.BUILD_NUMBER}"
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
                echo "Stage 2: Setup Environment & Dependencies"
                echo "=========================================================="
                sh '''
                    python3 -m venv ${VENV_DIR} || python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate

                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt

                    python -c "import flask, selenium; print(f'Flask {flask.__version__} & Selenium {selenium.__version__} verified.')"
                '''
            }
        }

        stage('Unit Testing') {
            when {
                expression { return params.RUN_UNIT_TESTS == true }
            }
            steps {
                echo "=========================================================="
                echo "Stage 3: Running Automated Unit & Integration Tests"
                echo "=========================================================="
                sh '''
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate
                    mkdir -p reports
                    pytest -v tests/test_app.py --junitxml=reports/unit-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/unit-results.xml'
                }
            }
        }

        stage('Continuous Testing (Selenium E2E)') {
            when {
                expression { return params.RUN_UI_TESTS == true }
            }
            steps {
                echo "=========================================================="
                echo "Stage 4: Automated End-to-End Headless Selenium Testing"
                echo "=========================================================="
                sh '''
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate
                    mkdir -p reports/screenshots

                    # Ensure Chrome/Chromium is accessible in headless mode
                    export BASE_URL="http://127.0.0.1:${PORT}"
                    
                    # Run Selenium UI test suite. Non-zero exit code will halt the pipeline immediately!
                    pytest -v tests/test_ui.py --junitxml=reports/selenium-results.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/selenium-results.xml'
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'reports/screenshots/*.png'
                }
                failure {
                    echo "⚠️ Continuous Testing FAILED! Failure screenshots and logs preserved in build artifacts."
                    echo "Halting pipeline: deployment stage skipped due to test regression."
                }
            }
        }

        stage('Package') {
            steps {
                echo "=========================================================="
                echo "Stage 5: Packaging Verified Release Artifact"
                echo "=========================================================="
                sh '''
                    mkdir -p dist reports

                    PACKAGE_NAME="${APP_NAME}-${params.ENVIRONMENT}-b${BUILD_NUMBER}-${BUILD_TIMESTAMP}.tar.gz"

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
                echo "Stage 6: Deploying Verified Build to ${params.ENVIRONMENT}"
                echo "=========================================================="
                sh '''
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate

                    echo "Terminating existing process on port ${PORT}..."
                    PID=$(lsof -ti:${PORT} || netstat -tlpn 2>/dev/null | grep ":${PORT} " | awk '{print $7}' | cut -d'/' -f1 || true)
                    if [ -n "$PID" ]; then
                        kill -15 $PID 2>/dev/null || kill -9 $PID 2>/dev/null || true
                        sleep 2
                    fi

                    echo "Launching Flask Application on port ${PORT} (${ENVIRONMENT})..."
                    export FLASK_ENV=${ENVIRONMENT}
                    export PORT=${PORT}

                    nohup python app.py > "app-${ENVIRONMENT}.log" 2>&1 &
                    APP_PID=$!
                    echo "Application started with PID: ${APP_PID}"

                    echo "Awaiting application readiness..."
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
            echo "Pipeline finished. Cleaning temporary caches..."
            cleanWs deleteDirs: false, notFailBuild: true
        }
        success {
            echo "✅ Pipeline Build #${BUILD_NUMBER} completed with all quality gates passed."
        }
        failure {
            echo "❌ Pipeline Build #${BUILD_NUMBER} failed quality gates. Deployment halted."
        }
    }
}
