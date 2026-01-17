# To Build the Docker Image

```json
docker buildx build --platform linux/amd64 -t prometheus-app --load .
```

# To Run the Docker Container
```json
docker run -d --platform linux/amd64 --name myapp prometheus-app
```
# To Stop the Docker Container
```json
docker stop myapp
```