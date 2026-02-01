---
name: kubernetes-deployer
description: |
  Deploy and scale containerized applications on Kubernetes from hello world to production systems.
  Use when creating deployments, services, ingress, configmaps, secrets, scaling applications,
  setting up health probes, managing resources, or troubleshooting Kubernetes workloads.
  Covers all workload types (Deployments, StatefulSets, DaemonSets, Jobs, CronJobs), networking
  (Services, Ingress), configuration (ConfigMaps, Secrets), autoscaling (HPA), and production
  best practices. NOT for Docker/container building (use containerizing skill) or cloud provider
  specific setup (use cloud-specific skills).
---

# Kubernetes Deployer

Deploy and scale containerized applications from hello world to production-grade systems.

## Quick Reference

### Project Levels

| Level | Features | Use Case |
|-------|----------|----------|
| 1 | Single Pod, basic Service | Learning, demos |
| 2 | Deployment with replicas, ConfigMaps | Simple apps |
| 3 | Full stack: Deployment, Service, Ingress, Secrets | Standard production |
| 4 | HPA, resource limits, health probes, multi-env | Professional production |
| 5 | StatefulSets, multi-zone, security policies | Enterprise production |

---

## How Kubernetes Works: The Reconciliation Loop

Kubernetes uses a **declarative model** - you describe the desired state, and controllers continuously work to make reality match that state.

### Control Plane Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CONTROL PLANE                                     │
│                                                                              │
│   ┌─────────────┐      ┌──────────────────┐      ┌─────────────────────┐   │
│   │   kubectl   │─────▶│    API SERVER    │◀────▶│        etcd         │   │
│   │   (client)  │      │                  │      │   (cluster state)   │   │
│   └─────────────┘      │  - Auth/Authz    │      │                     │   │
│                        │  - Validation    │      │  - Desired state    │   │
│                        │  - REST API      │      │  - Current state    │   │
│                        │  - Watch/Notify  │      │  - Distributed KV   │   │
│                        └────────┬─────────┘      └─────────────────────┘   │
│                                 │                                           │
│            ┌────────────────────┼────────────────────┐                     │
│            │                    │                    │                      │
│            ▼                    ▼                    ▼                      │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐           │
│   │   CONTROLLER    │  │    SCHEDULER    │  │  CLOUD          │           │
│   │   MANAGER       │  │                 │  │  CONTROLLER     │           │
│   │                 │  │  - Node select  │  │  MANAGER        │           │
│   │  - Deployment   │  │  - Resource fit │  │                 │           │
│   │  - ReplicaSet   │  │  - Affinity     │  │  - LoadBalancer │           │
│   │  - StatefulSet  │  │  - Taints       │  │  - Node lifecycle│          │
│   │  - DaemonSet    │  │  - Priorities   │  │  - Cloud routes │           │
│   │  - Job          │  │                 │  │                 │           │
│   │  - Endpoints    │  │                 │  │                 │           │
│   │  - Namespace    │  │                 │  │                 │           │
│   │  - ServiceAcct  │  │                 │  │                 │           │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### etcd - The Source of Truth

**Role**: Distributed key-value store holding all cluster state

