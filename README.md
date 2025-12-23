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

## Install Argo CD on kind

Install the official Argo CD Helm chart with the custom values provided in [`helm/argocd/values.yaml`](helm/argocd/values.yaml). These values keep the components at a single replica on kind, disable Redis HA, and configure the `argocd-server` service as a LoadBalancer so the `cloud-provider-kind` process can assign it an IP.

```
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd \
  --namespace argocd \
  --create-namespace \
  -f helm/argocd/values.yaml
```

Wait for the pods to become ready:

```
kubectl wait -n argocd --for=condition=ready pod --all --timeout=120s
```

List the LoadBalancer service to grab the external IP assigned by `cloud-provider-kind`:

```
kubectl get svc -n argocd argocd-server
```

In file `/etc/hosts` assign this IP address to domain `argocd.example.com` (see [values.yaml](helm/argocd/values.yaml)):

```
<IP> argocd.example.com
```

Use that domain to open the Argo CD UI.

Browser: URL =

- `http://argocd.example.com`

Retrieve the initial admin password with:

```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

## Configure ArgoCD Application for python-app

After accessing the ArgoCD UI at `https://argocd.example.com`, configure an Application to automatically deploy the python-app using the Helm chart from this GitHub repository.

### Step 1: Login to ArgoCD UI

1. Open browser and navigate to `https://argocd.example.com`
2. Login with:
   - **Username**: `admin`
   - **Password**: Use the command above to retrieve the initial password

### Step 2: Configure Repository Access (if needed)

**For Public Repositories**: No additional configuration needed - ArgoCD can directly access public GitHub repositories.

**For Private Repositories**: Configure repository credentials first:

1. In ArgoCD UI, go to **Settings** → **Repositories**
2. Click **"CONNECT REPO"**
3. Fill in:
   - **Type**: `git`
   - **Repository URL**: `https://github.com/janhaans/python-app.git`
   - **Username**: Your GitHub username
   - **Password**: GitHub Personal Access Token (PAT) with repo access
4. Click **"CONNECT"** to test and save

### Step 3: Create New Application

1. Click **"+ NEW APP"** button in the ArgoCD UI
2. Fill in the **General** section:
   - **Application Name**: `python-app`
   - **Project Name**: `default`
   - **Sync Policy**: `Manual` (or `Automatic` for auto-sync)

### Step 4: Configure Source Repository

In the **Source** section:

- **Repository URL**: `https://github.com/janhaans/python-app.git`
- **Revision**: `HEAD` (or specify branch like `main`)
- **Path**: `helm/python-app`

### Step 5: Configure Destination

In the **Destination** section:

- **Cluster URL**: `https://kubernetes.default.svc` (in-cluster)
- **Namespace**: `python-app`

### Step 6: Configure Helm Parameters (Optional)

In the **Helm** section, you can override default values:

- **Values Files**: Leave default or specify custom values
- **Parameters**: Add any custom Helm values if needed, for example:
  - `image.tag`: `latest` (to use latest image)
  - `replicaCount`: `3` (to override replica count)

### Step 7: Create and Sync Application

1. Click **"CREATE"** to create the application
2. The application will appear in "OutOfSync" status
3. Click on the application name to view details
4. Click **"SYNC"** button to deploy the application
5. Optionally click **"SYNC OPTIONS"** → **"REPLACE"** for force sync

### Step 8: Verify Deployment

After successful sync:

1. Check ArgoCD shows green "Synced" and "Healthy" status
2. Verify pods are running:
   ```
   kubectl get pods -n python-app
   kubectl get ingress -n python-app
   ```
3. Access the application:
   ```
   curl http://<INGRESS-IP>/api/v1/healthz
   curl http://<INGRESS-IP>/api/v1/details
   ```

### Auto-Sync Configuration (Optional)

To enable automatic synchronization when GitHub repository changes:

1. In ArgoCD UI, click on the `python-app` application
2. Click **"APP DETAILS"** → **"EDIT"**
3. Under **Sync Policy**, select **"AUTOMATIC"**
4. Enable **"PRUNE RESOURCES"** and **"SELF HEAL"** for complete GitOps workflow
5. Click **"SAVE"**

Now ArgoCD will automatically detect changes to the Helm chart in your GitHub repository and deploy updates to the kind cluster.

## Actions Runner Controller (ACR)

Use **Actions Runner Controller (ARC)** to run a GitHub Actions runner inside your Kubernetes cluster. The runner pod (living inside the cluster) will initiate an outbound HTTPS connection to GitHub. This allows it to receive jobs without you ever needing to expose the Kubernetes API server to the internet.

See [Actions Runner Controller](https://docs.github.com/en/actions/tutorials/use-actions-runner-controller/quickstart) for more information.

By running the runner inside the cluster, the runner can communicate with the Kubernetes API using its ServiceAccount tokens. It uses local networking to deploy your Helm charts.

Components:

- **Controller**: A manager that monitors GitHub for pending jobs.
- **Runner Scale Sets**: Dynamically created pods that execute the actual workflow steps.
- **Authentication**: Usually handled via a GitHub App or a Personal Access Token (PAT).

### Prerequisites

Before starting, ensure you have:

- Helm installed locally.
- A GitHub Personal Access Token (PAT) with repo scopes (or a GitHub App for better security).
- Your Kind cluster running

### Installation

#### Install ARC Controller

```
NAMESPACE="arc-systems"
helm install arc \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set-controller

```

#### Configure Runner Scale Set

To configure your runner scale set, run the following command in your terminal:

```
INSTALLATION_NAME="arc-runner-set"
NAMESPACE="arc-runners"
GITHUB_CONFIG_URL="https://github.com/janhaans/python-app"
GITHUB_PAT="<PAT>"
helm install "${INSTALLATION_NAME}" \
    --namespace "${NAMESPACE}" \
    --create-namespace \
    --set githubConfigUrl="${GITHUB_CONFIG_URL}" \
    --set githubConfigSecret.github_token="${GITHUB_PAT}" \
    oci://ghcr.io/actions/actions-runner-controller-charts/gha-runner-scale-set

```

#### Verify Installation

```
helm list -A
```

You should see something similar to:

```
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS       CHART                                    APP VERSION
arc             arc-system      1               2025-12-23 12:14:48.935814 +0100 CET    deployed        gha-runner-scale-set-controller-0.13.0   0.13.0
arc-runner-set  arc-runners     1               2025-12-23 12:29:56.173153 +0100 CET    deployed        gha-runner-scale-set-0.13.0              0.13.0
```

To check the manager pod, run the following command in your terminal.

```
kubectl get pods -n arc-system
```

You shoild see something similar to:

```
NAME                                     READY   STATUS    RESTARTS   AGE
arc-gha-rs-controller-645dfd698b-tbbjp   1/1     Running   0          55m
arc-runner-set-754b578d-listener         1/1     Running   0          40m
```

### Test

When configuring the Runner Scale Set an [GitHub Actions test workflow](.github/workflow/test-runner.yml) has been created.

Before testing the workflow give the runner service account the permissions to access Kubernetes API
