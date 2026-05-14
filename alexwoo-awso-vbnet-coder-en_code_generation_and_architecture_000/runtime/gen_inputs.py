import os
import random
import textwrap

random.seed(42)

BASE = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "src/Logistics.Inventory/Data",
    "src/Logistics.Inventory/Models",
    "src/Logistics.Inventory/Services",
    "src/Logistics.Inventory/Exceptions",
    "src/Logistics.Inventory/Interfaces",
    "src/Logistics.Inventory/Factories",
    "tests/Logistics.Inventory.Tests",
    "docs/architecture",
    "docs/api",
    "scripts",
    "config",
    "build",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── SKILL.md reference docs ─────────────────────────────────────────────────
skill_docs_dir = os.path.join(BASE, "docs")
os.makedirs(os.path.join(skill_docs_dir, "vbnet"), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────

# 1. Old broken VB.NET file (missing Option directives, wrong naming, bad patterns)
bad_vb = textwrap.dedent("""\
    ' Old code - DO NOT USE
    Imports System

    Public Class inventoryMgr
        Dim connectionStr As String
        Dim isDisposed As Boolean

        Public Sub New(connStr As String)
            connectionStr = connStr
        End Sub

        Public Function getProducts() As Object
            ' TODO: implement
            Return Nothing
        End Function

        Public Sub Dispose()
            isDisposed = True
        End Sub
    End Class
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Data/inventoryMgr.vb"), "w") as f:
    f.write(bad_vb)

# 2. C# stub file (wrong language, distractor)
cs_stub = textwrap.dedent("""\
    // C# version - being replaced by VB.NET
    using System;
    using System.Collections.Generic;
    using System.Threading.Tasks;

    namespace Logistics.Inventory.Data
    {
        public class ProductRepository : IDisposable
        {
            private bool _disposed = false;
            public async Task<IEnumerable<Product>> GetAllAsync() => throw new NotImplementedException();
            public void Dispose() { _disposed = true; }
        }
    }
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Data/ProductRepository.cs"), "w") as f:
    f.write(cs_stub)

# 3. Partial/incomplete interface file (missing Option directives, wrong naming)
bad_interface = textwrap.dedent("""\
    Imports System.Threading.Tasks

    Public Interface iProductRepo
        Function GetByIdAsync(id As Integer) As Task(Of Object)
        Function GetAllAsync() As Task(Of Object)
    End Interface
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Interfaces/iProductRepo.vb"), "w") as f:
    f.write(bad_interface)

# 4. Old exception class without proper structure
bad_exception = textwrap.dedent("""\
    Imports System

    Public Class InventoryException
        Inherits Exception
        Public Sub New(msg As String)
            MyBase.New(msg)
        End Sub
    End Class
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Exceptions/InventoryException.vb"), "w") as f:
    f.write(bad_exception)

# 5. Product model with Hungarian notation and wrong field naming
bad_model = textwrap.dedent("""\
    Public Class Product
        Public strProductName As String
        Public intQuantity As Integer
        Public dblPrice As Double
        Public boolIsActive As Boolean
        Public intWarehouseId As Integer
    End Class
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Models/Product.vb"), "w") as f:
    f.write(bad_model)

# 6. Config JSON
config_json = '{"ConnectionString": "Server=localhost;Database=Inventory;Trusted_Connection=True", "MaxRetries": 3, "TimeoutSeconds": 30}\n'
with open(os.path.join(BASE, "config/appsettings.json"), "w") as f:
    f.write(config_json)

# 7. Architecture notes
arch_notes = textwrap.dedent("""\
    # Architecture Notes
    
    The inventory system uses a layered architecture:
    - Data Layer: Repositories implementing IRepository(Of T)
    - Service Layer: Business logic, uses repositories
    - Factory: Creates product instances by type
    
    Product types:
    - Perishable: has expiry date tracking
    - Durable: has warranty period
    - Digital: no physical stock
    
    Warehouse zones: A (cold), B (dry), C (hazmat)
""")
with open(os.path.join(BASE, "docs/architecture/overview.md"), "w") as f:
    f.write(arch_notes)

# 8. API docs stub
api_doc = textwrap.dedent("""\
    # API Reference (draft)
    
    ## IProductRepository
    - GetByIdAsync(id) -> Product?
    - GetAllAsync() -> IEnumerable<Product>
    - GetByWarehouseAsync(warehouseId, cancellationToken) -> IEnumerable<Product>
    - AddAsync(product) -> void
    - UpdateAsync(product) -> void
    - DeleteAsync(id) -> void
    
    ## ProductFactory
    - CreateProduct(type) -> Product
    
    ## Exceptions
    - ProductNotFoundException(productId)
""")
with open(os.path.join(BASE, "docs/api/product-api.md"), "w") as f:
    f.write(api_doc)

# 9. Build script placeholder
with open(os.path.join(BASE, "scripts/build.sh"), "w") as f:
    f.write("#!/bin/bash\ndotnet build src/Logistics.Inventory/\n")

# 10. Test placeholder
test_placeholder = textwrap.dedent("""\
    ' Placeholder - unit tests to be added after implementation
    Imports System
    Imports Xunit

    Namespace Logistics.Inventory.Tests
        Public Class ProductRepositoryTests
            ' TODO: Add tests
        End Class
    End Namespace
""")
with open(os.path.join(BASE, "tests/Logistics.Inventory.Tests/ProductRepositoryTests.vb"), "w") as f:
    f.write(test_placeholder)

# 11. .vbproj file for context (without Option directives set, agent must add them per-file)
vbproj = textwrap.dedent("""\
    <Project Sdk="Microsoft.NET.Sdk">
      <PropertyGroup>
        <OutputType>Library</OutputType>
        <TargetFramework>net8.0</TargetFramework>
        <RootNamespace>Logistics.Inventory</RootNamespace>
        <AssemblyName>Logistics.Inventory</AssemblyName>
        <Nullable>enable</Nullable>
      </PropertyGroup>
    </Project>
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Logistics.Inventory.vbproj"), "w") as f:
    f.write(vbproj)

# 12. Warehouse model (partial, uses wrong style)
warehouse_model = textwrap.dedent("""\
    Public Class Warehouse
        Public id As Integer
        Public name As String
        Public zone As String
    End Class
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Models/Warehouse.vb"), "w") as f:
    f.write(warehouse_model)

# 13. Service stub with blocking async anti-pattern
bad_service = textwrap.dedent("""\
    Imports System.Threading.Tasks

    Public Class InventoryService
        Private repo As Object

        Public Sub New(r As Object)
            repo = r
        End Sub

        Public Function GetProducts() As Object
            ' Blocking - needs to be fixed
            Return Nothing
        End Function
    End Class
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Services/InventoryService.vb"), "w") as f:
    f.write(bad_service)

# 14. Logger interface stub
logger_interface = textwrap.dedent("""\
    Public Interface ILogger
        Sub LogError(message As String)
        Sub LogInfo(message As String)
        Sub LogWarning(message As String)
    End Interface
""")
with open(os.path.join(BASE, "src/Logistics.Inventory/Interfaces/ILogger.vb"), "w") as f:
    f.write(logger_interface)

print("Workspace scaffold created successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        full = os.path.join(root, fname)
        print(f"  {full}")