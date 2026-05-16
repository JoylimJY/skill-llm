import os
import random

random.seed(42)

workspace = "/workspace"

# ── SKILL.md reference files ──────────────────────────────────────────────────
skill_root = os.path.join(workspace, "elixir-performance-review")
refs_dir   = os.path.join(skill_root, "references")
os.makedirs(refs_dir, exist_ok=True)

skill_md = """\
---
name: elixir-performance-review
description: Reviews Elixir code for performance issues including GenServer bottlenecks, memory usage, and concurrency patterns. Use when reviewing high-throughput code or investigating performance issues.
---

# Elixir Performance Review

## Quick Reference

| Issue Type | Reference |
|------------|-----------|
| Mailbox overflow, blocking calls | [references/genserver-bottlenecks.md](references/genserver-bottlenecks.md) |
| When to use ETS, read/write concurrency | [references/ets-patterns.md](references/ets-patterns.md) |
| Binary handling, large messages | [references/memory.md](references/memory.md) |
| Task patterns, flow control | [references/concurrency.md](references/concurrency.md) |

## Review Checklist

### GenServer
- [ ] Not a single-process bottleneck for all requests
- [ ] No blocking operations in handle_call/cast
- [ ] Proper timeout configuration
- [ ] Consider ETS for read-heavy state

### Memory
- [ ] Large binaries not copied between processes
- [ ] Streams used for large data transformations
- [ ] No unbounded data accumulation

### Concurrency
- [ ] Task.Supervisor for dynamic tasks (not raw Task.async)
- [ ] No unbounded process spawning
- [ ] Proper backpressure for message producers

### Database
- [ ] Preloading to avoid N+1 queries
- [ ] Pagination for large result sets
- [ ] Indexes for frequent queries

## Valid Patterns (Do NOT Flag)

- **Single GenServer for low-throughput** - Not all state needs horizontal scaling
- **Synchronous calls for critical paths** - Consistency may require it
- **In-memory state without ETS** - ETS has overhead for small state
- **Enum over Stream for small collections** - Stream overhead not worth it

## Context-Sensitive Rules

| Issue | Flag ONLY IF |
|-------|--------------|
| GenServer bottleneck | Handles > 1000 req/sec OR blocking I/O in callbacks |
| Use streams | Processing > 10k items OR reading large files |
| Use ETS | Read:write ratio > 10:1 AND concurrent access |

## Before Submitting Findings

Load and follow [review-verification-protocol](../review-verification-protocol/SKILL.md) before reporting any issue.
"""

with open(os.path.join(skill_root, "SKILL.md"), "w") as f:
    f.write(skill_md)

