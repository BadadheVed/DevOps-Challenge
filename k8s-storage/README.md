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
