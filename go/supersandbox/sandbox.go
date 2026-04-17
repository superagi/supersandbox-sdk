package supersandbox

import (
	"context"
	"fmt"
	"net/url"
	"strconv"
	"time"
)

// SandboxHandle is a rich wrapper around a sandbox with convenience methods.
type SandboxHandle struct {
	ID             string
	Status         SandboxStatus
	Metadata       map[string]string
	Entrypoint     []string
	ExpiresAt      *time.Time
	CreatedAt      time.Time
	LastActivityAt *time.Time

	http *httpClient
}

func sandboxHandleFromInfo(info SandboxInfo, h *httpClient) *SandboxHandle {
	return &SandboxHandle{
		ID:             info.ID,
		Status:         info.Status,
		Metadata:       info.Metadata,
		Entrypoint:     info.Entrypoint,
		ExpiresAt:      info.ExpiresAt,
		CreatedAt:      info.CreatedAt,
		LastActivityAt: info.LastActivityAt,
		http:           h,
	}
}

// Tasks returns the Tasks sub-resource for this sandbox.
func (s *SandboxHandle) Tasks() *Tasks {
	return &Tasks{sandboxID: s.ID, http: s.http}
}

// Delete removes this sandbox.
func (s *SandboxHandle) Delete(ctx context.Context) error {
	return s.http.delete(ctx, fmt.Sprintf("/sandboxes/%s", s.ID))
}

// Pause suspends this sandbox.
func (s *SandboxHandle) Pause(ctx context.Context) error {
	return s.http.post(ctx, fmt.Sprintf("/sandboxes/%s/pause", s.ID), nil, nil)
}

// Resume resumes a paused sandbox.
func (s *SandboxHandle) Resume(ctx context.Context) error {
	return s.http.post(ctx, fmt.Sprintf("/sandboxes/%s/resume", s.ID), nil, nil)
}

// RenewExpiration extends the sandbox TTL.
func (s *SandboxHandle) RenewExpiration(ctx context.Context, ttlSeconds int) (*RenewExpirationResponse, error) {
	body := map[string]int{"timeout": ttlSeconds}
	var resp RenewExpirationResponse
	if err := s.http.put(ctx, fmt.Sprintf("/sandboxes/%s/expiration", s.ID), body, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// UpdateResourceLimits changes the CPU/memory limits for this sandbox.
func (s *SandboxHandle) UpdateResourceLimits(ctx context.Context, limits ResourceLimits) (*UpdateResourceLimitsResponse, error) {
	body := map[string]ResourceLimits{"resourceLimits": limits}
	var resp UpdateResourceLimitsResponse
	if err := s.http.put(ctx, fmt.Sprintf("/sandboxes/%s/resources", s.ID), body, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// UpdateEnv sets environment variables on the sandbox.
func (s *SandboxHandle) UpdateEnv(ctx context.Context, env map[string]string) (*UpdateEnvResponse, error) {
	body := map[string]map[string]string{"env": env}
	var resp UpdateEnvResponse
	if err := s.http.put(ctx, fmt.Sprintf("/sandboxes/%s/env", s.ID), body, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// GetEndpoint returns the public address for a port exposed by the sandbox.
func (s *SandboxHandle) GetEndpoint(ctx context.Context, port int, public bool) (*Endpoint, error) {
	params := url.Values{}
	if public {
		params.Set("public", "true")
	}
	var ep Endpoint
	if err := s.http.get(ctx, fmt.Sprintf("/sandboxes/%s/endpoints/%d", s.ID, port), params, &ep); err != nil {
		return nil, err
	}
	return &ep, nil
}

// GetLogs returns the last tail lines of container logs.
func (s *SandboxHandle) GetLogs(ctx context.Context, tail int) (string, error) {
	params := url.Values{}
	params.Set("tail", strconv.Itoa(tail))
	params.Set("follow", "false")
	var logs string
	if err := s.http.get(ctx, fmt.Sprintf("/sandboxes/%s/logs", s.ID), params, &logs); err != nil {
		return "", err
	}
	return logs, nil
}

// StreamLogs returns a channel that emits log lines in real time.
func (s *SandboxHandle) StreamLogs(ctx context.Context, tail int) <-chan StreamLine {
	params := url.Values{}
	params.Set("tail", strconv.Itoa(tail))
	params.Set("follow", "true")
	return s.http.stream(ctx, fmt.Sprintf("/sandboxes/%s/logs", s.ID), params)
}

// Terminal opens a WebSocket PTY session on the sandbox.
func (s *SandboxHandle) Terminal(ctx context.Context, opts ...TerminalOption) (*TerminalSession, error) {
	if s.Status.State != "Running" {
		return nil, fmt.Errorf("sandbox %s is not running (state: %s)", s.ID, s.Status.State)
	}
	return newTerminalSession(ctx, s.http, s.ID, opts...)
}

func (s *SandboxHandle) String() string {
	return fmt.Sprintf("SandboxHandle(id=%s, state=%s)", s.ID, s.Status.State)
}