**Responsibilities**:
- Stores desired state (what you declared in YAML)
- Stores current state (what's actually running)
- Provides consistency guarantees (Raft consensus)
- Supports watch notifications for changes

**Key insight**: etcd is the ONLY stateful component. If etcd is lost, cluster state is lost.

```bash
# etcd stores data like:
/registry/deployments/default/myapp     → Deployment spec + status
/registry/pods/default/myapp-xyz-123    → Pod spec + status
/registry/services/default/myapp        → Service spec
```

#### API Server - The Gateway

**Role**: Central hub - ALL communication goes through it

**Responsibilities**:
- REST API endpoint for all operations (kubectl, controllers, kubelets)
- Authentication (who are you?) and Authorization (can you do this?)
- Admission control (should this be allowed? modify it?)
- Validation (is this YAML valid?)
- Persists objects to etcd
- Watch mechanism - notifies subscribers of changes

**Key insight**: Components NEVER talk directly to each other. Everything goes through API server.

```bash
# All these use the API server:
kubectl apply -f deployment.yaml        # Client → API Server → etcd
controller watches Deployments          # Controller → API Server (watch)
kubelet reports pod status              # Kubelet → API Server → etcd
```

#### Controller Manager - The Brain

**Role**: Runs all built-in controllers as a single process

**Responsibilities**:
- Deployment Controller: manages ReplicaSets for Deployments
- ReplicaSet Controller: ensures correct number of pod replicas
- StatefulSet Controller: manages stateful workloads
- DaemonSet Controller: ensures pods on all/selected nodes
- Job Controller: manages batch jobs
- Endpoints Controller: populates Service endpoints
- Namespace Controller: handles namespace lifecycle
- ServiceAccount Controller: creates default accounts

**Key insight**: Each controller watches specific resources via API server and reconciles.

```bash
# Example: Deployment Controller logic
watch(Deployments)
for each Deployment:
    currentRS = list ReplicaSets owned by this Deployment
    desiredRS = compute from Deployment spec
    if currentRS != desiredRS:
        create/update/delete ReplicaSets
        update Deployment status
```

#### Scheduler - The Matchmaker

**Role**: Assigns Pods to Nodes

**Responsibilities**:
- Watches for Pods with no `nodeName` (unscheduled)
- Filters nodes (which CAN run this pod?)
  - Sufficient CPU/memory?
  - Node selectors match?
  - Tolerates node taints?
  - Meets affinity rules?
- Scores nodes (which SHOULD run this pod?)
  - Resource balance
  - Affinity preferences
  - Custom priorities
- Binds Pod to highest-scoring Node (sets `nodeName`)

**Key insight**: Scheduler only DECIDES where pods go. Kubelet actually runs them.

```bash
# Scheduling decision flow:
1. Pod created with nodeName=""
2. Scheduler sees unscheduled Pod
3. Filter: nodes A, B, C can run it; D cannot (not enough memory)
4. Score: A=80, B=95, C=70
5. Bind: set pod.spec.nodeName = "B"
```

### How Components Collaborate

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RECONCILIATION FLOW EXAMPLE                           │
│                                                                          │
│  User: kubectl apply -f deployment.yaml (replicas: 3)                   │
│                                                                          │
│  ┌────────┐  1. POST /apis/apps/v1/deployments                          │
│  │kubectl │────────────────────────────────────────▶┌───────────┐       │
│  └────────┘                                         │ API Server│       │
│                                                     └─────┬─────┘       │
│                                                           │             │
│  ┌──────┐  2. Store Deployment                           │             │
│  │ etcd │◀───────────────────────────────────────────────┘             │
│  └──────┘                                                               │
│      │                                                                  │
│      │ 3. Notify watchers: "new Deployment"                            │
│      ▼                                                                  │
│  ┌────────────────────┐                                                 │
│  │ Deployment         │  4. Create ReplicaSet                          │
│  │ Controller         │─────────────────────────────▶ API Server       │
│  └────────────────────┘                                   │             │
│                                                           │             │
│  etcd ◀───────────────────────────────────────────────────┘             │
│      │                                                                  │
│      │ 5. Notify: "new ReplicaSet"                                     │
│      ▼                                                                  │
│  ┌────────────────────┐                                                 │
│  │ ReplicaSet         │  6. Create 3 Pods                              │
│  │ Controller         │─────────────────────────────▶ API Server       │
│  └────────────────────┘                                   │             │
│                                                           │             │
│  etcd ◀───────────────────────────────────────────────────┘             │
│      │                                                                  │
│      │ 7. Notify: "3 unscheduled Pods"                                 │
│      ▼                                                                  │
│  ┌────────────────────┐                                                 │
│  │ Scheduler          │  8. Bind pods to nodes                         │
│  │                    │─────────────────────────────▶ API Server       │
│  └────────────────────┘                                   │             │
│                                                           │             │
│  etcd ◀───────────────────────────────────────────────────┘             │
│      │                                                                  │
│      │ 9. Notify: "Pods assigned to nodes"                             │
│      ▼                                                                  │
│  ┌────────────────────┐     ┌───────────────┐                          │
│  │ Kubelet (per node) │────▶│ Container     │  10. Pull image,        │
│  │                    │     │ Runtime       │      start container     │
│  └────────────────────┘     └───────────────┘                          │
│      │                                                                  │
│      │ 11. Report pod status                                           │
│      ▼                                                                  │
│  API Server ──────▶ etcd (update pod.status)                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Control Loop Pattern

Every Kubernetes controller runs the same basic loop:

```
┌─────────────────────────────────────────────────┐
│  1. OBSERVE   →   2. COMPARE   →   3. ACT      │
│  (current)        (vs desired)     (reconcile)  │
│       ↑                                  │      │
│       └──────────────────────────────────┘      │
│                    repeat                        │
└─────────────────────────────────────────────────┘
```

This is the **reconciliation loop** - the core mechanism that makes Kubernetes self-healing.

### Controller Chain: Deployment → ReplicaSet → Pod → Container

When you apply a Deployment, multiple controllers work together:

```
┌──────────────────────────────────────────────────────────────────┐
│                        CONTROL PLANE                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────┐    ┌─────────────────────┐              │
│  │ Deployment          │    │ ReplicaSet          │              │
│  │ Controller          │───▶│ Controller          │              │
│  │                     │    │                     │              │
│  │ Watches: Deployment │    │ Watches: ReplicaSet │              │
│  │ Creates: ReplicaSet │    │ Creates: Pods       │              │
│  └─────────────────────┘    └─────────────────────┘              │
│                                       │                          │
│                                       ▼                          │
│                             ┌─────────────────────┐              │
│                             │ Scheduler           │              │
│                             │                     │              │
│                             │ Watches: Unassigned │              │
│                             │          Pods       │              │
│                             │ Assigns: Node       │              │
│                             └─────────────────────┘              │
│                                       │                          │
└───────────────────────────────────────┼──────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────┐
│                           NODE                                     │
├───────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────┐              │
│  │ Kubelet             │───▶│ Container Runtime   │              │
│  │                     │    │ (containerd/Docker) │              │
│  │ Watches: Pods       │    │                     │              │
│  │ assigned to node    │    │ Runs: Containers    │              │
│  └─────────────────────┘    └─────────────────────┘              │
└───────────────────────────────────────────────────────────────────┘
```

### Step-by-Step: What Happens When You `kubectl apply -f deployment.yaml`

1. **API Server** receives and validates the Deployment, stores it in **etcd**

2. **Deployment Controller** (watching Deployments):
   - Sees new Deployment
   - Creates a ReplicaSet with matching pod template
   - Manages rollouts, rollbacks, scaling strategy

3. **ReplicaSet Controller** (watching ReplicaSets):
   - Sees new ReplicaSet with `replicas: 3`
   - Current pods = 0, desired = 3
   - Creates 3 Pod objects (not running yet, just API objects)

4. **Scheduler** (watching Pods with no `nodeName`):
   - Sees 3 unscheduled Pods
   - Evaluates nodes: resources, taints, affinity, etc.
   - Assigns each Pod to a node (sets `nodeName`)

5. **Kubelet** on each assigned node (watching Pods for its node):
   - Sees Pod assigned to it
   - Pulls image via container runtime
   - Starts containers
   - Reports status back to API server

### Why This Architecture Matters

**Self-healing**: If a Pod dies, the ReplicaSet controller notices (current < desired) and creates a replacement.

**Declarative**: You don't say "start 3 containers" - you say "I want 3 replicas" and controllers figure out how.

**Distributed**: Each controller handles one concern. They communicate only through the API server.

**Idempotent**: Controllers can crash and restart. They re-read state and continue reconciling.

### Observing the Reconciliation

```bash
# Watch controllers in action
kubectl get events -w

# See controller decisions
kubectl describe deployment myapp
kubectl describe replicaset myapp-xxxxx
kubectl describe pod myapp-xxxxx-yyyyy

# Check controller manager logs
kubectl logs -n kube-system kube-controller-manager-<node>
```

### Key Insight

Kubernetes doesn't run your containers directly. It stores desired state, and a chain of controllers continuously reconcile reality to match. This is why Kubernetes is resilient - it's always working to achieve the state you declared.

### Development vs Production: Single Node vs Multi-Node

#### Docker Desktop / Minikube / kind (Single Node)

All components run on ONE node - it acts as both control plane AND worker:

```
┌─────────────────────────────────────────────────────────────────┐
│                    docker-desktop node                          │
│                                                                 │
│  ┌─────────────── CONTROL PLANE ──────────────┐                │
│  │                                             │                │
│  │  etcd                    (cluster DB)      │                │
│  │  kube-apiserver          (API gateway)     │                │
│  │  kube-controller-manager (controllers)     │                │
│  │  kube-scheduler          (pod placement)   │                │
│  │                                             │                │
│  └─────────────────────────────────────────────┘                │
│                                                                 │
│  ┌─────────────── WORKER ─────────────────────┐                │
│  │                                             │                │
│  │  kubelet            (runs pods)            │                │
│  │  kube-proxy         (networking rules)     │                │
│  │  container runtime  (containerd/Docker)    │                │
│  │                                             │                │
│  └─────────────────────────────────────────────┘                │
│                                                                 │
│  ┌─────────────── ADD-ONS ────────────────────┐                │
│  │                                             │                │
│  │  coredns              (cluster DNS)        │                │
│  │  storage-provisioner  (local volumes)      │                │
│  │                                             │                │
│  └─────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

#### Production (Multi-Node)

Control plane and workers are separated for isolation and high availability:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCTION CLUSTER                                 │
│                                                                              │
│  ┌─────────────────────── CONTROL PLANE NODES ───────────────────────────┐  │
│  │                                                                        │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐              │  │
│  │  │  master-1    │   │  master-2    │   │  master-3    │              │  │
│  │  │              │   │              │   │              │              │  │
│  │  │ api-server   │   │ api-server   │   │ api-server   │  (HA)       │  │
│  │  │ controller   │   │ controller   │   │ controller   │              │  │
│  │  │ scheduler    │   │ scheduler    │   │ scheduler    │              │  │
│  │  │ etcd         │   │ etcd         │   │ etcd         │  (quorum)   │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘              │  │
│  │                                                                        │  │
│  │  Tainted: node-role.kubernetes.io/control-plane:NoSchedule           │  │
│  │  (no user workloads run here)                                         │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─────────────────────── WORKER NODES ──────────────────────────────────┐  │
│  │                                                                        │  │
│  │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────┐ │  │
│  │  │  worker-1    │   │  worker-2    │   │  worker-3    │   │  ...   │ │  │
│  │  │              │   │              │   │              │   │        │ │  │
│  │  │ kubelet      │   │ kubelet      │   │ kubelet      │   │        │ │  │
│  │  │ kube-proxy   │   │ kube-proxy   │   │ kube-proxy   │   │        │ │  │
│  │  │ containerd   │   │ containerd   │   │ containerd   │   │        │ │  │
│  │  │              │   │              │   │              │   │        │ │  │
│  │  │ [your pods]  │   │ [your pods]  │   │ [your pods]  │   │        │ │  │
│  │  └──────────────┘   └──────────────┘   └──────────────┘   └────────┘ │  │
│  │                                                                        │  │
│  │  Scalable: add/remove workers as needed                               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Comparison

| Aspect | Development (Single Node) | Production (Multi-Node) |
|--------|---------------------------|-------------------------|
| Control plane | Shared with workloads | Dedicated nodes (3+ for HA) |
| etcd | Single instance | Clustered (3+ replicas, Raft consensus) |
| Worker nodes | Same as control plane | Dedicated, scalable pool |
| Failure tolerance | None (single point of failure) | Survives node/zone failures |
| Taints | None (accepts all pods) | Control plane tainted |
| Resources | Shared, limited | Isolated, scalable |

#### Why Development Clusters Work

The **architecture is identical** - same components, same APIs, same reconciliation loops. Only the physical separation differs:

```bash
# Check taints on your node
kubectl describe node docker-desktop | grep Taints
# Output: Taints: <none>

# Production control plane would show:
# Taints: node-role.kubernetes.io/control-plane:NoSchedule
```

**Key insight**: YAML manifests you write on Docker Desktop work unchanged in production. You're learning real Kubernetes - only the infrastructure underneath scales out.

```bash
# See what's running in kube-system (control plane components)
kubectl get pods -n kube-system

# These are the same components as production, just on one node:
# - etcd-docker-desktop
# - kube-apiserver-docker-desktop
# - kube-controller-manager-docker-desktop
# - kube-scheduler-docker-desktop
# - coredns-xxxxx (cluster DNS)
# - kube-proxy-xxxxx (networking)
```

---

## Level 1: Hello World

### Minimal Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hello-world
  labels:
    app: hello
spec:
  containers:
  - name: hello
    image: nginx:latest
    ports:
    - containerPort: 80
```

### Expose with Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hello-service
spec:
  selector:
    app: hello
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

### Quick Commands

```bash
# Apply manifests
kubectl apply -f pod.yaml
kubectl apply -f service.yaml

# Verify
kubectl get pods
kubectl get services
kubectl describe pod hello-world

# Access (port-forward for local testing)
kubectl port-forward service/hello-service 8080:80
```

---

## Level 2: Deployments & Configuration

### Deployment (Recommended over raw Pods)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: APP_ENV
          value: "production"
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
data:
  # Simple key-value
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"

  # File-like configuration
  app.properties: |
    database.host=db.example.com
    database.port=5432
    cache.enabled=true
```

### Using ConfigMap in Deployment

```yaml
spec:
  containers:
  - name: myapp
    image: myapp:1.0.0
    # As environment variables
    env:
    - name: LOG_LEVEL
      valueFrom:
        configMapKeyRef:
          name: myapp-config
          key: LOG_LEVEL
    # As mounted files
    volumeMounts:
    - name: config-volume
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: config-volume
    configMap:
      name: myapp-config
```

### Deployment Commands

```bash
# Create deployment
kubectl apply -f deployment.yaml

# Check rollout status
kubectl rollout status deployment/myapp

# Scale deployment
kubectl scale deployment/myapp --replicas=5

# Update image (triggers rollout)
kubectl set image deployment/myapp myapp=myapp:2.0.0

# View rollout history
kubectl rollout history deployment/myapp

# Rollback
kubectl rollout undo deployment/myapp
kubectl rollout undo deployment/myapp --to-revision=2

# Pause/resume rollout
kubectl rollout pause deployment/myapp
kubectl rollout resume deployment/myapp
```

---

## Level 3: Production Stack

### Service Types

```yaml
# ClusterIP (internal only - default)
apiVersion: v1
kind: Service
metadata:
  name: myapp-internal
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080

---
# NodePort (external via node IP:port)
apiVersion: v1
kind: Service
metadata:
  name: myapp-nodeport
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # 30000-32767

---
# LoadBalancer (cloud provider LB)
apiVersion: v1
kind: Service
metadata:
  name: myapp-lb
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
type: Opaque
data:
  # Base64 encoded values
  db-password: cGFzc3dvcmQxMjM=
  api-key: c2VjcmV0LWFwaS1rZXk=
```

```bash
# Create secret from literal
kubectl create secret generic myapp-secrets \
  --from-literal=db-password=password123 \
  --from-literal=api-key=secret-api-key

# Create secret from file
kubectl create secret generic tls-secret \
  --from-file=tls.crt=./cert.pem \
  --from-file=tls.key=./key.pem
```

### Using Secrets in Deployment

```yaml
spec:
  containers:
  - name: myapp
    env:
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: myapp-secrets
          key: db-password
    volumeMounts:
    - name: secret-volume
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secret-volume
    secret:
      secretName: myapp-secrets
```

### Ingress (HTTP/HTTPS routing)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-service
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 80
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls-secret
```

**Path Types:**
- `Exact`: Matches URL path exactly
- `Prefix`: Matches based on URL path prefix split by `/`
- `ImplementationSpecific`: Depends on IngressClass

---

## Level 4: Professional Production

### Resource Requests and Limits

```yaml
spec:
  containers:
  - name: myapp
    image: myapp:1.0.0
    resources:
      requests:
        cpu: "250m"      # 0.25 CPU cores
        memory: "256Mi"  # 256 MiB
      limits:
        cpu: "500m"      # 0.5 CPU cores
        memory: "512Mi"  # 512 MiB
```

**Resource Units:**
- CPU: `1` = 1 core, `500m` = 0.5 cores, `100m` = 0.1 cores
- Memory: `Ki`, `Mi`, `Gi` (binary) or `K`, `M`, `G` (decimal)

### Health Probes

```yaml
spec:
  containers:
  - name: myapp
    image: myapp:1.0.0
    ports:
    - containerPort: 8080

    # Startup probe (for slow-starting apps)
    startupProbe:
      httpGet:
        path: /healthz
        port: 8080
      failureThreshold: 30
      periodSeconds: 10

    # Liveness probe (restart if unhealthy)
    livenessProbe:
      httpGet:
        path: /healthz
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3

    # Readiness probe (remove from LB if not ready)
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 3
```

**Probe Types:**
- `httpGet`: HTTP GET request (200-399 = success)
- `tcpSocket`: TCP connection attempt
- `exec`: Command execution (exit 0 = success)

### Horizontal Pod Autoscaler (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 min cooldown
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

```bash
# Create HPA imperatively
kubectl autoscale deployment myapp --cpu-percent=70 --min=2 --max=10

# Check HPA status
kubectl get hpa
kubectl describe hpa myapp-hpa
```

**Requirements for HPA:**
- Metrics Server must be installed
- Containers must have resource requests defined

### Complete Production Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
    version: "1.0.0"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
        version: "1.0.0"
    spec:
      containers:
      - name: myapp
        image: myapp:1.0.0
        ports:
        - containerPort: 8080

        resources:
          requests:
            cpu: "250m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: myapp-config
              key: APP_ENV
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: db-password

        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true

      volumes:
      - name: config
        configMap:
          name: myapp-config
```

### Resource Planning for AI/ML Workloads

AI workloads (LLMs, embeddings, agents) have unique resource characteristics.

#### Understanding Node Resources

```bash
# Check what's available on your node
kubectl describe node <node-name> | grep -A20 "Allocated resources:"

# Key fields:
# - Capacity: Total node resources
# - Allocatable: Available for pods (after system reservations)
# - Allocated: Currently requested by pods
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESOURCE HIERARCHY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Node Capacity (e.g., 8GB)                                      │
│  └── System Reserved (~5-10%)                                   │
│      └── Allocatable (~7.5GB)                                   │
│          └── kube-system pods (~300-500Mi)                      │
│              └── Available for YOUR pods (~7GB)                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### What Happens When Resources Exceed Limits

| Scenario | Behavior |
|----------|----------|
| **Request > Node Allocatable** | Pod stays `Pending` - scheduler can't place it |
| **Memory Usage > Limit** | Pod gets **OOMKilled** and restarts |
| **CPU Usage > Limit** | Pod gets **throttled** (not killed) |
| **Usage > Request** (no limit) | Works until node pressure, then eviction |
| **Node under memory pressure** | Kubelet evicts pods exceeding requests first |

```bash
# Diagnose resource issues
kubectl describe pod <pod-name> | grep -A10 "State:"
kubectl get events --field-selector reason=OOMKilling
kubectl get events --field-selector reason=FailedScheduling
```

#### AI Workload Resource Requirements

| Workload Type | Memory | CPU | Notes |
|---------------|--------|-----|-------|
| Local LLM (7B params) | 4-8 GB | 2-4 cores | Avoid on small clusters |
| Local LLM (13B params) | 8-16 GB | 4-8 cores | Needs dedicated node |
| Embedding model (local) | 1-2 GB | 1-2 cores | sentence-transformers |
| Vector DB (Chroma/Qdrant) | 512Mi-2GB | 0.5-1 core | Scales with data size |
| LangChain/Agent runtime | 256Mi-1GB | 0.25-1 core | Depends on tools |
| API-based agent (OpenAI/Claude) | 128-512Mi | 0.1-0.5 core | Minimal - just HTTP calls |

#### Resource Specs for Common AI Patterns

**API-based AI Agent (OpenAI, Claude, etc.):**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**LangChain Agent with Tools:**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1"
```

**Embedding Service (API-based):**
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

**Local Embedding Model (sentence-transformers):**
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1"
  limits:
    memory: "2Gi"
    cpu: "2"
```

**Vector Database (Chroma/Qdrant):**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

**Local LLM (Ollama - only on large nodes):**
```yaml
resources:
  requests:
    memory: "6Gi"    # Minimum for 7B model
    cpu: "2"
  limits:
    memory: "8Gi"
    cpu: "4"
```

#### Resource Quotas for AI Namespaces

Prevent runaway AI workloads from consuming all cluster resources:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ai-workloads-quota
  namespace: ai-agents
spec:
  hard:
    requests.memory: "6Gi"
    limits.memory: "8Gi"
    requests.cpu: "4"
    limits.cpu: "8"
    pods: "10"
```

#### LimitRange for Default Resources

Ensure all pods in AI namespace have resource specs:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: ai-limit-range
  namespace: ai-agents
spec:
  limits:
  - default:
      memory: "512Mi"
      cpu: "500m"
    defaultRequest:
      memory: "256Mi"
      cpu: "250m"
    max:
      memory: "4Gi"
      cpu: "2"
    type: Container
```

#### Monitoring Resource Usage

```bash
# Install metrics-server if not present
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Monitor node resources
kubectl top node

# Monitor pod resources
kubectl top pods
kubectl top pods --sort-by=memory

# Watch resources in real-time
watch kubectl top pods
```

#### Best Practices for AI Workloads

1. **Use API-based models for small clusters** - Local LLMs need dedicated resources
2. **Always set resource requests AND limits** - Prevents noisy neighbor issues
3. **Start conservative, scale up** - Monitor actual usage before increasing
4. **Use separate namespaces** - Isolate AI workloads with quotas
5. **Consider node affinity** - Pin heavy workloads to specific nodes
6. **Use HPA carefully** - AI workloads often have spiky, unpredictable load

```yaml
# Node affinity for GPU/high-memory nodes
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: workload-type
            operator: In
            values:
            - ai-compute
```

---

## Level 5: Enterprise Patterns

### Namespaces

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production
```

```bash
# Create namespace
kubectl create namespace production

# Deploy to namespace
kubectl apply -f deployment.yaml -n production

# Set default namespace
kubectl config set-context --current --namespace=production

# List resources in namespace
kubectl get all -n production
```

### StatefulSet (for stateful applications)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: standard
      resources:
        requests:
          storage: 10Gi
```

**StatefulSet guarantees:**
- Stable, unique network identifiers (postgres-0, postgres-1, postgres-2)
- Stable, persistent storage per pod
- Ordered, graceful deployment and scaling
- Ordered, automated rolling updates

### DaemonSet (one pod per node)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluentd:latest
        volumeMounts:
        - name: varlog
          mountPath: /var/log
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
```

**Use cases:** Log collectors, monitoring agents, node-level services

### Job (one-time tasks)

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 1
  parallelism: 1
  backoffLimit: 3
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: myapp-migrate:1.0.0
        command: ["./migrate.sh"]
```

### CronJob (scheduled tasks)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: backup-tool:1.0.0
            command: ["./backup.sh"]
```

---

## kubectl Essential Commands

### Cluster Health Verification

**Quick health check (run these first):**

```bash
# Cluster overview - is the API server responding?
kubectl cluster-info

# Node status - are nodes Ready?
kubectl get nodes -o wide

# All system pods healthy?
kubectl get pods -n kube-system

# Any pods in bad state? (should return empty)
kubectl get pods -A | grep -v Running | grep -v Completed
```

**Detailed cluster health:**

```bash
# Node conditions (Ready, MemoryPressure, DiskPressure, PIDPressure)
kubectl describe node <node-name> | grep -A5 "Conditions:"

# Quick check: are all nodes Ready?
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Component status (deprecated but still useful)
kubectl get componentstatuses

# Cluster resource usage (requires metrics-server)
kubectl top nodes
kubectl top pods -A --sort-by=memory | head -10
```

**Recent events (problems show up here):**

```bash
# All events sorted by time
kubectl get events -A --sort-by='.lastTimestamp' | tail -20

# Warning events only
kubectl get events -A --field-selector type=Warning

# Events for specific namespace
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

**Health check script:**

```bash
#!/bin/bash
echo "=== Cluster Health Check ==="

echo -e "\n1. API Server:"
kubectl cluster-info | head -1

echo -e "\n2. Nodes:"
kubectl get nodes

echo -e "\n3. System Pods:"
kubectl get pods -n kube-system --no-headers | awk '{print $1, $3}' | column -t

echo -e "\n4. Unhealthy Pods:"
BAD_PODS=$(kubectl get pods -A --no-headers | grep -v Running | grep -v Completed)
if [ -z "$BAD_PODS" ]; then
    echo "All pods healthy ✓"
else
    echo "$BAD_PODS"
fi

echo -e "\n5. Recent Warnings:"
kubectl get events -A --field-selector type=Warning --sort-by='.lastTimestamp' 2>/dev/null | tail -5 || echo "No warnings ✓"

echo -e "\n=== Health Check Complete ==="
```

**Common health issues:**

| Symptom | Command to Diagnose | Likely Cause |
|---------|---------------------|--------------|
| `kubectl` hangs | `kubectl cluster-info` | API server down, network issue |
| Node `NotReady` | `kubectl describe node <name>` | Kubelet issue, resource pressure |
| Pods `Pending` | `kubectl describe pod <name>` | No resources, no matching node |
| Pods `CrashLoopBackOff` | `kubectl logs <pod> --previous` | App error, bad config |
| Pods `ImagePullBackOff` | `kubectl describe pod <name>` | Wrong image, auth issue |

### Viewing Resources

```bash
# List resources
kubectl get pods                         # Pods in current namespace
kubectl get pods -A                      # All namespaces
kubectl get pods -o wide                 # Extended info (node, IP)
kubectl get pods -o yaml                 # Full YAML output
kubectl get all                          # All resource types

# Describe (detailed info)
kubectl describe pod <pod-name>
kubectl describe deployment <name>
kubectl describe service <name>

# Logs
kubectl logs <pod-name>                  # Current logs
kubectl logs <pod-name> -f               # Follow logs
kubectl logs <pod-name> -c <container>   # Specific container
kubectl logs <pod-name> --previous       # Previous container instance
kubectl logs -l app=myapp                # By label selector
```

### Managing Resources

```bash
# Apply/create
kubectl apply -f manifest.yaml           # Create or update
kubectl apply -f ./manifests/            # From directory
kubectl create -f manifest.yaml          # Create only

# Delete
kubectl delete -f manifest.yaml
kubectl delete pod <pod-name>
kubectl delete deployment <name>

# Edit live resource
kubectl edit deployment <name>

# Execute in container
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec <pod-name> -- ls /app

# Port forwarding
kubectl port-forward pod/<pod-name> 8080:80
kubectl port-forward svc/<svc-name> 8080:80
```

### Debugging

```bash
# Pod status and events
kubectl describe pod <pod-name>
kubectl get events --sort-by=.metadata.creationTimestamp

# Resource usage (requires metrics-server)
kubectl top pods
kubectl top nodes

# Debug with ephemeral container
kubectl debug <pod-name> -it --image=busybox

# Copy files
kubectl cp <pod-name>:/path/file ./local-file
kubectl cp ./local-file <pod-name>:/path/file
```

### Context and Configuration

```bash
# View config
kubectl config view
kubectl config get-contexts
kubectl config current-context

# Switch context
kubectl config use-context <context-name>

# Set namespace
kubectl config set-context --current --namespace=<namespace>
```

---

## Multi-Cluster Management

Managing multiple clusters (local dev, staging, production) safely.

### Adding Contexts from Cloud Providers

```bash
# Google Kubernetes Engine (GKE)
gcloud container clusters get-credentials my-cluster \
  --zone us-central1-a --project my-project

# Amazon EKS
aws eks update-kubeconfig --name my-cluster --region us-east-1

# Azure AKS
az aks get-credentials --resource-group my-rg --name my-cluster

# After adding, verify:
kubectl config get-contexts
# CURRENT   NAME             CLUSTER          AUTHINFO         NAMESPACE
# *         docker-desktop   docker-desktop   docker-desktop
#           gke-prod         gke_proj_us_c    gke_proj_us_c    default
#           gke-staging      gke_proj_us_s    gke_proj_us_s    default
```

### Manual Context Creation

```bash
# Add cluster
kubectl config set-cluster my-cluster \
  --server=https://api.example.com:6443 \
  --certificate-authority=ca.crt

# Add credentials
kubectl config set-credentials my-user \
  --client-certificate=client.crt \
  --client-key=client.key

# Create context (combines cluster + credentials + namespace)
kubectl config set-context my-context \
  --cluster=my-cluster \
  --user=my-user \
  --namespace=default
```

### Switching Between Clusters

```bash
# Switch context (changes default for all commands)
kubectl config use-context gke-prod
kubectl config use-context docker-desktop

# Run ONE command against different context (without switching)
kubectl --context=gke-prod get pods
kubectl --context=docker-desktop get pods

# Set default namespace for current context
kubectl config set-context --current --namespace=my-app

# Delete a context
kubectl config delete-context old-cluster

# Rename context for clarity
kubectl config rename-context gke_my-project_us-central1_cluster PROD-DANGER
```

### Avoiding Accidental Production Deployments

**1. Clear naming conventions:**
```bash
# Rename contexts to be obvious
kubectl config rename-context gke_prod_cluster PROD-DANGER
kubectl config rename-context docker-desktop LOCAL-dev
```

**2. Shell prompt showing current context:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export PS1='[k8s: $(kubectl config current-context)] \w $ '

# Result: [k8s: docker-desktop] ~/myapp $
```

**3. Separate kubeconfig files:**
```bash
# Keep production config separate (not in default file)
export KUBECONFIG=~/.kube/config              # dev only
export KUBECONFIG=~/.kube/config-prod         # production

# Merge temporarily when needed
export KUBECONFIG=~/.kube/config:~/.kube/config-prod
```

**4. Context-aware aliases:**
```bash
# Add to ~/.bashrc - forces explicit cluster choice
alias kprod='kubectl --context=PROD-DANGER'
alias kstg='kubectl --context=staging'
alias kdev='kubectl --context=docker-desktop'

# Usage - clearly shows intent
kprod get pods          # production
kdev apply -f app.yaml  # local dev
```

**5. Install kubectx/kubens (recommended):**
```bash
# macOS
brew install kubectx

# Usage
kubectx              # interactive context switcher with fuzzy search
kubens               # interactive namespace switcher
kubectx docker-desktop  # quick switch
```

### Safe Multi-Cluster Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SAFE MULTI-CLUSTER WORKFLOW                   │
│                                                                  │
│  1. Shell prompt shows context        [k8s: docker-desktop] $   │
│                                                                  │
│  2. Verify before dangerous commands                            │
│     $ kubectl config current-context                            │
│     docker-desktop   ✓                                          │
│                                                                  │
│  3. Use explicit context for production                         │
│     $ kubectl --context=PROD get pods    ✓ explicit             │
│     $ kubectl apply -f ...               ✗ uses current!        │
│                                                                  │
│  4. Color-code terminals                                        │
│     🟢 Green terminal  = local dev                              │
│     🔴 Red terminal    = production                             │
│                                                                  │
│  5. Use CI/CD for production deploys, not local kubectl         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Context Quick Reference

| Command | Description |
|---------|-------------|
| `kubectl config get-contexts` | List all contexts |
| `kubectl config current-context` | Show active context |
| `kubectl config use-context NAME` | Switch context |
| `kubectl --context=NAME get pods` | One-off command |
| `kubectl config set-context --current --namespace=NS` | Set default namespace |
| `kubectl config delete-context NAME` | Remove context |
| `kubectl config rename-context OLD NEW` | Rename context |

---

## Production Best Practices

### Security
- Never store secrets in ConfigMaps
- Enable encryption at rest for Secrets
- Use RBAC with least-privilege access
- Run containers as non-root
- Use Pod Security Standards

### Reliability
- Always set resource requests and limits
- Configure liveness and readiness probes
- Use multiple replicas (minimum 2-3)
- Set PodDisruptionBudget for critical apps
- Deploy across multiple availability zones

### Scalability
- Use HPA for automatic scaling
- Set appropriate resource requests for HPA to work
- Use Cluster Autoscaler for node scaling
- Consider Vertical Pod Autoscaler for resource optimization

### Updates
- Use RollingUpdate strategy
- Set `maxSurge` and `maxUnavailable` appropriately
- Test updates in staging first
- Keep rollback history (`revisionHistoryLimit`)

### Networking
- Use Services for internal communication
- Use Ingress for external HTTP traffic
- Implement Network Policies for isolation
- Use headless Services for StatefulSets

### Monitoring
- Deploy metrics-server for resource metrics
- Use Prometheus for application metrics
- Set up alerting for critical conditions
- Monitor cluster health and capacity

---

## Common Patterns

### Multi-Container Pod (Sidecar)

```yaml
spec:
  containers:
  - name: app
    image: myapp:1.0.0
    ports:
    - containerPort: 8080
  - name: log-shipper
    image: fluentd:latest
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  volumes:
  - name: logs
    emptyDir: {}
```

### Init Container

```yaml
spec:
  initContainers:
  - name: init-db
    image: busybox
    command: ['sh', '-c', 'until nc -z db-service 5432; do sleep 2; done']
  containers:
  - name: app
    image: myapp:1.0.0
```

### Environment-Specific Deployments

Use Kustomize or Helm for environment variations:

```bash
# Kustomize structure
base/
  deployment.yaml
  service.yaml
  kustomization.yaml
overlays/
  dev/
    kustomization.yaml
  prod/
    kustomization.yaml

# Apply with Kustomize
kubectl apply -k overlays/prod/
```

---

## Troubleshooting Guide

| Symptom | Check | Solution |
|---------|-------|----------|
| Pod stuck in Pending | `kubectl describe pod` | Check node resources, node selector, taints |
| Pod in CrashLoopBackOff | `kubectl logs` | Fix application error, check probes |
| Pod in ImagePullBackOff | `kubectl describe pod` | Check image name, registry auth |
| Service not reachable | `kubectl get endpoints` | Check selector labels match |
| HPA not scaling | `kubectl describe hpa` | Check metrics-server, resource requests |
| Deployment stuck | `kubectl rollout status` | Check pod errors, resource limits |
