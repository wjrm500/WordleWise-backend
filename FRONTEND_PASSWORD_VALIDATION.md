# Frontend Feature Request: Password Validation Error Handling

## Overview
The backend registration endpoint now enforces a minimum password length requirement. The frontend needs to handle the new validation error message.

## Backend Change
The `POST /register` endpoint now validates that passwords are at least 8 characters long.

## Error Response Structure
When a user attempts to register with a password shorter than 8 characters, the backend returns:

**HTTP Status Code:** `400 Bad Request`

**Response Body:**
```json
{
  "success": false,
  "error": "Password must be at least 8 characters long"
}
```

## Frontend Implementation Tasks

1. **Display Error Message**
   - When the registration API call returns a 400 status with the password validation error, display the error message to the user
   - The exact error message text is: `"Password must be at least 8 characters long"`

2. **Optional: Client-Side Validation**
   - Consider adding client-side validation to check password length before submitting
   - This provides immediate feedback and reduces unnecessary API calls
   - Validation rule: `password.length >= 8`

3. **User Experience**
   - Show the error message near the password input field
   - Clear the error when the user starts typing again
   - Maintain consistent error styling with other validation errors

## Testing
Test the following scenarios:
- ✅ Password with 7 characters → Should show error
- ✅ Password with exactly 8 characters → Should succeed
- ✅ Password with 9+ characters → Should succeed

## Example Error Handling Code
```javascript
try {
  const response = await fetch('/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, forename })
  });

  const data = await response.json();

  if (!data.success) {
    // Handle error - data.error contains the message
    setError(data.error);
  }
} catch (error) {
  // Handle network errors
}
```

## Questions?
Contact the backend team if you need clarification on the error format or validation rules.
