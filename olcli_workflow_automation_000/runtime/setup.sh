#!/bin/bash
set -e

# Create the mock olcli binary that simulates the real olcli behavior
# according to the SKILL.md specification

cat > /usr/local/bin/olcli << 'OLCLI_SCRIPT'
#!/bin/bash

# Mock olcli - simulates Overleaf CLI behavior

CONFIG_DIR="$HOME/.config/olcli"
CONFIG_FILE="$CONFIG_DIR/config.json"
STATE_DIR="$HOME/.local/share/olcli"

mkdir -p "$CONFIG_DIR" "$STATE_DIR"

cmd="$1"
shift

case "$cmd" in
  auth)
    # Parse --cookie flag
    cookie=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --cookie)
          cookie="$2"
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done
    if [[ -z "$cookie" ]]; then
      echo "Error: --cookie is required" >&2
      exit 1
    fi
    echo "{\"cookie\": \"$cookie\", \"user\": \"researcher@university.edu\", \"authenticated\": true}" > "$CONFIG_FILE"
    echo "Authentication successful. Logged in as researcher@university.edu"
    ;;

  whoami)
    if [[ ! -f "$CONFIG_FILE" ]]; then
      echo "Not authenticated. Run 'olcli auth --cookie <value>' first." >&2
      exit 1
    fi
    python3 -c "import json,sys; c=json.load(open('$CONFIG_FILE')); print('Logged in as: '+c['user']) if c.get('authenticated') else sys.exit(1)"
    ;;

  list)
    if [[ ! -f "$CONFIG_FILE" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    echo "Projects:"
    echo "  [6507f3a1b2c3d4e5f6a7b8c9] NeurIPS_2024_Paper"
    echo "  [6507f3a1b2c3d4e5f6a7b8ca] OldConferencePaper"
    echo "  [6507f3a1b2c3d4e5f6a7b8cb] ThesisChapter1"
    ;;

  pull)
    if [[ ! -f "$CONFIG_FILE" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    project_name="$1"
    target_dir="$2"

    # Normalize project name to directory name (spaces -> underscores)
    if [[ -z "$target_dir" ]]; then
      target_dir=$(echo "$project_name" | tr ' ' '_')
    fi

    if [[ "$project_name" != "NeurIPS_2024_Paper" && "$project_name" != "6507f3a1b2c3d4e5f6a7b8c9" ]]; then
      echo "Error: Project '$project_name' not found." >&2
      exit 1
    fi

    mkdir -p "$target_dir"

    # Create .olcli.json metadata file (auto-detect marker)
    cat > "$target_dir/.olcli.json" << 'EOF'
{
  "project_id": "6507f3a1b2c3d4e5f6a7b8c9",
  "project_name": "NeurIPS_2024_Paper",
  "last_sync": "2024-01-15T10:00:00Z"
}
EOF

    # Create realistic LaTeX project files
    cat > "$target_dir/main.tex" << 'EOF'
\documentclass[10pt,twocolumn]{article}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{natbib}

\title{Deep Neural Approaches to Sequential Prediction: A Comparative Study}
\author{Alice Smith \and Bob Johnson \and Carol White}
\date{January 2024}

\begin{document}
\maketitle

\begin{abstract}
We investigate several deep learning architectures for sequential prediction tasks.
Our experiments show competitive results across multiple benchmarks.
\end{abstract}

\section{Introduction}
Sequential prediction is a fundamental problem in machine learning. In this paper,
we present a comprehensive comparison of modern architectures.

\section{Method}
We employ a transformer-based architecture with several modifications.

\subsection{Architecture}
Our model follows the standard encoder-decoder paradigm.

\section{Experiments}
We evaluate on three standard benchmarks.

\section{Conclusion}
We have presented a thorough comparison of deep learning approaches.

\bibliographystyle{plain}
\bibliography{references}

\end{document}
EOF

    cat > "$target_dir/references.bib" << 'EOF'
@inproceedings{vaswani2017attention,
  author    = {Vaswani, Ashish and others},
  title     = {Attention Is All You Need},
  booktitle = {NeurIPS},
  year      = {2017}
}
@inproceedings{lecun1998gradient,
  author    = {LeCun, Yann and others},
  title     = {Gradient-based Learning Applied to Document Recognition},
  year      = {1998}
}
EOF

    cat > "$target_dir/commands.tex" << 'EOF'
% Custom commands
\newcommand{\ie}{\textit{i.e.}}
\newcommand{\eg}{\textit{e.g.}}
EOF

    echo "Pulled project '$project_name' to ./$target_dir/"
    echo "  main.tex"
    echo "  references.bib"
    echo "  commands.tex"
    ;;

  push)
    # Check for --dry-run flag
    dry_run=false
    target_dir="."
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --dry-run)
          dry_run=true
          shift
          ;;
        *)
          target_dir="$1"
          shift
          ;;
      esac
    done

    # Auto-detect: check for .olcli.json
    config_file="$target_dir/.olcli.json"
    if [[ ! -f "$config_file" ]]; then
      echo "Error: No .olcli.json found in '$target_dir'. Run 'olcli pull' first or specify a synced directory." >&2
      exit 1
    fi

    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi

    project_id=$(python3 -c "import json; print(json.load(open('$config_file'))['project_id'])")

    if [[ "$dry_run" == "true" ]]; then
      echo "[DRY RUN] Would upload the following changes:"
      echo "  Modified: main.tex"
      echo "[DRY RUN] No files were actually uploaded."
    else
      # Record push in state
      echo "{\"project_id\": \"$project_id\", \"pushed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"dir\": \"$target_dir\"}" >> "$STATE_DIR/push_log.jsonl"
      echo "Pushed changes to NeurIPS_2024_Paper"
      echo "  Uploaded: main.tex"
    fi
    ;;

  sync)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    target_dir="${1:-.}"
    config_file="$target_dir/.olcli.json"
    if [[ ! -f "$config_file" ]]; then
      echo "Error: No .olcli.json found." >&2
      exit 1
    fi
    echo "Syncing NeurIPS_2024_Paper..."
    echo "  Pull: No remote changes."
    echo "  Push: main.tex"
    echo "{\"project_id\": \"6507f3a1b2c3d4e5f6a7b8c9\", \"synced_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"dir\": \"$target_dir\"}" >> "$STATE_DIR/push_log.jsonl"
    ;;

  compile)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    # Check for .olcli.json in current or specified dir
    target_dir="${1:-.}"
    config_file="$target_dir/.olcli.json"
    if [[ ! -f "$config_file" && ! -f ".olcli.json" ]]; then
      echo "Error: No .olcli.json found." >&2
      exit 1
    fi
    echo "Compiling NeurIPS_2024_Paper on Overleaf..."
    echo "Compilation successful."
    echo "{\"project_id\": \"6507f3a1b2c3d4e5f6a7b8c9\", \"compiled_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$STATE_DIR/compile_log.jsonl"
    ;;

  pdf)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi

    output_file=""
    project_arg=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        -o)
          output_file="$2"
          shift 2
          ;;
        *)
          project_arg="$1"
          shift
          ;;
      esac
    done

    # Auto-detect from .olcli.json if present
    if [[ -f ".olcli.json" ]]; then
      project_id=$(python3 -c "import json; print(json.load(open('.olcli.json'))['project_id'])" 2>/dev/null || echo "")
    fi

    if [[ -z "$output_file" ]]; then
      output_file="NeurIPS_2024_Paper.pdf"
    fi

    # Write a minimal but recognizable mock PDF (has %PDF- header)
    printf '%%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n' > "$output_file"
    echo "Compiled NeurIPS_2024_Paper successfully."
    echo "Downloaded PDF to $output_file"
    echo "{\"project_id\": \"6507f3a1b2c3d4e5f6a7b8c9\", \"pdf_downloaded\": \"$output_file\", \"at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$STATE_DIR/compile_log.jsonl"
    ;;

  output)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi

    subcommand=""
    output_file=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --list)
          echo "Available compile outputs for NeurIPS_2024_Paper:"
          echo "  pdf   - Compiled PDF document"
          echo "  bbl   - BibTeX bibliography (for arXiv)"
          echo "  log   - Compilation log"
          echo "  aux   - LaTeX auxiliary file"
          exit 0
          ;;
        -o)
          output_file="$2"
          shift 2
          ;;
        bbl|pdf|log|aux)
          subcommand="$1"
          shift
          ;;
        *)
          shift
          ;;
      esac
    done

    if [[ -z "$subcommand" ]]; then
      echo "Error: specify output type (bbl, pdf, log, aux) or --list" >&2
      exit 1
    fi

    case "$subcommand" in
      bbl)
        if [[ -z "$output_file" ]]; then
          output_file="NeurIPS_2024_Paper.bbl"
        fi
        cat > "$output_file" << 'EOF'
