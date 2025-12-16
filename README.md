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

## Create kubernetes cluster (kind)
See [kind - quick-start](https://kind.sigs.k8s.io/docs/user/quick-start/#installing-from-release-binaries) for installation instructions

The kind cluster has:
- one control-plane node with extraPortMappings:
    - host port 80 mapped to control-plane container port 80
    - host port 443 mapped to control-plane container port 443
- two worker nodes

The configuration of the kind cluster is specified in file [kind-config.yaml](./kind-config.yaml)

Creat the kind cluster:
```
kind create cluste --config kind-config.yaml
```

Next the **NGINX Ingress Controller** should be deployed on the kind cluster to make deployed service available. The NGINX Ingress Controller project maintains a specific manifest for deployment on kind clusters.

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

