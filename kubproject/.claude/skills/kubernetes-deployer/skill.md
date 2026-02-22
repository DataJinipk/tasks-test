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

### Quick Cluster Verification and Context Check

**Always run these first to verify cluster and context:**

```bash
# Cluster verification
kubectl cluster-info                    # Verify API server is accessible
kubectl get nodes                       # Check node status (should be Ready)
kubectl config current-context         # Verify which cluster you're targeting
kubectl get namespaces                 # Check available namespaces

# Quick health check
kubectl get pods -A | head -10         # Check system pods are running
kubectl get componentstatuses 2>/dev/null || echo "Components OK"  # Check system components
```

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

**Comprehensive cluster verification commands:**

```bash
# Cluster overview - API server endpoints
kubectl cluster-info

# Node status and capacity
kubectl get nodes
kubectl get nodes -o wide                    # Extended info (IP, OS, arch)
kubectl describe nodes                       # Detailed node information

# Check node conditions
kubectl get nodes --show-labels
kubectl get nodes -L kubernetes.io/arch -L kubernetes.io/os
kubectl describe nodes | grep -A 8 "Conditions:"

# Check system pods
kubectl get pods -n kube-system
kubectl get pods -n kube-system -o wide

# Check cluster components
kubectl get componentstatuses 2>/dev/null || echo "ComponentStatus deprecated in newer versions"
kubectl get cs 2>/dev/null || echo "ComponentStatus deprecated in newer versions"

# Check cluster events
kubectl get events -A --sort-by='.lastTimestamp' | tail -10

# Check resource usage (requires metrics-server)
kubectl top nodes
kubectl top nodes --use-protocol-buffers    # Alternative for large clusters
kubectl top pods -A
kubectl top pods -A --sort-by=memory | head -10

# Check for issues
kubectl get pods -A | grep -E "(CrashLoopBackOff|ImagePullBackOff|Error|Pending)"
kubectl get nodes | grep -v Ready
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

**Essential context management commands:**

```bash
# View current context
kubectl config current-context

# View all contexts
kubectl config get-contexts

# View kubeconfig details
kubectl config view

# Switch context
kubectl config use-context <context-name>

# Set namespace for current context
kubectl config set-context --current --namespace=<namespace>

# View context details
kubectl config get-contexts --output=name
kubectl config view --minify               # View current context only
kubectl config view -o jsonpath='{.contexts[?(@.name=="<context-name>")].context.namespace}'

# Context-specific operations
kubectl --context=<context-name> get nodes
kubectl --context=<context-name> get pods
```

**Enhanced context and namespace switching with kubectx/kubens:**

```bash
# Install kubectx/kubens for faster switching (recommended)
# macOS: brew install kubectx
# Linux: sudo snap install kubectx

# Interactive context switching with fuzzy search
kubectx                                    # Interactive context selector
kubectx -                                  # Switch to previous context
kubectx <context-name>                     # Switch to specific context

# Interactive namespace switching with fuzzy search
kubens                                     # Interactive namespace selector
kubens -                                   # Switch to previous namespace
kubens <namespace-name>                    # Switch to specific namespace

# One-liner to show current context and namespace
echo "Context: $(kubectl config current-context), Namespace: $(kubectl config view --minify -o jsonpath='{..namespace}')"
```

**Complete kubeconfig management:**

```bash
# Basic config operations
kubectl config view                                    # Show all config
kubectl config get-contexts                           # List all contexts
kubectl config current-context                        # Show current context

# Context operations
kubectl config use-context <context-name>             # Switch to context
kubectl config set-context --current --namespace=<ns>  # Set default namespace
kubectl config set-context <context-name> --namespace=<ns>  # Set namespace for specific context

# Context management
kubectl config delete-context <context-name>          # Remove context
kubectl config rename-context <old-name> <new-name>   # Rename context

# Cluster operations
kubectl config get-clusters                           # List clusters
kubectl config set-cluster <cluster-name> --server=<server-url>  # Modify cluster
kubectl config delete-cluster <cluster-name>          # Remove cluster

# User operations
kubectl config get-users                              # List users
kubectl config set-credentials <user-name> --token=<token>  # Set token
kubectl config delete-user <user-name>                # Remove user

