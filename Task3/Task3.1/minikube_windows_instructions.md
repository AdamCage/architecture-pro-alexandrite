# Minikube (Windows) — короткая инструкция для Task 3.1

Проверено в **PowerShell**.

## 1) Старт Minikube
```powershell
minikube start --addons=ingress
````

## 2) Cert-manager

```powershell
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

kubectl -n cert-manager wait --for=condition=Available deployment/cert-manager --timeout=300s
kubectl -n cert-manager wait --for=condition=Available deployment/cert-manager-webhook --timeout=300s
kubectl -n cert-manager wait --for=condition=Available deployment/cert-manager-cainjector --timeout=300s
```

## 3) Jaeger Operator + Jaeger instance

```powershell
kubectl create namespace observability

kubectl apply -n observability -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml
kubectl -n observability rollout status deploy/jaeger-operator --timeout=300s

kubectl apply -f .\k8s\jaeger-instance.yaml
```

## 4) Сервисы (service-a вызывает service-b) + OpenTelemetry

Собираем образы прямо в Docker окружении Minikube:

```powershell
minikube image build -t service-a:latest .\services\service-a
minikube image build -t service-b:latest .\services\service-b
```

Деплоим сервисы:

```powershell
kubectl apply -f .\k8s\services.yaml
kubectl get pods
```

## 5) Генерируем трейс

В pod `service-a` может не быть `wget`, поэтому используем **port-forward** и запрос с хоста.

Окно 1:

```powershell
kubectl port-forward svc/service-a 18080:8080
```

Окно 2 (любой вариант):

```powershell
Invoke-RestMethod http://localhost:18080/
# или (важно: именно curl.exe, а не PowerShell-алиас)
curl.exe -s http://localhost:18080/
```

## 6) Jaeger UI

Окно 3:

```powershell
kubectl port-forward svc/simplest-query 16686:16686
```

Открыть в браузере:

* [http://localhost:16686](http://localhost:16686)