genserver_bottlenecks_md = """\
# GenServer Bottlenecks

## Single Process Bottleneck

### The Problem

```elixir
# BAD - all requests through one process
defmodule Cache do
  use GenServer

  def get(key), do: GenServer.call(__MODULE__, {:get, key})
  def put(key, val), do: GenServer.call(__MODULE__, {:put, key, val})
end
```

Every request queues in the GenServer's mailbox. Under load:
- Mailbox grows unbounded
- Latency increases linearly
- Memory pressure from queued messages

### Solutions

**1. Use ETS for read-heavy workloads:**

```elixir
defmodule Cache do
  def init do
    :ets.new(:cache, [:set, :public, :named_table, read_concurrency: true])
  end

  def get(key), do: :ets.lookup(:cache, key)
  def put(key, val), do: :ets.insert(:cache, {key, val})
end
```

**2. Partition by key:**

```elixir
defmodule PartitionedCache do
  @partitions 16

  def get(key) do
    partition = :erlang.phash2(key, @partitions)
    GenServer.call(:"cache_#{partition}", {:get, key})
  end
end
```

**3. Use Registry for dynamic workers:**

```elixir
defmodule WorkerPool do
  def get_worker(key) do
    case Registry.lookup(MyRegistry, key) do
      [{pid, _}] -> pid
      [] -> start_worker(key)
    end
  end
end
```

## Blocking Operations

### The Problem

```elixir
# BAD - blocks entire GenServer
def handle_call(:fetch_external, _from, state) do
  result = HTTPClient.get!(url)  # 500ms+ network call
  {:reply, result, state}
end
```

All other messages wait during the HTTP call.

### Solutions

**1. Use Task.Supervisor for async work:**

```elixir
def handle_call(:fetch_external, from, state) do
  task = Task.Supervisor.async_nolink(MyApp.TaskSupervisor, fn ->
    HTTPClient.get!(url)
  end)
  {:noreply, Map.put(state, :pending, {from, task.ref})}
end

def handle_info({ref, result}, %{pending: {from, ref}} = state) do
  Process.demonitor(ref, [:flush])
  GenServer.reply(from, result)
  {:noreply, Map.delete(state, :pending)}
end

def handle_info({:DOWN, ref, :process, _pid, reason}, %{pending: {from, ref}} = state) do
  GenServer.reply(from, {:error, reason})
  {:noreply, Map.delete(state, :pending)}
end
```

**2. Use handle_continue for expensive init:**

```elixir
def init(args) do
  {:ok, %{}, {:continue, :load_data}}
end

def handle_continue(:load_data, state) do
  data = expensive_load()
  {:noreply, %{state | data: data}}
end
```

## Timeouts

### Configure Appropriately

```elixir
# Client-side timeout (use catch, not rescue - timeouts are exit signals)
def fetch(pid) do
  try do
    GenServer.call(pid, :fetch, 10_000)  # 10 second timeout
  catch
    :exit, {:timeout, _} -> {:error, :timeout}
  end
end

# Server-side timeout for idle
def handle_info(:timeout, state) do
  {:stop, :normal, state}
end

def handle_call(:work, _from, state) do
  {:reply, :ok, state, 30_000}  # 30s idle timeout
end
```

## Review Questions

1. Is this GenServer a potential bottleneck under load?
2. Are there blocking I/O operations in callbacks?
3. Would ETS be more appropriate for this use case?
4. Are timeouts configured appropriately?
"""

with open(os.path.join(refs_dir, "genserver-bottlenecks.md"), "w") as f:
    f.write(genserver_bottlenecks_md)

ets_patterns_md = """\
# ETS Patterns

## When to Use ETS

| Use Case | ETS? |
|----------|------|
| Read-heavy cache | Yes |
| Write-heavy with consistency | No (use GenServer) |
| Shared state across processes | Yes |
| Small, single-process state | No (use GenServer) |

## Table Types

```elixir
# :set - one value per key (default)
:ets.new(:cache, [:set])

# :bag - multiple values per key
:ets.new(:events, [:bag])

# :ordered_set - sorted by key
:ets.new(:timeline, [:ordered_set])
```

## Concurrency Options

```elixir
# Read-heavy workload
:ets.new(:cache, [:set, :public, :named_table,
  read_concurrency: true
])

# Write-heavy workload
:ets.new(:counters, [:set, :public, :named_table,
  write_concurrency: true
])

# Both
:ets.new(:mixed, [:set, :public, :named_table,
  read_concurrency: true,
  write_concurrency: true
])
```

## Common Patterns

### Cache with TTL

```elixir
defmodule TTLCache do
  def put(key, value, ttl_ms) do
    expires_at = System.monotonic_time(:millisecond) + ttl_ms
    :ets.insert(:cache, {key, value, expires_at})
  end

  def get(key) do
    case :ets.lookup(:cache, key) do
      [{^key, value, expires_at}] ->
        if System.monotonic_time(:millisecond) < expires_at do
          {:ok, value}
        else
          :ets.delete(:cache, key)
          :expired
        end

      [] ->
        :not_found
    end
  end
end
```

### Counter

```elixir
# Atomic counter updates
:ets.update_counter(:stats, :requests, 1, {:requests, 0})
```

### Match Specifications

```elixir
# Find all users with role :admin
:ets.select(:users, [
  {{:"$1", %{role: :admin}}, [], [:"$1"]}
])

# Using match
:ets.match(:users, {:"$1", %{role: :admin, name: :"$2"}})
# Returns [[id1, name1], [id2, name2], ...]
```

## Access Control

```elixir
# :public - any process can read/write
# :protected - owner writes, any reads (default)
# :private - only owner

:ets.new(:shared, [:public])    # Multi-process cache
:ets.new(:config, [:protected]) # Owner updates, all read
:ets.new(:internal, [:private]) # Single process only
```

## Ownership and Lifecycle

```elixir
# ETS table dies with owner process
# Use a dedicated process to own long-lived tables

defmodule TableOwner do
  use GenServer

  def start_link(_) do
    GenServer.start_link(__MODULE__, [], name: __MODULE__)
  end

  def init(_) do
    table = :ets.new(:my_table, [:public, :named_table])
    {:ok, table}
  end
end
```

## Review Questions

1. Is ETS appropriate for this use case (read vs write ratio)?
2. Are concurrency options set correctly?
3. Is table ownership properly managed?
4. Are access controls appropriate?
"""