# Advanced kubeconfig management
export KUBECONFIG=~/.kube/config:~/.kube/production   # Combine config files
kubectl config set-credentials <user> --client-certificate=<cert> --client-key=<key>  # Cert auth
kubectl config set-cluster <cluster> --certificate-authority=<ca> --embed-certs=true  # CA cert
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
# Installation
# macOS
brew install kubectx

# Linux
# Using snap
sudo snap install kubectx

# Using script
curl -LO https://github.com/ahmetb/kubectx/releases/latest/download/kubectx_0.9.4_linux_x86_64.tar.gz
tar -xzf kubectx_0.9.4_linux_x86_64.tar.gz
sudo mv kubectx /usr/local/bin/
sudo mv kubens /usr/local/bin/

# Windows (using Chocolatey)
choco install kubectx
```

**Advanced kubectx/kubens usage:**
```bash
# Context switching (interactive fuzzy search)
kubectx                    # Interactive selection of contexts
kubectx -                  # Switch to previous context
kubectx ctx-name           # Switch to specific context by name
kubectx -l, --list         # List contexts with additional info
kubectx -d, --delete ctx-name  # Delete a context

# Namespace switching (interactive fuzzy search)
kubens                     # Interactive selection of namespaces
kubens -                   # Switch to previous namespace
kubens kube-system         # Switch to specific namespace
kubens -l, --list          # List all namespaces in current context
kubens -c, --current       # Show current namespace only

# Advanced filtering
kubectx | grep prod        # Filter contexts matching 'prod'
kubens | grep -v kube-system  # List namespaces excluding kube-system

# Setting up shell completions
# For bash
kubectx --completion bash > /etc/bash_completion.d/kubectx
kubens --completion bash > /etc/bash_completion.d/kubens

# For zsh
kubectx --completion zsh > /usr/local/share/zsh/site-functions/_kubectx
kubens --completion zsh > /usr/local/share/zsh/site-functions/_kubens

# Customization options
export KUBECTX_CURRENT_DIR="${HOME}/.kube"  # Custom config location
export KUBECTX_IGNORE_FZF=1                 # Disable fuzzy finder
export KUBECTX_HIDE_FZF_HEADER=1            # Hide header in fzf
export KUBECTX_USE_DEFAULT_FZF="true"       # Enable fzf features

# Keyboard shortcuts during interactive mode
# - Tab/Shift+Tab: Navigate
# - Enter: Select
# - Ctrl+C: Cancel
# - Ctrl+R: Reverse search history
```

**Integration with shell prompts:**
```bash
# Enhanced shell prompt showing both context and namespace
# Add to ~/.bashrc or ~/.zshrc
prompt_k8s_info() {
  local ctx=$(kubectl config current-context 2>/dev/null || echo "unknown")
  local ns=$(kubectl config view --minify -o jsonpath='{..namespace}' 2>/dev/null || echo "default")
  echo "[k8s: ${ctx}/${ns}]"
}

export PS1='$(prompt_k8s_info) \w $ '

# Or simpler version
export PS1='[k8s: $(kubectx -c)/$(kubens -c)] \w $ '

# Result: [k8s: docker-desktop/default] ~/myapp $
```

**kubectx/kubens best practices:**
- Use descriptive context names that include environment info (dev/staging/prod)
- Take advantage of fuzzy search for faster navigation
- Use shell prompt integration to avoid confusion between clusters
- Combine with aliases for even faster access to frequently used contexts/namespaces
- Use the -l flag to get additional information about your contexts/namespaces

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
| `kubectx` | Interactive context switcher with fuzzy search |
| `kubectx -` | Switch to previous context |
| `kubectx NAME` | Switch to specific context by name |
| `kubens` | Interactive namespace switcher with fuzzy search |
| `kubens -` | Switch to previous namespace |
| `kubens NAME` | Switch to specific namespace by name |

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

---

## GPU-Accelerated AI/ML Workloads

### GPU Resource Management in Kubernetes

Kubernetes supports GPU-accelerated workloads through device plugins that expose GPUs as schedulable resources. When a GPU is allocated to a container, the device plugin ensures that all required GPU libraries and binaries are mounted into the container.

#### Prerequisites

Before deploying GPU workloads, ensure:
1. GPU-enabled nodes with proper drivers installed
2. NVIDIA Device Plugin deployed on GPU nodes
3. NVIDIA Container Runtime configured
4. Appropriate node labels and taints set up

#### GPU Resource Requests

To request GPU resources in a pod specification, use the `nvidia.com/gpu` resource name:

```yaml
spec:
  containers:
  - name: gpu-app
    resources:
      requests:
        nvidia.com/gpu: 1    # Request 1 GPU
        memory: "4Gi"
        cpu: "2"
      limits:
        nvidia.com/gpu: 1    # Limit to 1 GPU
        memory: "8Gi"
        cpu: "4"
