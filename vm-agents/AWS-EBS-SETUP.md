# AWS EBS CSI Driver Setup Guide

This guide explains how to set up the AWS EBS CSI driver and enable persistent storage for the vm-agents Helm chart.

## Prerequisites

- EKS cluster running in AWS
- kubectl configured to access your cluster
- Helm 3.x installed
- IAM permissions to create service accounts and policies

## Step 1: Install AWS EBS CSI Driver

### Option A: Using EKS Add-on (Recommended)

```bash
# Get your cluster name
CLUSTER_NAME="your-cluster-name"
AWS_REGION="us-east-1"

# Create IAM service account for EBS CSI driver
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster ${CLUSTER_NAME} \
  --region ${AWS_REGION} \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --approve \
  --role-name AmazonEKS_EBS_CSI_DriverRole

# Install EBS CSI driver add-on
aws eks create-addon \
  --cluster-name ${CLUSTER_NAME} \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/AmazonEKS_EBS_CSI_DriverRole \
  --region ${AWS_REGION}

# Verify installation
kubectl get pods -n kube-system -l app.kubernetes.io/name=aws-ebs-csi-driver
```

### Option B: Using Helm

```bash
# Add AWS EBS CSI driver Helm repo
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update

# Install the driver
helm upgrade --install aws-ebs-csi-driver \
  --namespace kube-system \
  aws-ebs-csi-driver/aws-ebs-csi-driver
```

## Step 2: Verify EBS CSI Driver

```bash
# Check if driver is running
kubectl get pods -n kube-system | grep ebs-csi

# Check for default storage classes
kubectl get storageclass

# Expected output should include:
# gp2 (default for older clusters)
# gp3 (recommended for new clusters)
```

## Step 3: Configure vm-agents with Persistence

### Using Existing StorageClass (Recommended)

Edit your `values.yaml` or use `--set` flags:

```yaml
# Enable persistence
persistence:
  enabled: true
  storageClass: "gp3"  # Use existing AWS EBS storage class
  size: 10Gi
  mountPath: /data
  accessModes:
    - ReadWriteOnce

# Don't create a new StorageClass
storageClass:
  create: false
```

Install the chart:

```bash
helm install vm-agents ./vm-agents \
  --set persistence.enabled=true \
  --set persistence.storageClass=gp3 \
  --set persistence.size=20Gi
```

### Creating Custom StorageClass

If you want a custom StorageClass with specific parameters:

```yaml
# Enable custom StorageClass
storageClass:
  create: true
  name: "vm-agents-gp3"
  provisioner: "ebs.csi.aws.com"
  parameters:
    type: gp3
    fsType: ext4
    encrypted: "true"
    # Optional: Custom IOPS (io1/io2 only)
    # iops: "3000"
    # Optional: Custom throughput (gp3 only, 125-1000 MiB/s)
    # throughput: "250"
  allowVolumeExpansion: true
  reclaimPolicy: Delete
  volumeBindingMode: WaitForFirstConsumer

# Enable persistence using the custom StorageClass
persistence:
  enabled: true
  storageClass: "vm-agents-gp3"
  size: 20Gi
  mountPath: /data
```

Install with custom StorageClass:

```bash
helm install vm-agents ./vm-agents \
  --set persistence.enabled=true \
  --set storageClass.create=true \
  --set persistence.size=20Gi
```

## Storage Class Options

### EBS Volume Types

| Type | Use Case | IOPS | Throughput | Cost |
|------|----------|------|------------|------|
| **gp3** | General purpose (recommended) | 3,000-16,000 | 125-1,000 MiB/s | Low |
| **gp2** | General purpose (legacy) | 100-16,000 | Up to 250 MiB/s | Low |
| **io1** | High performance | Up to 64,000 | Up to 1,000 MiB/s | High |
| **io2** | High performance + durability | Up to 64,000 | Up to 1,000 MiB/s | Higher |
| **st1** | Throughput optimized (HDD) | N/A | Up to 500 MiB/s | Lower |
| **sc1** | Cold storage (HDD) | N/A | Up to 250 MiB/s | Lowest |

