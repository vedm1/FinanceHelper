#!/bin/bash
export BW_SESSION=$(bw unlock --raw)

# Check if item exists
ITEM_ID=$(bw list items --search "project-name-env" | jq -r '.[0].id // empty')

if [ -z "$ITEM_ID" ]; then
  # Create new secure note
  bw get template item | jq \
    --arg name "project-name-env" \
    --arg notes "$(cat .env)" \
    '.name=$name | .type=2 | .secureNote.type=0 | .notes=$notes' | \
    bw encode | bw create item
  echo "✓ Created new .env in Bitwarden"
else
  # Update existing note
  bw get item "$ITEM_ID" | jq \
    --arg notes "$(cat .env)" \
    '.notes=$notes' | \
    bw encode | bw edit item "$ITEM_ID"
  echo "✓ Updated .env in Bitwarden"
fi

bw sync