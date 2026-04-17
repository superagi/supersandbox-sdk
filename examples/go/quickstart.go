// Quickstart example for the SuperSandbox Go SDK.
//
// Run:
//
//	SUPERSANDBOX_API_KEY=<key> go run quickstart.go
package main

import (
	"context"
	"fmt"
	"os"
	"time"

	supersandbox "github.com/superagi/supersandbox-sdk/go/supersandbox"
)

func main() {
	apiKey := os.Getenv("SUPERSANDBOX_API_KEY")
	if apiKey == "" {
		fmt.Fprintln(os.Stderr, "SUPERSANDBOX_API_KEY is not set")
		os.Exit(1)
	}

	client := supersandbox.New(apiKey)
	ctx := context.Background()

	// ── Create ────────────────────────────────────────────────────────────────
	fmt.Println("Creating sandbox...")
	sb, err := client.Create(ctx, supersandbox.CreateSandboxParams{
		Image:          supersandbox.ImageSpec{URI: "python:3.11-slim"},
		Entrypoint:     []string{"sleep", "120"},
		ResourceLimits: supersandbox.ResourceLimits{"cpu": "250m", "memory": "256Mi"},
		Metadata:       map[string]string{"example": "quickstart"},
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "create: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("  %s\n", sb)

	defer func() {
		fmt.Println("Deleting sandbox...")
		_ = sb.Delete(context.Background())
		fmt.Println("  Done.")
	}()

	// ── Run a task ────────────────────────────────────────────────────────────
	fmt.Println("Running task...")
	task, err := sb.Tasks().Submit(ctx, `python3 -c "print('hello from sandbox')"`)
	if err != nil {
		fmt.Fprintf(os.Stderr, "submit: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("  task id=%s\n", task.EffectiveID())

	// Poll until done
	taskID := task.EffectiveID()
	for i := 0; i < 30; i++ {
		time.Sleep(time.Second)
		task, err = sb.Tasks().Get(ctx, taskID)
		if err != nil {
			fmt.Fprintf(os.Stderr, "get task: %v\n", err)
			os.Exit(1)
		}
		if task.Status != nil && (*task.Status == "completed" || *task.Status == "failed") {
			break
		}
	}
	if task.Status != nil {
		fmt.Printf("  status=%s exit_code=%v\n", *task.Status, task.ExitCode)
	}

	// Fetch logs
	result, err := sb.Tasks().Logs(ctx, taskID, nil)
	if err != nil {
		fmt.Fprintf(os.Stderr, "logs: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("  output: %q\n", result.Logs)

	// ── Container logs ────────────────────────────────────────────────────────
	fmt.Println("Fetching container logs...")
	logs, err := sb.GetLogs(ctx, 20)
	if err != nil {
		fmt.Fprintf(os.Stderr, "get logs: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("  %q\n", logs[:min(len(logs), 120)])
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
