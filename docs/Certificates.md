# Kubernetes TLS Certificates - Quick Guide

Concise guide for issuing TLS certificates on Kubernetes using cert-manager with separate YAML files.

---

## Required Resources for TLS Certificates

To issue a TLS certificate in Kubernetes, you need:

1. **cert-manager** - Certificate management controller
2. **ClusterIssuer** - Defines how certificates are issued (Let's Encrypt)
3. **Ingress** - Routes traffic and triggers certificate creation
4. **DNS Record** - Points your domain to the LoadBalancer
5. **Secret** - Automatically created by cert-manager to store the certificate

### Resource Flow

```
DNS Record → LoadBalancer → Ingress (with TLS) → ClusterIssuer → Certificate → Secret
```

### What Gets Created

When you create an Ingress with TLS:
- **Certificate** - Automatically created by cert-manager
- **CertificateRequest** - Intermediate resource for requesting cert
- **Order** - ACME order with Let's Encrypt
- **Challenge** - HTTP-01 or DNS-01 validation challenge
- **Secret** - Contains `tls.crt` and `tls.key` files

---

## 1. Install cert-manager

```bash
helm repo add jetstack https://charts.jetstack.io
```
Add the Jetstack Helm repository

```bash
helm repo update
```
Update Helm repository cache

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.13.0 \
  --set installCRDs=true
```
Install cert-manager with CRDs

```bash
kubectl get pods -n cert-manager
```
Verify cert-manager pods are running

---

## 2. Create ClusterIssuers

### File: `letsencrypt-staging.yaml`

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

### File: `letsencrypt-prod.yaml`

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

```bash
kubectl apply -f letsencrypt-staging.yaml
```
Create staging issuer for testing

```bash
kubectl apply -f letsencrypt-prod.yaml
```
Create production issuer for real certificates

```bash
kubectl get clusterissuer
```
List all ClusterIssuers

```bash
kubectl describe clusterissuer letsencrypt-prod
```
Check issuer status and configuration

---

## 3. Configure DNS

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```
Get LoadBalancer external IP/hostname

**In your DNS provider, create:**
- **Type:** CNAME (for ELB) or A (for IP)
- **Name:** subdomain (e.g., `app`, `grafana`)
- **Value:** LoadBalancer hostname/IP
- **TTL:** 300

```bash
nslookup app.example.com
```
Verify DNS resolves correctly

```bash
dig app.example.com +short
```
Show resolved IP address only

```bash
curl -I http://app.example.com
```
Test HTTP connectivity before requesting certificate

---

## 4. Create Ingress with TLS

### File: `ingress-default.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - app.example.com
    - api.example.com
    secretName: app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
```

### File: `ingress-monitoring.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: monitoring
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - grafana.example.com
    secretName: grafana-tls
  rules:
  - host: grafana.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: grafana
            port:
              number: 80
```

### File: `ingress-n8n.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: n8n-ingress
  namespace: n8n
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - n8n.example.com
    secretName: n8n-tls
  rules:
  - host: n8n.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: n8n
            port:
              number: 80
```

```bash
kubectl apply -f ingress-default.yaml
```
Create Ingress for default namespace

```bash
kubectl apply -f ingress-monitoring.yaml
```
Create Ingress for monitoring namespace

```bash
kubectl apply -f ingress-n8n.yaml
```
Create Ingress for n8n namespace

---

## 5. Verify Certificate Issuance

```bash
kubectl get certificate -A
```
List all certificates (READY=True when issued)

```bash
kubectl get certificate app-tls -n default
```
Check specific certificate status

```bash
kubectl describe certificate app-tls -n default
```
View certificate details and events

```bash
kubectl get certificaterequest -n default
```
List certificate requests

```bash
kubectl get order -n default
```
List ACME orders

```bash
kubectl get challenge -n default
```
List ACME challenges (HTTP-01 validation)

```bash
kubectl describe challenge <challenge-name> -n default
```
Debug stuck challenges

```bash
kubectl get secret app-tls -n default
```
Verify certificate secret was created

```bash
kubectl get secret app-tls -n default -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -text -noout
```
View certificate details from secret

---

## 6. Test HTTPS

```bash
curl -I https://app.example.com
```
Test HTTPS connection

```bash
openssl s_client -connect app.example.com:443 -servername app.example.com
```
View SSL/TLS connection details

```bash
curl -vI https://app.example.com 2>&1 | grep -A 10 "Server certificate"
```
Show certificate information

---

## 7. Troubleshooting

```bash
kubectl logs -n cert-manager -l app=cert-manager --tail=50
```
View cert-manager logs

```bash
kubectl logs -n cert-manager -l app=webhook --tail=50
```
View webhook logs

```bash
kubectl describe challenge <challenge-name> -n default
```
Check why challenge is failing

```bash
kubectl delete challenge --all -n default
```
Delete stuck challenges to retry

```bash
kubectl delete certificate app-tls -n default
```
Delete and recreate certificate

```bash
curl http://app.example.com/.well-known/acme-challenge/test
```
Test ACME challenge endpoint accessibility

```bash
kubectl get ingress -n default
```
Verify ingress was created

```bash
kubectl describe ingress app-ingress -n default
```
Check ingress configuration and events

```bash
kubectl get events -n default --sort-by='.lastTimestamp'
```
View recent events in namespace

---

## 8. Common Issues & Fixes

### Issue: Certificate stuck at False

```bash
kubectl describe certificate app-tls -n default
```
Check certificate status message

**Common causes:**
- DNS not configured
- Ingress controller not working
- Firewall blocking port 80

### Issue: Challenge failing with "no such host"

```bash
nslookup app.example.com
```
Verify DNS is configured correctly

```bash
kubectl get svc -n ingress-nginx
```
Verify LoadBalancer has external IP

**Fix:** Wait for DNS propagation (5-30 minutes)

### Issue: Challenge failing with 404/403

```bash
kubectl get pods -n default | grep cm-acme
```
Check if challenge solver pod exists

```bash
kubectl get ingress -n default
```
Verify challenge solver ingress was created

```bash
curl -v http://app.example.com/.well-known/acme-challenge/
```
Test challenge endpoint manually

### Issue: Rate limit exceeded

```bash
kubectl patch ingress app-ingress -n default -p '{"metadata":{"annotations":{"cert-manager.io/cluster-issuer":"letsencrypt-staging"}}}'
```
Switch to staging issuer temporarily

```bash
kubectl delete certificate app-tls -n default
```
Delete certificate to trigger new issuance with staging

---

## 9. Certificate Management

```bash
kubectl get certificate -A -o wide
```
View all certificates with expiration dates

```bash
kubectl delete secret app-tls -n default
```
Force certificate renewal (cert-manager recreates it)

```bash
kubectl get clusterissuer -o yaml
```
Export ClusterIssuer configuration

```bash
kubectl get certificate app-tls -n default -o yaml
```
Export certificate configuration

---

## 10. Wildcard Certificates (DNS-01)

### File: `letsencrypt-dns01.yaml`

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-dns
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-dns
    solvers:
    - dns01:
        route53:
          region: us-east-1
          accessKeyID: AKIAIOSFODNN7EXAMPLE
          secretAccessKeySecretRef:
            name: route53-credentials
            key: secret-access-key
```

### File: `wildcard-certificate.yaml`

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-example
  namespace: default
spec:
  secretName: wildcard-tls
  issuerRef:
    name: letsencrypt-dns
    kind: ClusterIssuer
  dnsNames:
  - example.com
  - "*.example.com"
```

```bash
kubectl apply -f letsencrypt-dns01.yaml
```
Create DNS-01 issuer for wildcard certificates

```bash
kubectl apply -f wildcard-certificate.yaml
```
Request wildcard certificate

---

## Quick Reference

```bash
# Install
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true

# Create issuers
kubectl apply -f letsencrypt-staging.yaml
kubectl apply -f letsencrypt-prod.yaml

# Create ingress
kubectl apply -f ingress-default.yaml

# Check status
kubectl get certificate -A
kubectl describe certificate <name> -n <namespace>

# Troubleshoot
kubectl logs -n cert-manager -l app=cert-manager --tail=50
kubectl describe challenge <name> -n <namespace>

# Test
curl -I https://app.example.com
```

---

## Best Practices

1. **Always test with staging first** to avoid rate limits
2. **Configure DNS before creating Ingress** to avoid failed challenges
3. **One Ingress per namespace** - cannot reference services across namespaces
4. **Monitor certificate expiration** - auto-renewal happens 30 days before expiry
5. **Use strong TLS settings** in Ingress annotations
6. **Backup certificate secrets** regularly