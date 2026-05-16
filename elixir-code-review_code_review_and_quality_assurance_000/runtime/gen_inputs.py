import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "lib/ecommerce",
    "lib/ecommerce/order",
    "lib/ecommerce/payment",
    "lib/ecommerce/inventory",
    "lib/ecommerce/notification",
    "lib/ecommerce/internal",
    "test/ecommerce",
    "config",
    "priv/repo/migrations",
    "docs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "mix.exs": """\
defmodule Ecommerce.MixProject do
  use Mix.Project

  def project do
    [
      app: :ecommerce,
      version: "0.1.0",
      elixir: "~> 1.15",
      deps: deps()
    ]
  end

  defp deps do
    [
      {:jason, "~> 1.4"},
      {:httpoison, "~> 2.0"}
    ]
  end
end
""",
    "config/config.exs": """\
import Config

config :ecommerce,
  env: :dev,
  repo: Ecommerce.Repo
""",
    "lib/ecommerce/payment/gateway.ex": """\
defmodule Ecommerce.Payment.Gateway do
  @moduledoc \"\"\"
  Handles payment gateway integration for processing charges.
  \"\"\"

  @doc \"\"\"
  Charges a payment method.
  \"\"\"
  @spec charge(map(), pos_integer()) :: {:ok, map()} | {:error, term()}
  def charge(%{token: token}, amount) when is_integer(amount) and amount > 0 do
    {:ok, %{transaction_id: "txn_#{token}_#{amount}", status: :approved}}
  end
end
""",
    "lib/ecommerce/inventory/stock.ex": """\
defmodule Ecommerce.Inventory.Stock do
  @moduledoc \"\"\"
  Tracks inventory stock levels.
  \"\"\"

  @doc \"\"\"
  Returns available quantity for a SKU.
  \"\"\"
  @spec available?(String.t()) :: boolean()
  def available?(sku) when is_binary(sku) do
    :ets.member(:stock_table, sku)
  end
end
""",
    "lib/ecommerce/notification/mailer.ex": """\
defmodule Ecommerce.Notification.Mailer do
  @moduledoc \"\"\"
  Sends transactional email notifications.
  \"\"\"

  @doc \"\"\"
  Sends an order confirmation email.
  \"\"\"
  @spec send_confirmation(map()) :: :ok | {:error, term()}
  def send_confirmation(%{email: email, order_id: _order_id}) when is_binary(email) do
    :ok
  end
end
""",
    "lib/ecommerce/internal/helpers.ex": """\
defmodule Ecommerce.Internal.Helpers do
  @moduledoc false

  def format_currency(cents) when is_integer(cents) do
    "\$#{div(cents, 100)}.#{rem(cents, 100) |> Integer.to_string() |> String.pad_leading(2, "0")}"
  end
end
""",
    "test/ecommerce/payment_test.exs": """\
defmodule Ecommerce.Payment.GatewayTest do
  use ExUnit.Case

  test "charge succeeds with valid token and amount" do
    assert {:ok, %{status: :approved}} = Ecommerce.Payment.Gateway.charge(%{token: "tok_123"}, 1000)
  end
end
""",
    "test/ecommerce/stock_test.exs": """\
defmodule Ecommerce.Inventory.StockTest do
  use ExUnit.Case

  test "available? returns false for unknown sku" do
    assert Ecommerce.Inventory.Stock.available?("UNKNOWN-SKU") == false
  end
end
""",
    "docs/architecture.md": """\
# Architecture

The order processing pipeline consists of:
1. OrderProcessor GenServer - manages order lifecycle
2. Payment.Gateway - charges customers
3. Inventory.Stock - validates stock
4. Notification.Mailer - sends confirmations
""",
    "priv/repo/migrations/20240101_create_orders.exs": """\
defmodule Ecommerce.Repo.Migrations.CreateOrders do
  use Ecto.Migration

  def change do
    create table(:orders) do
      add :status, :string
      add :total_cents, :integer
      timestamps()
    end
  end
