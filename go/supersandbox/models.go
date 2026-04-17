package supersandbox

import "time"

// SandboxStatus represents the current state of a sandbox.
type SandboxStatus struct {
	State            string     `json:"state"`
	Reason           *string    `json:"reason,omitempty"`
	Message          *string    `json:"message,omitempty"`
	LastTransitionAt *time.Time `json:"lastTransitionAt,omitempty"`
}

// Sandbox is a running sandbox instance.
type Sandbox struct {
	ID             string            `json:"id"`
	Status         SandboxStatus     `json:"status"`
	Metadata       map[string]string `json:"metadata,omitempty"`
	Entrypoint     []string          `json:"entrypoint"`
	ExpiresAt      *time.Time        `json:"expiresAt,omitempty"`
	CreatedAt      time.Time         `json:"createdAt"`
	LastActivityAt *time.Time        `json:"lastActivityAt,omitempty"`
}

// Task represents a background shell command running on a sandbox.
type Task struct {
	ID         string     `json:"id"`
	Status     string     `json:"status"`
	ExitCode   *int       `json:"exitCode,omitempty"`
	StartedAt  *time.Time `json:"startedAt,omitempty"`
	FinishedAt *time.Time `json:"finishedAt,omitempty"`
}

// Endpoint is the public address of a service running inside a sandbox.
type Endpoint struct {
	Endpoint string            `json:"endpoint"`
	Headers  map[string]string `json:"headers,omitempty"`
}

// ResourceLimits holds CPU/memory/storage constraints.
type ResourceLimits map[string]string

// CreateSandboxParams holds parameters for creating a sandbox.
type CreateSandboxParams struct {
	Image          ImageSpec         `json:"image"`
	Entrypoint     []string          `json:"entrypoint"`
	ResourceLimits ResourceLimits    `json:"resourceLimits"`
	Timeout        *int              `json:"timeout,omitempty"`
	Env            map[string]string `json:"env,omitempty"`
	Metadata       map[string]string `json:"metadata,omitempty"`
}

// ImageSpec describes the container image for a sandbox.
type ImageSpec struct {
	URI  string     `json:"uri"`
	Auth *ImageAuth `json:"auth,omitempty"`
}

// ImageAuth holds private registry credentials.
type ImageAuth struct {
	Username string `json:"username"`
	Password string `json:"password"`
}
