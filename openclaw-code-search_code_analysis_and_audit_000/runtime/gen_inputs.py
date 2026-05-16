#!/usr/bin/env python3
"""
Generate a realistic, messy legacy fintech codebase for the audit task.
The agent must search through this to produce audit_report.json.
"""

import os
import random
from pathlib import Path

random.seed(42)

BASE = Path("/workspace/legacybank")

# ─── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "cmd/server",
    "cmd/worker",
    "internal/payments",
    "internal/auth",
    "internal/ledger",
    "internal/compliance",
    "internal/notifications",
    "pkg/database",
    "pkg/cache",
    "pkg/crypto",
    "api/v1",
    "api/v2",
    "configs",
    "scripts",
    "tests/unit",
    "tests/integration",
    "deployments/k8s",
    "deployments/docker",
    "tools/migrate",
    "tools/audit",
    "vendor/github.com/lib/pq",
    "vendor/github.com/gorilla/mux",
    "web/static",
    "web/templates",
    "analytics/pipeline",
    "analytics/reports",
]

for d in dirs:
    (BASE / d).mkdir(parents=True, exist_ok=True)


def write(path, content):
    path = BASE / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ─── Go source files ──────────────────────────────────────────────────────────

write("cmd/server/main.go", '''\
package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/gorilla/mux"
	"legacybank/internal/payments"
	"legacybank/internal/auth"
)

func main() {
	r := mux.NewRouter()
	r.HandleFunc("/pay", payments.HandlePayment)
	r.HandleFunc("/auth", auth.HandleLogin)
	log.Println("Starting server on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatal(err)
	}
}
''')

write("cmd/worker/worker.go", '''\
package main

import (
	"fmt"
	"legacybank/internal/ledger"
	"legacybank/internal/notifications"
	"time"
)

func main() {
	for {
		ledger.ProcessQueue()
		notifications.SendPending()
		// TODO: replace with event-driven approach
		time.Sleep(5 * time.Second)
	}
}
''')

write("internal/payments/payments.go", '''\
package payments

import (
	"fmt"
	"legacybank/pkg/database"
	"legacybank/pkg/crypto"
	"errors"
)

// HandlePayment processes incoming payment requests.
func HandlePayment(w http.ResponseWriter, r *http.Request) {
	// DEPRECATED: use ProcessPaymentV2 instead
	result, err := ProcessPaymentV1(r)
	if err != nil {
		fmt.Println("payment error:", err)
		return
	}
	database.Save(result)
}

// ProcessPaymentV1 is the DEPRECATED legacy payment processor.
// WARNING: This function uses insecure_hash() which is flagged by compliance.
func ProcessPaymentV1(r *http.Request) (string, error) {
	raw := r.FormValue("amount")
	if raw == "" {
		return "", errors.New("amount missing")
	}
	hashed := crypto.insecure_hash(raw)
	fmt.Println("ProcessPaymentV1 called with amount:", raw)
	return hashed, nil
}

// ProcessPaymentV2 is the current approved payment processor.
func ProcessPaymentV2(amount string) (string, error) {
	hashed := crypto.SecureHash(amount)
	return hashed, nil
}
''')

write("internal/payments/payments_test.go", '''\
package payments

import (
	"testing"
)

func TestProcessPaymentV1_EmptyAmount(t *testing.T) {
	// TODO: remove this test once V1 is fully deprecated
	_, err := ProcessPaymentV1(nil)
	if err == nil {
		t.Fatal("expected error for empty amount")
	}
}

func TestProcessPaymentV2_Basic(t *testing.T) {
	result, err := ProcessPaymentV2("100.00")
	if err != nil || result == "" {
		t.Fatal("expected non-empty result")
	}
}
''')

write("internal/auth/auth.go", '''\
package auth

import (
	"fmt"
	"legacybank/pkg/database"
	"legacybank/pkg/crypto"
)

// HandleLogin processes user authentication.
func HandleLogin(w http.ResponseWriter, r *http.Request) {
	user := r.FormValue("username")
	pass := r.FormValue("password")

	// DEPRECATED: use AuthenticateV2 — this uses insecure_hash
	token, err := AuthenticateV1(user, pass)
	if err != nil {
		fmt.Println("auth error:", err)
		return
	}
	fmt.Println("login success for user:", user)
	database.StoreSession(token)
}

// AuthenticateV1 is DEPRECATED. Uses insecure_hash() for password comparison.
func AuthenticateV1(user, pass string) (string, error) {
	hashed := crypto.insecure_hash(pass)
	stored := database.GetStoredHash(user)
	if hashed != stored {
		return "", fmt.Errorf("invalid credentials")
	}
	return hashed, nil
}

func AuthenticateV2(user, pass string) (string, error) {
	hashed := crypto.SecureHash(pass)
	stored := database.GetStoredHash(user)
	if hashed != stored {
		return "", fmt.Errorf("invalid credentials")
	}
	token := crypto.GenerateToken(user)
	return token, nil
}
''')

