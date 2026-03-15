#!/bin/bash
# Parse instance input for Terraform
# Outputs Terraform list format or "null" for "all"

set -e

INSTANCES_INPUT="$1"

if [ -z "$INSTANCES_INPUT" ]; then
    echo "Error: No instances specified" >&2
    exit 1
fi

if [ "$INSTANCES_INPUT" = "all" ]; then
    echo "null"
else
    # Validate instance IDs contain only allowed characters
    if ! echo "$INSTANCES_INPUT" | grep -qE '^[a-zA-Z0-9,._-]+$'; then
        echo "Error: Invalid instance IDs" >&2
        exit 1
    fi
    # Convert comma-separated list to Terraform list format
    echo '["'$(echo "$INSTANCES_INPUT" | sed 's/,/","/g')'"]'
fi
