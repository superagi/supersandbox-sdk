package supersandbox

import (
	"context"
	"fmt"
	"strings"

	"github.com/gorilla/websocket"
)

// TerminalSession is a WebSocket PTY connection to a running sandbox.
type TerminalSession struct {
	conn *websocket.Conn
}

// TerminalOption configures a terminal session.
type TerminalOption func(*terminalParams)

type terminalParams struct {
	cols int
	rows int
}

// WithSize sets the initial terminal size.
func WithSize(cols, rows int) TerminalOption {
	return func(p *terminalParams) {
		p.cols = cols
		p.rows = rows
	}
}

func newTerminalSession(ctx context.Context, h *httpClient, sandboxID string, opts ...TerminalOption) (*TerminalSession, error) {
	p := &terminalParams{cols: 80, rows: 24}
	for _, o := range opts {
		o(p)
	}

	wsURL := strings.Replace(h.baseURL, "https://", "wss://", 1)
	wsURL = strings.Replace(wsURL, "http://", "ws://", 1)
	wsURL = fmt.Sprintf("%s/sandboxes/%s/terminal?cols=%d&rows=%d", wsURL, sandboxID, p.cols, p.rows)

	dialer := websocket.Dialer{}
	headers := map[string][]string{
		"OPEN-SANDBOX-API-KEY": {h.apiKey},
	}
	conn, _, err := dialer.DialContext(ctx, wsURL, headers)
	if err != nil {
		return nil, fmt.Errorf("terminal dial: %w", err)
	}
	return &TerminalSession{conn: conn}, nil
}

// Send writes input to the terminal (keyboard input).
func (t *TerminalSession) Send(data string) error {
	return t.conn.WriteMessage(websocket.TextMessage, []byte(data))
}

// Receive reads one message from the terminal output.
func (t *TerminalSession) Receive() (string, error) {
	_, msg, err := t.conn.ReadMessage()
	if err != nil {
		return "", err
	}
	return string(msg), nil
}

// Stream returns a channel that emits terminal output lines until the context
// is cancelled or the connection closes.
func (t *TerminalSession) Stream(ctx context.Context) <-chan StreamLine {
	ch := make(chan StreamLine, 64)
	go func() {
		defer close(ch)
		for {
			select {
			case <-ctx.Done():
				return
			default:
			}
			_, msg, err := t.conn.ReadMessage()
			if err != nil {
				if ctx.Err() == nil {
					ch <- StreamLine{Err: err}
				}
				return
			}
			ch <- StreamLine{Text: string(msg)}
		}
	}()
	return ch
}

// Close shuts down the terminal session.
func (t *TerminalSession) Close() error {
	return t.conn.Close()
}
