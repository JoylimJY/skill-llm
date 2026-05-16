import os
import random
import stat
import json
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skills/discogs-cli/bin",
    "skills/discogs-cli/cmd",
    "skills/discogs-cli/internal/api",
    "skills/discogs-cli/internal/cache",
    "skills/discogs-cli/internal/config",
    "projects/vinyl-audit/reports",
    "projects/vinyl-audit/raw",
    "notes/research",
    "notes/meetings",
    "tmp/downloads",
]
for d in dirs:
    Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "projects/vinyl-audit/reports/old_valuation_2023.txt": "Total: $4,210.00\nNote: outdated, do not use.",
    "projects/vinyl-audit/raw/collection_export.csv": "id,title,artist,year\n35198584,Discovery,Daft Punk,2001\n1419456,OK Computer,Radiohead,1997",
    "notes/research/discogs_notes.txt": "Discogs API base URL: https://api.discogs.com\nRate limit: 60 req/min",
    "notes/meetings/2024-01-15.txt": "Action item: automate collection valuation script.\nContact: vinyl@example.com",
    "tmp/downloads/placeholder.bin": "\x00\x01\x02",
    "skills/discogs-cli/internal/api/client.go.bak": "// old api client - do not use",
    "skills/discogs-cli/internal/cache/cache.go.bak": "// cache stub",
    "skills/discogs-cli/internal/config/config.go.bak": "// config stub",
    "skills/discogs-cli/.gitignore": "bin/\n*.cache\n",
    "skills/discogs-cli/go.sum": "# placeholder go.sum\n",
    "projects/vinyl-audit/raw/wantlist_ideas.txt": "Maybe add: Aphex Twin - Selected Ambient Works\nMaybe add: Boards of Canada - Music Has The Right To Children",
}
for rel, content in distractors.items():
    fpath = os.path.join(WORKSPACE, rel)
    mode = "wb" if isinstance(content, bytes) else "w"
    with open(fpath, mode) as f:
        f.write(content if isinstance(content, bytes) else content)

# ── go.mod ───────────────────────────────────────────────────────────────────
go_mod = textwrap.dedent("""\
    module discogs-cli

    go 1.21
""")
with open(os.path.join(WORKSPACE, "skills/discogs-cli/go.mod"), "w") as f:
    f.write(go_mod)