with open(os.path.join(refs_dir, "ets-patterns.md"), "w") as f:
    f.write(ets_patterns_md)

memory_md = """\
# Memory Patterns

## Binary Handling

### Large Binaries Are Reference Counted

Binaries > 64 bytes are stored on shared heap. Copying between processes is cheap (reference copy).

```elixir
# Efficient - only reference copied
send(pid, large_binary)

# But beware of sub-binaries holding reference to large binary
<<header::binary-size(100), _rest::binary>> = large_binary
# header still references entire large_binary!
```

### Force Copy When Needed

```elixir
# Release reference to large binary
header = :binary.copy(<<header::binary-size(100), _::binary>> = large_binary)
```

## Process Heap

### Large State = Large GC

Each process has its own heap. Large state means:
- Longer GC pauses
- More memory per process

```elixir
# BAD - accumulating large state
def handle_cast({:add, item}, state) do
  {:noreply, [item | state.items]}  # Grows forever!
end

# GOOD - bounded state
def handle_cast({:add, item}, state) do
  items = Enum.take([item | state.items], @max_items)
  {:noreply, %{state | items: items}}
end
```

### Use ETS for Large Shared State

```elixir
# BAD - large map in GenServer
defmodule BigCache do
  use GenServer
  def init(_), do: {:ok, %{}}  # Millions of entries here
end

# GOOD - ETS for large state
defmodule BigCache do
  def init do
    :ets.new(:cache, [:set, :public, :named_table])
  end
end
```

## Message Passing

### Avoid Large Message Copies

```elixir
# BAD - copies entire list to each process
Enum.each(workers, fn pid ->
  send(pid, {:process, large_list})
end)

# GOOD - send reference or key
Enum.each(workers, fn pid ->
  send(pid, {:process, :ets.whereis(:data), key})
end)
```

## Streams for Large Data

### Use Streams to Avoid Loading All in Memory

```elixir
# BAD - loads entire file
File.read!("large.csv")
|> String.split("\\n")
|> Enum.map(&parse_line/1)

# GOOD - streams line by line
File.stream!("large.csv")
|> Stream.map(&parse_line/1)
|> Enum.to_list()  # Or process incrementally
```

### Database Streams

```elixir
# BAD - loads all records
Repo.all(User)
|> Enum.map(&process/1)

# GOOD - streams from database
User
|> Repo.stream()
|> Stream.map(&process/1)
|> Stream.run()
```

## Detecting Memory Issues

```elixir
# Process memory
Process.info(self(), :memory)

# System memory
:erlang.memory()

# Binary memory specifically
:erlang.memory(:binary)
```

## Review Questions

1. Are large binaries being unnecessarily copied?
2. Is process state bounded or growing unbounded?
3. Are streams used for large data processing?
4. Is shared state in ETS rather than process heap?
"""

