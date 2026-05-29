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
    choice(
      name: 'TEST_TYPE',
      choices: ['all', 'positive', 'negative'],
      description: 'Test type: all (both), positive (in-scope questions), negative (edge/refusal cases)'
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
    GROQ_API_KEY = credentials('GROQ_API_KEY')
    HF_TOKEN = credentials('HF_TOKEN')
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
            bat "python validate_rag_pipeline.py --config ci/validation_config.json --out %VALIDATION_REPORT% --test-type ${params.TEST_TYPE}"
          } else {
            sh "python3 validate_rag_pipeline.py --config ci/validation_config.json --out \$VALIDATION_REPORT --test-type ${params.TEST_TYPE}"
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
        script {
          echo 'Deployment approved: AI quality gate passed.'
          // Write credentials to .env file so Streamlit can read them in background
          if (params.NODE_OS == 'windows') {
            bat 'taskkill /IM streamlit /F 2>nul || ver>nul'
            bat 'ping -n 4 127.0.0.1 >nul'
            // Write .env with credentials so background Streamlit has the API key
            writeFile file: '.env', text: "GROQ_API_KEY=${GROQ_API_KEY}\nHF_TOKEN=${HF_TOKEN}\n"
            // Write a launcher .bat that starts Streamlit outside Jenkins job object
            writeFile file: 'start_streamlit.bat', text: """@echo off
cd /d ${WORKSPACE}
streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0
"""
            bat 'START "" /MIN start_streamlit.bat'
          } else {
            sh 'pkill -f streamlit 2>/dev/null || true'
            sh "echo GROQ_API_KEY=$GROQ_API_KEY > $WORKSPACE/.env"
            sh "echo HF_TOKEN=$HF_TOKEN >> $WORKSPACE/.env"
            sh 'sleep 3'
            sh 'nohup streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0 > streamlit.log 2>&1 &'
          }
        }
      }
    }

    stage('Post-Deploy Health Validation') {
      when {
        expression { currentBuild.currentResult == null || currentBuild.currentResult == 'SUCCESS' }
      }
      steps {
        script {
          echo 'Checking if application is running on port 8501...'
          if (params.NODE_OS == 'windows') {
            bat 'ping -n 10 127.0.0.1 >nul'
            bat 'curl -s http://localhost:8501 >nul 2>&1 && (echo Application is UP. Access it at http://10.10.12.78:8501) || (echo Application failed to start - check streamlit.log)'
            bat 'type streamlit.log 2>nul || echo (no streamlit.log)'
          } else {
            sh 'sleep 10'
            sh 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 && echo " - Access at http://10.10.12.78:8501" || echo "Application failed to start"'
          }
        }
      }
    }

  }

  post {
    failure {
      echo 'Pipeline failed: deployment blocked by AI validation or pre-check failures.'
    }
  }
}
