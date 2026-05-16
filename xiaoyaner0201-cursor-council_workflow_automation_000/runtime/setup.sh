#!/bin/bash
set -e

# Create a mock 'agent' binary that simulates the agent CLI
cat > /usr/local/bin/agent << 'AGENT_SCRIPT'
#!/bin/bash
# Mock agent CLI - simulates cursor agent behavior

MODEL=""
PROMPT=""
FORCE=false
OUTPUT_FORMAT="text"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        -p)
            PROMPT="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --version)
            echo "agent version 2.0.0-mock"
            exit 0
            ;;
        login)
            echo "Already logged in (mock)"
            exit 0
            ;;
        *)
            shift
            ;;
    esac
done

# Simulate model responses based on the model used
case "$MODEL" in
    claude-opus-4-6)
        echo "=== Agent (claude-opus-4-6) Analysis ==="
        echo ""
        echo "## Architectural Assessment: Database Selection"
        echo ""
        echo "As a senior architect examining this through the lens of long-term system integrity,"
        echo "I recommend PostgreSQL (Option A) for this fintech ledger use case."
        echo ""
        echo "### Long-term Implications"
        echo "Financial systems require absolute ACID guarantees. The 'flexibility' of MongoDB"
        echo "becomes a liability when auditors demand transaction atomicity. Cassandra's eventual"
        echo "consistency model is fundamentally incompatible with ledger semantics."
        echo ""
        echo "### Edge Cases & Failure Modes"
        echo "- MongoDB: Potential for lost updates under concurrent writes without careful write concern configuration"
        echo "- Cassandra: Tombstone accumulation, read repair overhead at scale, compaction storms"
        echo "- PostgreSQL: Row-level locking, MVCC, and serializable isolation are battle-tested for financial data"
        echo ""
        echo "### 5-Year Outlook"
        echo "PostgreSQL with read replicas and partitioning can handle 10x current load."
        echo "Migrate to distributed PostgreSQL (Citus/CockroachDB) if horizontal scaling becomes critical."
        echo ""
        echo "### Verdict"
        echo "Use PostgreSQL. The other options are optimizing for problems you don't have yet."
        ;;
    claude-sonnet-4-5)
        echo "=== Agent (claude-sonnet-4-5) Analysis ==="
        echo ""
        echo "## Pragmatic Engineering Assessment"
        echo ""
        echo "Recommendation: PostgreSQL. Ship it."
        echo ""
        echo "### Implementation Estimate"
        echo "- PostgreSQL setup: 2 days including connection pooling (PgBouncer)"
        echo "- MongoDB setup: 3 days + ongoing tuning for consistency"
        echo "- Cassandra: 2 weeks minimum, ongoing ops nightmare for 1 part-time DevOps"
        echo ""
        echo "### Quickest Path to Production"
        echo "Use managed PostgreSQL (RDS/Cloud SQL/Supabase). Your team already knows it."
        echo "Zero learning curve = zero bugs from unfamiliarity."
        echo ""
        echo "```python"
        echo "# SQLAlchemy with PostgreSQL - your team can write this today"
        echo "from sqlalchemy import create_engine, Column, Numeric, String"
        echo "engine = create_engine('postgresql://user:pass@host/ledger')"
        echo "```"
        echo ""
        echo "### Technical Debt Assessment"
        echo "Choosing MongoDB or Cassandra to 'future-proof' is itself technical debt."
        echo "You'll spend months fighting consistency issues instead of building features."
        ;;
    gpt-5.2)
        echo "=== Agent (gpt-5.2) Analysis ==="
        echo ""
        echo "## Contrarian Perspective"
        echo ""
        echo "Everyone's converging on PostgreSQL - which might be right, but let me challenge the framing."
        echo ""
        echo "### Wrong Question Warning"
        echo "You're asking 'which database?' when the real question is 'what's your data model?'"
        echo "A ledger is fundamentally an append-only event log. That changes everything."
        echo ""
        echo "### Alternative Not Listed"
        echo "Consider an event-sourced architecture with PostgreSQL as the event store."
        echo "Transactions are immutable events. Current balances are projections."
        echo "This gives you ACID for writes AND horizontal read scaling."
        echo ""
        echo "### Assumptions That Might Be Wrong"
        echo "- '50 TPS peak' - this is extremely low. PostgreSQL handles 10,000+ TPS easily."
        echo "- 'MongoDB has flexible schema' - you actually WANT a rigid schema for financial data"
        echo "- 'Cassandra for future scale' - premature optimization for a 4-person team"
        echo ""
        echo "### Most Likely Regret"
        echo "If you pick MongoDB: you'll regret it the first time an auditor asks for a consistent"
        echo "point-in-time balance and you realize eventual consistency bit you."
        echo ""
        echo "### Verdict"
        echo "PostgreSQL + event sourcing pattern. Not because it's trendy, but because your"
        echo "domain (ledger) IS an event log. Stop fighting the data model."
        ;;
    *)
        echo "=== Agent (unknown model: $MODEL) ==="
        echo "Mock response: analysis complete"
        ;;
esac

echo ""
echo "Agent completed."
AGENT_SCRIPT

chmod +x /usr/local/bin/agent

# Verify tmux is available
which tmux > /dev/null 2>&1 && echo "tmux available: $(tmux -V)" || echo "WARNING: tmux not found"

# Verify agent mock is working
agent --version

# Set up a proper tmux server socket directory
mkdir -p /tmp/tmux-0
chmod 777 /tmp/tmux-0

# Create openclaw workspace directory
mkdir -p /root/.openclaw/workspace/pr-review

echo "Setup complete. Mock agent installed. tmux ready."