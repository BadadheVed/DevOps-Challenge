### Make Sure to sign the certificated from the K8s CA not by own CA

## To get the Certificate for User

```json
openssl genrsa -out user.key 2048
openssl req -new -key user.key -out user.csr -subj "/CN=user"
openssl x509 -req -in user.csr -signkey user.key -out user.crt
```

## To get the Certificate For Group run

```json
openssl genrsa -out group.key 2048
openssl req -new -key group.key -out group.csr -subj "/CN=group"
openssl x509 -req -in group.csr -signkey group.key -out group.crt
```

## To Sign Using the K8s CA

```json

docker exec kind-control-plane cat /etc/kubernetes/pki/ca.crt > ca.crt
docker exec kind-control-plane cat /etc/kubernetes/pki/ca.key > ca.key

```

## and then after this

openssl x509 -req \
 -in user.csr \
 -CA ca.crt \
 -CAkey ca.key \
 -CAcreateserial \
 -out user.crt \ <-- This will outpt the cert
-days 365

## after this update the kubeconfig

```json

kubectl config set-credentials user \
  --client-certificate=user.crt \
  --client-key=user.key

```

## to switch the user context

```json
kubectl config set-context dev-user-context \
  --cluster=kind-kind \
  --namespace=development \
  --user=user
```

kubectl config use-context dev-user-context
