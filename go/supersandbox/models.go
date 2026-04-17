package supersandbox

import "time"

// SandboxStatus represents the current state of a sandbox.
type SandboxStatus struct {
	State            string     `json:"state"`
	Reason           *string    `json:"reason,omitempty"`
	Message          *string    `json:"message,omitempty"`
	LastTransitionAt *time.Time `json:"lastTransitionAt,omitempty"`
}

// ImageAuth holds private registry credentials.
type ImageAuth struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// ImageSpec describes the container image for a sandbox.
type ImageSpec struct {
	URI  string     `json:"uri"`
	Auth *ImageAuth `json:"auth,omitempty"`
}

// ResourceLimits holds CPU/memory/storage constraints.
type ResourceLimits map[string]string

// NetworkRule is a single egress rule in a network policy.
type NetworkRule struct {
	Action string `json:"action"`
	Target string `json:"target"`
}

// NetworkPolicy controls outbound traffic from a sandbox.
type NetworkPolicy struct {
	DefaultAction *string       `json:"defaultAction,omitempty"`
	Egress        []NetworkRule `json:"egress,omitempty"`
}

// PVC is a Kubernetes PersistentVolumeClaim volume source.
type PVC struct {
	ClaimName string `json:"claimName"`
}

// HostPath is a host filesystem volume source.
type HostPath struct {
	Path string `json:"path"`
}

// OSSFS is an Alibaba Cloud OSS mount backend.
type OSSFS struct {
	Bucket          string   `json:"bucket"`
	Endpoint        string   `json:"endpoint"`
	Version         string   `json:"version,omitempty"`
	Options         []string `json:"options,omitempty"`
	AccessKeyID     *string  `json:"accessKeyId,omitempty"`
	AccessKeySecret *string  `json:"accessKeySecret,omitempty"`
}

// Volume describes a filesystem mount inside a sandbox.
type Volume struct {
	Name      string    `json:"name"`
	Host      *HostPath `json:"host,omitempty"`
	PVC       *PVC      `json:"pvc,omitempty"`
	OSSFS     *OSSFS    `json:"ossfs,omitempty"`
	MountPath string    `json:"mountPath"`
	ReadOnly  bool      `json:"readOnly,omitempty"`
	SubPath   *string   `json:"subPath,omitempty"`
}

// CreateSandboxParams holds parameters for creating a sandbox.
type CreateSandboxParams struct {
	Image          ImageSpec         `json:"image"`
	Entrypoint     []string          `json:"entrypoint"`
	ResourceLimits ResourceLimits    `json:"resourceLimits"`
	Timeout        *int              `json:"timeout,omitempty"`
	Env            map[string]string `json:"env,omitempty"`
	Metadata       map[string]string `json:"metadata,omitempty"`
	Volumes        []Volume          `json:"volumes,omitempty"`
	NetworkPolicy  *NetworkPolicy    `json:"networkPolicy,omitempty"`
}

// createSandboxResponse is the API response from POST /sandboxes.
type createSandboxResponse struct {
	ID         string            `json:"id"`
	Status     SandboxStatus     `json:"status"`
	Metadata   map[string]string `json:"metadata,omitempty"`
	ExpiresAt  *time.Time        `json:"expiresAt,omitempty"`
	CreatedAt  time.Time         `json:"createdAt"`
	Entrypoint []string          `json:"entrypoint"`
}

// SandboxInfo is the full sandbox representation returned by GET /sandboxes/:id.
type SandboxInfo struct {
	ID             string            `json:"id"`
	Image          ImageSpec         `json:"image"`
	Status         SandboxStatus     `json:"status"`
	Metadata       map[string]string `json:"metadata,omitempty"`
	Entrypoint     []string          `json:"entrypoint"`
	ExpiresAt      *time.Time        `json:"expiresAt,omitempty"`
	CreatedAt      time.Time         `json:"createdAt"`
	LastActivityAt *time.Time        `json:"lastActivityAt,omitempty"`
}

// PaginationInfo holds page metadata for list responses.
type PaginationInfo struct {
	Page        int  `json:"page"`
	PageSize    int  `json:"pageSize"`
	TotalItems  int  `json:"totalItems"`
	TotalPages  int  `json:"totalPages"`
	HasNextPage bool `json:"hasNextPage"`
}

// ListSandboxesResponse is returned by GET /sandboxes.
type ListSandboxesResponse struct {
	Items      []SandboxInfo  `json:"items"`
	Pagination PaginationInfo `json:"pagination"`
}

// Endpoint is the public address of a service running inside a sandbox.
type Endpoint struct {
	Endpoint string            `json:"endpoint"`
	Headers  map[string]string `json:"headers,omitempty"`
}

// Task represents a background shell command running on a sandbox.
type Task struct {
	ID         string     `json:"id"`
	TaskID     string     `json:"taskId"`
	Status     *string    `json:"status,omitempty"`
	ExitCode   *int       `json:"exitCode,omitempty"`
	StartedAt  *time.Time `json:"startedAt,omitempty"`
	FinishedAt *time.Time `json:"finishedAt,omitempty"`
}

// EffectiveID returns whichever of TaskID or ID is set (submit returns taskId).
func (t *Task) EffectiveID() string {
	if t.TaskID != "" {
		return t.TaskID
	}
	return t.ID
}

// TaskLogsResponse is returned by GET /sandboxes/:id/tasks/:taskId/logs.
type TaskLogsResponse struct {
	Logs       string
	NextCursor *int
}

// SubmitTaskParams holds parameters for submitting a task.
type SubmitTaskParams struct {
	Command string            `json:"command"`
	Envs    map[string]string `json:"envs,omitempty"`
	Timeout *int              `json:"timeout,omitempty"`
}

// UpdateEnvResponse is returned by PUT /sandboxes/:id/env.
type UpdateEnvResponse struct {
	ID  string            `json:"id"`
	Env map[string]string `json:"env"`
}

// UpdateResourceLimitsResponse is returned by PUT /sandboxes/:id/resources.
type UpdateResourceLimitsResponse struct {
	ID             string         `json:"id"`
	Status         SandboxStatus  `json:"status"`
	ResourceLimits ResourceLimits `json:"resourceLimits"`
}

// RenewExpirationResponse is returned by PUT /sandboxes/:id/expiration.
type RenewExpirationResponse struct {
	ExpiresAt time.Time `json:"expiresAt"`
}