```

### GPU-Accelerated AI Model Training Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-ai-trainer
  namespace: ai-workloads
  labels:
    app: gpu-ai-trainer
    workload-type: gpu-training
spec:
  replicas: 1  # Training jobs are often single instance
  selector:
    matchLabels:
      app: gpu-ai-trainer
  template:
    metadata:
      labels:
        app: gpu-ai-trainer
    spec:
      # Ensure pod lands on a GPU-enabled node
      nodeSelector:
        nvidia.com/gpu.present: "true"
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - name: ai-trainer
        image: pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
        command: ["python", "train_model.py"]
        ports:
        - containerPort: 8080
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: "all"
        - name: CUDA_VISIBLE_DEVICES
          value: "0"
        - name: PYTHONDONTWRITEBYTECODE
          value: "1"
        # GPU and memory intensive resource allocation
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4"
          limits:
            nvidia.com/gpu: 1
            memory: "32Gi"
            cpu: "8"
        # Volume for dataset access
        volumeMounts:
        - name: dataset-storage
          mountPath: /data
        - name: model-storage
          mountPath: /models
        # Health checks for long-running training
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "ls /tmp/training_active || exit 1"
          initialDelaySeconds: 300  # 5 minutes for model to start
          periodSeconds: 300       # Check every 5 minutes
          timeoutSeconds: 30
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "ls /tmp/model_loaded || exit 1"
          initialDelaySeconds: 180
          periodSeconds: 60
          timeoutSeconds: 15
      volumes:
      - name: dataset-storage
        persistentVolumeClaim:
          claimName: dataset-pvc
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-pvc
---
# Service for accessing training metrics
apiVersion: v1
kind: Service
metadata:
  name: gpu-ai-trainer-service
  namespace: ai-workloads
spec:
  selector:
    app: gpu-ai-trainer
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: metrics
    port: 8081
    targetPort: 8081
  type: ClusterIP
---
# GPU-specific resource quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gpu-resources-quota
  namespace: ai-workloads
spec:
  hard:
    requests.nvidia.com/gpu: "4"
    limits.nvidia.com/gpu: "4"
    requests.memory: "64Gi"
    limits.memory: "128Gi"
```

### GPU-Accelerated Inference Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-inference-service
  namespace: ai-workloads
  labels:
    app: gpu-inference
    workload-type: gpu-inference
spec:
  replicas: 2  # Multiple replicas for load balancing
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: gpu-inference
  template:
    metadata:
      labels:
        app: gpu-inference
    spec:
      # Node affinity for GPU nodes
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: nvidia.com/gpu.present
                operator: In
                values:
                - "true"
              - key: node-type
                operator: In
                values:
                - gpu-compute
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - name: inference-server
        image: nvcr.io/nvidia/tritonserver:23.08-py3
        ports:
        - containerPort: 8000  # HTTP
        - containerPort: 8001  # gRPC
        - containerPort: 8002  # metrics
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: "all"
        - name: TRITON_SERVER_GPU_ENABLED
          value: "1"
        - name: MODEL_STORE
          value: "/models"
        # GPU resources for inference
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "8Gi"
            cpu: "2"
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "4"
        # Volume for models
        volumeMounts:
        - name: model-storage
          mountPath: /models
        # Health checks
        livenessProbe:
          httpGet:
            path: /v2/health/live
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /v2/health/ready
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        startupProbe:
          httpGet:
            path: /v2/health/ready
            port: 8000
          failureThreshold: 30
          periodSeconds: 10
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: inference-models-pvc
---
# Service for the GPU inference service
apiVersion: v1
kind: Service
metadata:
  name: gpu-inference-service
  namespace: ai-workloads