write("internal/auth/auth_test.go", '''\
package auth

import "testing"

func TestAuthenticateV1_InvalidCredentials(t *testing.T) {
	// Legacy test — keep until V1 removed
	_, err := AuthenticateV1("baduser", "badpass")
	if err == nil {
		t.Fatal("expected error")
	}
}

func TestAuthenticateV2_ValidCredentials(t *testing.T) {
	// Requires test DB fixture
	t.Skip("integration test — run with -tags=integration")
}
''')

write("internal/ledger/ledger.go", '''\
package ledger

import (
	"fmt"
	"legacybank/pkg/database"
)

func ProcessQueue() {
	entries := database.FetchPendingEntries()
	for _, e := range entries {
		if err := applyEntry(e); err != nil {
			fmt.Println("ledger error:", err)
		}
	}
}

func applyEntry(e interface{}) error {
	// TODO: add double-entry bookkeeping validation
	fmt.Println("applying ledger entry:", e)
	return nil
}
''')

write("internal/compliance/checker.go", '''\
package compliance

import (
	"fmt"
	"legacybank/pkg/crypto"
	"legacybank/pkg/database"
)

// RunComplianceCheck scans recent transactions for policy violations.
func RunComplianceCheck() {
	txns := database.FetchRecentTransactions()
	for _, t := range txns {
		// DEPRECATED: insecure_hash usage flagged by auditors
		sig := crypto.insecure_hash(t.ID)
		if sig == "" {
			fmt.Println("compliance warning: empty signature for txn", t.ID)
		}
	}
}
''')

write("internal/compliance/checker_test.go", '''\
package compliance

import "testing"

func TestRunComplianceCheck_NoTransactions(t *testing.T) {
	// Should not panic on empty transaction set
	RunComplianceCheck()
}
''')

write("internal/notifications/notify.go", '''\
package notifications

import "fmt"

func SendPending() {
	fmt.Println("sending pending notifications")
	// TODO: integrate with email service
}
''')

write("pkg/database/db.go", '''\
package database

import (
	"fmt"
	"database/sql"
	_ "github.com/lib/pq"
)

var db *sql.DB

func Connect(dsn string) error {
	var err error
	db, err = sql.Open("postgres", dsn)
	return err
}

func Save(data interface{}) error {
	fmt.Println("saving:", data)
	return nil
}

func FetchPendingEntries() []interface{} {
	return nil
}

func FetchRecentTransactions() []struct{ ID string } {
	return nil
}

func GetStoredHash(user string) string {
	return ""
}

func StoreSession(token string) {}
''')

write("pkg/crypto/crypto.go", '''\
package crypto

import (
	"crypto/sha256"
	"crypto/md5"
	"fmt"
)

// insecure_hash uses MD5 — DEPRECATED, flagged by compliance team.
// All usages must be replaced with SecureHash before Q3 deadline.
func insecure_hash(input string) string {
	h := md5.Sum([]byte(input))
	return fmt.Sprintf("%x", h)
}

// SecureHash uses SHA-256 and is the approved hashing function.
func SecureHash(input string) string {
	h := sha256.Sum256([]byte(input))
	return fmt.Sprintf("%x", h)
}

func GenerateToken(user string) string {
	return SecureHash(user + "salt")
}
''')

write("pkg/cache/cache.go", '''\
package cache

import "sync"

var store = sync.Map{}

func Set(key, value string) {
	store.Store(key, value)
}

func Get(key string) (string, bool) {
	v, ok := store.Load(key)
	if !ok {
		return "", false
	}
	return v.(string), true
}
''')

write("api/v1/routes.go", '''\
package v1

import "github.com/gorilla/mux"

func RegisterRoutes(r *mux.Router) {
	r.HandleFunc("/api/v1/payment", paymentHandler)
	r.HandleFunc("/api/v1/login", loginHandler)
}
''')

write("api/v2/routes.go", '''\
package v2

import "github.com/gorilla/mux"

func RegisterRoutes(r *mux.Router) {
	r.HandleFunc("/api/v2/payment", paymentHandlerV2)
	r.HandleFunc("/api/v2/login", loginHandlerV2)
	r.HandleFunc("/api/v2/health", healthCheck)
}
''')

# ─── Config files ──────────────────────────────────────────────────────────────

write("configs/app.yaml", '''\
server:
  port: 8080
  timeout: 30s
database:
  host: localhost
  port: 5432
  name: legacybank
  user: appuser
  # password set via env: DB_PASSWORD
feature_flags:
  use_payment_v2: false
  use_auth_v2: true
  enable_compliance_scan: true
''')

write("configs/logging.yaml", '''\
level: info
format: json
output: stdout
rotate:
  max_size_mb: 100
  max_backups: 5
''')

write("configs/compliance.toml", '''\
[scan]
interval = "24h"
deprecated_functions = ["insecure_hash", "ProcessPaymentV1", "AuthenticateV1"]
alert_email = "compliance@legacybank.internal"

[thresholds]
max_deprecated_calls = 0
''')

