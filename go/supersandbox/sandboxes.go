package supersandbox

import (
	"context"
	"fmt"
	"net/url"
	"strconv"
	"strings"
)

// Create provisions a new sandbox and returns a SandboxHandle.
func (c *Client) Create(ctx context.Context, params CreateSandboxParams) (*SandboxHandle, error) {
	var resp createSandboxResponse
	if err := c.http.post(ctx, "/sandboxes", params, &resp); err != nil {
		return nil, err
	}
	return &SandboxHandle{
		ID:         resp.ID,
		Status:     resp.Status,
		Metadata:   resp.Metadata,
		Entrypoint: resp.Entrypoint,
		ExpiresAt:  resp.ExpiresAt,
		CreatedAt:  resp.CreatedAt,
		http:       c.http,
	}, nil
}

// Get fetches a sandbox by ID and returns a SandboxHandle.
func (c *Client) Get(ctx context.Context, id string) (*SandboxHandle, error) {
	var info SandboxInfo
	if err := c.http.get(ctx, "/sandboxes/"+id, nil, &info); err != nil {
		return nil, err
	}
	return sandboxHandleFromInfo(info, c.http), nil
}

// ListParams controls filtering and pagination for List.
type ListParams struct {
	State    []string
	Page     int
	PageSize int
}

// List returns all sandboxes matching the given filters, auto-paginating.
func (c *Client) List(ctx context.Context, p ListParams) ([]SandboxInfo, error) {
	params := url.Values{}
	if len(p.State) > 0 {
		params.Set("state", strings.Join(p.State, ","))
	}
	if p.Page > 0 {
		params.Set("page", strconv.Itoa(p.Page))
	}
	if p.PageSize > 0 {
		params.Set("pageSize", strconv.Itoa(p.PageSize))
	}

	var resp ListSandboxesResponse
	if err := c.http.get(ctx, "/sandboxes", params, &resp); err != nil {
		return nil, err
	}
	return resp.Items, nil
}

// Delete removes a sandbox by ID.
func (c *Client) Delete(ctx context.Context, id string) error {
	return c.http.delete(ctx, fmt.Sprintf("/sandboxes/%s", id))
}
