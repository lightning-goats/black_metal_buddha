#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?DATABASE_URL is required}"

BACKUP_DIR="${BMB_BACKUP_DIR:-/var/backups/blackmetalbuddha}"
RETENTION_DAYS="${BMB_BACKUP_RETENTION_DAYS:-30}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TARGET="$BACKUP_DIR/blackmetalbuddha-$STAMP.dump"
TMP="$TARGET.tmp"

DB_URL="${DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

mkdir -p "$BACKUP_DIR"
umask 077

pg_dump --format=custom --compress=6 --no-owner --file="$TMP" "$DB_URL"
mv "$TMP" "$TARGET"
sha256sum "$TARGET" > "$TARGET.sha256"

find "$BACKUP_DIR" -type f \( -name 'blackmetalbuddha-*.dump' -o -name 'blackmetalbuddha-*.dump.sha256' \) -mtime "+$RETENTION_DAYS" -delete

printf 'Created %s\n' "$TARGET"
