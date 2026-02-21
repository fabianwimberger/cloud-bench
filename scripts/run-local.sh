#!/bin/bash
# Local Hetzner benchmark runner script
set -e

# Configuration
RUN_ID="local-$(date +%Y%m%d-%H%M%S)"
PROVIDER="${PROVIDER:-hetzner}"
REGION="${REGION:-fsn1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Cloud-Bench Local Runner"
echo "Run ID: $RUN_ID"
echo ""

# Check prerequisites
check_prereqs() {
    local missing=()
    
    command -v terraform >/dev/null 2>&1 || missing+=("terraform")
    command -v ansible-playbook >/dev/null 2>&1 || missing+=("ansible")
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    
    if [ ${#missing[@]} -ne 0 ]; then
        echo "[ERROR] Missing prerequisites: ${missing[*]}"
        echo "Please install them and try again."
        exit 1
    fi
}

# Check SSH key
check_ssh_key() {
    # Allow custom SSH key path via environment variable
    SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/id_ed25519}"
    SSH_PUB_KEY_PATH="${SSH_KEY_PATH}.pub"
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        echo "[WARN] No SSH key found at $SSH_KEY_PATH"
        echo "Generating new SSH key pair..."
        ssh-keygen -t ed25519 -f "$SSH_KEY_PATH" -N ""
    fi
    
    # Export for use in other functions
    export SSH_KEY_PATH
    export SSH_PUB_KEY_PATH
}

# Validate credentials
validate_credentials() {
    if [ -z "$HCLOUD_TOKEN" ]; then
        echo "[ERROR] HCLOUD_TOKEN not set!"
        echo "Set it with: export HCLOUD_TOKEN=your-token"
        exit 1
    fi

    # Get local IP for firewall if not set
    if [ -z "$ALLOWED_SSH_IPS" ]; then
        echo "[WARN] ALLOWED_SSH_IPS not set, detecting your IP..."
        # Try multiple IP detection services with fallback
        IP_SERVICES=(
            "https://api.ipify.org"
            "https://icanhazip.com"
            "https://ifconfig.me"
            "https://ipecho.net/plain"
        )
        MY_IP=""
        for service in "${IP_SERVICES[@]}"; do
            MY_IP=$(curl -s --max-time 5 "$service" 2>/dev/null) && break
        done
        if [ -n "$MY_IP" ]; then
            export ALLOWED_SSH_IPS="${MY_IP}/32"
            echo "[OK] Detected IP: ${ALLOWED_SSH_IPS}"
        else
            echo "[ERROR] Could not detect your IP from any service. Please set ALLOWED_SSH_IPS manually:"
            echo "export ALLOWED_SSH_IPS=\"your-ip/32\""
            exit 1
        fi
    fi
}

# Main execution
main() {
    cd "$PROJECT_DIR"
    
    check_prereqs
    check_ssh_key
    validate_credentials
    
    # Terraform apply
    echo "[INFO] Provisioning infrastructure..."
    cd terraform

    terraform init

    terraform apply -auto-approve \
        -var="run_id=$RUN_ID" \
        -var="cloud_provider=$PROVIDER" \
        -var="default_region=$REGION" \
        -var="hcloud_token=$HCLOUD_TOKEN" \
        -var="ssh_public_key_path=$SSH_PUB_KEY_PATH" \
        -var="allowed_ssh_ips=[\"$ALLOWED_SSH_IPS\"]" \
        || {
            echo "[ERROR] Terraform apply failed!"
            exit 1
        }
    
    # Generate Ansible inventory from Terraform output
    terraform output -raw ansible_inventory > ../ansible/inventory.ini

    cd ..

    # Wait for instances to be ready via SSH
    echo "[INFO] Waiting for instances to be ready..."
    for i in $(seq 1 60); do
      if ansible all -i ansible/inventory.ini -m raw -a "echo ready" \
        --private-key "$SSH_KEY_PATH" \
        -e "ansible_python_interpreter=auto" \
        --ssh-common-args="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" 2>/dev/null | grep -q "ready"; then
        echo "[OK] All instances are ready!"
        break
      fi
      if [ $i -eq 60 ]; then
        echo "[ERROR] Instances did not become ready in time"
        exit 1
      fi
      sleep 5
    done

    # Run benchmarks
    echo "[INFO] Running benchmarks..."
    cd ansible

    export RUN_ID
    ansible-playbook -i inventory.ini playbooks/benchmark.yml \
        --private-key "$SSH_KEY_PATH" \
        --extra-vars "run_id=$RUN_ID" || {
            echo "[WARN] Benchmark completed with some errors"
        }

    cd ..

    # Process results
    echo "[INFO] Processing results..."
    pip install -q -r scripts/requirements.txt 2>/dev/null || true

    python3 scripts/process_results.py \
        --input results/ \
        --output frontend/public/data/ \
        --config config/instances.yaml \
        --region "${REGION:-fsn1}" \
        --provider "${PROVIDER:-hetzner}" || {
            echo "[WARN] Result processing had issues"
        }

    echo ""
    echo "[OK] Benchmark complete!"
    echo "Results saved to: frontend/public/data/"
    echo ""
    
    # Show results preview
    if [ -f frontend/public/data/benchmark-results.csv ]; then
        echo "Top performers:"
        head -5 frontend/public/data/benchmark-results.csv | column -t -s,
    fi
    
    # Cleanup prompt
    echo ""
    read -p "Destroy infrastructure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "[INFO] Destroying infrastructure..."
        cd terraform
        terraform destroy -auto-approve \
            -var="run_id=$RUN_ID" \
            -var="cloud_provider=$PROVIDER" \
            -var="default_region=$REGION" \
            -var="hcloud_token=$HCLOUD_TOKEN" \
            -var="ssh_public_key_path=$SSH_PUB_KEY_PATH" \
            -var="allowed_ssh_ips=[\"$ALLOWED_SSH_IPS\"]"
        echo "[OK] Cleanup complete!"
    else
        echo "[WARN] Infrastructure left running. Don't forget to clean up!"
        echo "Run 'cd terraform && terraform destroy' when done."
    fi
}

# Handle Ctrl+C
trap 'echo "\n[ERROR] Interrupted!"; exit 130' INT

main "$@"