spec:
  selector:
    app: gpu-inference
  ports:
  - name: http
    port: 80
    targetPort: 8000
    nodePort: 30080
  - name: grpc
    port: 8001
    targetPort: 8001
  - name: metrics
    port: 8002
    targetPort: 8002
  type: LoadBalancer  # Expose for external inference requests
---
# Horizontal Pod Autoscaler for GPU inference
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gpu-inference-hpa
  namespace: ai-workloads
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gpu-inference-service
  minReplicas: 2
  maxReplicas: 8
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
  # Custom metric for GPU utilization when available
  - type: Pods
    pods:
      metric:
        name: gpu_utilization
      target:
        type: AverageValue
        averageValue: "70"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

### Multi-GPU Training Job (StatefulSet for persistent state)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: multi-gpu-training
  namespace: ai-workloads
spec:
  serviceName: multi-gpu-training-headless
  replicas: 4  # 4 nodes with distributed training
  selector:
    matchLabels:
      app: multi-gpu-training
  template:
    metadata:
      labels:
        app: multi-gpu-training
    spec:
      # Ensure GPU availability
      nodeSelector:
        nvidia.com/gpu.present: "true"
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      initContainers:
      - name: init-gpu-check
        image: nvidia/cuda:11.7-base-ubuntu20.04
        command: ['sh', '-c', 'nvidia-smi']
      containers:
      - name: distributed-trainer
        image: pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
        command: ["torchrun", "--nnodes=4", "--nproc_per_node=2", "train_distributed.py"]
        env:
        - name: MASTER_ADDR
          value: "multi-gpu-training-0.multi-gpu-training-headless"
        - name: MASTER_PORT
          value: "29500"
        - name: RANK
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: WORLD_SIZE
          value: "4"
        - name: NVIDIA_VISIBLE_DEVICES
          value: "0,1"  # Use 2 GPUs per node
        ports:
        - containerPort: 29500  # Torch distributed port
        resources:
          requests:
            nvidia.com/gpu: 2  # Request 2 GPUs per pod
            memory: "32Gi"
            cpu: "8"
          limits:
            nvidia.com/gpu: 2  # Limit to 2 GPUs
            memory: "64Gi"
            cpu: "16"
        volumeMounts:
        - name: dataset-storage
          mountPath: /data
        - name: model-storage
          mountPath: /models
        - name: shared-tmp
          mountPath: /tmp/shared
        # Health checks for distributed training
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "ps aux | grep torchrun | grep -v grep || exit 1"
          initialDelaySeconds: 600
          periodSeconds: 600
          timeoutSeconds: 60
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "test -f /tmp/training_initialized || exit 1"
          initialDelaySeconds: 300
          periodSeconds: 120
          timeoutSeconds: 30
      volumes:
      - name: dataset-storage
        persistentVolumeClaim:
          claimName: large-dataset-pvc
      - name: model-storage
        persistentVolumeClaim:
          claimName: distributed-models-pvc
      - name: shared-tmp
        emptyDir: {}
---
# Headless service for StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: multi-gpu-training-headless
  namespace: ai-workloads
spec:
  clusterIP: None  # Headless service for StatefulSet
  selector:
    app: multi-gpu-training
