# Setup Guide - Zomato Microservices Workshop

Complete step-by-step setup for the Zomato-style microservices workshop on RHEL 9.

## 🔍 STEP 0: Pre-Check (IMPORTANT)

### Verify RHEL 9
```bash
cat /etc/redhat-release
```
**Expected**: `Red Hat Enterprise Linux release 9.x`

### Disable SELinux (Demo Stability)
```bash
sudo setenforce 0
getenforce
```
**Output**: `Permissive`

## 🐳 STEP 1: Install Docker (RHEL 9 - Valid Way)

### Remove Conflicting Packages
```bash
sudo dnf remove -y podman podman-docker
```

### Add Docker Repository
```bash
sudo dnf config-manager --add-repo \
https://download.docker.com/linux/centos/docker-ce.repo
```

### Install Docker
```bash
sudo dnf install -y docker-ce docker-ce-cli containerd.io
```

### Start Docker Service
```bash
sudo systemctl enable docker --now
```

### Add User Permissions
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Test Installation
```bash
docker run hello-world
```
✅ **If this runs → Docker OK**

## ☸️ STEP 2: Install kubectl

```bash
curl -LO https://dl.k8s.io/release/$(curl -L -s \
https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### Verify Installation
```bash
kubectl version --client
```

## 🎛️ STEP 3: Install k3d

```bash
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
```

### Verify Installation
```bash
k3d version
```

## 📦 STEP 4: Create Local Registry (MANDATORY)

```bash
k3d registry create zomato-registry --port 5000
```

### Verify Registry
```bash
docker ps | grep registry
curl http://localhost:5000/v2/_catalog
```
**Expected**: `{"repositories":[]}`

## 🏗️ STEP 5: Create Kubernetes Cluster

```bash
k3d cluster create zomato-cluster \
--agents 2 \
-p "8080:80@loadbalancer" \
--registry-use k3d-zomato-registry:5000
```

### Verify Cluster
```bash
kubectl get nodes
```
**Expected**: 1 server + 2 agents → Ready

## 🌐 STEP 6: Verify System Pods

### Check All System Pods
```bash
kubectl get pods -n kube-system
```

**You MUST see**:
- `coredns-xxxx` - 1/1 Running
- `helm-install-traefik-xxxx` - Completed
- `helm-install-traefik-crd-xxxx` - Completed
- `local-path-provisioner-xxxx` - 1/1 Running
- `metrics-server-xxxx` - 1/1 Running
- `traefik-xxxx` - 1/1 Running

⏱️ **This can take 2–4 minutes on RHEL 9**

## 📁 STEP 7: Project Structure

```bash
mkdir zomato && cd zomato
```

## 🟢 STEP 8: User Service (Node.js)

### Create Service Directory
```bash
mkdir user-service && cd user-service
```

### Create server.js
```javascript
const express = require('express');
const app = express();

app.get('/users', (req, res) => {
    res.json(["Rahul","Aisha","Zoya"]);
});

app.get('/health', (req, res) => {
    res.send("OK");
});

app.listen(3001, () => console.log("User service running"));
```

### Create Dockerfile
```dockerfile
FROM node:18-alpine
WORKDIR /app
RUN npm init -y && npm install express
COPY server.js .
EXPOSE 3001
CMD ["node", "server.js"]
```

### Test Locally (Important)
```bash
# Build test image
docker build -t user-test:v1 .

# Run container
docker run -d --name user-test -p 3001:3001 user-test:v1

# Check logs
docker logs user-test

# Test endpoint
curl http://localhost:3001/users
# Expected: ["Rahul","Aisha","Zoya"]

# Health check
curl http://localhost:3001/health
# Expected: OK

# Clean up
docker stop user-test
docker rm user-test
```

### Build & Push Final Image
```bash
docker build -t localhost:5000/user-service:v1 .
docker push localhost:5000/user-service:v1

# Verify registry
curl http://localhost:5000/v2/user-service/tags/list
```

```bash
cd ..
```

## 🐍 STEP 9: Restaurant Service (Python)

### Create Service Directory
```bash
mkdir restaurant-service && cd restaurant-service
```

### Create app.py
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/restaurants')
def restaurants():
    return jsonify(["Pizza Hub", "Biryani House"])

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)
```

### Create Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN pip install flask
COPY app.py .
EXPOSE 3002
CMD ["python", "app.py"]
```

### Test Locally
```bash
# Build test image
docker build -t restaurant-test:v1 .

# Run container
docker run -d --name restaurant-test -p 3002:3002 restaurant-test:v1

# Check logs
docker logs restaurant-test

# Test endpoint
curl http://localhost:3002/restaurants
# Expected: ["Pizza Hub","Biryani House"]

# Clean up
docker stop restaurant-test
docker rm restaurant-test
```

### Build & Push Final Image
```bash
docker tag restaurant-test:v1 localhost:5000/restaurant-service:v1
docker push localhost:5000/restaurant-service:v1

