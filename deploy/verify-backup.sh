#!/usr/bin/env bash
set -euo pipefail

BACKUP="${1:?Usage: verify-backup.sh /path/to/backup.dump}"
: "${BMB_RESTORE_TEST_DATABASE_URL:?BMB_RESTORE_TEST_DATABASE_URL is required}"
: "${BMB_ALLOW_RESTORE_TEST:?Set BMB_ALLOW_RESTORE_TEST=true to acknowledge the test DB will be overwritten}"

if [[ "$BMB_ALLOW_RESTORE_TEST" != "true" ]]; then
  echo "Refusing restore test without BMB_ALLOW_RESTORE_TEST=true" >&2
  exit 2
fi

if [[ ! -f "$BACKUP" ]]; then
  echo "Backup not found: $BACKUP" >&2
  exit 2
fi

if [[ -f "$BACKUP.sha256" ]]; then
  (cd "$(dirname "$BACKUP")" && sha256sum -c "$(basename "$BACKUP").sha256")
fi

TEST_URL="${BMB_RESTORE_TEST_DATABASE_URL/postgresql+psycopg:\/\//postgresql:\/\/}"

pg_restore --clean --if-exists --no-owner --dbname="$TEST_URL" "$BACKUP"
psql "$TEST_URL" -v ON_ERROR_STOP=1 -c 'SELECT COUNT(*) AS orders FROM orders;'
psql "$TEST_URL" -v ON_ERROR_STOP=1 -c 'SELECT COUNT(*) AS variants FROM product_variants;'
psql "$TEST_URL" -v ON_ERROR_STOP=1 -c 'SELECT version_num FROM alembic_version;'

echo "Restore verification passed."