```

### GPU Monitoring and Metrics DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: gpu-node-exporter
  namespace: monitoring
  labels:
    app: gpu-node-exporter
spec:
  selector:
    matchLabels:
      app: gpu-node-exporter
  template:
    metadata:
      labels:
        app: gpu-node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      tolerations:
      - key: node-role.kubernetes.io/master
        operator: Exists
        effect: NoSchedule
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - name: node-exporter
        image: nvidia/dcgm-exporter:latest
        ports:
        - name: metrics
          containerPort: 9400
        securityContext:
          runAsNonRoot: true
          runAsUser: 65534
        volumeMounts:
        - name: podinfo
          mountPath: /etc/podinfo
      volumes:
      - name: podinfo
        hostPath:
          path: /etc/podinfo
          type: Directory
---
# GPU-specific ConfigMap for monitoring
apiVersion: v1
kind: ConfigMap
metadata:
  name: gpu-monitoring-config
  namespace: monitoring
data:
  dcgm.conf: |
    [dcgm]
    collectd_enabled = false
    [nv-hostengine]
    remote_hosts =
    [dcgm-exporter]
    address = :9400
    collectinterval = 30000
    noconnectionretry = true
    gpuids =
    counters = DCGM_FI_DEV_GPU_TEMP,DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION,DCGM_FI_DEV_POWER_USAGE,DCGM_FI_DEV_FB_USED,DCGM_FI_DEV_FB_TOTAL
```

### Complete GPU-Accelerated AI/ML Pipeline

```yaml
---
# Namespace for GPU workloads
apiVersion: v1
kind: Namespace
metadata:
  name: gpu-ai-pipeline
  labels:
    name: gpu-ai-pipeline
---
# Resource quotas for GPU namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gpu-pipeline-quota
  namespace: gpu-ai-pipeline
spec:
  hard:
    requests.nvidia.com/gpu: "8"
    limits.nvidia.com/gpu: "8"
    requests.memory: "64Gi"
    limits.memory: "128Gi"
    requests.cpu: "16"
    limits.cpu: "32"
    pods: "20"
---
# Limit range for GPU containers
apiVersion: v1
kind: LimitRange
metadata:
  name: gpu-limit-range
  namespace: gpu-ai-pipeline
spec:
  limits:
  - type: Container
    default:
      nvidia.com/gpu: "1"
      memory: "8Gi"
      cpu: "2"
    defaultRequest:
      nvidia.com/gpu: "1"
      memory: "4Gi"
      cpu: "1"
    max:
      nvidia.com/gpu: "4"
      memory: "32Gi"
      cpu: "16"
    min:
      nvidia.com/gpu: "1"
      memory: "2Gi"
      cpu: "0.5"
---
# GPU-enabled AI pipeline deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-ai-pipeline
  namespace: gpu-ai-pipeline
  labels:
    app: gpu-ai-pipeline
    pipeline: gpu-inference
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gpu-ai-pipeline
  template:
    metadata:
      labels:
        app: gpu-ai-pipeline
    spec:
      # Node affinity for GPU nodes with specific requirements
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: nvidia.com/gpu.present
                operator: In
                values:
                - "true"
              - key: nvidia.com/gpu.memory
                operator: Gt
                values:
                - "15360"  # 15GB+ GPU memory (e.g., RTX 4090 or A100)
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      containers:
      - name: gpu-ai-service
        image: tensorflow/tensorflow:2.13.0-gpu
        command: ["python", "app.py"]
        ports:
        - containerPort: 8501  # TensorFlow Serving port
        env:
        - name: NVIDIA_VISIBLE_DEVICES
          value: "0"
        - name: TF_FORCE_GPU_ALLOW_GROWTH
          value: "true"
        - name: OMP_NUM_THREADS
          value: "4"
        - name: KMP_AFFINITY
          value: "granularity=fine,verbose,compact,1,0"
        resources:
          requests:
            nvidia.com/gpu: 1
            memory: "8Gi"
            cpu: "4"
          limits:
            nvidia.com/gpu: 1
            memory: "16Gi"
            cpu: "8"
        volumeMounts:
        - name: model-storage
          mountPath: /models
        - name: cache-storage
          mountPath: /tmp/cache
        livenessProbe:
          httpGet:
            path: /v1/models/default
            port: 8501
          initialDelaySeconds: 120
          periodSeconds: 60
        readinessProbe:
          httpGet:
            path: /v1/models/default:predict
            port: 8501
          initialDelaySeconds: 60
          periodSeconds: 30
        startupProbe:
          httpGet:
            path: /v1/models
            port: 8501
          failureThreshold: 60
          periodSeconds: 10
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: ai-models-pvc
      - name: cache-storage
        emptyDir:
          sizeLimit: 2Gi
---
# LoadBalancer service for external access
apiVersion: v1
kind: Service
metadata:
  name: gpu-ai-pipeline-service
  namespace: gpu-ai-pipeline
spec:
  selector:
    app: gpu-ai-pipeline
  ports:
  - port: 80
    targetPort: 8501
    name: inference
  - port: 8502
    targetPort: 8502
    name: metrics
  type: LoadBalancer
---
# Network policy for GPU AI services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gpu-ai-policy
  namespace: gpu-ai-pipeline
spec:
  podSelector:
    matchLabels:
      app: gpu-ai-pipeline
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
    ports:
    - protocol: TCP
      port: 8501
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
```

