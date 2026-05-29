pipeline {
  parameters {
    string(
      name: 'NODE_LABEL',
      defaultValue: 'copper-dev-10.10.12.78',
      description: 'Jenkins agent label (e.g. linux, windows, copper-dev-10.10.12.78)'
    )
    choice(
      name: 'NODE_OS',
      choices: ['windows', 'linux'],
      description: 'OS type of the target agent — controls whether bat or sh is used'
    )
  }

  agent { label params.NODE_LABEL }

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  environment {
    PYTHONUNBUFFERED = '1'
    VALIDATION_REPORT = 'reports/validation_report.json'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Install Dependencies') {
      options { timeout(time: 30, unit: 'MINUTES') }
      steps {
        script {
          if (params.NODE_OS == 'windows') {
            bat 'python -m pip install --upgrade pip'
            bat 'python -m pip install -e . --upgrade'
          } else {
            sh 'python3 -m pip install --upgrade pip'
            sh 'python3 -m pip install -e . --upgrade'
          }
        }
      }
    }

    stage('Dependency Validation') {
      steps {
        script {
          if (params.NODE_OS == 'windows') {
            bat 'python -V'
            bat 'python -c "import langchain, langchain_groq, pandas, streamlit, datasets, ragas; print(\\"core_deps_ok\\")"'
          } else {
            sh 'python3 -V'
            sh 'python3 -c "import langchain, langchain_groq, pandas, streamlit, datasets, ragas; print(\\"core_deps_ok\\")"'
          }
        }
      }
    }

    stage('Unit Validation') {
      steps {
        script {
          if (params.NODE_OS == 'windows') {
            bat 'python -m unittest discover -s tests -p "test_*.py" -v'
          } else {
            sh 'python3 -m unittest discover -s tests -p "test_*.py" -v'
          }
        }
      }
    }

    stage('RAG + RAGAS Validation') {
      steps {
        script {
          if (params.NODE_OS == 'windows') {
            bat 'python validate_rag_pipeline.py --config ci/validation_config.json --out %VALIDATION_REPORT%'
          } else {
            sh 'python3 validate_rag_pipeline.py --config ci/validation_config.json --out $VALIDATION_REPORT'
          }
        }
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/*.json', allowEmptyArchive: true
        }
      }
    }

    stage('AI Quality Gate') {
      steps {
        script {
          if (params.NODE_OS == 'windows') {
            bat 'python ci/gate_validation.py --report %VALIDATION_REPORT%'
          } else {
            sh 'python3 ci/gate_validation.py --report $VALIDATION_REPORT'
          }
        }
      }
    }

    stage('Deploy') {
      when {
        expression { currentBuild.currentResult == null || currentBuild.currentResult == 'SUCCESS' }
      }
      steps {
        echo 'Deployment approved: AI quality gate passed.'
      }
    }

    stage('Post-Deploy Health Validation') {
      when {
        expression { currentBuild.currentResult == null || currentBuild.currentResult == 'SUCCESS' }
      }
      steps {
        echo 'Run service health checks here (HTTP readiness, synthetic query checks).'
      }
    }
  }

  post {
    failure {
      echo 'Pipeline failed: deployment blocked by AI validation or pre-check failures.'
    }
  }
}