with open(os.path.join(refs_dir, "memory.md"), "w") as f:
    f.write(memory_md)

concurrency_md = """\
# Concurrency Patterns

## Task Patterns

### Use Task.Supervisor for Dynamic Tasks

```elixir
# BAD - unlinked task, crashes silently
Task.start(fn -> risky_work() end)

# BAD - linked task, crashes caller if task crashes
Task.async(fn -> risky_work() end) |> Task.await()

# GOOD - supervised, restartable
Task.Supervisor.async_nolink(MyTaskSupervisor, fn ->
  risky_work()
end)
```

### Parallel Processing

```elixir
# Process items concurrently with limit
Task.Supervisor.async_stream_nolink(
  MyTaskSupervisor,
  items,
  fn item -> process(item) end,
  max_concurrency: 10,
  ordered: false
)
|> Enum.to_list()
```

### Timeout Handling

```elixir
task = Task.Supervisor.async_nolink(MySup, fn -> slow_work() end)

case Task.yield(task, 5_000) || Task.shutdown(task) do
  {:ok, result} -> {:ok, result}
  nil -> {:error, :timeout}
  {:exit, reason} -> {:error, reason}
end
```

## Backpressure

### GenStage / Broadway for Backpressure

```elixir
# Producer-consumer with demand
defmodule MyConsumer do
  use GenStage

  def handle_events(events, _from, state) do
    process(events)
    {:noreply, [], state}  # Demand more when ready
  end
end
```

### Manual Backpressure

```elixir
# Limit concurrent operations
defmodule RateLimiter do
  use GenServer

  def init(_) do
    {:ok, %{active: 0, max: 10, queue: :queue.new()}}
  end

  def handle_call(:acquire, from, %{active: n, max: max} = state) when n < max do
    {:reply, :ok, %{state | active: n + 1}}
  end

  def handle_call(:acquire, from, state) do
    {:noreply, %{state | queue: :queue.in(from, state.queue)}}
  end

  def handle_cast(:release, %{queue: queue, active: n} = state) do
    case :queue.out(queue) do
      {{:value, from}, queue} ->
        GenServer.reply(from, :ok)
        {:noreply, %{state | queue: queue}}

      {:empty, _} ->
        {:noreply, %{state | active: n - 1}}
    end
  end
end
```

## Process Spawning

### Don't Spawn Unbounded

```elixir
# BAD - spawns process per request
def handle_request(req) do
  spawn(fn -> process(req) end)  # Unbounded!
end

# GOOD - use pool
def handle_request(req) do
  :poolboy.transaction(:worker_pool, fn pid ->
    Worker.process(pid, req)
  end)
end
```

### DynamicSupervisor for Bounded Children

```elixir
defmodule MyDynamicSup do
  use DynamicSupervisor

  def start_link(_) do
    DynamicSupervisor.start_link(__MODULE__, [],
      name: __MODULE__,
      max_children: 100  # Bounded!
    )
  end
end
```

## Review Questions

1. Are dynamic tasks under a Task.Supervisor?
2. Is there backpressure for high-volume producers?
3. Is process spawning bounded?
4. Are timeouts configured for async operations?
"""

with open(os.path.join(refs_dir, "concurrency.md"), "w") as f:
    f.write(concurrency_md)

# ── review-verification-protocol SKILL.md (sibling directory) ──────────────
rvp_dir = os.path.join(workspace, "review-verification-protocol")
os.makedirs(rvp_dir, exist_ok=True)

