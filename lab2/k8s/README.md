# Kubernetes (AWS EKS example)

1. Build and push images to ECR (one image per service using `lab2/docker/Dockerfile.service` with different `APP_MODULE` / `APP_PORT` build args — or four small Dockerfiles).
2. Create secrets for `DATABASE_URL`, `SECRET_KEY`, `MONGODB_URL`, API keys:
   `kubectl create secret generic yelp-secrets -n yelp-lab2 --from-literal=DATABASE_URL=...`
3. Apply manifests: `kubectl apply -f lab2/k8s/`
4. Install Kafka (e.g. Strimzi operator or Helm `bitnami/kafka`) in the same namespace; set `KAFKA_BOOTSTRAP_SERVERS` to the cluster service DNS name.
5. Expose the **gateway** (nginx) or individual services via **Ingress** or **LoadBalancer**; capture screenshots for the report.

Replace `REPLACE_WITH_ECR_OR_DOCKERHUB/...` image references before apply.
