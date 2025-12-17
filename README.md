# Devops

`Python-App` is a very simple python API application using Flask

## Application code
See [app.py](src/app.py) in `src` folder

## Create virtual environment
```
python3 -m venv venv
source venv/bin activate
```

## Import the dependencies
```
pip3 install -r requirements.txt
```

## Run application
```
cd src
python3 app.py
```

Browser: URL = 
- `http://localhost:5000/api/v1/details`
- `http://localhost:5000/api/v1/healthz`

## Create container image and push to Docker Hub
See [Dockerfile](Dockerfile) (Bind to all interface `0.0.0.0` otherwise it will not work)

In Docker Hub create a repository for `python-app` docker image and a Personal Access Token (PAT) with read/write permissions.

Build a `python-app` container image from [Dockerfile](./Dockerfile), Log into Docker Hub, Tag the container image for Docker Hub and push the container image to Docker Hub:

```
docker build -t python-app:v1.0.0 .
docker login -u janhaans (and use PAT for password)
docker tag python-app:v1.0.0 janhaans/python-app:v1.0.0
docker push janhaans/python-app:v1.0.0
```

## Run container image
```
docker run -d -p 8080:5000 --name app janhaans/python-app:v1.0.0
```

Browser: URL = 
- `http://localhost:8080/api/v1/details`
- `http://localhost:8080/api/v1/healthz`


## Create kubernetes cluster (kind)
See [kind - quick-start](https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries) for installation instructions

The kind kubernetes cluster has:
- one control-plane node with extraPortMappings:
    - host port 80 mapped to control-plane container port 80
    - host port 443 mapped to control-plane container port 443
- two worker nodes

The configuration of the kind cluster is specified in file [kind-config.yaml](./kind-config.yaml)

Create a kubernetes cluster with kind:
```
kind create cluster --config kind-config.yaml
```

Do a check if the cluster nodes are running
```
kubectl get nodes
```

## Run program `cloud-provider-kind`

First install this application with go:
```
go install sigs.k8s.io/cloud-provider-kind@latest
```

If go is not installed on Ubuntu, then install go before you install the application with go:
```
sudo snap install --classic go
```
When `cloud-provider-kind` has been installed, then run the program:
```
~/go/bin/cloud-provider-kind
```

This application will create ingress controller with name `cloud-provider-kind` and controller `kind.sigs.k8s.io/ingress-controller` (see `kubect get ingressclass`).
When this application is running you can also create a Service of type Loadbalancer (see [kind - loadbalancer](https://kind.sigs.k8s.io/docs/user/loadbalancer/))


## Deploy python-app on Kubernetes
Apply the Kubernetes manifests file `k8s/python-app.yaml` that deploy `python-app`, expose it as a ClusterIP service, and make it reachable through the `cloud-provider-kind` ingress controller:
```
kubectl apply -f k8s/python-app.yaml
```

Wait until the controller reports that the pods are ready:
```
kubectl wait --namespace python-app \
  --for=condition=ready pod \
  --selector=app=python-app \
  --timeout=90s
```

Inspect the deployment, service, pods and ingress to confirm these kubernetes resources exist:
```
kubectl get all -n python-app
kubectl get ingress -n python-app
```

The latest command will show the IP address that can be used from the host to access the application.

Browser: URL = 
- `http://<IP>/api/v1/details`
- `http://<IP>/api/v1/healthz`

Another option to access application `python-app` and bypass the ingress controller is port-forwarding
```
kubectl port-forward -n python-app service/python-app 8080
```

Browser: URL = 
- `http://localhost:8080/api/v1/details`
- `http://localhost:8080/api/v1/healthz`


## Delete python-app from Kubernetes
```
kubectl delete -f k8s/python-app
```

## Deploy python-app with Helm

Install Helm on Ubuntu 25:
```
sudo snap install --classic helm
```

Instead of applying the raw manifest, use the Helm chart in [`helm/python-app`](helm/python-app) which packages the same Deployment, Service, and Ingress resources and defaults to the `cloud-provider-kind` ingress class.

Install or upgrade the release into the `python-app` namespace (Helm will create it when the flag is used):
```
helm install python-app helm/python-app \
  --namespace python-app \
  --create-namespace
```

Get the status of the Helm release:
```
helm status list -n python-app
```

The defaults roll out two replicas of the `janhaans/python-app:v1.0.4` image, expose the service on port 8080 (targeting container port 5000), and create an ingress that serves `/`. After installation, wait for the pods to become ready and check the ingress IP that `cloud-provider-kind` assigns:
```
kubectl wait --namespace python-app \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/name=python-app \
  --timeout=90s
kubectl get ingress -n python-app
```

Use the reported address to reach the application (or port-forward the service as shown above):
```
curl http://<IP>/api/v1/healthz
curl http://<IP>/api/v1/details
```

## Delete python-app with Helm
```
helm uninstall python-app -n python-app
```
