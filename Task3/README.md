# Task 3.1 — OpenTelemetry + Jaeger (Kubernetes MVP)

В этом MVP два сервиса:
- **service-a** (REST `GET /`) — вызывает **service-b**
- **service-b** (REST `GET /`) — возвращает простой ответ

Оба сервиса инструментированы OpenTelemetry SDK так, чтобы **вызов service-a → service-b попадал в один trace** и отображался в Jaeger UI.

## 1) Поднять Jaeger (оператор + инстанс)

```bash
minikube start

# Установить Jaeger Operator и CRD (создаёт namespace observability)
kubectl apply -f k8s/services.yaml

# Создать Jaeger instance (all-in-one)
kubectl apply -f k8s/jaeger-instance.yaml

kubectl -n observability get pods
```

## 2) Собрать образы внутри Minikube

> Используем `minikube image build`, чтобы не пушить образы в registry.

```bash
minikube image build -t service-b:latest ./service-b
minikube image build -t service-a:latest ./service-a
```

## 3) Деплой сервисов

```bash
kubectl apply -f k8s/apps.yaml
kubectl get pods
```

## 4) Проверка вызова (service-a вызывает service-b)

```bash
kubectl exec -it $(kubectl get pods -l app=service-a -o jsonpath='{.items[0].metadata.name}') -- \
  wget -qO- http://service-a:8080
```

## 5) Открыть Jaeger UI

```bash
kubectl port-forward -n observability svc/simplest-query 16686:16686
```

Откройте в браузере: http://localhost:16686/

Далее:
1. В поле **Service** выберите `service-a`.
2. Нажмите **Find Traces**.
3. Откройте trace — внутри должны быть спаны по входящему запросу в service-a и по HTTP-вызову в service-b.

Скриншот положите рядом с этим README (например, `jaeger-trace.png`).
