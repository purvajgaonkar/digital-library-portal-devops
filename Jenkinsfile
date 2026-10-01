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
        string(
            name: 'DOCKER_IMAGE_NAME',
            defaultValue: 'digital-library-portal',
            description: 'Docker image repository name'
        )
        string(
            name: 'DOCKER_REGISTRY_USER',
            defaultValue: 'devopslab',
            description: 'Docker Hub username or organization namespace'
        )
        booleanParam(
            name: 'PUSH_TO_REGISTRY',
            defaultValue: true,
            description: 'Push tagged image to Docker Hub upon test success'
        )
    }

    environment {
        APP_NAME = 'digital-library-portal'
        VENV_DIR = '.venv'
        PYTHONUNBUFFERED = '1'
        BASE_URL = "http://127.0.0.1:${params.PORT}"
        CONTAINER_NAME = "${APP_NAME}-${params.ENVIRONMENT}"
        IMAGE_NAME = "${params.DOCKER_REGISTRY_USER}/${params.DOCKER_IMAGE_NAME}"
        IMAGE_TAG = "${IMAGE_NAME}:${BUILD_NUMBER}"
        IMAGE_LATEST = "${IMAGE_NAME}:latest"
        DEPLOY_URL = "http://localhost:${params.PORT}"
    }

    options {
        timeout(time: 25, unit: 'MINUTES')
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
                echo "Stage 2: Setup Local Environment & Dependencies"
                echo "=========================================================="
                sh '''
                    python3 -m venv ${VENV_DIR} || python -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate

                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt

                    python -c "import flask, selenium; print(f'Flask {flask.__version__} & Selenium {selenium.__version__} ready.')"
                '''
            }
        }

        stage('Unit Testing') {
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
            steps {
                echo "=========================================================="
                echo "Stage 4: Automated Headless Selenium UI Testing"
                echo "=========================================================="
                sh '''
                    . ${VENV_DIR}/bin/activate || . ${VENV_DIR}/Scripts/activate
                    mkdir -p reports/screenshots

                    export BASE_URL="http://127.0.0.1:${PORT}"
                    
                    # Non-zero exit code halts pipeline before Docker packaging & deployment!
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
                    echo "Halting pipeline: Docker image build and deployment skipped due to test regression."
                }
            }
        }

        stage('Docker Build & Tag') {
            steps {
                echo "=========================================================="
                echo "Stage 5: Building and Tagging Docker Container Image"
                echo "Image: ${IMAGE_TAG}"
                echo "=========================================================="
                sh '''
                    # Build lightweight, production-ready container image
                    docker build \
                        --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                        -t ${IMAGE_TAG} \
                        -t ${IMAGE_LATEST} \
                        .

                    # Inspect built image metadata and layer size
                    docker images | grep "${DOCKER_IMAGE_NAME}" | head -n 3
                '''
            }
        }

        stage('Docker Publish') {
            when {
                expression { return params.PUSH_TO_REGISTRY == true }
            }
            steps {
                echo "=========================================================="
                echo "Stage 6: Publishing Docker Image to Registry"
                echo "=========================================================="
                withCredentials([usernamePassword(
                    credentialsId: 'docker-hub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        # Secure non-interactive login via stdin
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                        # Push build-tagged image and latest tag
                        docker push ${IMAGE_TAG}
                        docker push ${IMAGE_LATEST}

                        # Logout to ensure credential hygiene on the Jenkins agent
                        docker logout
                    '''
                }
            }
        }

        stage('Docker Deploy') {
            steps {
                echo "=========================================================="
                echo "Stage 7: Deploying Fresh Docker Container (${params.ENVIRONMENT})"
                echo "=========================================================="
                sh '''
                    # Gracefully stop and remove existing container if running
                    echo "Stopping any existing container named ${CONTAINER_NAME}..."
                    docker stop ${CONTAINER_NAME} 2>/dev/null || true
                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                    # Ensure persistent Docker volume exists for SQLite data
                    docker volume create library_db_data 2>/dev/null || true

                    # Run fresh container with port mapping, volume mount, and restart policy
                    echo "Starting fresh container from image: ${IMAGE_TAG}..."
                    docker run -d \
                        --name ${CONTAINER_NAME} \
                        --restart unless-stopped \
                        -p ${PORT}:5000 \
                        -v library_db_data:/app \
                        -e PORT=5000 \
                        -e FLASK_ENV=${ENVIRONMENT} \
                        ${IMAGE_TAG}

                    # Await container health check readiness
                    echo "Probing container health endpoint..."
                    HEALTHY=0
                    for i in $(seq 1 12); do
                        sleep 2
                        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/health" || true)
                        if [ "$STATUS" = "200" ]; then
                            echo "Container responded HTTP 200 on attempt $i!"
                            HEALTHY=1
                            break
                        fi
                        echo "Attempt $i: container starting (HTTP $STATUS)..."
                    done

                    if [ "$HEALTHY" -ne 1 ]; then
                        echo "ERROR: Container health check failed!"
                        docker logs ${CONTAINER_NAME}
                        exit 1
                    fi

                    # Display running container inspection summary
                    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
                '''
                script {
                    echo "=========================================================="
                    echo "🎉 CONTINUOUS DEPLOYMENT SUCCESSFUL!"
                    echo "Target Environment : ${params.ENVIRONMENT}"
                    echo "Container Name     : ${env.CONTAINER_NAME}"
                    echo "Deployed Image     : ${env.IMAGE_TAG}"
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
            echo "Pipeline run completed. Cleaning workspace..."
            cleanWs deleteDirs: false, notFailBuild: true
        }
        success {
            echo "✅ Pipeline Build #${BUILD_NUMBER} completed: Container successfully tested, packaged, published, and deployed."
        }
        failure {
            echo "❌ Pipeline Build #${BUILD_NUMBER} failed. Deployment aborted."
        }
    }
}
