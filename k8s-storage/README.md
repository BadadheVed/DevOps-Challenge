# To get on which Node the pod is running

```json
kubectl get pod <pod-name> -o wide
```

## Common Confusion

```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-deploy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: "POSTGRES_USER"
          value: "ved"
        - name: "POSTGRES_PASSWORD"
          value: "ved"
        volumeMounts:
        - name: postgres-db-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-db-storage
        hostPath:
          path: /postgres           # This is where data lives on the Kind Node
          type: DirectoryOrCreate
```

- Here in the above yml file the path var/lib/postgresql/data will be mounted to the /postgres

Alse here we write the mount at which data will be store as the hostPath and the data that we want to store at the mountPath

## To take the AWS EKS to local terminal

```json
aws eks update-kubeconfig --region ap-south-1 --name YOUR_CLUSTER_NAME
```

## Associate Access Policy

```json
aws eks associate-access-policy \
  --cluster-name eks-storage-app \
  --principal-arn arn:aws:iam::327327820939:user/k8s \
  --access-scope type=cluster \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --region ap-south-1
```
