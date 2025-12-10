def runChecked(String label, Closure body) {
    echo "Starting ${label}..."
    notifyWebhook(label, "starting")
    try {
        body()
        echo "${label} succeeded."
        notifyWebhook(label, "succeeded")
    } catch (err) {
        echo "${label} failed: ${err}"
        notifyWebhook(label, "failed")
        throw err
    }
}

def shChecked(String label, String command) {
    runChecked(label) {
        sh """#!/usr/bin/env bash
set -euo pipefail
${command}
"""
    }
}

def notifyWebhook(String label, String status) {
    if (!env.STAGE_WEBHOOK_URL?.trim()) {
        echo "Webhook skipped for ${label} (${status}); STAGE_WEBHOOK_URL not set."
        return
    }
    def job = env.JOB_NAME ?: ''
    def build = env.BUILD_NUMBER ?: ''
    def url = env.BUILD_URL ?: ''
    sh """#!/usr/bin/env bash
set -euo pipefail
curl -sS -X POST -H 'Content-Type: application/json' -d @- "${STAGE_WEBHOOK_URL}" <<JSON
{"content":"${job} #${build}: ${label} -> ${status} (${url})","stage":"${label}","status":"${status}","job":"${job}","build":"${build}","url":"${url}"}
JSON
"""
}

pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        VENV = ".venv"
        DOCKER_IMAGE = "bookride-api:latest"
        GITHUB_PAT = credentials('github-pat')
        STAGE_WEBHOOK_URL = credentials('stage-webhook')
        BRANCH_SPEC = "blue"
    }

    stages {
        stage('Checkout Book & Ride Code') {
            steps {
                script {
                    runChecked('Checkout Book & Ride Code') {
                        // Uses the repository configured on the Jenkins job (adjust to explicit URL if needed)
                        checkout scm
                    }
                }
            }
        }

        stage('Verify Latest Commit') {
            steps {
                script {
                    shChecked('Verify Latest Commit', '''
                        git fetch origin ${BRANCH_SPEC}
                        LOCAL=$(git rev-parse HEAD)
                        REMOTE=$(git rev-parse origin/${BRANCH_SPEC})
                        if [ "$LOCAL" != "$REMOTE" ]; then
                            echo "Local commit $LOCAL is behind remote $REMOTE on ${BRANCH_SPEC}. Aborting build."
                            exit 1
                        fi
                    ''')
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    shChecked('Install Dependencies', '''
                        python3 -m venv ${VENV}
                        . ${VENV}/bin/activate
                        pip install --upgrade pip build
                        pip install -e .[dev]
                    ''')
                }
            }
        }

        stage('Run Book & Ride Tests') {
            steps {
                script {
                    shChecked('Run Book & Ride Tests', '''
                        . ${VENV}/bin/activate
                        mkdir -p reports
                        pytest -q --junitxml=reports/pytest-report.xml
                    ''')
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/pytest-report.xml'
                }
            }
        }

        stage('Build Package (sdist + wheel)') {
            steps {
                script {
                    shChecked('Build Package', '''
                        . ${VENV}/bin/activate
                        python -m build
                    ''')
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    shChecked('Build Docker Image', '''
                        docker build -t ${DOCKER_IMAGE} -f api/Dockerfile .
                    ''')
                }
            }
        }
    }

    post {
        success {
            echo 'Book & Ride CI pipeline completed successfully!'
        }
        failure {
            echo 'Book & Ride CI pipeline failed.'
        }
        cleanup {
            dir(env.WORKSPACE) {
                sh 'rm -rf ${VENV} build dist reports || true'
            }
        }
    }
}
