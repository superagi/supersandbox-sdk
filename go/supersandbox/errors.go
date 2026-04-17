package supersandbox

import "fmt"

// APIError is returned when the API responds with a non-2xx status code.
type APIError struct {
	StatusCode int
	Code       string
	Message    string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("[%d] %s: %s", e.StatusCode, e.Code, e.Message)
}

// NotFoundError is returned on 404 responses.
type NotFoundError struct{ APIError }

// UnauthorizedError is returned on 401 responses.
type UnauthorizedError struct{ APIError }

// ConflictError is returned on 409 responses.
type ConflictError struct{ APIError }

func newAPIError(status int, code, message string) error {
	base := APIError{StatusCode: status, Code: code, Message: message}
	switch status {
	case 404:
		return &NotFoundError{base}
	case 401:
		return &UnauthorizedError{base}
	case 409:
		return &ConflictError{base}
	default:
		return &base
	}
}