### Recommended Configuration

For most monitoring workloads:

```yaml
storageClass:
  parameters:
    type: gp3              # Best cost/performance ratio
    fsType: ext4           # Standard Linux filesystem
    encrypted: "true"      # Always encrypt at rest
    # throughput: "125"    # Default is fine for most cases
```

For high-performance requirements:

```yaml
storageClass:
  parameters:
    type: io2
    fsType: ext4
    encrypted: "true"
    iops: "10000"          # Higher IOPS for demanding workloads
```

## Verification

After installation, verify the resources:

```bash
# Check PVC status
kubectl get pvc

# Expected output:
# NAME             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
# vm-agents        Bound    pvc-xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx    10Gi       RWO            gp3            1m

# Check PV (automatically created)
kubectl get pv

# Check the volume mount in the pod
kubectl get pods
kubectl describe pod vm-agents-xxxxx | grep -A 5 "Mounts:"

# Verify data is persisted
kubectl exec -it vm-agents-xxxxx -- df -h /data
kubectl exec -it vm-agents-xxxxx -- ls -la /data
```

## Troubleshooting

### EBS CSI Driver Not Working

```bash
# Check driver logs
kubectl logs -n kube-system -l app=ebs-csi-controller

# Check node driver
kubectl logs -n kube-system -l app=ebs-csi-node
```

### PVC Stuck in Pending

```bash
# Check PVC events
kubectl describe pvc vm-agents

# Common issues:
# 1. EBS CSI driver not installed
# 2. IAM permissions missing
# 3. StorageClass doesn't exist
# 4. Volume size too small (minimum 1Gi)
```

### Volume Not Mounting

```bash
# Check pod events
kubectl describe pod vm-agents-xxxxx

# Check node where pod is scheduled
kubectl get pod vm-agents-xxxxx -o wide

# Check if EBS volume is attached to node
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/created-for/pvc/name,Values=vm-agents"
```

## Expanding Volume Size

If `allowVolumeExpansion: true` is set:

```bash
# Edit PVC to increase size
kubectl edit pvc vm-agents

# Change:
spec:
  resources:
    requests:
      storage: 20Gi  # Increase from 10Gi to 20Gi

# Wait for resize to complete
kubectl get pvc vm-agents -w

# Restart pod to reflect new size
kubectl rollout restart deployment vm-agents
```

## Backup and Restore

### Create EBS Snapshot

```bash
# Get PV name
PV_NAME=$(kubectl get pvc vm-agents -o jsonpath='{.spec.volumeName}')

# Get EBS volume ID
VOLUME_ID=$(kubectl get pv $PV_NAME -o jsonpath='{.spec.awsElasticBlockStore.volumeID}' | cut -d'/' -f4)

# Create snapshot
aws ec2 create-snapshot \
  --volume-id $VOLUME_ID \
  --description "vm-agents backup $(date +%Y-%m-%d)" \
  --tag-specifications "ResourceType=snapshot,Tags=[{Key=Name,Value=vm-agents-backup}]"
```

### Restore from Snapshot

```yaml
# Create PV from snapshot
apiVersion: v1
kind: PersistentVolume
metadata:
  name: vm-agents-restored
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: gp3
  awsElasticBlockStore:
    volumeID: vol-xxxxx  # Volume created from snapshot
    fsType: ext4
```

## Cost Optimization

1. **Use gp3 instead of gp2**: ~20% cheaper with better performance
2. **Right-size volumes**: Start small, expand as needed
3. **Use snapshots carefully**: Snapshots have storage costs
4. **Consider retention policy**: Use `Delete` for dev, `Retain` for prod
5. **Monitor unused volumes**: Delete PVs that are Released

## References

- [AWS EBS CSI Driver Documentation](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)
- [EBS Volume Types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-volume-types.html)
- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [EBS CSI Driver GitHub](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
