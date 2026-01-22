# EKS Auto Mode - EBS CSI Driver Storage Class Issue

## The Problem

When deploying Loki, Tempo, or any application requiring persistent storage on **EKS Auto Mode** clusters, PVCs (PersistentVolumeClaims) were stuck in `Pending` state with the error:
```
error generating accessibility requirements: no topology key found for node <node-id>
```

### Root Cause

**EKS Auto Mode uses a different EBS CSI provisioner than standard EKS clusters.**

- **Standard EKS**: Uses provisioner `ebs.csi.aws.com`
- **EKS Auto Mode**: Uses provisioner `ebs.csi.eks.amazonaws.com`

The default `gp2` StorageClass in many Helm charts uses the standard provisioner, which doesn't work with EKS Auto Mode.

## The Solution

### Step 1: Create the Correct StorageClass for EKS Auto Mode
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-auto-mode
provisioner: ebs.csi.eks.amazonaws.com  # Note: .eks. not .aws.
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
```

Apply it:
```bash
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-auto-mode
provisioner: ebs.csi.eks.amazonaws.com
parameters:
  type: gp3
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
EOF
```

### Step 2: Update Your Application Helm Values

#### For Loki (loki-aws.yml):
```yaml
backend:
  persistence:
    enabled: true
    size: 10Gi
    storageClass: ebs-auto-mode  # Changed from gp2
  replicas: 2

write:
  persistence:
    enabled: true
    size: 10Gi
    storageClass: ebs-auto-mode  # Changed from gp2
  replicas: 2

# ... rest of your Loki config
```

#### For Tempo (tempo-values.yaml):
```yaml
persistence:
  enabled: true
  storageClassName: ebs-auto-mode  # Changed from gp2
  accessModes:
    - ReadWriteOnce
  size: 10Gi

# ... rest of your Tempo config
```

### Step 3: Delete Existing Resources and Upgrade

**For Loki:**
```bash
# Delete old PVCs with gp2
kubectl delete pvc data-loki-backend-0 data-loki-backend-1 \
  data-loki-write-0 data-loki-write-1 -n monitoring

# Delete StatefulSets (required because volumeClaimTemplates are immutable)
kubectl delete statefulset loki-backend loki-write -n monitoring

# Upgrade with new storage class
helm upgrade loki grafana/loki -n monitoring -f loki-aws.yml

# Verify
kubectl get pvc -n monitoring
```

**For Tempo:**
```bash
# Delete old PVC
kubectl delete pvc storage-tempo-0 -n monitoring

# Delete StatefulSet
kubectl delete statefulset tempo -n monitoring

# Upgrade with new storage class
helm upgrade --install tempo grafana/tempo -n monitoring -f tempo-values.yaml

# Verify
kubectl get pvc -n monitoring
```

## Verification

After applying the fix, all PVCs should be in `Bound` state:
```bash
kubectl get pvc -n monitoring
```

Expected output:
```
NAME                  STATUS   VOLUME        CAPACITY   STORAGECLASS
data-loki-backend-0   Bound    pvc-xxxxx     10Gi       ebs-auto-mode
data-loki-backend-1   Bound    pvc-xxxxx     10Gi       ebs-auto-mode
data-loki-write-0     Bound    pvc-xxxxx     10Gi       ebs-auto-mode
data-loki-write-1     Bound    pvc-xxxxx     10Gi       ebs-auto-mode
storage-tempo-0       Bound    pvc-xxxxx     10Gi       ebs-auto-mode
```

All pods should be running:
```bash
kubectl get pods -n monitoring | grep -E "loki|tempo"
```

## Why the EBS CSI Driver Node Daemonset Wasn't Needed

In EKS Auto Mode, the storage provisioning works differently:

1. **Standard EKS**: Requires the `ebs-csi-node` daemonset to run on each node to register topology information
2. **EKS Auto Mode**: The `ebs.csi.eks.amazonaws.com` provisioner handles topology automatically without requiring the node daemonset

This is why we had `ebs-csi-node` daemonset showing `DESIRED: 0` - it's not needed in Auto Mode.

## Key Takeaways

- ✅ Always use `ebs.csi.eks.amazonaws.com` provisioner on EKS Auto Mode
- ✅ Update all Helm chart values to use `ebs-auto-mode` StorageClass
- ✅ StatefulSets must be deleted before changing volumeClaimTemplates
- ✅ The node daemonset (`ebs-csi-node`) is not required in Auto Mode
- ❌ Don't use the standard `ebs.csi.aws.com` provisioner on Auto Mode clusters
- ❌ Don't rely on manual topology labels - Auto Mode handles this

## References

- [EKS Storage Classes](https://docs.aws.amazon.com/eks/latest/userguide/storage-classes.html)
- [EBS CSI Driver for EKS](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [EKS Auto Mode Documentation](https://docs.aws.amazon.com/eks/latest/userguide/automode.html)