### Key Points for GPU-accelerated AI/ML Workloads:

1. **GPU Resource Requests**: Use `nvidia.com/gpu` as a resource request in container specs
2. **Node Selection**: Use node selectors or affinity rules to ensure pods land on GPU-enabled nodes
3. **Tolerations**: Add tolerations for GPU taints that prevent non-GPU workloads from running on GPU nodes
4. **Monitoring**: Deploy GPU monitoring tools like DCGM exporter to track GPU utilization
5. **Resource Quotas**: Set quotas specifically for GPU resources to prevent over-provisioning
6. **Storage**: Plan for high-performance storage for model loading and data access
7. **Health Checks**: Adjust probe parameters for long-startup GPU applications

---

## Workflow Orchestration in Kubernetes

### Introduction to Workflow Orchestration

Workflow orchestration in Kubernetes is the process of managing and automating complex, multi-step operations that span multiple pods, services, and resources. Instead of running individual deployments manually, orchestration allows you to define dependencies, handle failures gracefully, and execute multi-step processes automatically.

### Key Workflow Orchestration Tools

1. **Argo Workflows** - Cloud-native workflow engine for Kubernetes
2. **Kubeflow Pipelines** - ML-focused workflow orchestration
3. **Tekton** - Kubernetes-native CI/CD framework
4. **Apache Airflow** - Platform to programmatically author, schedule and monitor workflows

### Argo Workflows Example

Argo is one of the most popular workflow engines for Kubernetes:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: ai-training-workflow-
spec:
  entrypoint: ai-training
  serviceAccountName: argo
  volumes:
  - name: shared-data
    emptyDir: {}
  templates:
  - name: ai-training
    steps:
    - - name: data-preparation
        template: prep-data
    - - name: model-training
        template: train-model
        arguments:
          artifacts:
          - name: training-data
            from: "{{steps.data-preparation.outputs.artifacts.data}}"
    - - name: model-evaluation
        template: evaluate-model
        arguments:
          artifacts:
          - name: trained-model
            from: "{{steps.model-training.outputs.artifacts.model}}"

  - name: prep-data
    container:
      image: python:3.9
      command: [python]
      args: ["prep_data.py"]
      volumeMounts:
      - name: shared-data
        mountPath: /data
    outputs:
      artifacts:
      - name: data
        path: /data/training_data.json

  - name: train-model
    inputs:
      artifacts:
      - name: training-data
        path: /input/training_data.json
    container:
      image: pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
      command: [python]
      args: ["train.py", "/input/training_data.json"]
      resources:
        requests:
          nvidia.com/gpu: 1
          memory: "8Gi"
          cpu: "2"
        limits:
          nvidia.com/gpu: 1
          memory: "16Gi"
          cpu: "4"
    outputs:
      artifacts:
      - name: model
        path: /model/trained_model.pth

  - name: evaluate-model
    inputs:
      artifacts:
      - name: trained-model
        path: /model/trained_model.pth
    container:
      image: python:3.9
      command: [python]
      args: ["evaluate.py", "/model/trained_model.pth"]
```

### Kubeflow Pipeline Example

For ML-specific workflows:

```yaml
# This would be implemented as a KFP component
# Component: data-preparation
name: data-preparation
inputs: []
outputs:
- {name: output_dataset, type: Dataset}
implementation:
  container:
    image: my-data-prep:latest
    command: ['python', 'prepare_data.py']
    args: [
        '--output-path', {outputPath: output_dataset}
    ]

