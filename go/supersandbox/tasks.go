package supersandbox

import (
	"context"
	"fmt"
	"net/url"
	"strconv"
)

// Tasks is the tasks sub-resource for a sandbox.
type Tasks struct {
	sandboxID string
	http      *httpClient
}

func (t *Tasks) base() string {
	return fmt.Sprintf("/sandboxes/%s/tasks", t.sandboxID)
}

// Submit runs a shell command inside the sandbox and returns the Task.
func (t *Tasks) Submit(ctx context.Context, command string, opts ...TaskOption) (*Task, error) {
	p := SubmitTaskParams{Command: command}
	for _, o := range opts {
		o(&p)
	}
	var task Task
	if err := t.http.post(ctx, t.base(), p, &task); err != nil {
		return nil, err
	}
	return &task, nil
}

// Get fetches the current state of a task.
func (t *Tasks) Get(ctx context.Context, taskID string) (*Task, error) {
	var task Task
	if err := t.http.get(ctx, fmt.Sprintf("%s/%s", t.base(), taskID), nil, &task); err != nil {
		return nil, err
	}
	return &task, nil
}

// Logs returns buffered logs for a task with optional cursor-based pagination.
func (t *Tasks) Logs(ctx context.Context, taskID string, cursor *int) (*TaskLogsResponse, error) {
	params := url.Values{}
	if cursor != nil {
		params.Set("cursor", strconv.Itoa(*cursor))
	}
	var logs string
	headers, err := t.http.getWithHeaders(ctx, fmt.Sprintf("%s/%s/logs", t.base(), taskID), params, &logs)
	if err != nil {
		return nil, err
	}
	var nextCursor *int
	if raw := headers.Get("X-Task-Log-Cursor"); raw != "" {
		v, err := strconv.Atoi(raw)
		if err == nil {
			nextCursor = &v
		}
	}
	return &TaskLogsResponse{Logs: logs, NextCursor: nextCursor}, nil
}

// Kill terminates a running task.
func (t *Tasks) Kill(ctx context.Context, taskID string) error {
	return t.http.delete(ctx, fmt.Sprintf("%s/%s", t.base(), taskID))
}

// TaskOption configures a Submit call.
type TaskOption func(*SubmitTaskParams)

// WithEnvs sets environment variables for the task.
func WithEnvs(env map[string]string) TaskOption {
	return func(p *SubmitTaskParams) { p.Envs = env }
}

// WithTaskTimeout sets a timeout in seconds for the task.
func WithTaskTimeout(seconds int) TaskOption {
	return func(p *SubmitTaskParams) { p.Timeout = &seconds }
}