rvp_skill_md = """\
---
name: review-verification-protocol
description: Verification protocol that must be followed before submitting any code review findings.
---

# Review Verification Protocol

Before submitting findings, verify each issue passes ALL checks:

## Verification Steps

1. **Confirm the issue exists in context** - Re-read the flagged code in full. Is the issue real?
2. **Check threshold conditions** - Does the issue meet the quantitative thresholds (e.g., > 1000 req/sec, > 10k items)?
3. **Check for false positives** - Is this actually a valid pattern per the skill's "Valid Patterns" section?
4. **Assign severity** - Use the schema below.
5. **Write a clear description** - One sentence stating the problem.
6. **Write a concrete recommendation** - One actionable fix.

## Severity Schema

- `critical`: Causes data loss, crashes, or security vulnerability under normal load
- `high`: Significant performance degradation under expected production load
- `medium`: Performance issue that matters at scale but not immediately harmful
- `low`: Minor inefficiency or style concern

## Required Output Fields Per Issue

Each reported issue MUST include:
- `file`: relative path to the file
- `line`: line number (integer)
- `severity`: one of critical/high/medium/low
- `category`: one of genserver_bottleneck/memory/concurrency/database
- `description`: string
- `recommendation`: string
- `verified`: boolean (must be true — do not report unverified issues)

## Output Format

Findings MUST be submitted as a JSON object:

```json
{
  "review_verified": true,
  "findings": [
    {
      "file": "lib/foo.ex",
      "line": 42,
      "severity": "high",
      "category": "genserver_bottleneck",
      "description": "...",
      "recommendation": "...",
      "verified": true
    }
  ]
}
```
"""

with open(os.path.join(rvp_dir, "SKILL.md"), "w") as f:
    f.write(rvp_skill_md)

# ── Source files to review ────────────────────────────────────────────────────
src_dir = os.path.join(workspace, "finpay", "lib", "finpay")
os.makedirs(src_dir, exist_ok=True)

# ── FILE 1: transaction_router.ex
# Issues:
#  - GenServer handling > 1000 req/sec (stated in comment) + blocking HTTP in handle_call  => SHOULD FLAG
#  - unbounded Task.async (no supervisor)                                                   => SHOULD FLAG
# line numbers are deliberate
transaction_router_ex = """\
defmodule Finpay.TransactionRouter do
  @moduledoc \"\"\"
  Routes payment transactions to downstream processors.
  Handles ~5000 transactions/sec at peak load.
  \"\"\"
  use GenServer

  # Public API

  def start_link(opts) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  def route(transaction) do
    GenServer.call(__MODULE__, {:route, transaction})
  end

  # Callbacks

  def init(opts) do
    {:ok, %{processor_url: opts[:processor_url], routed: 0}}
  end

  def handle_call({:route, transaction}, _from, state) do
    # Synchronously calls external payment processor - can take 200-800ms
    result = HTTPClient.post!(state.processor_url, transaction)
    {:reply, result, %{state | routed: state.routed + 1}}
  end

  def handle_cast({:audit_log, transaction}, state) do
    # Fire-and-forget audit logging
    Task.async(fn ->
      AuditLogger.write(transaction)
    end)
    {:noreply, state}
  end
end
"""

with open(os.path.join(src_dir, "transaction_router.ex"), "w") as f:
    f.write(transaction_router_ex)

# ── FILE 2: rate_cache.ex
# Issues:
#  - GenServer used as read cache with >10:1 read:write AND concurrent access => SHOULD FLAG (ETS appropriate)
# Note: The comment explicitly says 95% reads, concurrent access by many worker processes
rate_cache_ex = """\
defmodule Finpay.RateCache do
  @moduledoc \"\"\"
  Stores FX exchange rates. Accessed by hundreds of worker processes concurrently.
  Reads happen ~95% of the time; rates are updated every 60 seconds.
  \"\"\"
  use GenServer

  def start_link(_), do: GenServer.start_link(__MODULE__, %{}, name: __MODULE__)

  def get_rate(currency_pair) do
    GenServer.call(__MODULE__, {:get, currency_pair})
  end

  def update_rate(currency_pair, rate) do
    GenServer.call(__MODULE__, {:put, currency_pair, rate})
  end

  def init(initial_rates), do: {:ok, initial_rates}

  def handle_call({:get, pair}, _from, rates) do
    {:reply, Map.get(rates, pair), rates}
  end

  def handle_call({:put, pair, rate}, _from, rates) do
    {:reply, :ok, Map.put(rates, pair, rate)}
  end
end
"""

