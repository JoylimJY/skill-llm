import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# Create deeply nested distractor structure
dirs = [
    "legacy_tools/vbs_scripts/archive",
    "legacy_tools/batch_helpers",
    "legacy_tools/powershell_drafts",
    "automation/com_tests/old",
    "automation/com_tests/wip",
    "automation/http_clients",
    "automation/file_ops",
    "docs/references/msdn",
    "docs/references/polyfill_notes",
    "configs/environments/prod",
    "configs/environments/dev",
    "output/logs",
    "output/reports",
    "temp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files — messy, realistic, wrong approaches
distractor_files = {
    "legacy_tools/vbs_scripts/archive/old_fetch.vbs": """\
' Old VBScript HTTP fetch - deprecated
Set http = CreateObject("Microsoft.XMLHTTP")
http.Open "GET", "http://example.com", False
http.Send
WScript.Echo http.responseText
""",
    "legacy_tools/vbs_scripts/archive/file_writer.vbs": """\
' VBScript file writer
Set fso = CreateObject("Scripting.FileSystemObject")
Set f = fso.CreateTextFile("C:\\output.txt", True)
f.WriteLine "done"
f.Close
""",
    "legacy_tools/batch_helpers/run.bat": """\
@echo off
cscript //NoLogo script.js
""",
    "legacy_tools/powershell_drafts/invoke_web.ps1": """\
# PowerShell draft - not compatible with legacy env
Invoke-WebRequest -Uri "https://example.com" -OutFile "out.txt"
""",
    "automation/com_tests/old/test_activex.js": """\
// WRONG: Direct ActiveX without fallback
var xhr = new ActiveXObject("Msxml2.XMLHTTP.3.0");
xhr.open("GET", "https://example.com", false);
xhr.send();
WScript.Echo(xhr.responseText);
""",
    "automation/com_tests/wip/http_attempt.js": """\
// INCOMPLETE: Missing fallback chain
var xhr = WScript.CreateObject("Msxml2.XMLHTTP.6.0");
""",
    "automation/http_clients/notes.txt": """\
Tried: Msxml2.XMLHTTP.6.0 - works on Win10
Tried: Msxml2.XMLHTTP.3.0 - works on WinXP
Need fallback for both.
User-Agent should match IE8 for polyfill CDN.
""",
    "automation/file_ops/fso_draft.js": """\
// Draft - writes a file using FSO
// Missing: CreateObject wrapper, no fallback
var fso = new ActiveXObject("Scripting.FileSystemObject");
var f = fso.CreateTextFile("result.txt", true);
f.WriteLine("hello");
f.Close();
""",
    "docs/references/msdn/com_objects.txt": """\
Scripting.FileSystemObject - file I/O
WScript.Shell - shell exec
ADODB.Stream - binary/text streams
Msxml2.XMLHTTP.6.0 - HTTP requests (IE9+)
Msxml2.XMLHTTP.3.0 - HTTP requests (IE6+)
""",
    "docs/references/polyfill_notes/cdn_info.txt": """\
Polyfill CDN: https://cdnjs.cloudflare.com/polyfill/
Endpoint: /v3/polyfill.min.js
Params: version, features
NOTE: features list uses commas
Version to use: 4.8.0
Features needed: default, es2015, es6
""",
    "configs/environments/prod/env.json": json.dumps({
        "target_os": "Windows Server 2008 R2",
        "jscript_version": "5.8",
        "ie_compat": "8.0",
        "polyfill_version": "4.8.0",
        "polyfill_features": ["default", "es2015", "es6"],
        "output_file": "C:\\automation\\status_report.json",
        "fetch_url": "https://httpbin.org/get"
    }, indent=2),
    "configs/environments/dev/env.json": json.dumps({
        "target_os": "Windows 10",
        "jscript_version": "5.8",
        "ie_compat": "8.0",
        "polyfill_version": "4.8.0",
        "polyfill_features": ["default", "es2015", "es6"],
        "output_file": "C:\\dev\\status_report.json",
        "fetch_url": "https://httpbin.org/get"
    }, indent=2),
    "output/logs/previous_run.log": """\
[2024-01-15 09:23:11] Script started
[2024-01-15 09:23:12] ERROR: ActiveXObject not found
[2024-01-15 09:23:12] Script failed - no fallback defined
""",
    "temp/scratch/ideas.txt": """\
TODO:
- Use proper CreateObject wrapper with fallback array
- Features param needs URL encoding for commas
- Must set User-Agent to match IE8 for polyfill CDN
- Write JSON report to disk after fetching polyfill
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# Create the task specification file (business requirements, no hints)
task_spec = {
    "task_id": "jsrt-claw-001",
    "project": "LegacyWindowsAutomation",
    "description": (
        "Produce a single JScript automation file named 'fetch_and_report.js'. "
        "When executed on a Windows machine (IE8-compatible JScript 5.8 environment), "
        "this script must: "
        "(1) fetch a compatibility polyfill bundle for 'default', 'es2015', and 'es6' features "
        "from the CDN at version 4.8.0, "
        "(2) save a JSON status report to disk at the path 'C:\\automation\\status_report.json' "
        "indicating success or failure, "
        "(3) be robust enough to work even if certain COM components are unavailable on a given Windows install."
    ),
    "constraints": [
        "Must work on Windows XP through Windows 10 (varied COM availability)",
        "Must use polyfill CDN version 4.8.0",
        "Output file: fetch_and_report.js"
    ],
    "polyfill_features": ["default", "es2015", "es6"],
    "output_report_path": "C:\\automation\\status_report.json"
}

with open(os.path.join(WORKSPACE, "task_spec.json"), "w") as f:
    json.dump(task_spec, f, indent=2)

print("Workspace generated successfully.")
print(f"Structure created under: {WORKSPACE}")