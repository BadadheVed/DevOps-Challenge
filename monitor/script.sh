
kubectl create configmap alloy \
  --from-file=config.alloy=alloy-config.alloy \
  --dry-run=client -o yaml \
  -n monitoring | kubectl apply -f -

echo "✅ Alloy ConfigMap updated"
echo ""
echo "Restarting Alloy pods to apply new config..."

kubectl rollout restart daemonset/alloy -n monitoring

echo ""
echo "Wait for rollout to complete:"
kubectl rollout status daemonset/alloy -n monitoring