# Component: model-training
name: model-training
inputs:
- {name: input_dataset, type: Dataset}
outputs:
- {name: trained_model, type: Model}
implementation:
  container:
    image: pytorch/training:latest
    command: ['python', 'train.py']
    args: [
        '--dataset-path', {inputPath: input_dataset},
        '--output-path', {outputPath: trained_model}
    ]
    resources:
      requests:
        nvidia.com/gpu: 1
        memory: "8Gi"
        cpu: "2"
      limits:
        nvidia.com/gpu: 1
        memory: "16Gi"
        cpu: "4"
---
# Pipeline DSL in Python
import kfp
from kfp import dsl

@dsl.pipeline(
    name='ai-training-pipeline',
    description='Complete AI model training pipeline'
)
def ai_training_pipeline():
    data_prep_task = kfp.components.load_component_from_file('data-prep.component.yaml')()

    train_task = kfp.components.load_component_from_file('training.component.yaml')(
        input_dataset=data_prep_task.outputs['output_dataset']
    )
    train_task.set_gpu_limit(1, "nvidia")

    eval_task = kfp.components.load_component_from_file('evaluation.component.yaml')(
        trained_model=train_task.outputs['trained_model']
    )
```

### Tekton Pipeline Example

For CI/CD-style workflows:

```yaml
apiVersion: tekton.dev/v1beta1
kind: Pipeline
metadata:
  name: ai-model-pipeline
spec:
  params:
  - name: model-image
    type: string
    default: "my-ai-model:latest"
  - name: git-url
    type: string
    default: "https://github.com/example/ai-model.git"
  tasks:
  - name: fetch-source
    taskRef:
      name: git-clone
    params:
    - name: url
      value: $(params.git-url)
    workspaces:
    - name: output
      workspace: shared-workspace

  - name: run-tests
    taskRef:
      name: run-python-tests
    runAfter: ["fetch-source"]
    workspaces:
    - name: source
      workspace: shared-workspace

  - name: build-model
    taskRef:
      name: buildah
    runAfter: ["run-tests"]
    params:
    - name: IMAGE
      value: $(params.model-image)
    workspaces:
    - name: source
      workspace: shared-workspace

  - name: deploy-model
    taskRef:
      name: kubectl-apply
    runAfter: ["build-model"]
    params:
    - name: manifests
      value: |
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: ai-model
        spec:
          replicas: 2
          selector:
            matchLabels:
              app: ai-model
          template:
            metadata:
              labels:
                app: ai-model
            spec:
              containers:
              - name: model
                image: $(params.model-image)
                ports:
                - containerPort: 8080
                resources:
                  requests:
                    memory: "2Gi"
                    cpu: "1"
                  limits:
                    memory: "4Gi"
                    cpu: "2"
---
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  name: ai-model-pipeline-run
spec:
  pipelineRef:
    name: ai-model-pipeline
  params:
  - name: model-image
    value: "my-ai-model:v1.2.3"
  - name: git-url
    value: "https://github.com/myorg/ai-model.git"
  workspaces:
  - name: shared-workspace
    volumeClaimTemplate:
      spec:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
```

### Custom Workflow with Jobs and CronJobs

For simpler workflows that don't require a dedicated workflow engine:

```yaml
---
# Workflow: Data Ingestion → Processing → Model Training → Validation
apiVersion: batch/v1
kind: Job
metadata:
  name: data-ingestion-job
spec:
  template:
    spec:
      containers:
      - name: ingester
        image: my-data-ingester:latest
        env:
        - name: OUTPUT_PATH
          value: "/data/raw"
        volumeMounts:
        - name: data-storage
          mountPath: /data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: workflow-data-pvc
      restartPolicy: OnFailure
  backoffLimit: 4
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: workflow-controller-config
data:
  workflow.yaml: |
    steps:
    - name: data-ingestion
      job: data-ingestion-job
      depends-on: []
    - name: data-processing
      job: data-processing-job
      depends-on: ["data-ingestion"]
    - name: model-training
      job: model-training-job
      depends-on: ["data-processing"]
    - name: model-validation
      job: model-validation-job
      depends-on: ["model-training"]
