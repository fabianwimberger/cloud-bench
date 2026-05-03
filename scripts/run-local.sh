#!/bin/bash
# Local benchmark runner script (supports Hetzner, AWS, OVHcloud, OCI, and GCP)
set -e

# Configuration
RUN_ID="local-$(date +%Y%m%d-%H%M%S)"
PROVIDER="${PROVIDER:-hetzner}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Auto-detect region based on provider
if [ -z "$REGION" ]; then
    case "$PROVIDER" in
        hetzner)  REGION="fsn1" ;;
        aws)      REGION="eu-central-1" ;;
        ovhcloud) REGION="DE1" ;;
        oci)      REGION="eu-frankfurt-1" ;;
        gcp)      REGION="europe-west3" ;;
        azure)    REGION="northeurope" ;;
        *)        REGION="fsn1" ;;
    esac
fi

echo "Cloud-Bench Local Runner"
echo "Provider: $PROVIDER"
echo "Region: $REGION"
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

# Validate credentials based on provider
validate_credentials() {
    case "$PROVIDER" in
        hetzner)
            if [ -z "$HCLOUD_TOKEN" ]; then
                echo "[ERROR] HCLOUD_TOKEN not set!"
                echo "Set it with: export HCLOUD_TOKEN=your-token"
                exit 1
            fi
            ;;
        aws)
            if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
                echo "[ERROR] AWS credentials not set!"
                echo "Set them with:"
                echo "  export AWS_ACCESS_KEY_ID=your-key-id"
                echo "  export AWS_SECRET_ACCESS_KEY=your-secret-key"
                exit 1
            fi
            ;;
        ovhcloud)
            local ovh_missing=()
            [ -z "$OVH_OPENSTACK_USERNAME" ] && ovh_missing+=("OVH_OPENSTACK_USERNAME")
            [ -z "$OVH_OPENSTACK_PASSWORD" ] && ovh_missing+=("OVH_OPENSTACK_PASSWORD")
            [ -z "$OVH_CLOUD_PROJECT_ID" ] && ovh_missing+=("OVH_CLOUD_PROJECT_ID")
            if [ ${#ovh_missing[@]} -ne 0 ]; then
                echo "[ERROR] OVHcloud credentials not set: ${ovh_missing[*]}"
                echo "Set them with:"
                echo "  export OVH_OPENSTACK_USERNAME=user-xxxxxxxxxxxxxxxx"
                echo "  export OVH_OPENSTACK_PASSWORD=your-password"
                echo "  export OVH_CLOUD_PROJECT_ID=your-project-id"
                exit 1
            fi
            ;;
        oci)
            local oci_missing=()
            [ -z "$OCI_TENANCY_OCID" ] && oci_missing+=("OCI_TENANCY_OCID")
            [ -z "$OCI_USER_OCID" ] && oci_missing+=("OCI_USER_OCID")
            [ -z "$OCI_FINGERPRINT" ] && oci_missing+=("OCI_FINGERPRINT")
            [ -z "$OCI_PRIVATE_KEY" ] && oci_missing+=("OCI_PRIVATE_KEY")
            [ -z "$OCI_COMPARTMENT_ID" ] && oci_missing+=("OCI_COMPARTMENT_ID")
            if [ ${#oci_missing[@]} -ne 0 ]; then
                echo "[ERROR] OCI credentials not set: ${oci_missing[*]}"
                echo "Set them with:"
                echo "  export OCI_TENANCY_OCID=ocid1.tenancy.oc1..xxx"
                echo "  export OCI_USER_OCID=ocid1.user.oc1..xxx"
                echo "  export OCI_FINGERPRINT=aa:bb:cc:..."
                echo "  export OCI_PRIVATE_KEY=\$(cat ~/.oci/oci_api_key.pem)"
                echo "  export OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxx"
                exit 1
            fi
            ;;
        gcp)
            local gcp_missing=()
            [ -z "$GCP_PROJECT_ID" ] && gcp_missing+=("GCP_PROJECT_ID")
            [ -z "$GCP_CREDENTIALS" ] && gcp_missing+=("GCP_CREDENTIALS")
            if [ ${#gcp_missing[@]} -ne 0 ]; then
                echo "[ERROR] GCP credentials not set: ${gcp_missing[*]}"
                echo "Set them with:"
                echo "  export GCP_PROJECT_ID=your-project-id"
                echo "  export GCP_CREDENTIALS=\$(cat /path/to/service-account-key.json)"
                exit 1
            fi
            ;;
        azure)
            local azure_missing=()
            [ -z "$AZURE_SUBSCRIPTION_ID" ] && azure_missing+=("AZURE_SUBSCRIPTION_ID")
            [ -z "$AZURE_CLIENT_ID" ] && azure_missing+=("AZURE_CLIENT_ID")
            [ -z "$AZURE_CLIENT_SECRET" ] && azure_missing+=("AZURE_CLIENT_SECRET")
            [ -z "$AZURE_TENANT_ID" ] && azure_missing+=("AZURE_TENANT_ID")
            if [ ${#azure_missing[@]} -ne 0 ]; then
                echo "[ERROR] Azure credentials not set: ${azure_missing[*]}"
                echo "Set them with:"
                echo "  export AZURE_SUBSCRIPTION_ID=your-subscription-id"
                echo "  export AZURE_CLIENT_ID=your-client-id"
                echo "  export AZURE_CLIENT_SECRET=your-client-secret"
                echo "  export AZURE_TENANT_ID=your-tenant-id"
                exit 1
            fi
            ;;
        *)
            echo "[ERROR] Unsupported provider: $PROVIDER"
            exit 1
            ;;
    esac

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

# Pass every credential var on every run — the OCI and Google provider blocks
# validate their config at plan time even when no resources of that kind exist.
build_tf_vars() {
    local action="$1"
    shift
    local common_vars=(
        -var="run_id=$RUN_ID"
        -var="cloud_provider=$PROVIDER"
        -var="default_region=$REGION"
        -var="ssh_public_key_path=$SSH_PUB_KEY_PATH"
        -var="allowed_ssh_ips=[\"$ALLOWED_SSH_IPS\"]"
        -var="hcloud_token=${HCLOUD_TOKEN:-0000000000000000000000000000000000000000000000000000000000000000}"
        -var="aws_access_key_id=${AWS_ACCESS_KEY_ID:-unused}"
        -var="aws_secret_access_key=${AWS_SECRET_ACCESS_KEY:-unused}"
        -var="ovh_openstack_username=${OVH_OPENSTACK_USERNAME:-unused}"
        -var="ovh_openstack_password=${OVH_OPENSTACK_PASSWORD:-unused}"
        -var="ovh_cloud_project_id=${OVH_CLOUD_PROJECT_ID:-unused}"
        -var="oci_tenancy_ocid=${OCI_TENANCY_OCID:-unused}"
        -var="oci_user_ocid=${OCI_USER_OCID:-unused}"
        -var="oci_fingerprint=${OCI_FINGERPRINT:-unused}"
        -var="oci_private_key=${OCI_PRIVATE_KEY:-unused}"
        -var="oci_compartment_id=${OCI_COMPARTMENT_ID:-unused}"
        -var="gcp_project_id=${GCP_PROJECT_ID:-unused}"
        -var="gcp_credentials=${GCP_CREDENTIALS:-}"
        -var="azure_subscription_id=${AZURE_SUBSCRIPTION_ID:-}"
        -var="azure_client_id=${AZURE_CLIENT_ID:-}"
        -var="azure_client_secret=${AZURE_CLIENT_SECRET:-}"
        -var="azure_tenant_id=${AZURE_TENANT_ID:-}"
    )

    common_vars+=("$@")
    printf '%s\n' "${common_vars[@]}"
}

# Run terraform with provider-specific vars
run_terraform() {
    local action="$1"
    shift
    local vars=()
    while IFS= read -r line; do
        vars+=("$line")
    done < <(build_tf_vars "$action" "$@")
    terraform "$action" -auto-approve "${vars[@]}"
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

    run_terraform apply \
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
        --input ansible/results/ \
        --output frontend/public/data/ \
        --config config/instances.yaml \
        --region "$REGION" \
        --provider "$PROVIDER" || {
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
        run_terraform destroy
        echo "[OK] Cleanup complete!"
    else
        echo "[WARN] Infrastructure left running. Don't forget to clean up!"
        echo "Run 'cd terraform && terraform destroy' when done."
    fi
}

# Handle Ctrl+C
trap 'echo "\n[ERROR] Interrupted!"; exit 130' INT

main "$@"
