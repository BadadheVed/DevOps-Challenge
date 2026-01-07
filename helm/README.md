### Install BItnami Which maintatins the Postgres and the other DB's like Mongo etc etc

- helm repo add bitnami https://charts.bitnami.com/bitnami

- helm repo update

# This Command is to basically install the things initially

```json
 helm install postgres bitnami/postgresql \
  --namespace databases \
  --create-namespace \
  --values pg.yml
```

## To Update the config e use the command as the

```json
helm upgrade postgres bitnami/postgresql \
  -n databases \
  -f pg.yml
```
