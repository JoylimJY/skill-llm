import sys
import os
import re
import json
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0
total_checks = 0

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

def find_target_file(filename):
    """Find a file by exact name anywhere in workspace."""
    matches = list(workspace.rglob(filename))
    return matches[0] if matches else None

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# FILES WE EXPECT TO BE CREATED
# ─────────────────────────────────────────────────────────────────────────────
target_files = {
    "IProductRepository.vb": None,
    "ProductNotFoundException.vb": None,
    "ProductRepository.vb": None,
    "ProductFactory.vb": None,
    "InventoryService.vb": None,
}

# Locate each file
for fname in list(target_files.keys()):
    found = find_target_file(fname)
    if found:
        # Exclude the distractor C# file
        if str(found).endswith(".cs"):
            found = None
    target_files[fname] = found

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: check Option directives
# ─────────────────────────────────────────────────────────────────────────────
def check_option_directives(content, file_label):
    results = []
    for directive in ["Option Explicit On", "Option Strict On", "Option Infer On"]:
        present = bool(re.search(r'(?i)' + re.escape(directive), content))
        results.append((f"{file_label}: has '{directive}'", present,
                        f"Found" if present else f"Missing '{directive}'"))
    return results

# ─────────────────────────────────────────────────────────────────────────────
# CHECK GROUP 1: IProductRepository.vb
# ─────────────────────────────────────────────────────────────────────────────
ipr_path = target_files["IProductRepository.vb"]
if ipr_path is None:
    add_check("IProductRepository.vb: file exists", False, "File not found anywhere in workspace")
else:
    content = read_file(ipr_path)
    if content is None:
        add_check("IProductRepository.vb: file readable", False, "Could not read file")
    else:
        add_check("IProductRepository.vb: file exists", True, str(ipr_path))

        for name, passed, detail in check_option_directives(content, "IProductRepository.vb"):
            add_check(name, passed, detail)

        # Interface name starts with I and is PascalCase
        has_iface_name = bool(re.search(r'Public\s+Interface\s+IProductRepository\b', content))
        add_check("IProductRepository.vb: interface named IProductRepository (I-prefix, PascalCase)",
                  has_iface_name, "Found" if has_iface_name else "Interface declaration missing or wrong name")

        # Methods must be Function returning Task (async interface methods return Task/Task(Of T))
        has_get_by_id = bool(re.search(
            r'Function\s+GetByIdAsync\s*\(.*\)\s+As\s+Task', content, re.IGNORECASE))
        add_check("IProductRepository.vb: GetByIdAsync returns Task",
                  has_get_by_id, "Found" if has_get_by_id else "Missing GetByIdAsync returning Task")

        has_get_all = bool(re.search(
            r'Function\s+GetAllAsync\s*\(.*\)\s+As\s+Task', content, re.IGNORECASE))
        add_check("IProductRepository.vb: GetAllAsync returns Task",
                  has_get_all, "Found" if has_get_all else "Missing GetAllAsync returning Task")

        has_get_by_warehouse = bool(re.search(
            r'Function\s+GetByWarehouseAsync\s*\(', content, re.IGNORECASE))
        add_check("IProductRepository.vb: GetByWarehouseAsync declared",
                  has_get_by_warehouse, "Found" if has_get_by_warehouse else "Missing GetByWarehouseAsync")

        has_cancellation = bool(re.search(r'CancellationToken', content, re.IGNORECASE))
        add_check("IProductRepository.vb: CancellationToken parameter present",
                  has_cancellation, "Found" if has_cancellation else "No CancellationToken in interface")

        # XML doc comments on interface
        has_xml_doc = bool(re.search(r"'''\s*<summary>", content))
        add_check("IProductRepository.vb: XML doc comments (''' <summary>) present",
                  has_xml_doc, "Found" if has_xml_doc else "Missing XML doc comments")

        # Generic type param T or typed to Product
        has_generic_or_product = bool(re.search(r'IRepository\s*\(Of\s+\w+\)|IProductRepository\b', content))
        add_check("IProductRepository.vb: proper VB.NET generic/interface syntax",
                  has_generic_or_product, "Found" if has_generic_or_product else "Generic/interface syntax suspicious")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK GROUP 2: ProductNotFoundException.vb
