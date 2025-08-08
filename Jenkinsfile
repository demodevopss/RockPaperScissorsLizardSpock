pipeline {
  agent any
  environment {
    IMAGE = "devopsserdar/rpsls"
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
      }
    }
    stage('Trivy Scan') {
      steps {
        sh 'trivy image --no-progress --ignorefile .trivyignore --exit-code 1 --severity CRITICAL $IMAGE:latest || trivy image --no-progress --ignorefile .trivyignore --exit-code 1 --severity CRITICAL $IMAGE:$BUILD_NUMBER'
      }
    }
    stage('Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
          sh 'docker push $IMAGE:latest && docker push $IMAGE:$BUILD_NUMBER'
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
  - port: 80
    targetPort: 8080
    nodePort: 30080
YAML
kubectl rollout status deploy/rpsls -n rpsls --timeout=120s || true
'''
      }
    }
  }
}


