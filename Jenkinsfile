pipeline {
  agent any

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
      steps {
        sh 'python3 -m pip install -e . --quiet'
      }
    }

    stage('Dependency Validation') {
      steps {
        sh 'python3 -V'
        sh 'python3 -c "import langchain, langchain_groq, pandas, streamlit, datasets, ragas; print(\\"core_deps_ok\\")"'
      }
    }

    stage('Unit Validation') {
      steps {
        sh 'python3 -m unittest discover -s tests -p "test_*.py" -v'
      }
    }

    stage('RAG + RAGAS Validation') {
      steps {
        sh 'python3 validate_rag_pipeline.py --config ci/validation_config.json --out $VALIDATION_REPORT'
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/*.json', allowEmptyArchive: true
        }
      }
    }

    stage('AI Quality Gate') {
      steps {
        sh 'python3 ci/gate_validation.py --report $VALIDATION_REPORT'
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
