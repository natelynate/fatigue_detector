document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Remove any existing error messages
        const existingError = loginForm.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        try {
            const response = await fetch('/login', {
                method: 'POST',
                body: new FormData(loginForm),
                credentials: 'include'  
            });

            const data = await response.json();  

            if (response.ok) {
                // If login successful
                window.location.href = '/monitoring ';
            } else {
                // Show error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = data.detail || 'Login failed';  // Use data.detail for FastAPI errors
                loginForm.appendChild(errorDiv);
            }
        } catch (error) {
            console.error('Login error:', error);
            // Show network/unexpected error
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = 'An unexpected error occurred';
            loginForm.appendChild(errorDiv);
        }
    });
});