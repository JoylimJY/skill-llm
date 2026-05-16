import os
import random
random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "tradedash/cmd",
    "tradedash/internal/ui",
    "tradedash/internal/ui/components",
    "tradedash/internal/ui/styles",
    "tradedash/internal/model",
    "tradedash/internal/feed",
    "tradedash/internal/auth",
    "tradedash/pkg/utils",
    "tradedash/pkg/config",
    "tradedash/docs",
    "tradedash/scripts",
    "tradedash/test",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "tradedash/cmd/main.go": """\
package main

import (
    "fmt"
    "os"
    tea "github.com/charmbracelet/bubbletea"
    "tradedash/internal/ui"
)

func main() {
    p := tea.NewProgram(ui.NewModel(), tea.WithAltScreen())
    if _, err := p.Run(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\\n", err)
        os.Exit(1)
    }
}
""",
    "tradedash/internal/feed/feed.go": """\
package feed

import (
    "encoding/json"
    "net/http"
)

type Quote struct {
    Symbol string  `json:"symbol"`
    Price  float64 `json:"price"`
    Change float64 `json:"change"`
}

func FetchQuotes(symbols []string) ([]Quote, error) {
    resp, err := http.Get("https://api.example.com/quotes")
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    var quotes []Quote
    json.NewDecoder(resp.Body).Decode(&quotes)
    return quotes, nil
}
""",
    "tradedash/internal/auth/auth.go": """\
package auth

import "errors"

type Credentials struct {
    Username string
    Token    string
}

func Validate(creds Credentials) error {
    if creds.Username == "" || creds.Token == "" {
        return errors.New("invalid credentials")
    }
    return nil
}
""",
    "tradedash/internal/model/quote.go": """\
package model

type Quote struct {
    Symbol    string
    Price     float64
    Change    float64
    Volume    int64
    Timestamp int64
}

type Portfolio struct {
    Quotes    []Quote
    TotalValue float64
}
""",
    "tradedash/pkg/utils/format.go": """\
package utils

import "fmt"

func FormatPrice(price float64) string {
    return fmt.Sprintf("$%.2f", price)
}

func FormatChange(change float64) string {
    if change >= 0 {
        return fmt.Sprintf("+%.2f%%", change)
    }
    return fmt.Sprintf("%.2f%%", change)
}
""",
    "tradedash/pkg/config/config.go": """\
package config

import (
    "encoding/json"
    "os"
)

type Config struct {
    RefreshInterval int      `json:"refresh_interval"`
    Symbols         []string `json:"symbols"`
    Theme           string   `json:"theme"`
}

func Load(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var cfg Config
    return &cfg, json.Unmarshal(data, &cfg)
}
""",
    "tradedash/docs/architecture.md": """\
# TradeDash Architecture

TradeDash is a terminal-based trading dashboard built with Go.

## Components
- Feed: Real-time market data
- UI: Terminal user interface
- Auth: Authentication
- Config: Application configuration
""",
    "tradedash/scripts/build.sh": """\
#!/bin/bash
go build -o bin/tradedash ./cmd/
""",
    "tradedash/test/feed_test.go": """\
package test

import (
    "testing"
    "tradedash/internal/feed"
)

func TestFetchQuotes(t *testing.T) {
    // placeholder
    _ = feed.FetchQuotes
}
""",
    "tradedash/go.mod": """\
module tradedash

go 1.22

require (
    github.com/charmbracelet/bubbletea v0.26.0
    github.com/charmbracelet/bubbles v0.18.0
    github.com/charmbracelet/lipgloss v0.10.0
    github.com/charmbracelet/huh v0.4.0
)
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ============================================================
# THE ACTUAL FILES TO REVIEW (with intentional bugs + correct patterns)
# ============================================================

# File 1: dashboard.go — the main UI model
# BUGS:
#   - Line with os.ReadFile inside Update (actual bug)
#   - time.Sleep inside Update (actual bug)
#   - Lipgloss style created inside View (actual bug)
# CORRECT PATTERNS (must NOT be flagged):
#   - return m, m.refreshFeed() — helper returns tea.Cmd (correct)
#   - m.table, cmd = m.table.Update(msg) — nested component update (correct)
#   - value receiver on Update (correct)
dashboard_go = """\
package ui

import (
	"fmt"
	"os"
	"time"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/table"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"tradedash/internal/feed"
	"tradedash/internal/model"
)

// -----------------------------------------------------------------------------
// Messages
// -----------------------------------------------------------------------------

type quotesLoadedMsg struct {
	quotes []model.Quote
}

type errMsg struct {
	err error
}

// -----------------------------------------------------------------------------
// Styles  (package-level — correct pattern)
// -----------------------------------------------------------------------------

var (
	headerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("205")).
			Padding(0, 1)

	footerStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("241")).
			Padding(0, 1)
)

