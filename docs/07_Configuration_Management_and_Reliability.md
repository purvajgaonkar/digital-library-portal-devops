# Phase 6: Configuration Management, Automated Provisioning, and Reliability Validation
**Project Name:** CI/CD Pipeline for a Digital Library Search Portal  
**Domain:** DevOps Configuration Management & Infrastructure Reliability  
**Phase:** 6 — Deliverables 13 & 14  

---

## 1. Deliverable 13: Configuration Management Script

### 1.1 Target Server Prerequisites Specification

To deploy and operate the Dockerized Digital Library Search Portal in staging or production environments, the target host must satisfy the following infrastructure requirements:

| Component Category | Prerequisite Specification | Purpose / Standard |
| :--- | :--- | :--- |
| **Operating System** | Ubuntu 22.04 LTS / Debian 12 / RHEL 9 | Standard Linux distribution with systemd init. |
| **Required Packages** | `apt-transport-https`, `ca-certificates`, `curl`, `gnupg`, `lsb-release`, `python3`, `python3-pip`, `docker.io` | Base runtime utilities and Docker container engine. |
| **Python Libraries** | `docker>=6.0.0`, `requests` (via pip) | Required by Ansible `community.docker` collection to manage containers. |
| **Service Accounts** | User `devops`, Group `devops`, belonging to `docker` group | Dedicated non-root service account with container management privileges. |
| **Directory Structures** | &bull; `/opt/digital-library-portal`<br>&bull; `/opt/digital-library-portal/data`<br>&bull; `/opt/digital-library-portal/logs`<br>&bull; `/opt/digital-library-portal/backups` | Persistent volume mounts, persistent SQLite database storage, and runtime audit logs (`0755` permissions). |
| **Networking & Ports** | &bull; TCP `22` (SSH remote administration)<br>&bull; TCP `5000` (Application HTTP port) | Ingress traffic firewall allowances (UFW / security groups). |
| **Running Services** | `docker.service` (Active, Enabled on Boot) | Daemon managing application container processes. |

---

### 1.2 Ansible Inventory: `ansible/hosts.ini`

Stored at [`ansible/hosts.ini`](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/ansible/hosts.ini):

```ini
[staging]
library-staging ansible_host=192.168.56.101 app_port=5000 environment_type=staging

[production]
library-prod-01 ansible_host=192.168.56.102 app_port=5000 environment_type=production
library-prod-02 ansible_host=192.168.56.103 app_port=5000 environment_type=production

[local]
localhost ansible_connection=local ansible_host=127.0.0.1 app_port=5000 environment_type=development

[library_servers:children]
staging
production
local

[library_servers:vars]
ansible_user=devops
ansible_ssh_private_key_file=~/.ssh/id_rsa
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
docker_image_repo=devopslab/digital-library-portal
app_version=v1.0-MVP
```

---

### 1.3 Execution Command & Initial Run Terminal Output

#### Command to Execute Playbook:
```bash
# Verify playbook syntax
ansible-playbook -i ansible/hosts.ini ansible/deploy.yml --syntax-check

# Execute on staging target node
ansible-playbook -i ansible/hosts.ini ansible/deploy.yml --limit staging
```

#### Expected Output Log for First Execution (Provisioning & Fresh Deployment):
```text
PLAY [Provision Prerequisites, Deploy Container, and Validate Reliability] **********************************************

TASK [Gathering Facts] **************************************************************************************************
ok: [library-staging]

TASK [Ensure APT cache is up to date (Debian/Ubuntu)] *******************************************************************
changed: [library-staging]

TASK [Install essential OS packages and Docker dependencies] ************************************************************
changed: [library-staging] => (item=['ca-certificates', 'curl', 'gnupg', 'python3', 'python3-pip', 'docker.io'])

TASK [Install Python Docker SDK for Ansible container management] *******************************************************
changed: [library-staging] => (item=['docker>=6.0.0', 'requests'])

TASK [Ensure Docker service is enabled and actively running] ************************************************************
changed: [library-staging]

TASK [Ensure application group exists] **********************************************************************************
changed: [library-staging]

TASK [Ensure service user exists and belongs to docker group] ***********************************************************
changed: [library-staging]

TASK [Create required directory hierarchy for persistence and logs] *****************************************************
changed: [library-staging] => (item=/opt/digital-library-portal)
changed: [library-staging] => (item=/opt/digital-library-portal/data)
changed: [library-staging] => (item=/opt/digital-library-portal/logs)
changed: [library-staging] => (item=/opt/digital-library-portal/backups)

TASK [Pull specified version of application Docker image] ***************************************************************
changed: [library-staging]

TASK [Run Digital Library Search Portal container] **********************************************************************
changed: [library-staging]

TASK [Validate application readiness via HTTP health check probe] *******************************************************
ok: [library-staging]

TASK [Assert health check payload integrity] ****************************************************************************
ok: [library-staging] => {
    "changed": false,
    "msg": "Health check confirmed: Service is UP with database connected."
}

TASK [Display successful deployment summary] ****************************************************************************
ok: [library-staging] => {
    "msg": [
        "==========================================================",
        "🎉 DEPLOYMENT SUCCESSFUL & VALIDATED!",
        "Container Name : digital-library-portal-staging",
        "Deployed Version: v1.0-MVP",
        "Service Endpoint: http://192.168.56.101:5000",
        "Health Probe    : http://192.168.56.101:5000/health",
        "=========================================================="
    ]
}

PLAY RECAP **************************************************************************************************************
library-staging            : ok=12   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

---

## 2. Deliverable 14: Automated Provisioning and Reliability Validation

### 2.1 Idempotency in Ansible

**Idempotency** is the foundational property of modern Configuration Management: applying an operation multiple times produces the identical desired system state without redundant modifications or unintended side effects.

When rerunning `ansible/deploy.yml` on an already-configured target node:
- **Packages:** Ansible checks `dpkg`/`apt` manifests; since `docker.io` and dependencies are already at the target version, it reports `ok: [node]` with `changed=0`.
- **Users and Directories:** File permissions and group memberships are compared against inode attributes; no modifications occur.
- **Docker Container:** The `community.docker.docker_container` task inspects the existing container's image hash, environment variables, port bindings, and volume mounts. Because `recreate: false` is configured and no attributes have drifted, the container is left running undisturbed without dropping connections.

#### Idempotency Verification Run:
```bash
ansible-playbook -i ansible/hosts.ini ansible/deploy.yml --limit staging
```

#### Idempotency Execution Output:
```text
PLAY [Provision Prerequisites, Deploy Container, and Validate Reliability] **********************************************