---
# Workflow controller deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: workflow-controller
spec:
  replicas: 1
  selector:
    matchLabels:
      app: workflow-controller
  template:
    metadata:
      labels:
        app: workflow-controller
    spec:
      containers:
      - name: controller
        image: my-workflow-controller:latest
        env:
        - name: WORKFLOW_CONFIG
          valueFrom:
            configMapKeyRef:
              name: workflow-controller-config
              key: workflow.yaml
        volumeMounts:
        - name: config-volume
          mountPath: /etc/workflow
      volumes:
      - name: config-volume
        configMap:
          name: workflow-controller-config
```

### Advanced Workflow Patterns

#### Conditional Execution

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: conditional-workflow-
spec:
  entrypoint: conditional-example
  templates:
  - name: conditional-example
    steps:
    - - name: check-data-quality
        template: validate-data
    - - name: process-optimization
        template: optimize-processing
        when: "{{steps.check-data-quality.outputs.result}} > 0.8"
    - - name: fallback-processing
        template: basic-processing
        when: "{{steps.check-data-quality.outputs.result}} <= 0.8"

  - name: validate-data
    script:
      image: python:3.9
      command: [python]
      source: |
        import random
        quality_score = random.uniform(0.5, 1.0)
        print(quality_score)
      outputs:
        parameters:
        - name: quality-score
          valueFrom:
            path: /dev-stdout

  - name: optimize-processing
    container:
      image: my-optimized-processor:latest
      command: [echo]
      args: ["Running optimized processing pipeline"]

  - name: basic-processing
    container:
      image: my-basic-processor:latest
      command: [echo]
      args: ["Running basic processing pipeline"]
```

#### Parallel Processing and Fan-out/Fan-in

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: parallel-workflow-
spec:
  entrypoint: parallel-example
  arguments:
    parameters:
    - name: model-types
      value: "[{'name': 'model-a'}, {'name': 'model-b'}, {'name': 'model-c'}]"
  templates:
  - name: parallel-example
    steps:
    - - name: fan-out
        template: train-model
        arguments:
          parameters:
          - name: model-type
            value: "{{item}}"
        withParam: "{{workflow.parameters.model-types}}"
    - - name: fan-in
        template: aggregate-results
        arguments:
          parameters:
          - name: results
            value: "{{steps.fan-out.outputs.result}}"

  - name: train-model
    inputs:
      parameters:
      - name: model-type
    script:
      image: python:3.9
      command: [python]
      source: |
        import time
        import json
        print(f"Training { {{inputs.parameters.model-type.name}} }")
        time.sleep(10)  # Simulate training
        result = {
          "model": "{{inputs.parameters.model-type.name}}",
          "accuracy": 0.85 + (hash("{{inputs.parameters.model-type.name}}") % 100) / 1000
        }
        print(json.dumps(result))
      outputs:
        parameters:
        - name: result
          valueFrom:
            path: /dev-stdout

  - name: aggregate-results
    inputs:
      parameters:
      - name: results
    script:
      image: python:3.9
      command: [python]
      source: |
        import json
        results = json.loads("{{inputs.parameters.results}}")
        best_model = max(results, key=lambda x: x.get('accuracy', 0))
        print(f"Best model: {best_model['model']} with accuracy {best_model['accuracy']:.3f}")
```

### Best Practices for Workflow Orchestration

1. **Error Handling**: Always define retry policies and failure handling
2. **Resource Management**: Set appropriate resource requests and limits
3. **Security**: Use proper service accounts and RBAC for workflow execution
4. **Monitoring**: Implement proper logging and monitoring for workflows
5. **Parameterization**: Make workflows configurable through parameters
6. **Versioning**: Version your workflow templates and components
7. **Cleanup**: Implement proper cleanup policies for completed workflows

### Workflow Monitoring and Observability

```yaml
# ServiceMonitor for Argo Workflows
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argo-workflows-monitor
  labels:
    app: argo-workflows
spec:
  selector:
    matchLabels:
      app: workflow-controller
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
---
# Workflow logging configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: workflow-logging-config
  namespace: argo
data:
  log-config: |
    {
      "level": "info",
      "format": "json",
      "output": {
        "type": "stdout"
      },
      "handlers": [
        {
          "type": "elasticsearch",
          "host": "elasticsearch:9200",
          "index": "argo-workflows"
        }
      ]
    }
```
