# AWS deployment (for report screenshots)

Capture and paste into `LabPair-##_Lab2_Report.pdf`:

1. EKS (or kops/minikube on EC2) **kubectl get pods -n yelp-lab2** showing all services Running.  
2. **Services / Ingress** exposing the gateway or load balancer DNS.  
3. Optional: **MSK** or self-hosted Kafka broker status if used instead of in-cluster Kafka.

Replace image names in [../k8s/](../k8s/) with your ECR URLs before apply.
