#!/bin/bash
set -e

# ── Create the mock `gmx` binary that simulates GROMACS behavior ─────────────
# This mock intercepts commands and produces realistic output files
# based on the arguments provided, enabling full workflow testing.

cat > /usr/local/bin/gmx << 'GMXEOF'
#!/usr/bin/env python3
"""
Mock GROMACS `gmx` binary.
Simulates realistic behavior for: trjconv, rms, gyrate, sham, make_ndx, covar, anaeig
Reads stdin for group selections, parses -f/-s/-o/-n flags, writes output files.
"""

import sys
import os
import re
import math
import random

random.seed(123)

def write_xvg(path, title, xlabel, ylabel, rows, comments=None):
    lines = []
    if comments:
        for c in comments:
            lines.append(f"# {c}")
    lines += [
        f'@ title "{title}"',
        f'@ xaxis label "{xlabel}"',
        f'@ yaxis label "{ylabel}"',
        '@ TYPE xy',
    ]
    for row in rows:
        lines.append("    ".join(f"{v:.6f}" for v in row))
    with open(path, 'w') as f:
        f.write("\n".join(lines) + "\n")

def parse_args(args):
    """Return dict of flag->value and list of flags without values."""
    d = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith('-'):
            # check if next arg is a value (not another flag)
            if i + 1 < len(args) and not args[i+1].startswith('-'):
                d[a] = args[i+1]
                i += 2
            else:
                d[a] = True
                i += 1
        else:
            i += 1
    return d

def read_stdin_lines():
    """Read all stdin lines, stripping whitespace."""
    try:
        data = sys.stdin.read()
        lines = [l.strip() for l in data.replace('\\n', '\n').split('\n') if l.strip()]
        return lines
    except:
        return []

def cmd_trjconv(args, selections):
    flags = parse_args(args)
    out = flags.get('-o', 'traj_out.xtc')
    # trjconv requires: centering group (if -center), fitting group (if -fit), output group
    # Write a mock output trajectory file
    # The key check: was -pbc, -center, -fit used correctly?
    has_center = '-center' in flags
    has_fit = '-fit' in flags
    has_pbc = '-pbc' in flags
    
    # Record what was done in a metadata sidecar for eval
    meta_path = out + '.meta'
    meta_lines = [
        f"command=trjconv",
        f"input_traj={flags.get('-f', '')}",
        f"input_tpr={flags.get('-s', '')}",
        f"output={out}",
        f"pbc={flags.get('-pbc', 'none')}",
        f"center={has_center}",
        f"fit={flags.get('-fit', 'none')}",
        f"selections={repr(selections)}",
        f"b={flags.get('-b', '')}",
        f"e={flags.get('-e', '')}",
    ]
    with open(meta_path, 'w') as f:
        f.write('\n'.join(meta_lines) + '\n')
    
    # Write fake xtc output
    with open(out, 'wb') as f:
        f.write(b'\x00MOCK_TRJCONV_OUTPUT\x00' + out.encode() + b'\x00')
    
    print(f"gmx trjconv: wrote {out}", file=sys.stderr)
    return 0

def cmd_rms(args, selections):
    flags = parse_args(args)
    out = flags.get('-o', 'rmsd.xvg')
    
    # Generate realistic RMSD data: 0→10ns, starts near 0, rises and plateaus
    rows = []
    for i in range(201):
        t = i * 50.0  # 0 to 10000 ps
        # RMSD plateau around 0.25 nm with noise
        rmsd = 0.25 * (1 - math.exp(-t / 1000.0)) + 0.02 * (hash((i, 'rmsd')) % 100) / 1000.0
        rows.append((t, rmsd))
    
    # Record metadata
    meta_path = out + '.meta'
    meta_lines = [
        f"command=rms",
        f"input_traj={flags.get('-f', '')}",
        f"input_tpr={flags.get('-s', '')}",
        f"output={out}",
        f"selections={repr(selections)}",
        f"n={flags.get('-n', '')}",
    ]
    with open(meta_path, 'w') as f:
        f.write('\n'.join(meta_lines) + '\n')
    
    write_xvg(out, "RMSD", "Time (ps)", "RMSD (nm)", rows,
              comments=["This file was created by GROMACS mock"])
    print(f"gmx rms: wrote {out}", file=sys.stderr)
    return 0