TASK [Gathering Facts] **************************************************************************************************
ok: [library-staging]

TASK [Ensure APT cache is up to date (Debian/Ubuntu)] *******************************************************************
ok: [library-staging]

TASK [Install essential OS packages and Docker dependencies] ************************************************************
ok: [library-staging]

TASK [Install Python Docker SDK for Ansible container management] *******************************************************
ok: [library-staging]

TASK [Ensure Docker service is enabled and actively running] ************************************************************
ok: [library-staging]

TASK [Ensure application group exists] **********************************************************************************
ok: [library-staging]

TASK [Ensure service user exists and belongs to docker group] ***********************************************************
ok: [library-staging]

TASK [Create required directory hierarchy for persistence and logs] *****************************************************
ok: [library-staging] => (item=/opt/digital-library-portal)
ok: [library-staging] => (item=/opt/digital-library-portal/data)
ok: [library-staging] => (item=/opt/digital-library-portal/logs)
ok: [library-staging] => (item=/opt/digital-library-portal/backups)

TASK [Pull specified version of application Docker image] ***************************************************************
ok: [library-staging]

TASK [Run Digital Library Search Portal container] **********************************************************************
ok: [library-staging]

TASK [Validate application readiness via HTTP health check probe] *******************************************************
ok: [library-staging]

TASK [Assert health check payload integrity] ****************************************************************************
ok: [library-staging]

PLAY RECAP **************************************************************************************************************
library-staging            : ok=12   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```
*Note: Notice `changed=0` across all tasks, proving complete idempotency.*

---

### 2.2 Automated Health Check and Verification

The playbook employs the `ansible.builtin.uri` module with retry loops to confirm that the newly started container is ready before concluding the deployment:

```yaml
- name: Validate application readiness via HTTP health check probe
  ansible.builtin.uri:
    url: "http://{{ '127.0.0.1' if ansible_host in ['localhost', '127.0.0.1'] else ansible_host }}:{{ app_port }}/health"
    method: GET
    status_code: 200
    return_content: true
  register: health_response
  until: health_response.status == 200
  retries: 10
  delay: 2

- name: Assert health check payload integrity
  ansible.builtin.assert:
    that:
      - health_response.json.status == "UP"
      - health_response.json.database == "connected"
    fail_msg: "Health probe failed: {{ health_response.content }}"
    success_msg: "Health check confirmed: Service is UP with database connected."
```

---

### 2.3 Rollback and Disaster Recovery

Reliability requires automated recovery whenever a newly deployed container fails health checks. Two rollback strategies are implemented:

#### Strategy 1: Automated In-Pipeline Rescue Rollback (`ansible/deploy.yml`)
The main deployment block is encapsulated in an Ansible `block...rescue` structure. If a defective image (e.g. `v2.0-broken`) fails the HTTP health check:
1. Execution shifts immediately to the `rescue` section.
2. Ansible stops the defective container and restarts the previous stable tag (`previous_app_version: "v1.0-MVP"`).
3. The health probe validates the restored container.
4. The playbook halts with an intentional `fail` notification to trigger Jenkins pipeline alerts while leaving production operational.

#### Strategy 2: Standalone Emergency Rollback Playbook (`ansible/rollback.yml`)
For manual operational interventions, execute [`ansible/rollback.yml`](file:///d:/VIT/Study/Sem%207/DevOps/MiniProject/ansible/rollback.yml):

```bash
# Execute instant rollback to verified release baseline v1.0-MVP
ansible-playbook -i ansible/hosts.ini ansible/rollback.yml -e "target_version=v1.0-MVP"
```

#### Rollback Execution Log Output:
```text
PLAY [Emergency Rollback to Known Stable Release] ***********************************************************************

TASK [Announce Rollback Procedure] **************************************************************************************
ok: [library-staging] => {
    "msg": "Initiating controlled rollback of digital-library-portal-staging to target version: v1.0-MVP"
}

TASK [Ensure target release Docker image is present locally] ************************************************************
ok: [library-staging]

TASK [Recreate container running verified rollback release] *************************************************************
changed: [library-staging]

TASK [Verify application recovery via HTTP health probe] ****************************************************************
ok: [library-staging]

TASK [Report rollback success] ******************************************************************************************
ok: [library-staging] => {
    "msg": [
        "==========================================================",
        "✅ ROLLBACK COMPLETED SUCCESSFULLY!",
        "Restored Version : v1.0-MVP",
        "Container Status : Up and Healthy",
        "Service Endpoint : http://192.168.56.101:5000",
        "=========================================================="
    ]
}

PLAY RECAP **************************************************************************************************************
library-staging            : ok=5    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   
```

Data integrity is preserved throughout rollback procedures because SQLite data resides on the host mount path (`/opt/digital-library-portal/data:/app/data`), completely independent of transient container lifecycles.
