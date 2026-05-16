import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
distractor_dirs = [
    "/workspace/contracts/legacy",
    "/workspace/contracts/drafts",
    "/workspace/tests/unit",
    "/workspace/tests/integration",
    "/workspace/scripts",
    "/workspace/docs/api",
    "/workspace/docs/audit",
    "/workspace/deployments/mainnet",
    "/workspace/deployments/testnet",
    "/workspace/frontend/src/abi",
    "/workspace/ci",
]

for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

# ── Distractor files (10+) ────────────────────────────────────────────────────

# 1. Old Solidity ERC20 (wrong language, distractor)
with open("/workspace/contracts/legacy/OldToken.sol", "w") as f:
    f.write("""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
contract OldToken {
    string public name = "OldToken";
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
}
""")

# 2. Broken Cairo v0 syntax (outdated, should NOT be used as reference)
with open("/workspace/contracts/drafts/broken_token.cairo", "w") as f:
    f.write("""%lang starknet
%builtins pedersen range_check
from starkware.cairo.common.cairo_builtins import HashBuiltin
@storage_var
func balance(user: felt) -> (res: felt):
end
@external
func transfer{syscall_ptr: felt*, pedersen_ptr: HashBuiltin*, range_check_ptr}(to: felt, amount: felt):
    return ()
end
""")

# 3. Partial ERC20 interface file
with open("/workspace/contracts/drafts/IERC20.cairo", "w") as f:
    f.write("""// Incomplete interface - do not use directly
trait IERC20 {
    fn total_supply() -> u256;
    fn balance_of(account: ContractAddress) -> u256;
}
""")

# 4. Deployment config (irrelevant)
with open("/workspace/deployments/testnet/config.json", "w") as f:
    f.write('{"network": "sepolia", "rpc": "https://starknet-sepolia.example.com", "fee_token": "ETH"}\n')

with open("/workspace/deployments/mainnet/config.json", "w") as f:
    f.write('{"network": "mainnet", "rpc": "https://starknet-mainnet.example.com", "fee_token": "ETH"}\n')

# 5. Unit test stub (wrong format)
with open("/workspace/tests/unit/test_token.py", "w") as f:
    f.write("""# Placeholder - tests not yet written
def test_transfer():
    pass

def test_mint():
    pass
""")

# 6. Integration test notes
with open("/workspace/tests/integration/notes.txt", "w") as f:
    f.write("TODO: Write integration tests against testnet deployment.\nNeed to handle pause/unpause flows.\n")

# 7. ABI JSON (distractor)
with open("/workspace/frontend/src/abi/token_abi.json", "w") as f:
    f.write('[{"type":"function","name":"transfer","inputs":[{"name":"to","type":"felt"},{"name":"amount","type":"felt"}]}]\n')

# 8. Audit checklist
with open("/workspace/docs/audit/checklist.md", "w") as f:
    f.write("""# Audit Checklist
- [ ] Reentrancy guards
- [ ] Integer overflow checks
- [ ] Event emission on all state changes
- [ ] Access control on admin functions
- [ ] Pause mechanism present and tested
""")

# 9. CI config
with open("/workspace/ci/pipeline.yml", "w") as f:
    f.write("""stages:
  - build
  - test
  - deploy
build:
  script:
    - scarb build
test:
  script:
    - snforge test
""")

# 10. Old migration notes
with open("/workspace/docs/api/migration_notes.txt", "w") as f:
    f.write("Migrating from Cairo 0.x to Cairo 2.x requires rewriting all storage vars and events.\nUse new attribute macros.\n")

# 11. Another distractor contract
with open("/workspace/contracts/legacy/Ownable.cairo", "w") as f:
    f.write("""// WARNING: Cairo 0 syntax - do not use
@storage_var
func owner() -> (res: felt):
end
""")

# 12. requirements stub
with open("/workspace/docs/api/requirements.txt", "w") as f:
    f.write("- Pausable ERC20 token\n- Only owner can pause/unpause\n- Emit event on pause state change\n- Block transfers when paused\n")

