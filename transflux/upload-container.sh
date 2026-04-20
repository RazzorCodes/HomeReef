#!/usr/bin/env bash
# upload-container.sh — Upload a locally built container image to a remote registry.
#
# Usage:
#   ./upload-container.sh --source localhost/homereef-transflux:v1.0.1 --dest 192.168.0.127:5000/homereef:v1.0.1

set -euo pipefail

SOURCE=""
DEST=""
TLS_VERIFY="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE="$2"
      shift 2
      ;;
    --dest)
      DEST="$2"
      shift 2
      ;;
    --insecure)
      TLS_VERIFY="false"
      shift
      ;;
    *)
      echo "Unknown argument: $1"
      echo "Usage: $0 --source <source> --dest <dest> [--insecure]"
      exit 1
      ;;
  esac
done

if [[ -z "$SOURCE" || -z "$DEST" ]]; then
  echo "Error: Both --source and --dest are required."
  echo "Usage: $0 --source <source_image> --dest <dest_image>"
  echo "Example: $0 --source localhost/homereef-transflux:latest --dest 192.168.0.127:5000/homereef-transflux:latest"
  exit 1
fi

echo "==> Uploading container image..."
echo "    Source: $SOURCE"
echo "    Dest:   $DEST"

# Note: Disabling TLS verification (--dest-tls-verify=false) is insecure and should only be used for testing logs
# Copy from local podman (containers-storage) to remote registry
skopeo copy --all --dest-tls-verify="${TLS_VERIFY}" "containers-storage:${SOURCE}" "docker://${DEST}"

echo "==> Upload complete!"