# Verify registry
curl http://localhost:5000/v2/restaurant-service/tags/list
```

```bash
cd ..
```

## 🔵 STEP 10: Order Service (Go)

### Create Service Directory
```bash
mkdir order-service && cd order-service
```

### Create main.go
```go
package main

import (
    "net/http"
)

func main() {
    http.HandleFunc("/orders", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("Order Placed Successfully"))
    })
    
    http.ListenAndServe(":3003", nil)
}
```

### Create Dockerfile
```dockerfile
FROM golang:1.21-alpine
WORKDIR /app
ENV GO111MODULE=off
COPY main.go .
RUN go build -o main main.go
EXPOSE 3003
CMD ["./main"]
```

### Test Locally
```bash
# Build test image
docker build -t order-service:test .

# Run container
docker run -d --name order-test -p 3003:3003 order-service:test

# Test endpoint
curl http://localhost:3003/orders
# Expected: Order Placed Successfully

# Clean up
docker stop order-test
docker rm order-test
```

### Build & Push Final Image
```bash
docker tag order-service:test localhost:5000/order-service:v1
docker push localhost:5000/order-service:v1

# Verify registry
curl http://localhost:5000/v2/_catalog
# Must include: order-service
```

```bash
cd ..
```

## ☸️ STEP 11: Kubernetes Deployment Files

### Create k8s Directory
```bash
mkdir k8s
```

### Create k8s/user.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user
  template:
    metadata:
      labels:
        app: user
    spec:
      containers:
      - name: user
        image: k3d-zomato-registry:5000/user-service:v1
        ports:
        - containerPort: 3001
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user
  ports:
  - port: 3001
```

### Create k8s/restaurant.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: restaurant-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: restaurant
  template:
    metadata:
      labels:
        app: restaurant
    spec:
      containers:
      - name: restaurant
        image: k3d-zomato-registry:5000/restaurant-service:v1
        ports:
        - containerPort: 3002
---
apiVersion: v1
kind: Service
metadata:
  name: restaurant-service
spec:
  selector:
    app: restaurant
  ports:
  - port: 3002
    targetPort: 3002
```

### Create k8s/order.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order
  template:
    metadata:
      labels:
        app: order
    spec:
      containers:
      - name: order
        image: k3d-zomato-registry:5000/order-service:v1
        ports:
        - containerPort: 3003
---
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order
  ports:
  - port: 3003
    targetPort: 3003
```

### Deploy All Services
```bash
kubectl apply -f k8s/user.yaml
kubectl apply -f k8s/restaurant.yaml
kubectl apply -f k8s/order.yaml
```

### Test Services with Debug Pod
```bash
kubectl run curl-test \
--image=curlimages/curl:8.5.0 \
--restart=Never \
-it -- sh
```

**Inside the pod shell**:
```bash
# Test User Service
curl http://user-service:3001/users
# Expected: ["Rahul","Aisha","Zoya"]

# Test Restaurant Service
curl http://restaurant-service:3002/restaurants
# Expected: ["Pizza Hub","Biryani House"]

# Test Order Service
curl http://order-service:3003/orders
# Expected: Order Placed Successfully

# Exit pod
exit
```

✅ **If this works → STEP 11 IS 100% SUCCESSFUL**

## 🌐 STEP 12: Ingress (FINAL & WORKING)

### Create k8s/ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zomato-ingress
  annotations:
    kubernetes.io/ingress.class: traefik
spec:
  rules:
  - host: localhost
    http:
      paths:
      - path: /users
        pathType: Prefix
        backend:
          service:
            name: user-service
            port:
              number: 3001
      - path: /restaurants
        pathType: Prefix
        backend:
          service:
            name: restaurant-service
            port:
              number: 3002
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: order-service
            port:
              number: 3003
```

### Apply Ingress
```bash
kubectl apply -f k8s/ingress.yaml
```

### Verify Ingress
```bash
kubectl get ingress
```

## 🧪 STEP 13: Final Test (THIS WILL WORK)

```bash
curl http://localhost:8080/users
curl http://localhost:8080/restaurants
curl http://localhost:8080/orders
```

**Expected**:
- `["Rahul","Aisha","Zoya"]`
- `["Pizza Hub","Biryani House"]`
- `Order Placed Successfully`

## 🔄 STEP 14: Auto-Healing Demo (WOW MOMENT)

```bash
kubectl delete pod -l app=user
kubectl get pods
```
➡️ **Pod re-created automatically**

## 🧹 Complete Cleanup

### Full System Cleanup
```bash
# Delete all k3d clusters
k3d cluster delete --all

# Delete all k3d registries
k3d registry delete --all

# Remove all Docker containers
docker rm -f $(docker ps -aq)

# Remove all Docker images
docker rmi -f $(docker images -aq)

# Clean Docker system
docker system prune -a -f --volumes
```

### Verify Cleanup
```bash
docker ps -a
docker images
k3d cluster list
k3d registry list
```
**All should be empty/clean**

---

**Workshop practical Complete!** 🎉