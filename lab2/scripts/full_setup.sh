#!/bin/bash
# =============================================================
#   Yelp Lab2 — Full End-to-End Setup (FROM SCRATCH)
#
#   Single script that builds the entire AWS deployment:
#     1. Creates EKS cluster + m7i-flex.large nodegroup
#     2. Installs OIDC, EBS CSI driver, AWS Load Balancer Controller
#     3. Tags subnets, opens security groups
#     4. Builds & pushes 6 Docker images to ECR
#     5. Deploys all manifests with shared SECRET_KEY
#     6. Adds Yelp API key as secret
#     7. Waits for NLBs, rebuilds frontend with public URL
#     8. Seeds 300 restaurants
#
#   Run:  bash lab2/scripts/full_setup.sh
#   Time: ~30-40 minutes
# =============================================================

set -e

# ── CONFIG ───────────────────────────────────────────────────
CLUSTER_NAME="yelp-lab2"
REGION="us-west-2"
NAMESPACE="yelp-lab2"
NODE_TYPE="m7i-flex.large"   # Free Plan eligible (paid tier instance)
NODE_COUNT=2
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/yelp-lab2"
K8S_DIR="lab2/k8s"

# Optional: paste your Yelp Fusion API key here to enable real Yelp data
YELP_API_KEY="${YELP_API_KEY:-}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
log()    { echo -e "${GREEN}✅ $1${NC}"; }
warn()   { echo -e "${YELLOW}⚠️  $1${NC}"; }
error()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
info()   { echo -e "${BLUE}ℹ️  $1${NC}"; }
header() { echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLUE}  $1${NC}"; echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }

# ── Pre-flight ────────────────────────────────────────────────
header "Pre-flight checks"
for tool in aws eksctl kubectl helm docker; do
  command -v $tool >/dev/null 2>&1 || error "$tool not found. Please install it."
done
aws sts get-caller-identity >/dev/null 2>&1 || error "AWS credentials invalid. Run 'aws configure'."
log "All tools present | Account: $ACCOUNT_ID | Region: $REGION"

# ── STEP 1: ECR repository ────────────────────────────────────
header "Step 1: Ensure ECR repository exists"
aws ecr describe-repositories --repository-names yelp-lab2 --region $REGION >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name yelp-lab2 --region $REGION >/dev/null
log "ECR repository ready"

# ── STEP 2: Login to ECR ──────────────────────────────────────
header "Step 2: Docker login to ECR"
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com >/dev/null
log "ECR login OK"

# ── STEP 3: Build & push images ───────────────────────────────
header "Step 3: Build and push 6 Docker images (~10-15 min)"

build_service () {
  local tag=$1 module=$2 port=$3
  info "Building $tag..."
  docker buildx build --platform linux/amd64 \
    -t ${ECR_REPO}:$tag \
    --build-arg APP_MODULE=$module \
    --build-arg APP_PORT=$port \
    -f lab2/docker/Dockerfile.service --push . > /dev/null 2>&1 \
    && log "$tag pushed" || error "$tag build failed"
}

build_service user-service       lab2.services.user_service.app:app       8001
build_service owner-service      lab2.services.owner_service.app:app      8002
build_service restaurant-service lab2.services.restaurant_service.app:app 8003
build_service review-service     lab2.services.review_service.app:app     8004

info "Building review-worker..."
docker buildx build --platform linux/amd64 \
  -t ${ECR_REPO}:review-worker \
  -f lab2/docker/Dockerfile.worker --push . > /dev/null 2>&1 && log "review-worker pushed"

# Frontend gets built TWICE: once with placeholder URL, then again after we know NLB DNS
info "Building frontend (placeholder URL — will rebuild after NLB exists)..."
docker buildx build --platform linux/amd64 \
  -t ${ECR_REPO}:frontend \
  --build-arg REACT_APP_API_URL=http://localhost:8000 \
  -f lab2/docker/Dockerfile.frontend --push . > /dev/null 2>&1 && log "frontend pushed (round 1)"

# ── STEP 4: Create EKS cluster ────────────────────────────────
header "Step 4: Create EKS cluster (~12-15 min)"

if aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.status" --output text 2>/dev/null | grep -q ACTIVE; then
  warn "Cluster already exists — skipping creation"
else
  info "Creating cluster '$CLUSTER_NAME'..."
  eksctl create cluster \
    --name $CLUSTER_NAME \
    --region $REGION \
    --version 1.34 \
    --without-nodegroup
  log "Cluster control plane ACTIVE"
fi

aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME --alias $CLUSTER_NAME >/dev/null
log "kubectl configured"

# ── STEP 5: Create nodegroup ──────────────────────────────────
header "Step 5: Create m7i-flex.large nodegroup"
if eksctl get nodegroup --cluster $CLUSTER_NAME --region $REGION 2>/dev/null | grep -q workers; then
  warn "Nodegroup already exists — skipping"
else
  eksctl create nodegroup \
    --cluster=$CLUSTER_NAME \
    --region=$REGION \
    --name=workers \
    --node-type=$NODE_TYPE \
    --nodes=$NODE_COUNT \
    --nodes-min=$NODE_COUNT \
    --nodes-max=$NODE_COUNT \
    --managed
  log "Nodegroup ready ($NODE_COUNT × $NODE_TYPE)"
