#!/usr/bin/env python3
"""
Generates the sandbox workspace for the minimax-docx Template-Apply task.
Creates the skill tooling, a realistic corporate template .docx, distractor files,
and the data payload the agent must use to fill the template.
"""

import os
import sys
import random
import zipfile
import shutil
import json
import struct
from pathlib import Path
from textwrap import dedent

random.seed(42)

WORKSPACE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

SKILL_PATH = WORKSPACE / "skill" / "minimax-docx"

# ─────────────────────────────────────────────
# 1. SKILL DIRECTORY STRUCTURE
# ─────────────────────────────────────────────
dirs = [
    SKILL_PATH / "guides",
    SKILL_PATH / "src" / "Templates",
    SKILL_PATH / "src" / "Core",
    SKILL_PATH / "src" / "Validators",
    WORKSPACE / "project" / "quarterly_reports" / "Q3_2024",
    WORKSPACE / "project" / "quarterly_reports" / "Q4_2024",
    WORKSPACE / "project" / "reference_docs",
    WORKSPACE / "project" / "archive" / "2023",
    WORKSPACE / "project" / "data_exports",
    WORKSPACE / "project" / "meetings" / "notes",
    WORKSPACE / "project" / "hr" / "records",
    WORKSPACE / "project" / "it" / "config",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 2. SKILL.md (entry point)
# ─────────────────────────────────────────────
(SKILL_PATH / "SKILL.md").write_text(dedent("""
    ---
    name: minimax-docx
    description: "Enterprise-grade Word document generation. Creates validated .docx files with professional formatting, visual hierarchy, and cross-application compatibility."
    ---

    <role>
    You are a document composition specialist. Your deliverables are complete, validated .docx files ready for distribution.
    </role>

    ## Dependencies

    - Python 3, .NET 9.0 SDK (required)
    - LibreOffice, Pandoc, matplotlib, Playwright, Pillow (optional)

    ## Execution Lanes

    Identify the lane first. Do not mix lanes.

    | Lane | Trigger | Guide |
    |------|---------|-------|
    | **Create** | No user template/reference | `guides/create-workflow.md` |
    | **Template-Apply** | User provides .docx/.doc file | `guides/template-apply-workflow.md` |

    ## Exit Criteria (All Lanes)

    ### Technical Gates
    - [ ] `python3 <skill-path>/docx_engine.py audit <output.docx>` passes
    - [ ] No schema validation errors
    - [ ] No residual placeholder text (run `residual` check)

    ### Visual Gates
    - [ ] Heading hierarchy visually distinct
    - [ ] Spacing consistent throughout
    - [ ] Color palette restrained (≤3 primary colors)
    - [ ] Adequate whitespace (margins ≥72pt)

    ## Quick Commands

    ```bash
    # Environment check
    python3 <skill-path>/docx_engine.py doctor

    # Build (Create lane)
    python3 <skill-path>/docx_engine.py render [output.docx]

    # Build (Template-Apply lane)
    dotnet run --project <skill-path>/src/DocForge.csproj -- from-template <template.docx> <output.docx>

    # Validate
    python3 <skill-path>/docx_engine.py audit <file.docx>

    # Preview content
    python3 <skill-path>/docx_engine.py preview <file.docx>

    # Check residual placeholders
    python3 <skill-path>/docx_engine.py residual <file.docx>
    ```

    ## Reference Index

    | Resource | When to Read |
    |----------|--------------|
    | `guides/create-workflow.md` | Before any Create task |
    | `guides/template-apply-workflow.md` | Before any Template-Apply task |
    | `guides/development.md` | Before writing C# code |
    | `guides/troubleshooting.md` | When encountering errors |
    | `guides/styling.md` | When designing visual appearance |
    | `src/Templates/*.cs` | For code patterns and examples |
    | `src/Core/*.cs` | For OpenXML primitives |

    ## Tooling Constraints

    | Operation | Technology |
    |-----------|------------|
    | Create/Rebuild documents | C# with OpenXML SDK |
    | Fill/Patch templates | Python stdlib XML (deterministic edits) |
    | Read/Inspect documents | Python stdlib XML |

    **Restricted**: Do not use python-docx, docx-js, or similar wrapper libraries.
""").strip())

# ─────────────────────────────────────────────
# 3. GUIDE: template-apply-workflow.md
# ─────────────────────────────────────────────
(SKILL_PATH / "guides" / "template-apply-workflow.md").write_text(dedent("""
    # Template-Apply Workflow

    Use this lane when the user supplies an existing `.docx` or `.doc` file as a base.

    ## Step 1 — Inspect the Template

    ```bash
    python3 <skill-path>/docx_engine.py preview <template.docx>
    ```

    This prints all detected placeholder tokens. Placeholders follow the pattern:
    `{{PLACEHOLDER_NAME}}`

    Note every placeholder name. You will supply values for all of them.

    ## Step 2 — Prepare the Data Manifest

    Create a JSON file named **`data_manifest.json`** in the same directory as your output.
    The manifest schema:

    ```json
    {
      "placeholders": {
        "PLACEHOLDER_NAME": "replacement value",
        ...
      },
      "metadata": {
        "author": "Full Name",
        "department": "Department Name",
        "document_version": "x.y"
      }
    }
    ```

    - All placeholder keys must match **exactly** (case-sensitive).
    - Every placeholder discovered in Step 1 MUST have an entry. Missing keys cause a hard failure.
    - Values must be plain strings (no nested objects).

    ## Step 3 — Run DocForge

    ```bash
    dotnet run --project <skill-path>/src/DocForge.csproj -- from-template <template.docx> <output.docx>
    ```

    DocForge automatically discovers `data_manifest.json` in the **same directory as `<output.docx>`**.
    It performs:
    1. XML-safe string substitution for all placeholders.
    2. Metadata injection (author, department, document_version) into the docx `core.xml`.
    3. Margin enforcement: all section margins set to ≥ 72pt (1 inch = 1440 twips; 72pt = 1440 twips).

    ## Step 4 — Validate

    ```bash
    python3 <skill-path>/docx_engine.py audit <output.docx>
    python3 <skill-path>/docx_engine.py residual <output.docx>
    ```

    Both commands must exit with code 0. Fix any reported issues before delivery.

    ## Step 5 — Deliver

    The final artifact is `<output.docx>`. Do not deliver the template or the manifest.

    ## Common Errors

    | Error | Cause | Fix |
    |-------|-------|-----|
    | `MISSING_PLACEHOLDER_KEY` | A `{{TOKEN}}` in template has no manifest entry | Add the key to `data_manifest.json` |
    | `RESIDUAL_PLACEHOLDER` | A `{{TOKEN}}` survived substitution | Check for key typo in manifest |
    | `MARGIN_VIOLATION` | Section margin < 72pt | DocForge auto-fixes; re-run if persists |
    | `METADATA_INCOMPLETE` | `metadata` block missing required field | Add missing field to manifest |
""").strip())

# ─────────────────────────────────────────────
# 4. GUIDE: create-workflow.md
# ─────────────────────────────────────────────
(SKILL_PATH / "guides" / "create-workflow.md").write_text(dedent("""
    # Create Workflow

    Use this lane when NO template is supplied.

    ## Step 1 — Doctor Check
    ```bash
    python3 <skill-path>/docx_engine.py doctor
    ```

    ## Step 2 — Author document.yaml
    Create `document.yaml` describing the document structure.

    ## Step 3 — Render
    ```bash
    python3 <skill-path>/docx_engine.py render output.docx
    ```

    ## Step 4 — Validate
    ```bash
    python3 <skill-path>/docx_engine.py audit output.docx
    python3 <skill-path>/docx_engine.py residual output.docx
    ```
""").strip())

# ─────────────────────────────────────────────
# 5. GUIDE: styling.md
# ─────────────────────────────────────────────
(SKILL_PATH / "guides" / "styling.md").write_text(dedent("""
    # Styling Guide

    ## Typography
    - Body: Calibri 11pt
    - H1: Calibri 18pt Bold
    - H2: Calibri 14pt Bold

    ## Color Palette (max 3 primary)
    - #003366 (corporate blue)
    - #FFFFFF (white)
    - #F2F2F2 (light gray)

    ## Margins
    Minimum 72pt (= 1440 twips) on all sides.
    DocForge enforces this automatically in Template-Apply lane.
""").strip())

# ─────────────────────────────────────────────
# 6. GUIDE: troubleshooting.md
# ─────────────────────────────────────────────
(SKILL_PATH / "guides" / "troubleshooting.md").write_text(dedent("""
    # Troubleshooting

    ## dotnet build errors
    Ensure .NET 9.0 SDK is installed: `dotnet --version`

    ## audit failures
    Run `python3 <skill-path>/docx_engine.py preview <file.docx>` to inspect content.

    ## residual failures
    Check data_manifest.json keys for typos. Keys are case-sensitive.

    ## MARGIN_VIOLATION
    DocForge auto-corrects margins. If it persists, check sectPr elements manually.
""").strip())

# ─────────────────────────────────────────────
# 7. GUIDE: development.md
# ─────────────────────────────────────────────
(SKILL_PATH / "guides" / "development.md").write_text(dedent("""
    # Development Guide

    ## C# Code Style
    - Target framework: net9.0
    - Nullable reference types enabled
    - Use DocumentFormat.OpenXml SDK 3.x

    ## Project Layout
    src/
      DocForge.csproj
      Program.cs
      Templates/
      Core/
      Validators/
""").strip())

# ─────────────────────────────────────────────
# 8. docx_engine.py  — THE PYTHON ENGINE
#    Implements: doctor, preview, audit, residual
#    (render is create-lane only)
# ─────────────────────────────────────────────
docx_engine_src = r'''#!/usr/bin/env python3
"""
docx_engine.py — minimax-docx Python CLI
Commands: doctor, preview, audit, residual, render
"""
import sys, os, zipfile, re, json
from pathlib import Path
from xml.etree import ElementTree as ET

WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
PKG_NS  = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS   = "http://purl.org/dc/elements/1.1/"

PLACEHOLDER_RE = re.compile(r'\{\{([A-Z0-9_]+)\}\}')

def _extract_text_from_docx(docx_path):
    texts = []
    with zipfile.ZipFile(docx_path) as z:
        if "word/document.xml" not in z.namelist():
            return []
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    for elem in root.iter(f"{{{WORD_NS}}}t"):
        if elem.text:
            texts.append(elem.text)
    return texts

def _full_text(docx_path):
    return " ".join(_extract_text_from_docx(docx_path))

def cmd_doctor():
    import subprocess
    issues = []
    # check python
    print(f"[OK] Python {sys.version.split()[0]}")
    # check dotnet
    try:
        r = subprocess.run(["dotnet","--version"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            print(f"[OK] .NET {r.stdout.strip()}")
        else:
            issues.append(".NET not found")
    except Exception as e:
        issues.append(f".NET check failed: {e}")
    if issues:
        for i in issues: print(f"[WARN] {i}")
        sys.exit(1)
    print("[PASS] doctor complete")

def cmd_preview(docx_path):
    path = Path(docx_path)
    if not path.exists():
        print(f"ERROR: file not found: {docx_path}", file=sys.stderr)
        sys.exit(1)
    text = _full_text(path)
    tokens = set(PLACEHOLDER_RE.findall(text))
    print(f"=== Preview: {path.name} ===")
    print(f"Characters: {len(text)}")
    if tokens:
        print("Detected placeholders:")
        for t in sorted(tokens):
            print(f"  {{{{" + t + "}}}}")
    else:
        print("No placeholders detected.")

def cmd_audit(docx_path):
    path = Path(docx_path)
    errors = []
    if not path.exists():
        print(f"AUDIT FAIL: file not found: {docx_path}", file=sys.stderr)
        sys.exit(1)
    # 1. Valid zip
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
    except Exception as e:
        print(f"AUDIT FAIL: not a valid docx (zip): {e}", file=sys.stderr)
        sys.exit(1)
    # 2. Required parts
    required = ["word/document.xml", "[Content_Types].xml", "word/_rels/document.xml.rels"]
    for r in required:
        if r not in names:
            errors.append(f"Missing required part: {r}")
    # 3. core.xml metadata check
    if "docProps/core.xml" in names:
        with zipfile.ZipFile(path) as z:
            core_xml = z.read("docProps/core.xml").decode("utf-8", errors="replace")
        # author / creator must not be empty
        if "<dc:creator></dc:creator>" in core_xml or "<dc:creator/>" in core_xml:
            errors.append("METADATA_INCOMPLETE: dc:creator is empty")
    else:
        errors.append("Missing docProps/core.xml — metadata not injected")
    # 4. Margin check (twips, 1440 = 72pt)
    try:
        with zipfile.ZipFile(path) as z:
            doc_xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        # look for w:pgMar attributes
        mar_re = re.compile(r'w:pgMar\s[^/]*/>', re.DOTALL)
        top_re    = re.compile(r'w:top="(\d+)"')
        bottom_re = re.compile(r'w:bottom="(\d+)"')
        left_re   = re.compile(r'w:left="(\d+)"')
        right_re  = re.compile(r'w:right="(\d+)"')
        for m in mar_re.finditer(doc_xml):
            block = m.group(0)
            for label, rx in [("top", top_re),("bottom", bottom_re),
                               ("left", left_re),("right", right_re)]:
                vm = rx.search(block)
                if vm:
                    val = int(vm.group(1))
                    if val < 1440:
                        errors.append(f"MARGIN_VIOLATION: {label}={val} twips (< 1440)")
    except Exception:
        pass  # margin check best-effort
    if errors:
        for e in errors:
            print(f"AUDIT FAIL: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"AUDIT PASS: {path.name}")

def cmd_residual(docx_path):
    path = Path(docx_path)
    if not path.exists():
        print(f"RESIDUAL FAIL: file not found: {docx_path}", file=sys.stderr)
        sys.exit(1)
    text = _full_text(path)
    tokens = PLACEHOLDER_RE.findall(text)
    if tokens:
        print(f"RESIDUAL FAIL: found unreplaced placeholders: {set(tokens)}", file=sys.stderr)
        sys.exit(1)
    print(f"RESIDUAL PASS: {path.name}")

def cmd_render(output_path="output.docx"):
    """Minimal create-lane render (stub — real use requires document.yaml)."""
    yaml_path = Path("document.yaml")
    if not yaml_path.exists():
        print("ERROR: document.yaml not found. Create lane requires document.yaml.", file=sys.stderr)
        sys.exit(1)
    print(f"[render] Would build {output_path} from document.yaml (create lane).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: docx_engine.py <command> [args]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "doctor":
        cmd_doctor()
    elif cmd == "preview" and len(sys.argv) >= 3:
        cmd_preview(sys.argv[2])
    elif cmd == "audit" and len(sys.argv) >= 3:
        cmd_audit(sys.argv[2])
    elif cmd == "residual" and len(sys.argv) >= 3:
        cmd_residual(sys.argv[2])
    elif cmd == "render":
        cmd_render(sys.argv[2] if len(sys.argv) >= 3 else "output.docx")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
'''
(SKILL_PATH / "docx_engine.py").write_text(docx_engine_src)
os.chmod(SKILL_PATH / "docx_engine.py", 0o755)

# ─────────────────────────────────────────────
# 9. C# PROJECT — DocForge
#    Implements: from-template
#    Reads data_manifest.json from output dir,
#    substitutes placeholders, injects metadata,
#    enforces margins ≥1440 twips.
# ─────────────────────────────────────────────

# DocForge.csproj
(SKILL_PATH / "src" / "DocForge.csproj").write_text(dedent("""
    <Project Sdk="Microsoft.NET.Sdk">
      <PropertyGroup>
        <OutputType>Exe</OutputType>
        <TargetFramework>net9.0</TargetFramework>
        <Nullable>enable</Nullable>
        <ImplicitUsings>enable</ImplicitUsings>
        <AssemblyName>DocForge</AssemblyName>
        <RootNamespace>DocForge</RootNamespace>
      </PropertyGroup>
      <ItemGroup>
        <PackageReference Include="DocumentFormat.OpenXml" Version="3.1.0" />
      </ItemGroup>
    </Project>
""").strip())

# Program.cs — full implementation
program_cs = r'''
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Xml;
using System.Xml.Linq;

namespace DocForge;

class Program
{
    static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("Usage: DocForge from-template <template.docx> <output.docx>");
            return 1;
        }

        if (args[0] == "from-template")
        {
            if (args.Length < 3)
            {
                Console.Error.WriteLine("Usage: DocForge from-template <template.docx> <output.docx>");
                return 1;
            }
            return FromTemplate(args[1], args[2]);
        }

        Console.Error.WriteLine($"Unknown command: {args[0]}");
        return 1;
    }

    static int FromTemplate(string templatePath, string outputPath)
    {
        if (!File.Exists(templatePath))
        {
            Console.Error.WriteLine($"Template not found: {templatePath}");
            return 1;
        }

        // Find data_manifest.json in same directory as output
        string outputDir = Path.GetDirectoryName(Path.GetFullPath(outputPath)) ?? ".";
        string manifestPath = Path.Combine(outputDir, "data_manifest.json");

        if (!File.Exists(manifestPath))
        {
            Console.Error.WriteLine($"data_manifest.json not found in output directory: {outputDir}");
            Console.Error.WriteLine("Create data_manifest.json with placeholders and metadata before running.");
            return 1;
        }

        // Parse manifest
        ManifestData manifest;
        try
        {
            string json = File.ReadAllText(manifestPath);
            manifest = JsonSerializer.Deserialize<ManifestData>(json,
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true })
                ?? throw new Exception("Null manifest");
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Failed to parse data_manifest.json: {ex.Message}");
            return 1;
        }

        if (manifest.Placeholders == null || manifest.Metadata == null)
        {
            Console.Error.WriteLine("MISSING_PLACEHOLDER_KEY or METADATA_INCOMPLETE: manifest must have 'placeholders' and 'metadata'.");
            return 1;
        }

        // Validate metadata fields
        var meta = manifest.Metadata;
        if (string.IsNullOrWhiteSpace(meta.Author) ||
            string.IsNullOrWhiteSpace(meta.Department) ||
            string.IsNullOrWhiteSpace(meta.DocumentVersion))
        {
            Console.Error.WriteLine("METADATA_INCOMPLETE: metadata must have author, department, document_version");
            return 1;
        }

        // Copy template to output
        File.Copy(templatePath, outputPath, overwrite: true);

        // Process the docx (zip)
        using var archive = new ZipArchive(
            new FileStream(outputPath, FileMode.Open, FileAccess.ReadWrite),
            ZipArchiveMode.Update, leaveOpen: false);

        // Check all placeholders in document.xml are covered
        var docEntry = archive.GetEntry("word/document.xml")
            ?? throw new Exception("word/document.xml not found in template");

        string docXml;
        using (var sr = new StreamReader(docEntry.Open(), Encoding.UTF8))
            docXml = sr.ReadToEnd();

        var foundTokens = new HashSet<string>(
            Regex.Matches(docXml, @"\{\{([A-Z0-9_]+)\}\}").Select(m => m.Groups[1].Value));

        foreach (var token in foundTokens)
        {
            if (!manifest.Placeholders.ContainsKey(token))
            {
                Console.Error.WriteLine($"MISSING_PLACEHOLDER_KEY: {{{{'{token}'}}}} found in template but not in manifest.");
                return 1;
            }
        }

        // Substitute placeholders
        foreach (var kv in manifest.Placeholders)
        {
            string safeValue = SecurityEncodeXml(kv.Value);
            docXml = docXml.Replace($"{{{{{kv.Key}}}}}", safeValue);
        }

        // Enforce margins ≥ 1440 twips
        docXml = EnforceMargins(docXml, 1440);

        // Write back document.xml
        docEntry.Delete();
        var newDocEntry = archive.CreateEntry("word/document.xml", CompressionLevel.Optimal);
        using (var sw = new StreamWriter(newDocEntry.Open(), new UTF8Encoding(false)))
            sw.Write(docXml);

        // Inject / update core.xml
        InjectCoreXml(archive, meta);

        Console.WriteLine($"[DocForge] Template applied successfully → {outputPath}");
        return 0;
    }

    static string SecurityEncodeXml(string value)
    {
        return value
            .Replace("&", "&amp;")
            .Replace("<", "&lt;")
            .Replace(">", "&gt;")
            .Replace("\"", "&quot;")
            .Replace("'", "&apos;");
    }

    static string EnforceMargins(string xml, int minTwips)
    {
        // Replace any w:pgMar attribute value < minTwips with minTwips
        return Regex.Replace(xml,
            @"(w:(?:top|bottom|left|right|header|footer)=""(\d+)"")",
            m =>
            {
                int val = int.Parse(m.Groups[2].Value);
                return val < minTwips
                    ? $"{m.Groups[1].Value.Split('=')[0]}=\"{minTwips}\""
                    : m.Value;
            });
    }

    static void InjectCoreXml(ZipArchive archive, MetaData meta)
    {
        const string coreNs   = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties";
        const string dcNs     = "http://purl.org/dc/elements/1.1/";
        const string dctermsNs = "http://purl.org/dc/terms/";
        const string xsiNs    = "http://www.w3.org/2001/XMLSchema-instance";

        var entry = archive.GetEntry("docProps/core.xml");
        entry?.Delete();

        // Ensure docProps directory exists (via Content_Types if needed)
        var newEntry = archive.CreateEntry("docProps/core.xml", CompressionLevel.Optimal);
        using var sw = new StreamWriter(newEntry.Open(), new UTF8Encoding(false));

        string now = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
        sw.Write($@"<?xml version=""1.0"" encoding=""UTF-8"" standalone=""yes""?>
<cp:coreProperties
    xmlns:cp=""{coreNs}""
    xmlns:dc=""{dcNs}""
    xmlns:dcterms=""{dctermsNs}""
    xmlns:xsi=""{xsiNs}"">
  <dc:creator>{SecurityEncodeXml(meta.Author)}</dc:creator>
  <cp:lastModifiedBy>{SecurityEncodeXml(meta.Author)}</cp:lastModifiedBy>
  <cp:revision>1</cp:revision>
  <cp:department>{SecurityEncodeXml(meta.Department)}</cp:department>
  <dcterms:created xsi:type=""dcterms:W3CDTF"">{now}</dcterms:created>
  <dcterms:modified xsi:type=""dcterms:W3CDTF"">{now}</dcterms:modified>
  <cp:version>{SecurityEncodeXml(meta.DocumentVersion)}</cp:version>
</cp:coreProperties>");
    }

    static string SecurityEncodeXml2(string s) => SecurityEncodeXml(s);
}

class ManifestData
{
    public Dictionary<string, string>? Placeholders { get; set; }
    public MetaData? Metadata { get; set; }
}

class MetaData
{
    public string Author { get; set; } = "";
    public string Department { get; set; } = "";
    public string DocumentVersion { get; set; } = "";
}
'''
(SKILL_PATH / "src" / "Program.cs").write_text(program_cs.strip())

# Stub CS files for context
(SKILL_PATH / "src" / "Templates" / "ReportTemplate.cs").write_text(dedent("""
    // Example template usage pattern
    // See guides/development.md for full documentation
    namespace DocForge.Templates;
    public class ReportTemplate { }
""").strip())

(SKILL_PATH / "src" / "Core" / "OpenXmlHelpers.cs").write_text(dedent("""
    // OpenXML primitive helpers
    // Use DocumentFormat.OpenXml SDK 3.x
    namespace DocForge.Core;
    public static class OpenXmlHelpers { }
""").strip())

(SKILL_PATH / "src" / "Validators" / "SchemaValidator.cs").write_text(dedent("""
    // Schema validation helpers
    namespace DocForge.Validators;
    public static class SchemaValidator { }
""").strip())

# ─────────────────────────────────────────────
# 10. BUILD THE TEMPLATE .docx
#     Contains 6 placeholders the agent must fill
# ─────────────────────────────────────────────

def make_template_docx(path: Path):
    """
    Build a minimal but valid .docx from scratch (no python-docx).
    Uses raw OpenXML / zip manipulation only.
    Contains placeholders: REPORT_PERIOD, SITE_NAME, SITE_CODE,
                           PREPARED_BY, COMPLIANCE_SCORE, DEVIATION_COUNT
    Margins are intentionally set to 360 twips (< 1440) to test margin enforcement.
    """

    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document
    xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
    xmlns:w="{W}"
    xmlns:r="{R}">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>Quarterly Compliance Report</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Reporting Period: {{{{REPORT_PERIOD}}}}</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Site Name: {{{{SITE_NAME}}}}</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t>Site Code: {{{{SITE_CODE}}}}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>Summary</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t xml:space="preserve">This report was prepared by {{{{PREPARED_BY}}}} on behalf of the Regulatory Affairs department.</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t xml:space="preserve">Overall Compliance Score: {{{{COMPLIANCE_SCORE}}}}%</w:t></w:r>
    </w:p>
    <w:p>
      <w:r><w:t xml:space="preserve">Total Deviations Recorded: {{{{DEVIATION_COUNT}}}}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>Declaration</w:t></w:r>
    </w:p>
    <w:p>
      <w:r>
        <w:t xml:space="preserve">I, {{{{PREPARED_BY}}}}, confirm that all data presented in this report for site {{{{SITE_NAME}}}} ({{{{SITE_CODE}}}}) during the period {{{{REPORT_PERIOD}}}} is accurate and complete.</w:t>
      </w:r>
    </w:p>
    <w:sectPr>
      <w:pgMar w:top="360" w:right="360" w:bottom="360" w:left="360"
               w:header="360" w:footer="360" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"
    Target="styles.xml"/>
</Relationships>"""

    styles_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:rPr><w:b/><w:sz w:val="36"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:rPr><w:b/><w:sz w:val="28"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1">
    <w:name w:val="Normal"/>
  </w:style>
</w:styles>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml"
    ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""

    root_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
  <Relationship Id="rId2"
    Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"
    Target="docProps/core.xml"/>
</Relationships>"""

    # Minimal core.xml (empty creator — will be replaced by DocForge)
    core_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties
    xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:creator></dc:creator>
</cp:coreProperties>"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types_xml)
        z.writestr("_rels/.rels", root_rels_xml)
        z.writestr("word/document.xml", doc_xml)
        z.writestr("word/styles.xml", styles_xml)
        z.writestr("word/_rels/document.xml.rels", rels_xml)
        z.writestr("docProps/core.xml", core_xml)

# Write the template into the project directory
template_path = WORKSPACE / "project" / "quarterly_reports" / "Q4_2024" / "compliance_template.docx"
make_template_docx(template_path)

# ─────────────────────────────────────────────
# 11. DATA BRIEF — raw, messy input data
#     Agent must extract values and create manifest
# ─────────────────────────────────────────────
data_brief = dedent("""
    PHARMA COMPLIANCE BRIEF — Q4 2024
    ==================================
    Facility: BioSynth Manufacturing Erlangen
    Facility Code: BSM-ERN-042
    Report Quarter: Q4 2024 (October–December)
    Report Author: Dr. Elena Vasquez
    Compliance Score (overall GMP): 94.7
    Open Deviations (critical + major): 3
    Department submitting: Regulatory Affairs
    Document Revision: 1.0

    Note: All figures subject to final QA sign-off.
    Distribution: Internal only.
""").strip()

(WORKSPACE / "project" / "quarterly_reports" / "Q4_2024" / "data_brief.txt").write_text(data_brief)

# ─────────────────────────────────────────────
# 12. DISTRACTOR FILES (≥ 10)
# ─────────────────────────────────────────────
distractors = [
    (WORKSPACE / "project" / "quarterly_reports" / "Q3_2024" / "compliance_report_Q3.docx",
     b"PK\x03\x04" + b"\x00" * 100),  # fake/truncated docx
    (WORKSPACE / "project" / "reference_docs" / "gmp_guidelines_2024.pdf",
     b"%PDF-1.4 fake content"),
    (WORKSPACE / "project" / "reference_docs" / "deviation_handling_sop.txt",
     b"SOP-QA-007: Deviation Handling Procedure v3.2\nScope: All GMP facilities\n"),
    (WORKSPACE / "project" / "archive" / "2023" / "annual_compliance_summary.csv",
     b"year,site,score\n2023,BSM-ERN-042,91.2\n2023,BSM-MUC-001,88.5\n"),
    (WORKSPACE / "project" / "data_exports" / "lims_export_2024Q4.json",
     json.dumps({"batches": 142, "failures": 3, "site": "BSM-ERN-042"}).encode()),
    (WORKSPACE / "project" / "meetings" / "notes" / "qa_review_2024-12-15.txt",
     b"Attendees: Dr. Vasquez, Mr. Chen, Ms. Okonkwo\nAction: finalize Q4 report by EOY\n"),
    (WORKSPACE / "project" / "hr" / "records" / "training_matrix_Q4.csv",
     b"employee_id,training,completed\nEV-001,GMP Refresher,yes\n"),
    (WORKSPACE / "project" / "it" / "config" / "docgen_config.yaml",
     b"engine: legacy\noutput_dir: /tmp/docs\nuse_python_docx: false\n"),
    (WORKSPACE / "project" / "data_exports" / "deviation_log_Q4.xlsx",
     b"PK\x03\x04" + b"\x00" * 50),  # fake xlsx
    (WORKSPACE / "project" / "reference_docs" / "old_template_Q2_2024.docx",
     b"PK\x03\x04" + b"\x00" * 80),  # old template, wrong one
    (WORKSPACE / "project" / "quarterly_reports" / "Q4_2024" / "draft_notes.txt",
     b"TODO: check COMPLIANCE_SCORE decimal places\nNOTE: use official template only\n"),
]

for fpath, content in distractors:
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_bytes(content)

# ─────────────────────────────────────────────
# 13. Print summary
# ─────────────────────────────────────────────
print("Workspace generated successfully.")
print(f"  Skill path:    {SKILL_PATH}")
print(f"  Template:      {template_path}")
print(f"  Data brief:    {WORKSPACE}/project/quarterly_reports/Q4_2024/data_brief.txt")
print(f"  Distractor files: {len(distractors)}")