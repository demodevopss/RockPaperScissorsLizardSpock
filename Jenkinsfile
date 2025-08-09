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
# Clean up broken last-applied annotation or old deployment to avoid patch errors
kubectl -n rpsls annotate deploy/rpsls kubectl.kubernetes.io/last-applied-configuration- || true
kubectl -n rpsls delete deploy rpsls --ignore-not-found=true || true
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

# Web (Blazor Server) deploy
cat <<YAML | kubectl apply -f -
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
              value: http://rpsls.rpsls.svc.cluster.local:8080
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
'''
      }
    }
  }
}


