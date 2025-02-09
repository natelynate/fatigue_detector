// static/js/home.js
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(loginForm);

        try {
            const response = await fetch('/login', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Redirect to monitoring page
                window.location.href = '/monitoring';
            } else {
                // Show error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                errorDiv.textContent = data.message || 'Login failed';
                loginForm.appendChild(errorDiv);
            }
        } catch (error) {
            console.error('Login error:', error);
        }
    });
});