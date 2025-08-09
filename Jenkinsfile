pipeline {
  agent any
  environment {
    IMAGE = "devopsserdar/rpsls"
    IMAGE_WEB = "devopsserdar/rpsls-web"
    KUBECONFIG = "/var/jenkins_home/.kube/config"
  }
  options { timestamps() }
  stages {
    stage('Checkout') {
      steps {
        checkout([$class: 'GitSCM', branches: [[name: '*/main']], userRemoteConfigs: [[url: 'https://github.com/demodevopss/RockPaperScissorsLizardSpock.git']]])
      }
    }
    stage('Docker Build') {
      steps {
        sh 'docker version'
        sh 'docker build -t $IMAGE:latest -t $IMAGE:$BUILD_NUMBER .'
        sh 'docker build -t $IMAGE_WEB:latest -t $IMAGE_WEB:$BUILD_NUMBER -f Source/Services/RPSLS.Game/Server/Dockerfile Source/Services'
      }
    }
    stage('Trivy Scan') {
      steps {
        sh 'trivy image --no-progress --ignorefile .trivyignore --exit-code 1 --severity CRITICAL $IMAGE:latest || trivy image --no-progress --ignorefile .trivyignore --exit-code 1 --severity CRITICAL $IMAGE:$BUILD_NUMBER'
      }
    }
    stage('UI Tests (Smoke)') {
      steps {
        sh '''
set -e
WEB_URL=${WEB_URL:-http://192.168.64.153:30081}
API_URL=${API_URL:-http://192.168.64.153:30080}
mkdir -p reports/ui
docker network create rpsls-tests >/dev/null 2>&1 || true
docker rm -f selenium >/dev/null 2>&1 || true
docker run -d --name selenium --network rpsls-tests -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest || docker run -d --name selenium --network rpsls-tests -p 4444:4444 --shm-size=2g selenium/standalone-chrome:latest
 docker run --rm --network rpsls-tests --volumes-from jenkins -e SELENIUM_URL=http://selenium:4444/wd/hub -e WEB_URL=$WEB_URL -e API_URL=$API_URL -w "$WORKSPACE" python:3.11-slim sh -lc "pip install --no-cache-dir pytest selenium && pytest -q -m smoke --junitxml=reports/ui/smoke.xml tests/ui || pytest -q -m smoke --junitxml=reports/ui/smoke.xml"
'''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'reports/ui/*.xml'
          archiveArtifacts artifacts: 'reports/ui/*.xml', allowEmptyArchive: true
          sh 'docker rm -f selenium >/dev/null 2>&1 || true; docker network rm rpsls-tests >/dev/null 2>&1 || true'
        }
      }
    }

    
    stage('Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
          sh 'docker push $IMAGE:latest && docker push $IMAGE:$BUILD_NUMBER'
          sh 'docker push $IMAGE_WEB:latest && docker push $IMAGE_WEB:$BUILD_NUMBER'
        }
      }
    }
    stage('Deploy') {
      steps {
        sh '''
set -e
kubectl create namespace rpsls --dry-run=client -o yaml | kubectl apply -f - || true

cat <<YAML | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rpsls
  namespace: rpsls
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rpsls
  template:
    metadata:
      labels:
        app: rpsls
    spec:
      containers:
      - name: rpsls
        image: "$IMAGE:$BUILD_NUMBER"
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: rpsls
  namespace: rpsls
spec:
  type: NodePort
  selector:
    app: rpsls
  ports:
  - name: http
    port: 80
    targetPort: 8080
    nodePort: 30080
  - name: grpc
    port: 8081
    targetPort: 8081
    nodePort: 30082
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rpsls-web
  namespace: rpsls
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rpsls-web
  template:
    metadata:
      labels:
        app: rpsls-web
    spec:
      containers:
      - name: rpsls-web
        image: "$IMAGE_WEB:$BUILD_NUMBER"
        imagePullPolicy: Always
        env:
        - name: GameManager__Url
          value: "http://rpsls.rpsls.svc.cluster.local:8081"
        - name: GameManager__Grpc__GrpcOverHttp
          value: "true"
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: rpsls-web
  namespace: rpsls
spec:
  type: NodePort
  selector:
    app: rpsls-web
  ports:
  - name: http
    port: 80
    targetPort: 80
    nodePort: 30081
YAML

kubectl -n rpsls rollout status deploy/rpsls --timeout=120s || true
kubectl -n rpsls rollout status deploy/rpsls-web --timeout=120s || true
'''
        script { env.DEPLOYED = 'true' }
      }
    }

    stage('UI Tests (Regression)') {
      steps {
        sh '''
set -e
WEB_URL=${WEB_URL:-http://192.168.64.153:30081}
API_URL=${API_URL:-http://192.168.64.153:30080}
mkdir -p reports/ui
docker network create rpsls-tests >/dev/null 2>&1 || true
docker rm -f selenium >/dev/null 2>&1 || true
docker run -d --name selenium --network rpsls-tests -p 4444:4444 --shm-size=2g seleniarm/standalone-chromium:latest || docker run -d --name selenium --network rpsls-tests -p 4444:4444 --shm-size=2g selenium/standalone-chrome:latest
 docker run --rm --network rpsls-tests --volumes-from jenkins -e SELENIUM_URL=http://selenium:4444/wd/hub -e WEB_URL=$WEB_URL -e API_URL=$API_URL -w "$WORKSPACE" python:3.11-slim sh -lc "pip install --no-cache-dir pytest selenium && pytest -q -m regression --junitxml=reports/ui/regression.xml tests/ui || pytest -q -m regression --junitxml=reports/ui/regression.xml"
'''
      }
      post {
        always {
          junit allowEmptyResults: true, testResults: 'reports/ui/*.xml'
          archiveArtifacts artifacts: 'reports/ui/*.xml', allowEmptyArchive: true
          sh 'docker rm -f selenium >/dev/null 2>&1 || true; docker network rm rpsls-tests >/dev/null 2>&1 || true'
        }
      }
    }
  }
}