# ── The core skill script that the agent MUST use ────────────────────────────
# scripts/script.sh must exist and be executable

os.makedirs("/workspace/scripts", exist_ok=True)

script_content = r'''#!/usr/bin/env bash
# BytesAgain Cairo StarkNet Skill Script v2.0.0

CMD="${1}"
ARG="${2}"

case "$CMD" in
  syntax)
    cat <<'SYNTAX'
## Cairo Syntax Reference

### Variables
```cairo
let x: felt252 = 5;
let mut counter: u32 = 0;
```

### Functions
```cairo
fn add(a: u32, b: u32) -> u32 {
    a + b
}
```

### Control Flow
```cairo
if condition {
    // do something
} else {
    // do something else
}

loop {
    if done { break; }
}
```

### Imports
```cairo
use starknet::ContractAddress;
use starknet::get_caller_address;
```
SYNTAX
    ;;

  types)
    cat <<'TYPES'
## Cairo Type System

### Primitives
- `felt252`  — field element (252-bit), default Cairo type
- `u8`, `u16`, `u32`, `u64`, `u128`, `u256` — unsigned integers
- `bool`     — boolean
- `ContractAddress` — StarkNet contract address

### Structs
```cairo
#[derive(Drop, Serde, starknet::Store)]
struct TokenInfo {
    name: felt252,
    symbol: felt252,
    decimals: u8,
}
```

### Enums
```cairo
#[derive(Drop, Serde)]
enum Status {
    Active,
    Paused,
    Terminated,
}
```

### Arrays
```cairo
let mut arr: Array<u256> = ArrayTrait::new();
arr.append(1_u256);
```

### Option & Result
```cairo
let maybe: Option<u256> = Option::Some(42_u256);
let result: Result<u256, felt252> = Result::Ok(1_u256);
```
TYPES
    ;;

  storage)
    cat <<'STORAGE'
## Storage Variable Patterns

Storage variables in Cairo 2 / StarkNet are declared inside a `Storage` struct
annotated with `#[storage]` inside a `#[starknet::contract]` module.

### Basic Storage Struct
```cairo
#[storage]
struct Storage {
    owner: ContractAddress,
    total_supply: u256,
    paused: bool,
    balances: LegacyMap<ContractAddress, u256>,
    allowances: LegacyMap<(ContractAddress, ContractAddress), u256>,
}
```

### Reading Storage
```cairo
let current_owner = self.owner.read();
let bal = self.balances.read(account);
```

### Writing Storage
```cairo
self.owner.write(new_owner);
self.balances.write(account, new_balance);
self.paused.write(true);
```

### LegacyMap
- `LegacyMap<K, V>` maps a key type to a value type.
- Nested mapping: `LegacyMap<(ContractAddress, ContractAddress), u256>`

### Access Pattern in Functions
Storage is accessed via `self` (read) and `ref self` (write):
```cairo
fn read_example(self: @ContractState) -> bool {
    self.paused.read()
}

fn write_example(ref self: ContractState) {
    self.paused.write(true);
}
```
STORAGE
    ;;

  events)
    cat <<'EVENTS'
## Event Declaration, Emission, and Indexing

### Event Enum Pattern (Cairo 2 / StarkNet)
Events are declared as an enum annotated with `#[event]` and `#[derive(Drop, starknet::Event)]`
inside the contract module.

```cairo
#[event]
#[derive(Drop, starknet::Event)]
enum Event {
    Transfer: Transfer,
    Approval: Approval,
    Paused: Paused,
    Unpaused: Unpaused,
}
```

### Event Structs
Each variant maps to a struct. Use `#[key]` to index fields (queryable off-chain).

```cairo
#[derive(Drop, starknet::Event)]
struct Transfer {
    #[key]
    from: ContractAddress,
    #[key]
    to: ContractAddress,
    value: u256,
}

#[derive(Drop, starknet::Event)]
struct Approval {
    #[key]
    owner: ContractAddress,
    #[key]
    spender: ContractAddress,
    value: u256,
}

#[derive(Drop, starknet::Event)]
struct Paused {
    #[key]
    account: ContractAddress,
}

#[derive(Drop, starknet::Event)]
struct Unpaused {
    #[key]
    account: ContractAddress,
}
```

### Emitting Events
Events are emitted via `self.emit(...)`:

```cairo
self.emit(Transfer { from: sender, to: recipient, value: amount });
self.emit(Paused { account: caller });
self.emit(Unpaused { account: caller });
```

### Component-based Events
When using components, the Event enum wraps component events:
```cairo
#[event]
#[derive(Drop, starknet::Event)]
enum Event {
    #[flat]
    ERC20Event: ERC20Component::Event,
    Paused: Paused,
    Unpaused: Unpaused,
}
```
EVENTS
    ;;

  template)
    case "$ARG" in
      erc20)
        cat <<'ERC20_TEMPLATE'
## ERC20 Contract Template

```cairo
#[starknet::contract]
mod ERC20Token {
    use starknet::ContractAddress;
    use starknet::get_caller_address;

    #[storage]
    struct Storage {
        name: felt252,
        symbol: felt252,
        decimals: u8,
        total_supply: u256,
        balances: LegacyMap<ContractAddress, u256>,
        allowances: LegacyMap<(ContractAddress, ContractAddress), u256>,
    }

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        Transfer: Transfer,
        Approval: Approval,
    }

    #[derive(Drop, starknet::Event)]
    struct Transfer {
        #[key]
        from: ContractAddress,
        #[key]
        to: ContractAddress,
        value: u256,
    }

    #[derive(Drop, starknet::Event)]
    struct Approval {
        #[key]
        owner: ContractAddress,
        #[key]
        spender: ContractAddress,
        value: u256,
    }

    #[constructor]
    fn constructor(
        ref self: ContractState,
        name: felt252,
        symbol: felt252,
        decimals: u8,
        initial_supply: u256,
        recipient: ContractAddress,
    ) {
        self.name.write(name);
        self.symbol.write(symbol);
        self.decimals.write(decimals);
        self.total_supply.write(initial_supply);
        self.balances.write(recipient, initial_supply);
        self.emit(Transfer { from: starknet::contract_address_const::<0>(), to: recipient, value: initial_supply });
    }

    #[abi(embed_v0)]
    impl ERC20Impl of super::IERC20<ContractState> {
        fn name(self: @ContractState) -> felt252 {
            self.name.read()
        }

        fn symbol(self: @ContractState) -> felt252 {
            self.symbol.read()
        }

        fn decimals(self: @ContractState) -> u8 {
            self.decimals.read()
        }

        fn total_supply(self: @ContractState) -> u256 {
            self.total_supply.read()
        }

        fn balance_of(self: @ContractState, account: ContractAddress) -> u256 {
            self.balances.read(account)
        }

        fn allowance(self: @ContractState, owner: ContractAddress, spender: ContractAddress) -> u256 {
            self.allowances.read((owner, spender))
        }

        fn transfer(ref self: ContractState, recipient: ContractAddress, amount: u256) -> bool {
            let sender = get_caller_address();
            let sender_balance = self.balances.read(sender);
            assert(sender_balance >= amount, 'ERC20: insufficient balance');
            self.balances.write(sender, sender_balance - amount);
            let recipient_balance = self.balances.read(recipient);
            self.balances.write(recipient, recipient_balance + amount);
            self.emit(Transfer { from: sender, to: recipient, value: amount });
            true
        }

        fn transfer_from(
            ref self: ContractState,
            sender: ContractAddress,
            recipient: ContractAddress,
            amount: u256,
        ) -> bool {
            let caller = get_caller_address();
            let current_allowance = self.allowances.read((sender, caller));
            assert(current_allowance >= amount, 'ERC20: insufficient allowance');
            self.allowances.write((sender, caller), current_allowance - amount);
            let sender_balance = self.balances.read(sender);
            assert(sender_balance >= amount, 'ERC20: insufficient balance');
            self.balances.write(sender, sender_balance - amount);
            let recipient_balance = self.balances.read(recipient);
            self.balances.write(recipient, recipient_balance + amount);
            self.emit(Transfer { from: sender, to: recipient, value: amount });
            true
        }

        fn approve(ref self: ContractState, spender: ContractAddress, amount: u256) -> bool {
            let owner = get_caller_address();
            self.allowances.write((owner, spender), amount);
            self.emit(Approval { owner, spender, value: amount });
            true
        }
    }

    #[generate_trait]
    impl InternalImpl of InternalTrait {
        fn _only_owner(self: @ContractState) {
            let caller = get_caller_address();
            assert(caller == self.owner.read(), 'Ownable: not owner');
        }
    }
}
```
ERC20_TEMPLATE
        ;;
      ownable)
        cat <<'OWNABLE_TEMPLATE'
## Ownable Contract Template

```cairo
#[starknet::contract]
mod Ownable {
    use starknet::ContractAddress;
    use starknet::get_caller_address;

    #[storage]
    struct Storage {
        owner: ContractAddress,
    }

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        OwnershipTransferred: OwnershipTransferred,
    }

    #[derive(Drop, starknet::Event)]
    struct OwnershipTransferred {
        #[key]
        previous_owner: ContractAddress,
        #[key]
        new_owner: ContractAddress,
    }

    #[constructor]
    fn constructor(ref self: ContractState, initial_owner: ContractAddress) {
        self.owner.write(initial_owner);
        self.emit(OwnershipTransferred {
            previous_owner: starknet::contract_address_const::<0>(),
            new_owner: initial_owner,
        });
    }

    #[abi(embed_v0)]
    impl OwnableImpl of super::IOwnable<ContractState> {
        fn owner(self: @ContractState) -> ContractAddress {
            self.owner.read()
        }

        fn transfer_ownership(ref self: ContractState, new_owner: ContractAddress) {
            self._only_owner();
            let previous = self.owner.read();
            self.owner.write(new_owner);
            self.emit(OwnershipTransferred { previous_owner: previous, new_owner });
        }

        fn renounce_ownership(ref self: ContractState) {
            self._only_owner();
            let previous = self.owner.read();
            self.owner.write(starknet::contract_address_const::<0>());
            self.emit(OwnershipTransferred {
                previous_owner: previous,
                new_owner: starknet::contract_address_const::<0>(),
            });
        }
    }

    #[generate_trait]
    impl InternalImpl of InternalTrait {
        fn _only_owner(self: @ContractState) {
            let caller = get_caller_address();
            assert(caller == self.owner.read(), 'Ownable: not owner');
        }
    }
}
```
OWNABLE_TEMPLATE
        ;;
      *)
        echo "Unknown template: $ARG. Available templates: erc20, ownable"
        exit 1
        ;;
    esac
    ;;

  help)
    cat <<'HELP'
## Cairo StarkNet Skill — Available Commands

  bash scripts/script.sh syntax      Core Cairo syntax reference
  bash scripts/script.sh types       Cairo type system reference
  bash scripts/script.sh storage     Storage variable patterns
  bash scripts/script.sh events      Event declaration and emission
  bash scripts/script.sh template erc20     Generate ERC20 template
  bash scripts/script.sh template ownable   Generate Ownable template
  bash scripts/script.sh help        Show this help message

Powered by BytesAgain | bytesagain.com
HELP
    ;;

  *)
    echo "Unknown command: $CMD"
    echo "Run: bash scripts/script.sh help"
    exit 1
    ;;
esac
'''

with open("/workspace/scripts/script.sh", "w") as f:
    f.write(script_content)

os.chmod("/workspace/scripts/script.sh", 0o755)

print("Workspace initialized successfully.")
print("Distractor files and skill script created.")