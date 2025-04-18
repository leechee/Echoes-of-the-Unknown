# Makefile for UFO Sightings Project

# Docker build
build:
	docker build -t flask-api:latest -f Dockerfile .
	docker build -t worker:latest -f Dockerfile .

# Apply test configs
k8s-test:
	kubectl apply -f kubernetes/test/app-test-pvc-redis.yml
	kubectl apply -f kubernetes/test/app-test-deployment-redis.yml
	kubectl apply -f kubernetes/test/app-test-service-redis.yml
	kubectl apply -f kubernetes/test/app-test-deployment-flask.yml
	kubectl apply -f kubernetes/test/app-test-service-flask.yml
	kubectl apply -f kubernetes/test/app-test-service-nodeport-flask.yml
	kubectl apply -f kubernetes/test/app-test-deployment-worker.yml
	kubectl apply -f kubernetes/test/app-test-ingress-flask.yml

# Apply prod configs
k8s-prod:
	kubectl apply -f kubernetes/prod/app-prod-pvc-redis.yml
	kubectl apply -f kubernetes/prod/app-prod-deployment-redis.yml
	kubectl apply -f kubernetes/prod/app-prod-service-redis.yml
	kubectl apply -f kubernetes/prod/app-prod-deployment-flask.yml
	kubectl apply -f kubernetes/prod/app-prod-service-flask.yml
	kubectl apply -f kubernetes/prod/app-prod-service-nodeport-flask.yml
	kubectl apply -f kubernetes/prod/app-prod-deployment-worker.yml
	kubectl apply -f kubernetes/prod/app-prod-ingress-flask.yml

# Clean all Kubernetes resources in test
k8s-clean-test:
	kubectl delete -f kubernetes/test --ignore-not-found=true

# Clean all Kubernetes resources in prod
k8s-clean-prod:
	kubectl delete -f kubernetes/prod --ignore-not-found=true

# Show Flask service URL in test environment (minikube only)
open-test:
	minikube service flask-api-nodeport-test

# Show Flask service URL in prod environment (minikube only)
open-prod:
	minikube service flask-api-nodeport-prod