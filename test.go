package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/creack/pty"
)

func main() {
	// 1. Setup
	cmd := exec.Command("/opt/homebrew/bin/claude", "mcp", "list")
	cmd.Dir = "/Users/ved"
	// Use xterm to ensure the tool behaves comfortably
	cmd.Env = append(os.Environ(), "TERM=xterm-256color")

	// 2. Start
	ptmx, err := pty.Start(cmd)
	if err != nil {
		panic(err)
	}
	defer func() { _ = ptmx.Close() }()

	// 3. Size
	_ = pty.Setsize(ptmx, &pty.Winsize{Rows: 40, Cols: 100})

	fmt.Println("Starting... (Waiting 5s to ensure stability)")

	// Buffer for reading
	buf := make([]byte, 1024)

	// Flags
	step1Done := false

	for {
		n, err := ptmx.Read(buf)
		if err != nil {
			fmt.Println("Process exited:", err)
			break
		}
		output := string(buf[:n])
		fmt.Print(output) // Print live output

		// --- STEP 1: Select Figma ---
		if !step1Done && strings.Contains(output, "Needs authentication") {

			// CRITICAL: The tool is slow to start its listener.
			// If we type too fast, it crashes or prints the text.
			fmt.Println("\n\n>> [GO]: Menu detected. Waiting 5 seconds for TUI to settle...")
			time.Sleep(5 * time.Second)

			fmt.Println(">> [GO]: Sending '2'...")
			ptmx.Write([]byte("2")) // Send just '2'

			step1Done = true
			continue
		}

		// --- STEP 2: Select Authenticate ---
		// Note: We look for "Authenticate" OR "Status"
		if step1Done && (strings.Contains(output, "Authenticate") || strings.Contains(output, "Status")) {

			// Check if we already sent the '1' to avoid looping
			// Simple way: check if we haven't seen "Authenticate" in a while or just wait
			// But simpler: just wait a bit and send 1.

			fmt.Println("\n\n>> [GO]: Submenu detected. Waiting 2 seconds...")
			time.Sleep(2 * time.Second)

			fmt.Println(">> [GO]: Sending '1'...")
			ptmx.Write([]byte("1"))

			// Mark this step as "processing" so we don't spam '1'
			// In a loop this simple, we can just rely on capturing the URL next.
			step1Done = false // Hack to stop looking for this step
			continue
		}

		// --- STEP 3: Capture URL ---
		if strings.Contains(output, "https://") && strings.Contains(output, "figma") {
			fmt.Println("\n\n✅ URL CAPTURED:")

			lines := strings.Split(output, "\n")
			for _, line := range lines {
				if strings.Contains(line, "https://") {
					// Clean URL logic
					clean := line
					if idx := strings.Index(clean, "https://"); idx != -1 {
						clean = clean[idx:]
					}
					clean = strings.Split(clean, " ")[0]
					clean = strings.TrimRight(clean, "│")
					clean = strings.TrimSpace(clean)

					fmt.Println(clean)

					// Optional: Open browser automatically
					// exec.Command("open", clean).Start()
					return
				}
			}
		}
	}
}