def cmd_gyrate(args, selections):
    flags = parse_args(args)
    out = flags.get('-o', 'gyrate.xvg')
    
    # Generate Rg data
    rows = []
    for i in range(201):
        t = i * 50.0
        rg = 1.85 + 0.05 * math.sin(t / 500.0) + 0.01 * (hash((i, 'rg')) % 100) / 100.0
        rows.append((t, rg))
    
    meta_path = out + '.meta'
    with open(meta_path, 'w') as f:
        f.write(f"command=gyrate\noutput={out}\nselections={repr(selections)}\n")
    
    write_xvg(out, "Radius of gyration", "Time (ps)", "Rg (nm)", rows,
              comments=["This file was created by GROMACS mock"])
    print(f"gmx gyrate: wrote {out}", file=sys.stderr)
    return 0

def cmd_sham(args, selections):
    flags = parse_args(args)
    # sham uses -ls for output (Gibbs FEL), not -o
    out_ls = flags.get('-ls', 'gibbs.xpm')
    out_o = flags.get('-o', 'bindex.ndx')  # default secondary output
    inp = flags.get('-f', '')
    tsham = flags.get('-tsham', '298')
    nlevels = flags.get('-nlevels', '25')
    
    meta_path = out_ls + '.meta'
    meta_lines = [
        f"command=sham",
        f"input={inp}",
        f"output_ls={out_ls}",
        f"tsham={tsham}",
        f"nlevels={nlevels}",
    ]
    with open(meta_path, 'w') as f:
        f.write('\n'.join(meta_lines) + '\n')
    
    # Write a mock XPM file (valid format)
    xpm_content = '''/* XPM */
/* This file was created by GROMACS mock gmx sham */
/* title   : "Gibbs Energy Landscape" */
/* legend  : "G (kJ/mol)" */
/* x-label : "RMSD (nm)" */
/* y-label : "Rg (nm)" */
/* type    : Continuous */
static char *gromacs_xpm[] = {
/* " nColors */
"10 10   3 1",
"  c #FFFFFF " /* "0.00" */,
". c #FF0000 " /* "5.00" */,
"X c #0000FF " /* "10.00" */,
"          ",
"  ......  ",
" .XXXXXX. ",
" .XXXXXX. ",
"  ......  ",
"          ",
"          ",
"          ",
"          ",
"          "
};
'''
    with open(out_ls, 'w') as f:
        f.write(xpm_content)
    
    print(f"gmx sham: wrote {out_ls}", file=sys.stderr)
    return 0

def cmd_make_ndx(args, selections):
    flags = parse_args(args)
    out = flags.get('-o', 'index.ndx')
    inp_f = flags.get('-f', '')
    inp_n = flags.get('-n', '')
    
    # Start with default groups or read existing
    base_ndx = """[ System ]
 1 2 3 4 5 6 7 8 9 10

[ Protein ]
 1 2 3 4 5 6

[ Backbone ]
 1 3 5

[ C-alpha ]
 2 4 6

[ Water ]
 7 8 9 10

"""
    if inp_n and os.path.exists(inp_n):
        with open(inp_n) as f:
            base_ndx = f.read()
    
    with open(out, 'w') as f:
        f.write(base_ndx)
    
    print(f"gmx make_ndx: wrote {out}", file=sys.stderr)
    return 0

def cmd_check(args, selections):
    flags = parse_args(args)
    s = flags.get('-s', '')
    f = flags.get('-f', '')
    print(f"Checking file(s): {s} {f}", file=sys.stderr)
    print("No errors found (mock check)", file=sys.stderr)
    return 0