# ── main Go source ────────────────────────────────────────────────────────────
# This Go program implements the CLI described in SKILL.md.
# It reads DISCOGS_BASE_URL env var to redirect to the mock server.
main_go = textwrap.dedent(r"""
package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

const defaultBase = "https://api.discogs.com"

type Config struct {
	Username string `yaml:"username"`
	Token    string `yaml:"token"`
	BaseURL  string `yaml:"base_url"`
}

func configPath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "discogs-cli", "config.yaml")
}

func loadConfig() Config {
	var cfg Config
	data, err := os.ReadFile(configPath())
	if err != nil {
		return cfg
	}
	yaml.Unmarshal(data, &cfg)
	if cfg.BaseURL == "" {
		cfg.BaseURL = defaultBase
	}
	return cfg
}

func saveConfig(cfg Config) {
	p := configPath()
	os.MkdirAll(filepath.Dir(p), 0700)
	data, _ := yaml.Marshal(cfg)
	os.WriteFile(p, data, 0600)
}

func apiGet(cfg Config, path string) ([]byte, error) {
	base := cfg.BaseURL
	if base == "" {
		base = defaultBase
	}
	url := base + path
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", fmt.Sprintf("Discogs token=%s", cfg.Token))
	req.Header.Set("User-Agent", "discogs-cli/1.0")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}

func apiPut(cfg Config, path string) ([]byte, error) {
	base := cfg.BaseURL
	if base == "" {
		base = defaultBase
	}
	url := base + path
	req, _ := http.NewRequest("PUT", url, nil)
	req.Header.Set("Authorization", fmt.Sprintf("Discogs token=%s", cfg.Token))
	req.Header.Set("User-Agent", "discogs-cli/1.0")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}

func apiDelete(cfg Config, path string) ([]byte, error) {
	base := cfg.BaseURL
	if base == "" {
		base = defaultBase
	}
	url := base + path
	req, _ := http.NewRequest("DELETE", url, nil)
	req.Header.Set("Authorization", fmt.Sprintf("Discogs token=%s", cfg.Token))
	req.Header.Set("User-Agent", "discogs-cli/1.0")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	return io.ReadAll(resp.Body)
}

func cachePath() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".cache", "discogs-cli", "collection.json")
}

func main() {
	args := os.Args[1:]
	if len(args) == 0 {
		fmt.Println("Usage: discogs-cli <command> [subcommand] [args]")
		os.Exit(1)
	}

	cmd := args[0]

	switch cmd {
	case "config":
		if len(args) < 2 {
			fmt.Println("Usage: discogs-cli config set -u <user> -t <token>")
			os.Exit(1)
		}
		if args[1] == "set" {
			var user, token, baseURL string
			for i := 2; i < len(args); i++ {
				switch args[i] {
				case "-u":
					i++; user = args[i]
				case "-t":
					i++; token = args[i]
				case "--base-url":
					i++; baseURL = args[i]
				}
			}
			cfg := loadConfig()
			if user != "" { cfg.Username = user }
			if token != "" { cfg.Token = token }
			if baseURL != "" { cfg.BaseURL = baseURL }
			saveConfig(cfg)
			fmt.Println("Configuration saved.")
		}

	case "collection":
		cfg := loadConfig()
		if len(args) < 2 {
			fmt.Println("Usage: discogs-cli collection <list|list-folders|sync|value|get>")
			os.Exit(1)
		}
		sub := args[1]
		switch sub {
		case "list-folders":
			data, err := apiGet(cfg, fmt.Sprintf("/users/%s/collection/folders", cfg.Username))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			var result map[string]interface{}
			json.Unmarshal(data, &result)
			folders, _ := result["folders"].([]interface{})
			fmt.Printf("%-10s %-30s %s\n", "ID", "Name", "Count")
			fmt.Println(strings.Repeat("-", 50))
			for _, f := range folders {
				fm := f.(map[string]interface{})
				fmt.Printf("%-10v %-30v %v\n", fm["id"], fm["name"], fm["count"])
			}

		case "list":
			folderID := "0"
			for i := 2; i < len(args); i++ {
				if args[i] == "--folder" && i+1 < len(args) {
					folderID = args[i+1]
				}
			}
			data, err := apiGet(cfg, fmt.Sprintf("/users/%s/collection/folders/%s/releases", cfg.Username, folderID))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			var result map[string]interface{}
			json.Unmarshal(data, &result)
			releases, _ := result["releases"].([]interface{})
			fmt.Printf("%-12s %-35s %-25s %s\n", "Release ID", "Title", "Artist", "Year")
			fmt.Println(strings.Repeat("-", 80))
			for _, r := range releases {
				rm := r.(map[string]interface{})
				info := rm["basic_information"].(map[string]interface{})
				artists, _ := info["artists"].([]interface{})
				artist := ""
				if len(artists) > 0 { artist = artists[0].(map[string]interface{})["name"].(string) }
				fmt.Printf("%-12v %-35v %-25v %v\n", rm["id"], info["title"], artist, info["year"])
			}

		case "sync":
			fmt.Println("Syncing collection details... this may take a while.")
			data, err := apiGet(cfg, fmt.Sprintf("/users/%s/collection/folders/0/releases", cfg.Username))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			var result map[string]interface{}
			json.Unmarshal(data, &result)
			releases, _ := result["releases"].([]interface{})
			type CacheEntry struct {
				ID     float64 `json:"id"`
				Title  string  `json:"title"`
				Artist string  `json:"artist"`
				Value  float64 `json:"value"`
			}
			var entries []CacheEntry
			for _, r := range releases {
				rm := r.(map[string]interface{})
				info := rm["basic_information"].(map[string]interface{})
				artists, _ := info["artists"].([]interface{})
				artist := ""
				if len(artists) > 0 { artist = artists[0].(map[string]interface{})["name"].(string) }
				id, _ := rm["id"].(float64)
				val, _ := info["value"].(float64)
				entries = append(entries, CacheEntry{ID: id, Title: info["title"].(string), Artist: artist, Value: val})
			}
			os.MkdirAll(filepath.Dir(cachePath()), 0700)
			out, _ := json.MarshalIndent(entries, "", "  ")
			os.WriteFile(cachePath(), out, 0600)
			fmt.Printf("Sync complete. %d releases cached.\n", len(entries))

		case "value":
			data, err := os.ReadFile(cachePath())
			if err != nil {
				fmt.Fprintln(os.Stderr, "Cache not found. Please run 'collection sync' first.")
				os.Exit(1)
			}
			type CacheEntry struct {
				ID     float64 `json:"id"`
				Title  string  `json:"title"`
				Artist string  `json:"artist"`
				Value  float64 `json:"value"`
			}
			var entries []CacheEntry
			json.Unmarshal(data, &entries)
			total := 0.0
			fmt.Printf("%-12s %-35s %-25s %s\n", "Release ID", "Title", "Artist", "Est. Value")
			fmt.Println(strings.Repeat("-", 85))
			for _, e := range entries {
				fmt.Printf("%-12v %-35v %-25v $%.2f\n", e.ID, e.Title, e.Artist, e.Value)
				total += e.Value
			}
			fmt.Println(strings.Repeat("-", 85))
			fmt.Printf("Total Collection Value: $%.2f\n", total)

		case "get":
			if len(args) < 3 { fmt.Println("Usage: discogs-cli collection get <release_id>"); os.Exit(1) }
			releaseID := args[2]
			data, err := apiGet(cfg, fmt.Sprintf("/releases/%s", releaseID))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			fmt.Println(string(data))
		}

	case "search":
		cfg := loadConfig()
		searchType := "release"
		query := ""
		for i := 1; i < len(args); i++ {
			if args[i] == "--type" && i+1 < len(args) {
				searchType = args[i+1]; i++
			} else {
				query = args[i]
			}
		}
		data, err := apiGet(cfg, fmt.Sprintf("/database/search?q=%s&type=%s", strings.ReplaceAll(query, " ", "+"), searchType))
		if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
		var result map[string]interface{}
		json.Unmarshal(data, &result)
		results, _ := result["results"].([]interface{})
		fmt.Printf("%-12s %-50s %s\n", "ID", "Title", "Type")
		fmt.Println(strings.Repeat("-", 75))
		for _, r := range results {
			rm := r.(map[string]interface{})
			id := rm["id"]
			title := rm["title"]
			rtype := rm["type"]
			fmt.Printf("%-12v %-50v %v\n", id, title, rtype)
		}

	case "wantlist":
		cfg := loadConfig()
		if len(args) < 2 { fmt.Println("Usage: discogs-cli wantlist <list|add|remove>"); os.Exit(1) }
		sub := args[1]
		switch sub {
		case "list":
			data, err := apiGet(cfg, fmt.Sprintf("/users/%s/wants", cfg.Username))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			var result map[string]interface{}
			json.Unmarshal(data, &result)
			wants, _ := result["wants"].([]interface{})
			fmt.Printf("%-12s %-50s\n", "ID", "Title")
			fmt.Println(strings.Repeat("-", 65))
			for _, w := range wants {
				wm := w.(map[string]interface{})
				info := wm["basic_information"].(map[string]interface{})
				fmt.Printf("%-12v %-50v\n", wm["id"], info["title"])
			}
		case "add":
			if len(args) < 3 { fmt.Println("Usage: discogs-cli wantlist add <release_id>"); os.Exit(1) }
			releaseID := args[2]
			_, err := apiPut(cfg, fmt.Sprintf("/users/%s/wants/%s", cfg.Username, releaseID))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			fmt.Printf("Release %s added to wantlist.\n", releaseID)
		case "remove":
			if len(args) < 3 { fmt.Println("Usage: discogs-cli wantlist remove <release_id>"); os.Exit(1) }
			releaseID := args[2]
			_, err := apiDelete(cfg, fmt.Sprintf("/users/%s/wants/%s", cfg.Username, releaseID))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			fmt.Printf("Release %s removed from wantlist.\n", releaseID)
		}

	case "release":
		cfg := loadConfig()
		if len(args) >= 3 && args[1] == "art" {
			releaseID := args[2]
			data, err := apiGet(cfg, fmt.Sprintf("/releases/%s", releaseID))
			if err != nil { fmt.Fprintf(os.Stderr, "Error: %v\n", err); os.Exit(1) }
			fmt.Printf("[Album Art for release %s]\n%s\n", releaseID, string(data))
		}

	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n", cmd)
		os.Exit(1)
	}
}
""")

