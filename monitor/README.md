## Remember this command for to add an access entry to the cluster

```json
aws eks create-access-entry \
  --cluster-name prometheus \
  --region ap-south-1 \
  --principal-arn arn:aws:iam::327327820939:user/k8s
```

## To link the local .kube/config to the AWS EKS Cluster do as the Add this

```json
aws eks associate-access-policy \
  --cluster-name prometheus \
  --region ap-south-1 \
  --principal-arn arn:aws:iam::327327820939:user/k8s \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```

## Tag the public subnets in VPC

```json
aws ec2 create-tags \
  --resources <public-subnet-1> <public-subnet-2> \
  --tags \
    Key=kubernetes.io/cluster/prometheus,Value=shared \
    Key=kubernetes.io/role/elb,Value=1
```

## The after that apply the service

```json
kubectl apply -f svc.yml
```

## Commands to install prometheus and the grafana

```json
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring

helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring
```

## After this create a ServiceMonitor

```json
kubectl apply -f svcmonitor.yml
```

# Then Get the grafana password/credentials

```json
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

# Then port forward the grafana to your local machine

```json
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

# Then open the grafana in your browser

http://localhost:3000

## To Install the telemetry collector

```json
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

```

## After this install the telemetry collector

```json
helm install otel-collector open-telemetry/opentelemetry-collector \
  -n monitoring -f otel-values.yml
```

## To pass the secrets in the yaml from the k8sin runtime use the

```json
kubectl create secret generic loki-s3-credentials \
  -n monitoring \
  --from-literal=AWS_ACCESS_KEY_ID=<key> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<secret>
```

- And then use them in the file as the means add this in the bottom of the file

```yml
extraEnvFrom:
  - secretRef:
      name: loki-s3-credentials
```

## To launch teh ngix ingress controller

```json
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.6/deploy/static/provider/aws/deploy.yaml

```

**After Launching the ingress controller patch t with the command**

```yml
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{
  "metadata": {
    "annotations": {
      "service.beta.kubernetes.io/aws-load-balancer-type": "nlb",
      "service.beta.kubernetes.io/aws-load-balancer-scheme": "internet-facing"
    }
  }
}'
```

**Command to install cert manager**

```json
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
```

## To update the alloy config here

- Run this command

```bash
kubectl create configmap alloy \
  --from-file=config.alloy=alloy-config.alloy \
  --dry-run=client -o yaml \
  -n monitoring | kubectl apply -f -
```
