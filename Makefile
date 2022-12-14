.PHONY: build_app
build_app:
	docker build traffic_pod_autoscaler -t ops-club/traffic_pod_autoscaler:latest --no-cache

.PHONY: k_apply
k_apply:
	kubectl apply -f example --recursive

.PHONY: k_delete
k_delete:
	kubectl delete deploy frontend -n webapp
	kubectl delete deploy traffic-pod-autoscaler -n webapp
	kubectl delete deploy redis-replica -n webapp
	kubectl delete deploy redis-master -n webapp
	kubectl delete ingress webapp-ingress -n webapp

.PHONY: k_namespace
k_namespace:
	kubectl config set-context --current --namespace=webapp

.PHONY: k_ingress_logs
k_ingress_logs:
	kubectl  logs -n ingress-nginx -f ingress-nginx-controller-AAAAAAA

.PHONY: k_ingress_forward
k_ingress_forward:
	kubectl port-forward --namespace=ingress-nginx service/ingress-nginx-controller --address 0.0.0.0 9000:80
