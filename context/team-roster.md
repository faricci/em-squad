# Team Roster

> Layer 2 context artifact. Update this file when roles, skills, or workload change.
> Version: 0.1.0 | Last updated: 2026-03-05

## Team

This is a DevOps team in a financial sector organization. The team owns infrastructure,
CI/CD pipelines, and deployment processes for critical trading systems.

---

### Anna Ricci — Senior DevOps Engineer

**Role:** Infrastructure & CI/CD lead
**Workload:** partial (20% allocated)

**Skills:**
- Kubernetes, Helm, ArgoCD
- Docker, Docker Compose
- Terraform, Ansible
- Jenkins, GitHub Actions, Gitlab CI
- Python scripting
- On-call rotation lead
- Linux administration

**Notes:** Go-to for anything pipeline or infra. 

---

### Domenico Ricci — Platform Engineer

**Role:** Platform tooling & observability
**Workload:** available (20% allocated)

**Skills:**
- Prometheus, Grafana, Alertmanager
- ELK stack (Elasticsearch, Logstash, Kibana)
- Docker, Docker Compose
- Bash scripting
- API testing (Postman, k6)
- Python (FastAPI, Flask)
- PostgreSQL, Redis
- REST API design

**Notes:** Best match for monitoring, alerting, and dashboards. Greenfield tasks welcome. Builds internal tools the team uses. Not the right match for infra tasks. Prefer for automation scripts, internal dashboards, or API integrations.

---

### Giulia Ricci — Cloud Specialist Engineer

**Role:** Cloud architectures and CI/CD
**Workload:** full (10% allocated)

**Skills:**
- Pytest, Selenium
- Docker, Microservices
- Terraform, Ansible
- Python (FastAPI, Flask)
- DevSecOps
- Finops
- AWS, Azure
- Test automation

**Notes:** Preferred when deeper cloud knowledge is required

---

## Routing Guidelines

| Task Category          | Primary Owner | Fallback       |
|------------------------|---------------|----------------|
| CI/CD pipeline issues  | Anna          | Giulia         |
| Infrastructure changes | Anna          | Giulia         |
| Monitoring / alerts    | Domenico      | Giulia         |
| Internal tooling       | Domenico      | Anna           |
| API / scripting        | Domenico      | Anna           |
| Test automation        | Giulia        | Domenico       |
| Security patches       | Giulia        | escalate to EM |
| Cost optimization      | Giulia        | Anna           |