# ─────────────────────────────────────────────────────────────────────────────
pnf_path = target_files["ProductNotFoundException.vb"]
if pnf_path is None:
    add_check("ProductNotFoundException.vb: file exists", False, "File not found anywhere in workspace")
else:
    content = read_file(pnf_path)
    if content is None:
        add_check("ProductNotFoundException.vb: file readable", False, "Could not read file")
    else:
        add_check("ProductNotFoundException.vb: file exists", True, str(pnf_path))

        for name, passed, detail in check_option_directives(content, "ProductNotFoundException.vb"):
            add_check(name, passed, detail)

        # Class name is PascalCase and Inherits Exception
        has_class = bool(re.search(r'Public\s+Class\s+ProductNotFoundException\b', content))
        add_check("ProductNotFoundException.vb: class named ProductNotFoundException",
                  has_class, "Found" if has_class else "Wrong or missing class declaration")

        inherits_exception = bool(re.search(r'Inherits\s+Exception\b', content, re.IGNORECASE))
        add_check("ProductNotFoundException.vb: Inherits Exception",
                  inherits_exception, "Found" if inherits_exception else "Missing 'Inherits Exception'")

        # ReadOnly Property for domain data (ProductId)
        has_readonly_prop = bool(re.search(
            r'Public\s+ReadOnly\s+Property\s+Product\w*\s+As\s+Integer', content, re.IGNORECASE))
        add_check("ProductNotFoundException.vb: ReadOnly Property for ProductId (Integer)",
                  has_readonly_prop, "Found" if has_readonly_prop else "Missing ReadOnly Property ProductId As Integer")

        # Two constructors: one(id), one(id, innerException)
        constructor_matches = re.findall(r'Public\s+Sub\s+New\s*\(', content, re.IGNORECASE)
        has_two_ctors = len(constructor_matches) >= 2
        add_check("ProductNotFoundException.vb: at least 2 constructors (id-only and id+innerException)",
                  has_two_ctors,
                  f"Found {len(constructor_matches)} constructor(s)" if not has_two_ctors else "Found 2+ constructors")

        # Inner exception constructor uses MyBase.New(msg, innerException)
        has_inner_ex_ctor = bool(re.search(
            r'MyBase\.New\s*\(.*,\s*\w+\)', content, re.IGNORECASE))
        add_check("ProductNotFoundException.vb: inner-exception constructor calls MyBase.New(msg, innerException)",
                  has_inner_ex_ctor, "Found" if has_inner_ex_ctor else "Missing MyBase.New(msg, innerEx) pattern")

        # XML doc
        has_xml_doc = bool(re.search(r"'''\s*<summary>", content))
        add_check("ProductNotFoundException.vb: XML doc comments",
                  has_xml_doc, "Found" if has_xml_doc else "Missing XML doc comments")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK GROUP 3: ProductRepository.vb
# ─────────────────────────────────────────────────────────────────────────────
pr_path = target_files["ProductRepository.vb"]
# Make sure we don't pick up the C# distractor
if pr_path is not None and str(pr_path).endswith(".cs"):
    pr_path = None

if pr_path is None:
    # Try to find the VB one specifically
    vb_matches = [p for p in workspace.rglob("ProductRepository.vb") if not str(p).endswith(".cs")]
    pr_path = vb_matches[0] if vb_matches else None

if pr_path is None:
    add_check("ProductRepository.vb: file exists", False, "File not found (only .cs distractor exists)")