with open(os.path.join(WORKSPACE, "skills/discogs-cli/main.go"), "w") as f:
    f.write(main_go)

# ── install.sh ────────────────────────────────────────────────────────────────
install_sh = textwrap.dedent("""\
    #!/usr/bin/env bash
    set -e
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BIN_DIR="$SCRIPT_DIR/bin"
    mkdir -p "$BIN_DIR"
    echo "Building discogs-cli..."
    cd "$SCRIPT_DIR"
    # Install yaml dependency
    go get gopkg.in/yaml.v3 2>/dev/null || true
    go build -o "$BIN_DIR/discogs-cli" .
    echo "Build complete: $BIN_DIR/discogs-cli"
""")
install_path = os.path.join(WORKSPACE, "skills/discogs-cli/install.sh")
with open(install_path, "w") as f:
    f.write(install_sh)
os.chmod(install_path, 0o755)

# ── mock server script ────────────────────────────────────────────────────────
mock_server = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"Local mock Discogs API server for testing.\"\"\"
    import json
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    COLLECTION = [
        {"id": 35198584, "basic_information": {"title": "Discovery", "artists": [{"name": "Daft Punk"}], "year": 2001, "value": 42.50}},
        {"id": 1419456,  "basic_information": {"title": "OK Computer", "artists": [{"name": "Radiohead"}], "year": 1997, "value": 38.00}},
        {"id": 3575126,  "basic_information": {"title": "Selected Ambient Works 85-92", "artists": [{"name": "Aphex Twin"}], "year": 1992, "value": 55.75}},
        {"id": 7526507,  "basic_information": {"title": "Music Has the Right to Children", "artists": [{"name": "Boards of Canada"}], "year": 1998, "value": 61.20}},
    ]

    FOLDERS = [
        {"id": 0, "name": "All", "count": 4},
        {"id": 1, "name": "Uncategorized", "count": 4},
        {"id": 8815833, "name": "Electronic", "count": 2},
    ]

    SEARCH_RESULTS = {
        "Aphex Twin": [{"id": 3575126, "title": "Aphex Twin - Selected Ambient Works 85-92", "type": "release"},
                       {"id": 9982341, "title": "Aphex Twin - Richard D. James Album", "type": "release"}],
        "Boards of Canada": [{"id": 7526507, "title": "Boards of Canada - Music Has the Right to Children", "type": "release"},
                              {"id": 4412893, "title": "Boards of Canada - Geogaddi", "type": "release"}],
        "Daft Punk": [{"id": 35198584, "title": "Daft Punk - Discovery", "type": "release"},
                      {"id": 2091759,  "title": "Daft Punk - Random Access Memories", "type": "release"}],
    }

    wantlist = {}

    @app.route("/users/<username>/collection/folders")
    def list_folders(username):
        return jsonify({"folders": FOLDERS})

    @app.route("/users/<username>/collection/folders/<folder_id>/releases")
    def list_releases(username, folder_id):
        return jsonify({"releases": COLLECTION, "pagination": {"items": len(COLLECTION)}})

    @app.route("/releases/<int:release_id>")
    def get_release(release_id):
        for r in COLLECTION:
            if r["id"] == release_id:
                return jsonify(r)
        return jsonify({"message": "Release not found"}), 404

    @app.route("/database/search")
    def search():
        q = request.args.get("q", "").replace("+", " ")
        results = []
        for key, vals in SEARCH_RESULTS.items():
            if key.lower() in q.lower() or q.lower() in key.lower():
                results.extend(vals)
        return jsonify({"results": results, "pagination": {"items": len(results)}})

    @app.route("/users/<username>/wants")
    def list_wants(username):
        items = []
        for rid, info in wantlist.items():
            items.append({"id": rid, "basic_information": {"title": info}})
        return jsonify({"wants": items, "pagination": {"items": len(items)}})

    @app.route("/users/<username>/wants/<int:release_id>", methods=["PUT"])
    def add_want(username, release_id):
        title = f"Release {release_id}"
        for r in COLLECTION:
            if r["id"] == release_id:
                title = r["basic_information"]["title"]
                break
        wantlist[release_id] = title
        return jsonify({"id": release_id, "status": "added"}), 201

    @app.route("/users/<username>/wants/<int:release_id>", methods=["DELETE"])
    def remove_want(username, release_id):
        wantlist.pop(release_id, None)
        return "", 204

    if __name__ == "__main__":
        app.run(host="127.0.0.1", port=8765, debug=False)
