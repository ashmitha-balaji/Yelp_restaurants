#!/bin/bash
# =============================================================
#   Yelp Lab2 — Full Cleanup
#
#   Deletes EVERYTHING:
#     - EKS cluster (control plane + nodegroup + IAM roles)
#     - All NLBs (active + orphans in default VPC)
#     - All EBS volumes (via cluster delete)
#     - ECR images (optional)
#
#   Run:  bash lab2/scripts/delete_all.sh
#   Time: ~10-15 minutes
# =============================================================

set -e

CLUSTER_NAME="yelp-lab2"
REGION="us-west-2"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
log()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()   { echo -e "${YELLOW}⚠️  $1${NC}"; }
header() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── STEP 1: Delete any orphan NLBs (in default VPC from bug-fix history) ──
header "Step 1: Delete orphan NLBs"
ORPHAN_LBS=$(aws elbv2 describe-load-balancers --region $REGION \
  --query "LoadBalancers[?contains(LoadBalancerName, 'yelplab2')].LoadBalancerArn" --output text)
for arn in $ORPHAN_LBS; do
  name=$(echo $arn | awk -F/ '{print $(NF-1)}')
  aws elbv2 delete-load-balancer --load-balancer-arn $arn --region $REGION 2>/dev/null && log "Deleted: $name"
done

# ── STEP 2: Delete LoadBalancer services first (so Mongo PVC drains cleanly) ──
header "Step 2: Delete app services to free LBs"
kubectl delete svc gateway frontend -n yelp-lab2 2>/dev/null || true
sleep 10

# ── STEP 3: Delete the cluster (this cascades — nodes, NLBs, EBS) ──
header "Step 3: Delete EKS cluster"
warn "This takes ~10-15 minutes..."
eksctl delete cluster --name $CLUSTER_NAME --region $REGION --wait

# ── STEP 4: Verify ──
header "Step 4: Verify everything is gone"
echo "Clusters:"
aws eks list-clusters --region $REGION --output table
echo ""
echo "EC2 instances tagged for $CLUSTER_NAME:"
aws ec2 describe-instances --region $REGION \
  --filters "Name=tag:eks:cluster-name,Values=$CLUSTER_NAME" "Name=instance-state-name,Values=running,pending" \
  --query "Reservations[].Instances[].[InstanceId,State.Name]" --output table
echo ""
echo "Load balancers:"
aws elbv2 describe-load-balancers --region $REGION \
  --query "LoadBalancers[?contains(LoadBalancerName, 'yelplab2')].LoadBalancerName" --output table

# ── STEP 5: Optionally delete ECR images ──
header "Step 5: Delete ECR images (saves ~\$0.18/month)"
read -p "Delete ECR repository 'yelp-lab2'? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  aws ecr delete-repository --repository-name yelp-lab2 --region $REGION --force
  log "ECR repository deleted"
else
  warn "ECR images kept — they'll save build time on next setup"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🧹 CLEANUP COMPLETE 🧹                      ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  AWS billing for this lab has stopped.               ║${NC}"
echo -e "${GREEN}║                                                      ║${NC}"
echo -e "${GREEN}║  To rebuild tomorrow:                                ║${NC}"
echo -e "${GREEN}║    bash lab2/scripts/full_setup.sh                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
