package supersandbox

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
)

type httpClient struct {
	apiKey     string
	baseURL    string
	httpClient *http.Client
}

func (c *httpClient) newRequest(ctx context.Context, method, path string, body any) (*http.Request, error) {
	var r io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		r = bytes.NewReader(b)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, r)
	if err != nil {
		return nil, err
	}
	req.Header.Set("OPEN-SANDBOX-API-KEY", c.apiKey)
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	return req, nil
}

func (c *httpClient) do(ctx context.Context, method, path string, body, out any) error {
	_, err := c.doWithHeaders(ctx, method, path, body, out)
	return err
}

func (c *httpClient) doWithHeaders(ctx context.Context, method, path string, body, out any) (http.Header, error) {
	req, err := c.newRequest(ctx, method, path, body)
	if err != nil {
		return nil, err
	}
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, parseAPIError(resp)
	}
	if out != nil && resp.StatusCode != http.StatusNoContent {
		ct := resp.Header.Get("Content-Type")
		if strings.Contains(ct, "json") {
			if err := json.NewDecoder(resp.Body).Decode(out); err != nil {
				return resp.Header, err
			}
		} else {
			b, err := io.ReadAll(resp.Body)
			if err != nil {
				return resp.Header, err
			}
			if sp, ok := out.(*string); ok {
				*sp = string(b)
			}
		}
	}
	return resp.Header, nil
}

func (c *httpClient) get(ctx context.Context, path string, params url.Values, out any) error {
	if len(params) > 0 {
		path = path + "?" + params.Encode()
	}
	return c.do(ctx, http.MethodGet, path, nil, out)
}

func (c *httpClient) getWithHeaders(ctx context.Context, path string, params url.Values, out any) (http.Header, error) {
	if len(params) > 0 {
		path = path + "?" + params.Encode()
	}
	return c.doWithHeaders(ctx, http.MethodGet, path, nil, out)
}

func (c *httpClient) post(ctx context.Context, path string, body, out any) error {
	return c.do(ctx, http.MethodPost, path, body, out)
}

func (c *httpClient) put(ctx context.Context, path string, body, out any) error {
	return c.do(ctx, http.MethodPut, path, body, out)
}

func (c *httpClient) patch(ctx context.Context, path string, body, out any) error {
	return c.do(ctx, http.MethodPatch, path, body, out)
}

func (c *httpClient) delete(ctx context.Context, path string) error {
	return c.do(ctx, http.MethodDelete, path, nil, nil)
}

// StreamLine is a line emitted by stream().
type StreamLine struct {
	Text string
	Err  error
}

func (c *httpClient) stream(ctx context.Context, path string, params url.Values) <-chan StreamLine {
	ch := make(chan StreamLine, 64)
	go func() {
		defer close(ch)
		if len(params) > 0 {
			path = path + "?" + params.Encode()
		}
		req, err := c.newRequest(ctx, http.MethodGet, path, nil)
		if err != nil {
			ch <- StreamLine{Err: err}
			return
		}
		resp, err := c.httpClient.Do(req)
		if err != nil {
			ch <- StreamLine{Err: err}
			return
		}
		defer resp.Body.Close()
		if resp.StatusCode < 200 || resp.StatusCode >= 300 {
			ch <- StreamLine{Err: parseAPIError(resp)}
			return
		}
		sc := bufio.NewScanner(resp.Body)
		for sc.Scan() {
			line := sc.Text()
			if line != "" {
				ch <- StreamLine{Text: line}
			}
		}
		if err := sc.Err(); err != nil {
			ch <- StreamLine{Err: err}
		}
	}()
	return ch
}

func parseAPIError(resp *http.Response) error {
	var body struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	}
	b, _ := io.ReadAll(resp.Body)
	_ = json.Unmarshal(b, &body)
	if body.Code == "" {
		body.Code = "unknown"
	}
	if body.Message == "" {
		body.Message = fmt.Sprintf("HTTP %d", resp.StatusCode)
	}
	return newAPIError(resp.StatusCode, body.Code, body.Message)
}