with open(os.path.join(src_dir, "rate_cache.ex"), "w") as f:
    f.write(rate_cache_ex)

# ── FILE 3: report_generator.ex
# Issues:
#  - Enum.map on large dataset (100k+ records stated in comment)  => SHOULD FLAG (stream needed > 10k items)
#  - Unbounded spawn (spawn per settlement record)                => SHOULD FLAG
report_generator_ex = """\
defmodule Finpay.ReportGenerator do
  @moduledoc \"\"\"
  Generates end-of-day settlement reports.
  Processes up to 150,000 settlement records per report.
  \"\"\"

  def generate_settlement_report(date) do
    # Loads all records into memory, then maps over them
    Repo.all(from s in Settlement, where: s.date == ^date)
    |> Enum.map(&format_settlement/1)
    |> Enum.join("\\n")
    |> write_report(date)
  end

  def fan_out_notifications(settlements) do
    # Notify each counterparty in parallel
    Enum.each(settlements, fn settlement ->
      spawn(fn -> NotificationService.notify(settlement.counterparty_id, settlement) end)
    end)
  end

  defp format_settlement(s) do
    "#{s.id},#{s.amount},#{s.currency},#{s.status}"
  end

  defp write_report(content, date) do
    File.write!("reports/settlement_#{date}.csv", content)
  end
end
"""

with open(os.path.join(src_dir, "report_generator.ex"), "w") as f:
    f.write(report_generator_ex)

# ── FILE 4: config_loader.ex
# This is a VALID PATTERN — low-throughput GenServer, small state, no blocking I/O
# Agent MUST NOT flag this
config_loader_ex = """\
defmodule Finpay.ConfigLoader do
  @moduledoc \"\"\"
  Loads and caches application configuration at startup.
  Config is read once at boot and rarely changes (admin-only updates).
  Receives ~5 requests/sec at most.
  \"\"\"
  use GenServer

  def start_link(_), do: GenServer.start_link(__MODULE__, %{}, name: __MODULE__)

  def get(key), do: GenServer.call(__MODULE__, {:get, key})

  def reload do
    GenServer.call(__MODULE__, :reload)
  end

  def init(_) do
    config = Application.get_all_env(:finpay)
    {:ok, Map.new(config)}
  end

  def handle_call({:get, key}, _from, config) do
    {:reply, Map.get(config, key), config}
  end

  def handle_call(:reload, _from, _config) do
    new_config = Map.new(Application.get_all_env(:finpay))
    {:reply, :ok, new_config}
  end
end
"""

with open(os.path.join(src_dir, "config_loader.ex"), "w") as f:
    f.write(config_loader_ex)

# ── FILE 5: small_batch_processor.ex
# This is a VALID PATTERN — Enum over small collection (200 items), not > 10k
# Agent MUST NOT flag this
small_batch_processor_ex = """\
defmodule Finpay.SmallBatchProcessor do
  @moduledoc \"\"\"
  Processes small micro-batch corrections.
  Each batch contains at most 200 records by design.
  \"\"\"

  def process_corrections(corrections) when length(corrections) <= 200 do
    corrections
    |> Enum.map(&apply_correction/1)
    |> Enum.filter(&correction_valid?/1)
    |> Enum.each(&persist/1)
  end

  defp apply_correction(c), do: %{c | amount: c.amount + c.adjustment}
  defp correction_valid?(c), do: c.amount >= 0
  defp persist(c), do: Repo.insert!(c)
end
"""

