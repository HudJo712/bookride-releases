def runChecked(String label, Closure body) {
    echo "Starting ${label}..."
    try {
        body()
        echo "${label} succeeded."
    } catch (err) {
        echo "${label} failed: ${err}"
        throw err
    }
}

def shChecked(String label, String command) {
    runChecked(label) {
        sh """
            set -euo pipefail
            ${command}
        """
    }
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