""")
mock_path = os.path.join(WORKSPACE, "skills/discogs-cli/mock_server.py")
with open(mock_path, "w") as f:
    f.write(mock_server)
os.chmod(mock_path, 0o755)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = textwrap.dedent("""\
    ---
    name: discogs-cli
    description: An OpenClaw skill to manage a user's vinyl record collection on Discogs.
    metadata: {"clawdbot":{"emoji":"Vinyl","requires":{"bins":["go"]}}}
    ---

    # Discogs Collection Manager Skill for OpenClaw

    This skill provides a command-line interface to interact with a user's record collection on Discogs.com. It is designed specifically for use within the OpenClaw assistant and uses a subcommand structure similar to `git` or `gog`.

    ## Prerequisites

    This skill is a Go program and requires the Go toolchain to be installed.

    **Installation (Debian/Ubuntu):**
    `sudo apt-get update && sudo apt-get install -y golang-go`

    ## One-Time Setup

    Before first use, you must run the included installer script. This will compile the Go binary and place it in a predictable location within the skill's directory.

    1.  **Run the installer:**
        ```bash
        skills/discogs-cli/install.sh
        ```

    2.  **Configure Credentials:**
        This command saves your Discogs token and username to a configuration file (`~/.config/discogs-cli/config.yaml`).
        ```bash
        skills/discogs-cli/bin/discogs-cli config set -u "YourUsername" -t "YourSecretToken"
        ```

    ## Usage

    All commands must be prefixed with the full path to the binary.

    ### Fetch Album Art

    Downloads the album art for a given release and displays it in the chat.

    ```bash
    skills/discogs-cli/bin/discogs-cli release art <release_id>
    ```

    ### List Collection Folders

    Shows all folders and their record counts.

    ```bash
    skills/discogs-cli/bin/discogs-cli collection list-folders
    ```

    ### List Releases in a Folder

    Shows all records within a specific folder. The output is a formatted table.

    ```bash
    # List all releases from the "All" folder (default)
    skills/discogs-cli/bin/discogs-cli collection list

    # List all releases from a specific folder by ID
    skills/discogs-cli/bin/discogs-cli collection list --folder 8815833
    ```

    ## Search the Discogs Database

    Search for releases, artists, or labels.

    ```bash
    # Search for a release (default type)
    skills/discogs-cli/bin/discogs-cli search "Daft Punk - Discovery"

    # Search for an artist
    skills/discogs-cli/bin/discogs-cli search --type artist "Aphex Twin"
    ```

    ## Manage Your Wantlist

    Work with your Discogs wantlist.

    ### List Your Wantlist

    Displays all items in your wantlist.

    ```bash
    skills/discogs-cli/bin/discogs-cli wantlist list
    ```

    ### Add to Your Wantlist

    Adds a release to your wantlist by its ID.

    ```bash
    skills/discogs-cli/bin/discogs-cli wantlist add 12345
    ```

    ### Remove from Your Wantlist

    Removes a release from your wantlist by its ID.

    ```bash
    skills/discogs-cli/bin/discogs-cli wantlist remove 12345
    ```

    ## Caching and Valuation Commands

    These commands rely on a local cache for performance. You must run `sync` first to populate the cache.

    ### Sync Collection Details (Slow)

    Fetches detailed data for every item in the collection and builds a local cache. This command is slow and should be run in the background. Inform the user that this will take time.

    ```bash
    skills/discogs-cli/bin/discogs-cli collection sync
    ```

    ### Get Collection Value (Fast)

    Reads the local cache to provide the estimated market value for each item and the total collection. This command is fast. If it fails, the cache is likely missing, and you need to run the `sync` command.

    ```bash
    skills/discogs-cli/bin/discogs-cli collection value
    ```

    ### Get Single Release Details (Fast)

    Provides a detailed view of a single release, including tracklist.

    ```bash
    skills/discogs-cli/bin/discogs-cli collection get 35198584
    ```
""")
with open(os.path.join(WORKSPACE, "skills/discogs-cli/SKILL.md"), "w") as f:
    f.write(skill_md)

print("Workspace generated successfully.")