with open(os.path.join(src_dir, "small_batch_processor.ex"), "w") as f:
    f.write(small_batch_processor_ex)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_dir = os.path.join(workspace, "finpay")
os.makedirs(os.path.join(distractor_dir, "test"), exist_ok=True)
os.makedirs(os.path.join(distractor_dir, "config"), exist_ok=True)
os.makedirs(os.path.join(distractor_dir, "priv", "repo", "migrations"), exist_ok=True)
os.makedirs(os.path.join(distractor_dir, "lib", "finpay_web"), exist_ok=True)

with open(os.path.join(distractor_dir, "mix.exs"), "w") as f:
    f.write("""\
defmodule Finpay.MixProject do
  use Mix.Project

  def project do
    [
      app: :finpay,
      version: "2.1.0",
      elixir: "~> 1.15",
      deps: deps()
    ]
  end

  defp deps do
    [
      {:phoenix, "~> 1.7"},
      {:ecto_sql, "~> 3.10"},
      {:postgrex, ">= 0.0.0"},
      {:gen_stage, "~> 1.2"},
      {:poolboy, "~> 1.5"}
    ]
  end
end
""")

with open(os.path.join(distractor_dir, "config", "config.exs"), "w") as f:
    f.write("""\
import Config

config :finpay, Finpay.Repo,
  username: "postgres",
  password: "postgres",
  hostname: "localhost",
  database: "finpay_dev"

config :finpay, :processor_url, "https://payments.internal/v2/route"
""")

with open(os.path.join(distractor_dir, "test", "transaction_router_test.exs"), "w") as f:
    f.write("""\
defmodule Finpay.TransactionRouterTest do
  use ExUnit.Case

  test "routes a valid transaction" do
    # TODO: implement
  end
end
""")

with open(os.path.join(distractor_dir, "priv", "repo", "migrations", "20240101000001_create_settlements.exs"), "w") as f:
    f.write("""\
defmodule Finpay.Repo.Migrations.CreateSettlements do
  use Ecto.Migration

  def change do
    create table(:settlements) do
      add :date, :date, null: false
      add :amount, :decimal, null: false
      add :currency, :string, null: false
      add :status, :string, null: false
      add :counterparty_id, :integer, null: false
      timestamps()
    end
  end
end
""")

with open(os.path.join(distractor_dir, "lib", "finpay_web", "router.ex"), "w") as f:
    f.write("""\
defmodule FinpayWeb.Router do
  use FinpayWeb, :router

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/api", FinpayWeb do
    pipe_through :api
    post "/transactions", TransactionController, :create
  end
end
""")

with open(os.path.join(distractor_dir, "lib", "finpay_web", "transaction_controller.ex"), "w") as f:
    f.write("""\
defmodule FinpayWeb.TransactionController do
  use FinpayWeb, :controller

  def create(conn, params) do
    case Finpay.TransactionRouter.route(params) do
      {:ok, result} -> json(conn, %{status: "ok", id: result.id})
      {:error, reason} -> json(conn, %{status: "error", reason: reason})
    end
  end
end
""")

with open(os.path.join(distractor_dir, "lib", "finpay", "application.ex"), "w") as f:
    f.write("""\
defmodule Finpay.Application do
  use Application

  def start(_type, _args) do
    children = [
      Finpay.Repo,
      Finpay.ConfigLoader,
      Finpay.RateCache,
      Finpay.TransactionRouter,
      {Task.Supervisor, name: Finpay.TaskSupervisor}
    ]
    Supervisor.start_link(children, strategy: :one_for_one)
  end
end
""")

# One more distractor: a changelog with no hints
with open(os.path.join(distractor_dir, "CHANGELOG.md"), "w") as f:
    f.write("""\
# Changelog

## v2.1.0
- Added FX rate caching layer
- Improved settlement report generation
- Added audit logging for all transactions

## v2.0.0
- Migrated to Phoenix 1.7
- Added GenStage pipeline for event processing
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')