\begin{thebibliography}{10}

\bibitem{vaswani2017attention}
Ashish Vaswani et~al.
\newblock Attention is all you need.
\newblock In {\em Advances in Neural Information Processing Systems}, 2017.

\bibitem{lecun1998gradient}
Yann LeCun et~al.
\newblock Gradient-based learning applied to document recognition.
\newblock {\em Proceedings of the IEEE}, 1998.

\end{thebibliography}
EOF
        echo "Downloaded bbl to $output_file"
        ;;
      log)
        if [[ -z "$output_file" ]]; then
          output_file="NeurIPS_2024_Paper.log"
        fi
        echo "This is pdfTeX, Version 3.14159265-2.6-1.40.21 (TeX Live 2020)" > "$output_file"
        echo "Downloaded log to $output_file"
        ;;
      *)
        echo "Error: Unknown output type '$subcommand'" >&2
        exit 1
        ;;
    esac
    ;;

  download)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    echo "Downloading file: $1"
    ;;

  upload)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    echo "Uploading file: $1"
    ;;

  zip)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    echo "Downloading project as ZIP..."
    ;;

  info)
    if [[ ! -f "$HOME/.config/olcli/config.json" ]]; then
      echo "Not authenticated." >&2
      exit 1
    fi
    echo "Project: NeurIPS_2024_Paper"
    echo "ID: 6507f3a1b2c3d4e5f6a7b8c9"
    echo "Last modified: 2024-01-15"
    ;;

  *)
    echo "Usage: olcli <command> [options]"
    echo "Commands: auth, whoami, list, info, pull, push, sync, upload, download, zip, compile, pdf, output"
    exit 1
    ;;
esac
OLCLI_SCRIPT

chmod +x /usr/local/bin/olcli

echo "olcli mock installed at /usr/local/bin/olcli"
olcli --help || true