// -----------------------------------------------------------------------------
// Model
// -----------------------------------------------------------------------------

type Model struct {
	table   table.Model
	spinner spinner.Model
	quotes  []model.Quote
	loading bool
	err     error
	width   int
	height  int
}

func NewModel() Model {
	columns := []table.Column{
		{Title: "Symbol", Width: 10},
		{Title: "Price",  Width: 12},
		{Title: "Change", Width: 12},
	}
	t := table.New(
		table.WithColumns(columns),
		table.WithFocused(true),
		table.WithHeight(10),
	)

	s := spinner.New()
	s.Spinner = spinner.Dot

	return Model{
		table:   t,
		spinner: s,
		loading: true,
	}
}

// -----------------------------------------------------------------------------
// Init
// -----------------------------------------------------------------------------

func (m Model) Init() tea.Cmd {
	return tea.Batch(
		m.spinner.Tick,
		m.refreshFeed(),
	)
}

// -----------------------------------------------------------------------------
// Update  (VALUE RECEIVER — correct BubbleTea pattern)
// -----------------------------------------------------------------------------

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd
	var cmd tea.Cmd

	switch msg := msg.(type) {

	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.table.SetColumns([]table.Column{
			{Title: "Symbol", Width: msg.Width / 4},
			{Title: "Price",  Width: msg.Width / 4},
			{Title: "Change", Width: msg.Width / 4},
		})
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "q", "ctrl+c":
			return m, tea.Quit
		case "r":
			// Trigger a refresh — returns tea.Cmd, NOT blocking
			return m, m.refreshFeed()
		case "c":
			// BUG: reads config file directly in Update — blocks UI
			data, _ := os.ReadFile("config.json")
			_ = data
			return m, nil
		case "s":
			// BUG: sleeps in Update — freezes UI
			time.Sleep(2 * time.Second)
			return m, nil
		}

	case spinner.TickMsg:
		if m.loading {
			m.spinner, cmd = m.spinner.Update(msg)
			cmds = append(cmds, cmd)
		}

	case quotesLoadedMsg:
		m.loading = false
		m.quotes = msg.quotes
		rows := make([]table.Row, len(msg.quotes))
		for i, q := range msg.quotes {
			rows[i] = table.Row{q.Symbol, fmt.Sprintf("$%.2f", q.Price), fmt.Sprintf("%.2f%%", q.Change)}
		}
		m.table.SetRows(rows)
		return m, nil

	case errMsg:
		m.err = msg.err
		m.loading = false
		return m, nil
	}

	// Nested component update — CORRECT pattern, must NOT be flagged
	m.table, cmd = m.table.Update(msg)
	cmds = append(cmds, cmd)

	return m, tea.Batch(cmds...)
}

// -----------------------------------------------------------------------------
// View
// -----------------------------------------------------------------------------

func (m Model) View() string {
	if m.err != nil {
		// BUG: creating Lipgloss style inside View on every render
		errStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("196"))
		return errStyle.Render(fmt.Sprintf("Error: %v", m.err))
	}
	if m.loading {
		return m.spinner.View() + " Loading market data..."
	}

	header := headerStyle.Render("TradeDash — Live Market Feed")
	footer := footerStyle.Render("r: refresh • q: quit")
	return header + "\\n" + m.table.View() + "\\n" + footer
}

// -----------------------------------------------------------------------------
// Commands — these return tea.Cmd (closures), NOT blocking in Update
// -----------------------------------------------------------------------------

func (m Model) refreshFeed() tea.Cmd {
	return func() tea.Msg {
		quotes, err := feed.FetchQuotes([]string{"AAPL", "GOOG", "MSFT"})
		if err != nil {
			return errMsg{err}
		}
		return quotesLoadedMsg{quotes}
	}
}
"""

# File 2: orderform.go — Huh form integration
# BUGS:
#   - huh.Form.Run() called inside Update (actual bug)
#   - Lipgloss style defined inside View helper (actual bug)
# CORRECT PATTERNS (must NOT be flagged):
#   - form.Update(msg) inside Update (correct embedding)
#   - checking form.State == huh.StateCompleted (correct)
orderform_go = """\
package ui

import (
	"fmt"

	"github.com/charmbracelet/huh"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// -----------------------------------------------------------------------------
// Styles (package-level — correct)
// -----------------------------------------------------------------------------

var (
	confirmStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("78"))
)

// -----------------------------------------------------------------------------
// OrderFormModel
// -----------------------------------------------------------------------------

type OrderFormModel struct {
	form      *huh.Form
	confirmed bool
	symbol    string
	quantity  string
	orderType string
}