def cmd_help(subcmd):
    helps = {
        'trjconv': """
gmx trjconv - Convert and manipulates trajectory files

SYNOPSIS
gmx trjconv [-f [<.xtc/.trr/...>]] [-s [<.tpr/.gro/...>]]
            [-n [<.ndx>]] [-o [<.xtc/.trr/...>]]
            [-b <time>] [-e <time>] [-dt <time>]
            [-pbc <enum>] [-[no]center] [-fit <enum>]
            [-ur <enum>]

DESCRIPTION
  -pbc <enum>     PBC treatment (none/mol/res/atom/nojump/cluster/whole)
  -[no]center     Center atoms in box
  -fit <enum>     Fit molecule to ref structure (none/rot+trans/...)

NOTES
  When using -center: first select centering group, then output group.
  When using -fit: first select fit group, then output group.
  When using both -center and -fit: select centering group, fit group, output group.
""",
        'rms': """
gmx rms - Calculate RMSDs with a reference structure and MSDs

SYNOPSIS
gmx rms [-s [<.tpr/.gro/...>]] [-f [<.xtc/.trr/...>]]
        [-n [<.ndx>]] [-o [<.xvg>]]

DESCRIPTION
  Select two groups: first for least squares fit, second for RMSD calculation.
""",
        'gyrate': """
gmx gyrate - Calculate the radius of gyration

SYNOPSIS  
gmx gyrate [-s [<.tpr>]] [-f [<.xtc>]] [-o [<.xvg>]]

DESCRIPTION
  Select group for radius of gyration calculation.
""",
        'sham': """
gmx sham - Compute free energies or other histograms from histograms

SYNOPSIS
gmx sham [-f [<.xvg>]] [-ls [<.xpm>]] [-o [<.xpm>]]
         [-tsham <real>] [-nlevels <int>]

DESCRIPTION
  Reads XVG file with one or more columns (first column = x-axis,
  remaining columns are reaction coordinates).
  -ls  <.xpm>   Output Gibbs free energy landscape (DEFAULT: gibbs.xpm)
  -tsham <real> Temperature for sham (K)
  -nlevels <int> Number of contour levels

NOTE: Use -ls for the free energy landscape output (XPM format).
""",
        'energy': """
gmx energy - Writes energies to xvg files and calculates averages

SYNOPSIS
gmx energy [-f [<.edr>]] [-o [<.xvg>]]

DESCRIPTION
  Select energy terms from list to extract.
""",
    }
    if subcmd in helps:
        print(helps[subcmd])
    else:
        print(f"gmx {subcmd}: mock help. Use gmx <cmd> -h for details.")
    return 0

def main():
    args = sys.argv[1:]
    
    if not args:
        print("GROMACS 2024.1 (mock)")
        print("Usage: gmx [-h] <command> [options]")
        return 0
    
    if args[0] in ('--version', '-version'):
        print("GROMACS version: 2024.1 (mock)")
        print("Precision: mixed")
        print("Memory model: 64 bit")
        return 0
    
    cmd = args[0]
    rest = args[1:]
    
    # Check for -h flag
    if '-h' in rest or '--help' in rest:
        return cmd_help(cmd)
    
    # Read stdin for group selections
    selections = read_stdin_lines()
    
    dispatch = {
        'trjconv': cmd_trjconv,
        'rms': cmd_rms,
        'gyrate': cmd_gyrate,
        'sham': cmd_sham,
        'make_ndx': cmd_make_ndx,
        'check': cmd_check,
    }
    
    if cmd in dispatch:
        return dispatch[cmd](rest, selections)
    else:
        print(f"gmx {cmd}: command not implemented in mock (but would work in real GROMACS)", file=sys.stderr)
        # Still create output file if -o specified
        flags = parse_args(rest)
        for flag in ['-o', '-ls', '-num', '-od']:
            if flag in flags and isinstance(flags[flag], str):
                outf = flags[flag]
                if not os.path.exists(outf):
                    with open(outf, 'w') as f:
                        f.write(f"# mock output for gmx {cmd}\n")
        return 0

sys.exit(main())
GMXEOF

chmod +x /usr/local/bin/gmx

echo "Mock gmx installed at $(which gmx)"
gmx --version

echo "Setup complete."