write("deployments/k8s/deployment.yaml", '''\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: legacybank-server
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: server
          image: legacybank/server:latest
          ports:
            - containerPort: 8080
''')

write("deployments/docker/docker-compose.yml", '''\
version: "3.8"
services:
  server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_PASSWORD=secret
  postgres:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: secret
''')

write("scripts/migrate.sh", '''\
#!/usr/bin/env bash
# Runs database migrations
set -e
psql "$DATABASE_URL" -f migrations/001_initial.sql
psql "$DATABASE_URL" -f migrations/002_add_sessions.sql
''')

write("scripts/build.sh", '''\
#!/usr/bin/env bash
set -e
go build -o bin/server ./cmd/server
go build -o bin/worker ./cmd/worker
''')

write("tools/audit/audit.go", '''\
package main

import "fmt"

func main() {
	fmt.Println("Audit tool — stub. Implement full audit logic.")
}
''')

write("tools/migrate/migrate.go", '''\
package main

import (
	"fmt"
	"legacybank/pkg/database"
)

func main() {
	fmt.Println("Running migrations...")
	database.Connect("postgres://localhost/legacybank")
}
''')

write("analytics/pipeline/ingest.go", '''\
package pipeline

import "fmt"

func Ingest(source string) error {
	fmt.Println("ingesting from:", source)
	return nil
}
''')

write("analytics/reports/monthly.go", '''\
package reports

import "fmt"

func GenerateMonthly() {
	fmt.Println("generating monthly report")
	// TODO: pull from data warehouse
}
''')

# ─── Vendor stubs ─────────────────────────────────────────────────────────────

write("vendor/github.com/lib/pq/pq.go", '''\
// stub vendor file
package pq
''')

write("vendor/github.com/gorilla/mux/mux.go", '''\
// stub vendor file
package mux

type Router struct{}
func NewRouter() *Router { return &Router{} }
func (r *Router) HandleFunc(path string, f interface{}) {}
''')

# ─── Extra distractor files ───────────────────────────────────────────────────

write("web/static/app.js", '''\
// Frontend placeholder
console.log("LegacyBank v1.0");
''')

write("web/templates/index.html", '''\
<!DOCTYPE html>
<html><body><h1>LegacyBank Portal</h1></body></html>
''')

write("go.mod", '''\
module legacybank

go 1.21

require (
	github.com/gorilla/mux v1.8.0
	github.com/lib/pq v1.10.7
)
''')

write(".gitignore", '''\
bin/
*.log
.env
''')

# ─── Python analytics scripts (distractor, different type) ────────────────────

write("analytics/reports/fraud_detect.py", '''\
#!/usr/bin/env python3
"""Fraud detection heuristics — experimental."""

def check_velocity(transactions):
    """Flag accounts with > 10 txns in 60s."""
    # TODO: insecure_hash usage needs to be audited here too
    from hashlib import md5
    flagged = []
    for t in transactions:
        sig = md5(t["id"].encode()).hexdigest()  # insecure_hash equivalent
        if t.get("count", 0) > 10:
            flagged.append(sig)
    return flagged

if __name__ == "__main__":
    print(check_velocity([]))
''')

write("analytics/pipeline/transform.py", '''\
#!/usr/bin/env python3
"""Data transformation pipeline."""

import json

def transform(raw):
    return {k: str(v).strip() for k, v in raw.items()}

if __name__ == "__main__":
    sample = {"amount": " 100.00 ", "currency": "USD"}
    print(json.dumps(transform(sample)))
''')

# ─── Additional test files to inflate count ───────────────────────────────────

write("tests/unit/crypto_test.go", '''\
package unit

import "testing"

func TestInsecureHash_KnownValue(t *testing.T) {
	// MD5 of "hello" = 5d41402abc4b2a76b9719d911017c592
	// This test documents the deprecated behavior
	result := insecure_hash("hello")
	if result != "5d41402abc4b2a76b9719d911017c592" {
		t.Fatalf("unexpected: %s", result)
	}
}
''')

write("tests/unit/ledger_test.go", '''\
package unit

import "testing"

func TestApplyEntry_Noop(t *testing.T) {
	// placeholder
	t.Log("ledger unit test placeholder")
}
''')

write("tests/integration/payment_integration_test.go", '''\
package integration

import "testing"

func TestPaymentFlow_EndToEnd(t *testing.T) {
	t.Skip("requires running postgres")
}

func TestAuthFlow_EndToEnd(t *testing.T) {
	t.Skip("requires running postgres")
}
''')

write("tests/integration/compliance_integration_test.go", '''\
package integration

import "testing"

func TestComplianceScan_LiveDB(t *testing.T) {
	t.Skip("integration only")
}
''')

print("Workspace generated at:", BASE)
print("Files created:")
for f in sorted(BASE.rglob("*")):
    if f.is_file():
        print(" ", f.relative_to(BASE))