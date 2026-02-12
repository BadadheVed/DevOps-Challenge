# Kubernetes RBAC Setup for User "ved"

## Overview
Grant user `ved` (dev-team) access to the `dev` namespace only.

## Prerequisites
- kubectl access to the cluster
- OpenSSL installed

## Quick Setup

### 1. Generate User Certificate
```bash
# Generate private key
openssl genrsa -out ved.key 2048

# Create certificate signing request
openssl req -new -key ved.key -out ved.csr -subj "/CN=ved/O=dev-team"

# Create CSR YAML file
cat > ved-csr.yaml <<EOF
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: ved
spec:
  request: $(cat ved.csr | base64 | tr -d '\n')
  signerName: kubernetes.io/kube-apiserver-client
  usages:
  - client auth
EOF

# Apply and approve CSR
kubectl apply -f ved-csr.yaml
kubectl certificate approve ved
kubectl get csr ved -o jsonpath='{.status.certificate}' | base64 -d > ved.crt
```

### 2. Create Namespace and Apply RBAC
```bash
kubectl create namespace dev
kubectl apply -f dev-rbac.yaml
```

### 3. Configure kubectl Context
```bash
kubectl config set-credentials ved \
  --client-certificate=ved.crt \
  --client-key=ved.key \
  --embed-certs=true

kubectl config set-context ved-context \
  --cluster=kind-my-cluster \
  --namespace=dev \
  --user=ved
```

### 4. Test Access
```bash
# Switch to ved context
kubectl config use-context ved-context

# Should work
kubectl get pods -n dev

# Should fail
kubectl get pods -n default

# Switch back to admin
kubectl config use-context kind-my-cluster
```

## Files
- `dev-rbac.yaml` - Role and RoleBinding definitions
- `ved-csr.yaml` - Kubernetes CertificateSigningRequest
- `ved.key` - User private key
- `ved.crt` - User certificate
- `ved.csr` - Certificate signing request

## Permissions
User `ved` has full access to these resources in `dev` namespace:
- Pods, Deployments, Services
- ConfigMaps, Secrets
- Ingresses, PersistentVolumeClaims
- ReplicaSets, DaemonSets, StatefulSets