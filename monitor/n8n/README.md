## TO Create A Service Account

```
kubectl create token n8n-monitor-sa -n n8n --duration=0s
```

## To check if user can access that specific resource

```bash 
kubectl auth can-i list nodes --as=system:serviceaccount:n8n:n8n-monitor-sa
```


## To create a token 

```bash
kubectl create token n8n-monitor-sa -n n8n --duration=0s
```

- here *n8n-monitor-sa* in the service account name