fi

# ── STEP 6: Associate OIDC provider ───────────────────────────
header "Step 6: Associate OIDC provider"
eksctl utils associate-iam-oidc-provider --region=$REGION --cluster=$CLUSTER_NAME --approve 2>&1 | tail -1
log "OIDC ready"

# ── STEP 7: Install AWS Load Balancer Controller ──────────────
header "Step 7: Install AWS Load Balancer Controller"

# 7a: Download v2.11.0 IAM policy + extra perms (DescribeRouteTables not in v2.11 default)
curl -sSL https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.11.0/docs/install/iam_policy.json -o /tmp/iam_policy.json

# 7b: Create base policy if missing
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file:///tmp/iam_policy.json \
  --no-cli-pager 2>/dev/null && log "Base IAM policy created" || warn "Base IAM policy already exists"

# 7c: Create IRSA service account
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve \
  --region=$REGION 2>&1 | tail -1
log "Service account ready"

# 7d: Inline-attach the missing perms (DescribeRouteTables, DescribeNatGateways, DescribeVpcEndpoints)
cat > /tmp/extra_perms.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ec2:DescribeRouteTables", "ec2:DescribeNatGateways", "ec2:DescribeVpcEndpoints"],
    "Resource": "*"
  }]
}
EOF
aws iam put-role-policy --role-name AmazonEKSLoadBalancerControllerRole \
  --policy-name ExtraEC2DescribePerms --policy-document file:///tmp/extra_perms.json
log "Extra EC2 perms attached"

# 7e: Helm install with CORRECT VPC (the EKS-managed VPC, NOT the default VPC)
EKS_VPC=$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.resourcesVpcConfig.vpcId" --output text)
info "EKS VPC: $EKS_VPC"

helm repo add eks https://aws.github.io/eks-charts 2>/dev/null || true
helm repo update eks > /dev/null
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
sleep 5

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --set region=$REGION \
  --set vpcId=$EKS_VPC > /dev/null

kubectl rollout status deployment/aws-load-balancer-controller -n kube-system --timeout=180s
log "Load Balancer Controller running"

# ── STEP 8: Tag public subnets so the controller can place NLBs ───────
header "Step 8: Tag public subnets for ELB discovery"
PUBLIC_SUBNETS=$(aws ec2 describe-subnets --region $REGION \
  --filters "Name=vpc-id,Values=$EKS_VPC" "Name=map-public-ip-on-launch,Values=true" \
  --query "Subnets[*].SubnetId" --output text)
aws ec2 create-tags --region $REGION --resources $PUBLIC_SUBNETS \
  --tags Key=kubernetes.io/role/elb,Value=1
log "Tagged subnets: $PUBLIC_SUBNETS"

# ── STEP 9: Open node security group for NLB → pod traffic ────────────
header "Step 9: Open node SG for NLB ingress"
NODE_SG=$(aws ec2 describe-instances --region $REGION \
  --filters "Name=tag:eks:cluster-name,Values=$CLUSTER_NAME" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].SecurityGroups[0].GroupId" --output text)
VPC_CIDR=$(aws ec2 describe-vpcs --vpc-ids $EKS_VPC --region $REGION --query "Vpcs[0].CidrBlock" --output text)
info "Node SG: $NODE_SG | VPC CIDR: $VPC_CIDR"
aws ec2 authorize-security-group-ingress --region $REGION --group-id $NODE_SG \
  --protocol tcp --port 8000 --cidr $VPC_CIDR 2>/dev/null && log "Opened port 8000 from $VPC_CIDR" || warn "Port 8000 rule already exists"
aws ec2 authorize-security-group-ingress --region $REGION --group-id $NODE_SG \
  --protocol tcp --port 80 --cidr $VPC_CIDR 2>/dev/null && log "Opened port 80 from $VPC_CIDR" || warn "Port 80 rule already exists"

# ── STEP 10: Install EBS CSI driver (needed for MongoDB PVC) ──────────
header "Step 10: Install EBS CSI driver"
eksctl create iamserviceaccount \
  --name ebs-csi-controller-sa \
  --namespace kube-system \
  --cluster $CLUSTER_NAME \
  --region $REGION \
  --role-name AmazonEKS_EBS_CSI_DriverRole \
  --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
  --override-existing-serviceaccounts \
  --approve 2>&1 | tail -1

aws eks create-addon \
  --cluster-name $CLUSTER_NAME \
  --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::${ACCOUNT_ID}:role/AmazonEKS_EBS_CSI_DriverRole \
  --resolve-conflicts OVERWRITE \
  --region $REGION >/dev/null

aws eks wait addon-active --cluster-name $CLUSTER_NAME --addon-name aws-ebs-csi-driver --region $REGION
log "EBS CSI driver ready"

# Make gp2 the default storage class
kubectl patch storageclass gp2 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}' 2>/dev/null || true

# ── STEP 11: Deploy app stack ─────────────────────────────────────────
header "Step 11: Deploy application"
kubectl create namespace $NAMESPACE 2>/dev/null || true