end
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE PROBLEM FILE: lib/ecommerce/order/processor.ex ──────────────────────
# This file contains deliberate violations across OTP, pattern-matching,
# and documentation domains.  The violations are:
#
#  V1 (OTP)         expensive_operation in init body (should use handle_continue)
#  V2 (OTP)         HTTPClient.get! blocking call inside handle_call (no Task offload)
#  V3 (OTP)         fire-and-forget status update uses call instead of cast
#  V4 (Pattern)     with clause has no else handler
#  V5 (Pattern)     destructuring done in function body, not head
#  V6 (Docs)        @moduledoc false on a genuinely public (non-internal) module
#  V7 (Docs)        public function submit_order/1 missing @doc and @spec
#  V8 (Docs)        doctest on side-effectful function (DB write)
#
# NON-VIOLATIONS the agent must NOT flag:
#  NV1  single |> pipe chain                  (valid per skill)
#  NV2  @doc false on handle_call/handle_cast (callback impl, valid per skill)
#  NV3  defp private_helper without @spec     (private functions ok per skill)

processor_code = """\
defmodule Ecommerce.Order.Processor do
  # VIOLATION V6: @moduledoc false on a genuinely public module
  @moduledoc false

  use GenServer
  require Logger

  alias Ecommerce.Payment.Gateway
  alias Ecommerce.Inventory.Stock
  alias Ecommerce.Notification.Mailer

  # VIOLATION V1: expensive work done synchronously in init/1
  def init(args) do
    catalog = load_full_product_catalog()
    {:ok, %{catalog: catalog, orders: %{}}}
  end

  # NON-VIOLATION NV2: @doc false on a callback implementation
  @doc false
  def handle_call({:fetch_shipping_rates, address}, _from, state) do
    # VIOLATION V2: blocking HTTP call inside handle_call
    result = HTTPClient.get!("https://shipping-api.internal/rates?addr=#{address}")
    {:reply, result, state}
  end

  @doc false
  def handle_cast({:log_order, order_id}, state) do
    Logger.info("Order logged: #{order_id}")
    {:noreply, state}
  end

  def handle_info(:refresh_catalog, state) do
    new_catalog = load_full_product_catalog()
    {:noreply, %{state | catalog: new_catalog}}
  end

  # VIOLATION V7: public function with no @doc and no @spec
  def submit_order(order_params) do
    # VIOLATION V4: with clause missing else handler
    with {:ok, validated} <- validate_order(order_params),
         {:ok, _stock}    <- Stock.available?(validated.sku),
         {:ok, charge}    <- Gateway.charge(validated.payment, validated.total_cents) do
      {:ok, charge}
    end
  end

  # VIOLATION V8: doctest on a side-effectful function (writes to DB/state)
  @doc \"\"\"
  Cancels an existing order by ID.

  ## Examples

      iex> Ecommerce.Order.Processor.cancel_order("ord_123")
      {:ok, :cancelled}

  \"\"\"
  @spec cancel_order(String.t()) :: {:ok, :cancelled} | {:error, term()}
  def cancel_order(order_id) when is_binary(order_id) do
    # VIOLATION V3: cast semantics but using call (fire-and-forget notification)
    GenServer.call(__MODULE__, {:notify_cancellation, order_id})
    {:ok, :cancelled}
  end

  # VIOLATION V5: destructuring done in body, not in function head
  def process_refund(payment_info) do
    token = payment_info.token
    amount = payment_info.amount
    Gateway.charge(%{token: token}, -amount)
  end

  # NON-VIOLATION NV1: single |> pipe, readability choice - must NOT be flagged
  def normalize_sku(sku) do
    sku
    |> String.upcase()
  end

  # PRIVATE FUNCTIONS

  # NON-VIOLATION NV3: private function without @spec - must NOT be flagged
  defp validate_order(params) do
    if Map.has_key?(params, :sku) and Map.has_key?(params, :total_cents) do
      {:ok, params}
    else
      {:error, :invalid_params}
    end
  end

  defp load_full_product_catalog do
    :timer.sleep(3000)
    %{products: []}
  end
end
"""

processor_path = os.path.join(workspace, "lib/ecommerce/order/processor.ex")
with open(processor_path, "w") as f:
    f.write(processor_code)

print("Workspace generated successfully.")
print(f"Problem file: {processor_path}")