func NewOrderFormModel() OrderFormModel {
	form := huh.NewForm(
		huh.NewGroup(
			huh.NewInput().
				Key("symbol").
				Title("Ticker Symbol").
				Placeholder("e.g. AAPL"),

			huh.NewInput().
				Key("quantity").
				Title("Quantity"),

			huh.NewSelect[string]().
				Key("order_type").
				Title("Order Type").
				Options(
					huh.NewOption("Market", "market"),
					huh.NewOption("Limit", "limit"),
					huh.NewOption("Stop", "stop"),
				),

			huh.NewConfirm().
				Key("confirm").
				Title("Submit order?"),
		),
	).WithTheme(huh.ThemeDracula())

	return OrderFormModel{form: form}
}

func (m OrderFormModel) Init() tea.Cmd {
	return m.form.Init()
}

func (m OrderFormModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// BUG: calling blocking form.Run() inside Update
	if keyMsg, ok := msg.(tea.KeyMsg); ok && keyMsg.String() == "enter" && !m.confirmed {
		m.form.Run()  // BLOCKS THE UI
		return m, nil
	}

	// Correct form embedding pattern
	if m.form.State == huh.StateCompleted {
		m.confirmed = true
		m.symbol    = m.form.GetString("symbol")
		m.quantity  = m.form.GetString("quantity")
		m.orderType = m.form.GetString("order_type")
		return m, nil
	}

	form, cmd := m.form.Update(msg)
	if f, ok := form.(*huh.Form); ok {
		m.form = f
	}
	return m, cmd
}

func (m OrderFormModel) View() string {
	if m.confirmed {
		return m.renderConfirmation()
	}
	return m.form.View()
}

func (m OrderFormModel) renderConfirmation() string {
	// BUG: creating Lipgloss style inside a View helper function
	detailStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("241")).PaddingLeft(2)
	return confirmStyle.Render("Order Submitted!") + "\\n" +
		detailStyle.Render(fmt.Sprintf("Symbol: %s | Qty: %s | Type: %s",
			m.symbol, m.quantity, m.orderType))
}
"""

# File 3: watchlist.go — a mostly-correct file with one subtle viewport anti-pattern
# BUGS:
#   - viewport.SetContent called in View (side effect in View)
# CORRECT PATTERNS (must NOT be flagged):
#   - return m, m.loadWatchlist() — helper returning tea.Cmd (correct)
#   - WindowSizeMsg handled (correct)
watchlist_go = """\
package ui

import (
	"strings"

	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"tradedash/internal/model"
)

// -----------------------------------------------------------------------------
// Messages
// -----------------------------------------------------------------------------

type watchlistLoadedMsg struct {
	quotes []model.Quote
}

// -----------------------------------------------------------------------------
// WatchlistModel
// -----------------------------------------------------------------------------

type WatchlistModel struct {
	viewport viewport.Model
	quotes   []model.Quote
	width    int
	height   int
	loading  bool
}

func NewWatchlistModel() WatchlistModel {
	vp := viewport.New(80, 20)
	return WatchlistModel{
		viewport: vp,
		loading:  true,
	}
}

func (m WatchlistModel) Init() tea.Cmd {
	// Correct: helper returns tea.Cmd, not blocking
	return m.loadWatchlist()
}

func (m WatchlistModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.viewport.Width = msg.Width
		m.viewport.Height = msg.Height - 4
		return m, nil

	case watchlistLoadedMsg:
		m.loading = false
		m.quotes = msg.quotes
		// Correctly sets content in Update
		m.viewport.SetContent(m.renderQuotes())
		return m, nil

	case tea.KeyMsg:
		if msg.String() == "R" {
			return m, m.loadWatchlist()
		}
	}

	m.viewport, cmd = m.viewport.Update(msg)
	return m, cmd
}

func (m WatchlistModel) View() string {
	if m.loading {
		return "Loading watchlist..."
	}
	// BUG: setting viewport content inside View — side effect in pure function
	m.viewport.SetContent(m.renderQuotes())
	return m.viewport.View()
}

func (m WatchlistModel) renderQuotes() string {
	var b strings.Builder
	for _, q := range m.quotes {
		b.WriteString(q.Symbol + "\\n")
	}
	return b.String()
}

func (m WatchlistModel) loadWatchlist() tea.Cmd {
	return func() tea.Msg {
		// Simulated load — async, correct pattern
		return watchlistLoadedMsg{quotes: []model.Quote{
			{Symbol: "AAPL", Price: 189.5, Change: 1.2},
			{Symbol: "GOOG", Price: 175.3, Change: -0.8},
		}}
	}
}
"""

files_to_create = {
    "tradedash/internal/ui/dashboard.go": dashboard_go,
    "tradedash/internal/ui/orderform.go": orderform_go,
    "tradedash/internal/ui/watchlist.go": watchlist_go,
}

for path, content in files_to_create.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print("Files to review:")
for path in files_to_create:
    print(f"  /workspace/{path}")