# Patch ConfigMap to include shared SECRET_KEY (required: services share JWT secret)
kubectl apply -f $K8S_DIR/configmap-env.yaml
kubectl patch configmap yelp-lab2-env -n $NAMESPACE --type merge \
  -p '{"data":{"SECRET_KEY":"lab1-partner-jwt-secret-key-8x9k2m4n7p3q5"}}'

# Stateful infra first
kubectl apply -f $K8S_DIR/deployment-mongo.yaml
kubectl apply -f $K8S_DIR/deployment-zookeeper.yaml
kubectl apply -f $K8S_DIR/deployment-kafka.yaml
sleep 60

# All app services
kubectl apply -f $K8S_DIR/deployment-user-service.yaml
kubectl apply -f $K8S_DIR/deployment-owner-service.yaml
kubectl apply -f $K8S_DIR/deployment-restaurant-service.yaml
kubectl apply -f $K8S_DIR/deployment-review-service.yaml
kubectl apply -f $K8S_DIR/deployment-review-worker.yaml
kubectl apply -f $K8S_DIR/deployment-gateway.yaml
kubectl apply -f $K8S_DIR/deployment-frontend.yaml

# Inject SECRET_KEY into every service so JWT validation works across services
for svc in user-service owner-service restaurant-service review-service review-worker; do
  kubectl set env deployment/$svc -n $NAMESPACE --from=configmap/yelp-lab2-env --keys=SECRET_KEY 2>&1 | tail -1
done

# user-service must be 1 replica so profile photos don't disappear (uses local FS)
kubectl scale deployment/user-service -n $NAMESPACE --replicas=1
log "All services deployed"

# ── STEP 12: Optional Yelp API key ────────────────────────────────────
if [ -n "$YELP_API_KEY" ]; then
  header "Step 12: Add Yelp API key"
  kubectl create secret generic yelp-api-keys -n $NAMESPACE \
    --from-literal=YELP_API_KEY="$YELP_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -
  kubectl set env deployment/restaurant-service -n $NAMESPACE --from=secret/yelp-api-keys
  log "Yelp API key injected"
else
  warn "YELP_API_KEY not set in env — Yelp endpoints will return empty (graceful)"
fi

# ── STEP 13: Wait for all pods ────────────────────────────────────────
header "Step 13: Wait for all pods Ready"
until [ "$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | grep -v 'Running\|Completed' | wc -l | tr -d ' ')" = "0" ] \
  && [ "$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null | wc -l | tr -d ' ')" -ge "10" ]; do
  printf "."
  sleep 10
done
echo ""
kubectl get pods -n $NAMESPACE
log "All pods Ready"

# ── STEP 14: Wait for NLB DNS ─────────────────────────────────────────
header "Step 14: Wait for NLB public DNS"
until GW_URL=$(kubectl get svc gateway -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null) && [ -n "$GW_URL" ]; do
  printf "."
  sleep 10
done
echo ""
log "Gateway NLB: $GW_URL"

until FE_URL=$(kubectl get svc frontend -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null) && [ -n "$FE_URL" ]; do
  printf "."
  sleep 10
done
echo ""
log "Frontend NLB: $FE_URL"

# ── STEP 15: Rebuild frontend with real gateway URL ───────────────────
header "Step 15: Rebuild frontend with public gateway URL"
docker buildx build --no-cache --platform linux/amd64 \
  -t ${ECR_REPO}:frontend \
  --build-arg REACT_APP_API_URL=http://${GW_URL}:8000 \
  -f lab2/docker/Dockerfile.frontend --push . > /dev/null
kubectl rollout restart deployment/frontend -n $NAMESPACE
kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=180s
log "Frontend rebuilt with API URL: http://${GW_URL}:8000"

# ── STEP 16: Wait for NLB targets to be healthy ───────────────────────
header "Step 16: Wait for NLB targets to register healthy"
TG_GW=$(aws elbv2 describe-target-groups --region $REGION --query "TargetGroups[?contains(LoadBalancerArns[0], 'yelplab2-gateway')].TargetGroupArn" --output text | head -1)
until aws elbv2 describe-target-health --target-group-arn $TG_GW --region $REGION \
  --query "TargetHealthDescriptions[?TargetHealth.State=='healthy'] | length(@)" --output text | grep -v ^0$ >/dev/null 2>&1; do
  printf "."
  sleep 15
done
echo ""
log "Gateway target group healthy"

# ── STEP 17: Seed 300 restaurants ─────────────────────────────────────
header "Step 17: Seed database (300 restaurants + reviews)"
GATEWAY_API_URL="http://${GW_URL}:8000" python3 lab2/scripts/seed_data.py 2>&1 | tail -5

# ── DONE ──────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  🎉 DEPLOYMENT COMPLETE 🎉                     ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Frontend:  http://${FE_URL}${NC}"
echo -e "${GREEN}║  API:       http://${GW_URL}:8000${NC}"
echo -e "${GREEN}║  Login:     seed@yelp.com / Seed1234!                          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "After demo, run:  eksctl delete cluster --name $CLUSTER_NAME --region $REGION"
