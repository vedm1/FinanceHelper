#!/bin/bash
export BW_SESSION=$(bw unlock --raw)
bw sync
bw get item "project-name-env" | jq -r '.notes' > .env
echo "✓ .env synced from Bitwarden"