else:
    content = read_file(pr_path)
    if content is None:
        add_check("ProductRepository.vb: file readable", False, "Could not read file")
    else:
        add_check("ProductRepository.vb: file exists", True, str(pr_path))

        for name, passed, detail in check_option_directives(content, "ProductRepository.vb"):
            add_check(name, passed, detail)

        # Implements IProductRepository or IRepository(Of Product)
        implements_iface = bool(re.search(
            r'Implements\s+IProductRepository\b|Implements\s+IRepository\s*\(Of\s+Product\)', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Implements IProductRepository or IRepository(Of Product)",
                  implements_iface, "Found" if implements_iface else "Missing Implements declaration")

        # IDisposable implementation
        implements_idisposable = bool(re.search(r'Implements\s+IDisposable', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Implements IDisposable",
                  implements_idisposable, "Found" if implements_idisposable else "Missing IDisposable implementation")

        # _disposed boolean field
        has_disposed_field = bool(re.search(
            r'Private\s+_disposed\s+As\s+Boolean', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Private _disposed As Boolean field (_camelCase)",
                  has_disposed_field, "Found" if has_disposed_field else "Missing '_disposed' boolean field")

        # Protected Overridable Sub Dispose(disposing As Boolean)
        has_protected_dispose = bool(re.search(
            r'Protected\s+(?:Overridable\s+)?Sub\s+Dispose\s*\(\s*\w+\s+As\s+Boolean\s*\)', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Protected Overridable Sub Dispose(disposing As Boolean)",
                  has_protected_dispose, "Found" if has_protected_dispose else "Missing protected dispose pattern")

        # Private fields with underscore prefix (at least one)
        has_underscore_field = bool(re.search(r'Private\s+(?:ReadOnly\s+)?_\w+\s+As\s+', content))
        add_check("ProductRepository.vb: private fields use _camelCase prefix",
                  has_underscore_field, "Found" if has_underscore_field else "No _camelCase private fields found")

        # Async methods with Async Function ... As Task
        has_async_methods = bool(re.search(
            r'Public\s+Async\s+Function\s+\w+Async\s*\(', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Async Function methods with Async suffix",
                  has_async_methods, "Found" if has_async_methods else "No 'Public Async Function ...Async' methods found")

        # ConfigureAwait(False) present (library code)
        has_configure_await = bool(re.search(r'\.ConfigureAwait\s*\(\s*False\s*\)', content, re.IGNORECASE))
        add_check("ProductRepository.vb: ConfigureAwait(False) used in library async code",
                  has_configure_await, "Found" if has_configure_await else "Missing ConfigureAwait(False)")

        # Using statement for IDisposable resources
        has_using = bool(re.search(r'\bUsing\b', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Using statement for IDisposable objects",
                  has_using, "Found" if has_using else "No Using statement found")

        # Try/Catch with specific exceptions (not just generic Exception)
        specific_catch = bool(re.search(
            r'Catch\s+\w+\s+As\s+(?!Exception\b)\w+Exception\b', content, re.IGNORECASE))
        add_check("ProductRepository.vb: Try/Catch with specific exception types (not just Exception)",
                  specific_catch, "Found" if specific_catch else "No specific-exception Catch blocks found")

        # ProductNotFoundException thrown
        throws_pnf = bool(re.search(r'Throw\s+New\s+ProductNotFoundException\b', content, re.IGNORECASE))
        add_check("ProductRepository.vb: throws ProductNotFoundException for missing product",
                  throws_pnf, "Found" if throws_pnf else "Missing 'Throw New ProductNotFoundException'")

        # Method-syntax LINQ (not pure query syntax)
        has_method_linq = bool(re.search(
            r'\.(Where|Select|OrderBy|FirstOrDefault|ToList|Any|All|GroupBy)\s*\(', content, re.IGNORECASE))
        add_check("ProductRepository.vb: method-syntax LINQ used",
                  has_method_linq, "Found" if has_method_linq else "No method-syntax LINQ found")

        # LINQ filtering with Function lambda
        has_lambda_linq = bool(re.search(
            r'\.(Where|Select|OrderBy|FirstOrDefault)\s*\(\s*Function\s*\(', content, re.IGNORECASE))
        add_check("ProductRepository.vb: LINQ lambdas use Function keyword",
                  has_lambda_linq, "Found" if has_lambda_linq else "No LINQ Function lambdas found")

        # GC.SuppressFinalize in Dispose
        has_gc_suppress = bool(re.search(r'GC\.SuppressFinalize', content, re.IGNORECASE))
        add_check("ProductRepository.vb: GC.SuppressFinalize(Me) in Dispose",
                  has_gc_suppress, "Found" if has_gc_suppress else "Missing GC.SuppressFinalize(Me)")

        # XML doc comments
        has_xml_doc = bool(re.search(r"'''\s*<summary>", content))
        add_check("ProductRepository.vb: XML doc comments (''' <summary>)",
                  has_xml_doc, "Found" if has_xml_doc else "Missing XML doc comments")

        # No blocking .Result or .Wait() anti-patterns
        has_blocking = bool(re.search(r'\.(Result|Wait\(\))\b', content))
        add_check("ProductRepository.vb: no blocking .Result or .Wait() anti-patterns",
                  not has_blocking,
                  "No blocking calls found" if not has_blocking else "Found blocking .Result or .Wait() - deadlock risk")

        # No Async Sub (except event handlers)
        has_async_sub = bool(re.search(r'Public\s+Async\s+Sub\s+(?!.*EventHandler)', content, re.IGNORECASE))
        add_check("ProductRepository.vb: no 'Public Async Sub' (must use Async Function returning Task)",
                  not has_async_sub,
                  "Correct: no invalid Async Sub found" if not has_async_sub else "Found 'Public Async Sub' - use Async Function returning Task instead")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK GROUP 4: ProductFactory.vb
# ─────────────────────────────────────────────────────────────────────────────
pf_path = target_files["ProductFactory.vb"]
if pf_path is None:
    add_check("ProductFactory.vb: file exists", False, "File not found anywhere in workspace")
else:
    content = read_file(pf_path)
    if content is None:
        add_check("ProductFactory.vb: file readable", False, "Could not read file")
    else:
        add_check("ProductFactory.vb: file exists", True, str(pf_path))

        for name, passed, detail in check_option_directives(content, "ProductFactory.vb"):
            add_check(name, passed, detail)

        # Class named ProductFactory (PascalCase)
        has_class = bool(re.search(r'Public\s+Class\s+ProductFactory\b', content))
        add_check("ProductFactory.vb: class named ProductFactory (PascalCase)",
                  has_class, "Found" if has_class else "Missing ProductFactory class")

        # Public Shared Function CreateProduct
        has_shared_factory = bool(re.search(
            r'Public\s+Shared\s+Function\s+CreateProduct\s*\(', content, re.IGNORECASE))
        add_check("ProductFactory.vb: Public Shared Function CreateProduct",
                  has_shared_factory, "Found" if has_shared_factory else "Missing 'Public Shared Function CreateProduct'")

        # Select Case used for factory branching (per SKILL.md class-design-and-patterns.md)
        has_select_case = bool(re.search(r'Select\s+Case\b', content, re.IGNORECASE))
        add_check("ProductFactory.vb: Select Case for product type branching",
                  has_select_case, "Found" if has_select_case else "Missing Select Case (required for factory branching per docs)")

        # Case Else with Throw New ArgumentException
        has_case_else_throw = bool(re.search(
            r'Case\s+Else.*Throw\s+New\s+ArgumentException', content, re.IGNORECASE | re.DOTALL))
        add_check("ProductFactory.vb: Case Else throws ArgumentException for invalid type",
                  has_case_else_throw, "Found" if has_case_else_throw else "Missing Case Else + Throw New ArgumentException")

        # XML doc
        has_xml_doc = bool(re.search(r"'''\s*<summary>", content))
        add_check("ProductFactory.vb: XML doc comments",
                  has_xml_doc, "Found" if has_xml_doc else "Missing XML doc comments")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK GROUP 5: InventoryService.vb (new version replacing the distractor)
# ─────────────────────────────────────────────────────────────────────────────
# The agent should produce a new InventoryService.vb or overwrite the stub
is_path = find_target_file("InventoryService.vb")
if is_path is None:
    add_check("InventoryService.vb: file exists", False, "File not found")
else:
    content = read_file(is_path)
    if content is None:
        add_check("InventoryService.vb: file readable", False, "Could not read file")
    else:
        # Verify it's not just the stub (stub has "Blocking - needs to be fixed")
        is_stub = "Blocking - needs to be fixed" in content
        add_check("InventoryService.vb: is not the original stub",
                  not is_stub,
                  "New implementation detected" if not is_stub else "Still the original stub - not replaced")

        if not is_stub:
            for name, passed, detail in check_option_directives(content, "InventoryService.vb"):
                add_check(name, passed, detail)

            # Class named InventoryService
            has_class = bool(re.search(r'Public\s+Class\s+InventoryService\b', content))
            add_check("InventoryService.vb: class named InventoryService",
                      has_class, "Found" if has_class else "Missing InventoryService class")

            # Uses IProductRepository (injected via constructor, not concrete type)
            has_iface_injection = bool(re.search(
                r'Private\s+(?:ReadOnly\s+)?_\w+\s+As\s+IProductRepository', content, re.IGNORECASE))
            add_check("InventoryService.vb: IProductRepository injected as _camelCase ReadOnly private field",
                      has_iface_injection,
                      "Found" if has_iface_injection else "Missing 'Private ReadOnly _xxx As IProductRepository'")

            # Task.WhenAll or parallel async operations
            has_when_all = bool(re.search(r'Task\.WhenAll\b', content, re.IGNORECASE))
            add_check("InventoryService.vb: Task.WhenAll used for parallel async loading",
                      has_when_all, "Found" if has_when_all else "Missing Task.WhenAll for parallel operations")

            # CancellationToken in at least one method
            has_ct = bool(re.search(r'CancellationToken', content, re.IGNORECASE))
            add_check("InventoryService.vb: CancellationToken parameter in async methods",
                      has_ct, "Found" if has_ct else "No CancellationToken found")

            # ThrowIfCancellationRequested used
            has_throw_if_cancelled = bool(re.search(
                r'cancellationToken\.ThrowIfCancellationRequested\(\)', content, re.IGNORECASE))
            add_check("InventoryService.vb: cancellationToken.ThrowIfCancellationRequested() called",
                      has_throw_if_cancelled,
                      "Found" if has_throw_if_cancelled else "Missing ThrowIfCancellationRequested()")

            # Boolean property uses Is/Has/Can prefix
            bool_prop_pattern = bool(re.search(
                r'Public\s+(?:ReadOnly\s+)?Property\s+(?:Is|Has|Can|Should)\w+\s+As\s+Boolean', content, re.IGNORECASE))
            # Check for boolean local vars or properties
            bool_naming = bool(re.search(
                r'\b(?:is|has|can|should)\w+\s+As\s+Boolean\b', content, re.IGNORECASE))
            add_check("InventoryService.vb: Boolean variables/properties use Is/Has/Can/Should prefix",
                      bool_prop_pattern or bool_naming,
                      "Found" if (bool_prop_pattern or bool_naming) else "No Is/Has/Can/Should boolean naming found")

            # XML doc
            has_xml_doc = bool(re.search(r"'''\s*<summary>", content))
            add_check("InventoryService.vb: XML doc comments",
                      has_xml_doc, "Found" if has_xml_doc else "Missing XML doc comments")

            # No Hungarian notation (strXxx, intXxx, boolXxx, dblXxx)
            has_hungarian = bool(re.search(
                r'\b(?:str|int|dbl|bool|obj|arr|lst)\w+\s+As\s+', content))
            add_check("InventoryService.vb: no Hungarian notation (strXxx, intXxx, etc.)",
                      not has_hungarian,
                      "Clean naming" if not has_hungarian else "Found Hungarian notation variable names")

# ─────────────────────────────────────────────────────────────────────────────
# CROSS-FILE CHECK: Namespace consistency
# ─────────────────────────────────────────────────────────────────────────────
all_vb_files_created = [p for p in [ipr_path, pnf_path, pr_path, pf_path, is_path]
                         if p is not None and not str(p).endswith(".cs")]
namespace_pattern = re.compile(r'Namespace\s+([\w.]+)', re.IGNORECASE)
namespaces_found = set()
for fpath in all_vb_files_created:
    c = read_file(fpath)
    if c:
        for m in namespace_pattern.finditer(c):
            namespaces_found.add(m.group(1))

if all_vb_files_created:
    # All namespaces should be from the same root (Logistics.Inventory)
    consistent = all(
        ns.startswith("Logistics") or ns.startswith("logistics")
        for ns in namespaces_found
    ) if namespaces_found else False
    add_check("Cross-file: Namespace follows PascalCase hierarchical convention (Logistics.Inventory.*)",
              consistent or len(namespaces_found) == 0,
              f"Namespaces found: {namespaces_found}" if namespaces_found else "No Namespace declarations found (acceptable if inside project)")

# ─────────────────────────────────────────────────────────────────────────────
# SCORE CALCULATION
# ─────────────────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total_count = len(checks)
final_score = round(passed_count / total_count, 4) if total_count > 0 else 0.0
all_passed = passed_count == total_count

result = {
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))