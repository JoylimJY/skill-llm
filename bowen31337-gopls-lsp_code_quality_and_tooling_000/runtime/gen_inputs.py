#!/usr/bin/env python3
"""
Generate a messy, realistic Go microservice workspace for the currency conversion task.
The agent must: fix formatting, resolve vet issues, set up go module, make tests pass,
and create gopls.yaml with correct configuration.
"""

import os
import random

random.seed(42)

workspace = "/workspace"

# ── directory structure ────────────────────────────────────────────────────────
dirs = [
    "currencyservice",
    "currencyservice/converter",
    "currencyservice/converter/testdata",
    "currencyservice/config",
    "currencyservice/internal/rates",
    "currencyservice/internal/cache",
    "currencyservice/cmd/server",
    "currencyservice/docs",
    "currencyservice/scripts",
    "currencyservice/deployments",
    "currencyservice/deployments/k8s",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ───────────────────────────────────────────────────────────
distractors = {
    "currencyservice/docs/architecture.md": """\
# Currency Service Architecture

This service handles real-time currency conversions.
It is intended to replace the legacy FOREX handler.
""",
    "currencyservice/scripts/deploy.sh": """\
#!/bin/bash
echo "Deploying currency service..."
kubectl apply -f deployments/k8s/
""",
    "currencyservice/deployments/k8s/deployment.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: currency-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: currency-service
""",
    "currencyservice/internal/cache/cache.go": """\
package cache

import "sync"

type RateCache struct {
	mu    sync.RWMutex
	store map[string]float64
}

func NewRateCache() *RateCache {
	return &RateCache{store: make(map[string]float64)}
}

func (c *RateCache) Set(key string, val float64) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.store[key] = val
}

func (c *RateCache) Get(key string) (float64, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	v, ok := c.store[key]
	return v, ok
}
""",
    "currencyservice/internal/rates/rates.go": """\
package rates

// SupportedCurrencies lists all ISO 4217 codes supported by this service.
var SupportedCurrencies = []string{
	"USD", "EUR", "GBP", "JPY", "AUD",
	"CAD", "CHF", "CNY", "SEK", "NZD",
}
""",
    "currencyservice/config/config.go": """\
package config

import "os"

// ServiceConfig holds runtime configuration.
type ServiceConfig struct {
	Port        string
	LogLevel    string
	BaseURL     string
}

func Load() ServiceConfig {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	return ServiceConfig{
		Port:     port,
		LogLevel: "info",
		BaseURL:  "https://api.exchangerate.example.com",
	}
}
""",
    "currencyservice/converter/testdata/sample_rates.json": """\
{
  "base": "USD",
  "rates": {
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 149.50
  }
}
""",
    "currencyservice/deployments/k8s/service.yaml": """\
apiVersion: v1
kind: Service
metadata:
  name: currency-service
spec:
  selector:
    app: currency-service
  ports:
    - port: 80
      targetPort: 8080
""",
    "currencyservice/docs/api.md": """\
# API Reference

## GET /convert?from=USD&to=EUR&amount=100

Returns the converted amount using the latest cached rate.

## GET /health

Returns 200 OK if the service is healthy.
""",
    "currencyservice/scripts/run_tests.sh": """\
#!/bin/bash
cd currencyservice && go test ./...
""",
    "currencyservice/internal/cache/cache_test_notes.txt": """\
TODO: add expiration logic to cache entries
TODO: benchmark concurrent read performance
""",
}

for path, content in distractors.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ── MAIN PROBLEM FILES ─────────────────────────────────────────────────────────

# 1. converter/converter.go — badly formatted, has vet issue (printf verb mismatch),
#    uses a shadowed variable, has unused parameter in exported function.
#    The agent must: gofmt it, fix vet errors so `go vet` passes, ensure it compiles.
converter_go = """\
package converter

import   "fmt"
import "errors"
import  "math"


// ErrUnknownCurrency is returned when the currency code is not recognised.
var ErrUnknownCurrency = errors.New( "unknown currency code" )

// rates maps currency pairs (FROM_TO) to their conversion factor.
var rates = map[string]float64{
"USD_EUR": 0.92,
"USD_GBP": 0.79,
"USD_JPY": 149.50,
"EUR_USD": 1.087,
"EUR_GBP": 0.859,
"GBP_USD": 1.266,
"JPY_USD": 0.0067,
}

// Convert converts an amount from one currency to another.
// precision controls how many decimal places are returned.
func Convert(from, to string, amount float64, precision int) (float64,  error) {
if from == to {
return amount, nil
}
key := from + "_" + to
rate, ok := rates[key]
if !ok {
// Bad format verb — should be %s not %d
fmt.Printf("unsupported pair: %d\\n", key)
return 0, ErrUnknownCurrency
}
result := amount * rate
factor := math.Pow(10, float64(precision))
result = math.Round(result * factor) / factor
return result, nil
}

// RoundTrip converts from->to->from and checks for drift.
// unused parameter: label is never used inside the function body.
func RoundTrip(from, to string, amount float64, label string) (float64, error) {
intermediate, err := Convert(from, to, amount, 6)
if err != nil {
return 0,  err
}
back, err := Convert(to, from, intermediate, 6)
if err != nil {
return 0, err
}
// shadow: err is re-declared with := in inner scope
{
result, err := back - amount, error(nil)
_ = err
return result, nil
}
_ = result
}
"""

# 2. converter/converter_test.go — valid tests (they should PASS after fixes)
converter_test_go = """\
package converter

import (
\t"math"
\t"testing"
)

func TestConvert_KnownPair(t *testing.T) {
\tgot, err := Convert("USD", "EUR", 100.0, 2)
\tif err != nil {
\t\tt.Fatalf("unexpected error: %v", err)
\t}
\tif math.Abs(got-92.0) > 0.01 {
\t\tt.Errorf("expected 92.0, got %f", got)
\t}
}

func TestConvert_SameCurrency(t *testing.T) {
\tgot, err := Convert("GBP", "GBP", 50.0, 2)
\tif err != nil {
\t\tt.Fatalf("unexpected error: %v", err)
\t}
\tif got != 50.0 {
\t\tt.Errorf("expected 50.0, got %f", got)
\t}
}

func TestConvert_UnknownPair(t *testing.T) {
\t_, err := Convert("USD", "XYZ", 100.0, 2)
\tif err == nil {
\t\tt.Error("expected error for unknown pair, got nil")
\t}
}

func TestRoundTrip_Small(t *testing.T) {
\tdrift, err := RoundTrip("USD", "EUR", 100.0, "test-label")
\tif err != nil {
\t\tt.Fatalf("unexpected error: %v", err)
\t}
\tif math.Abs(drift) > 0.01 {
\t\tt.Errorf("drift too large: %f", drift)
\t}
}
"""

# 3. cmd/server/main.go — minimal, just needs to compile cleanly
main_go = """\
package main

import  "fmt"
import "os"

func main()  {
port := os.Getenv("PORT")
if port == "" {
port = "8080"
}
fmt.Printf("Currency service starting on port %s\\n", port)
}
"""

# Write the broken Go files — NO go.mod present (agent must create it)
with open(os.path.join(workspace, "currencyservice/converter/converter.go"), "w") as f:
    f.write(converter_go)

with open(os.path.join(workspace, "currencyservice/converter/converter_test.go"), "w") as f:
    f.write(converter_test_go)

with open(os.path.join(workspace, "currencyservice/cmd/server/main.go"), "w") as f:
    f.write(main_go)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fn in files:
        print("  ", os.path.join(root, fn).replace(workspace + "/", ""))