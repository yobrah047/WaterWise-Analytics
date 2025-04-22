document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("authForm");
    const predictForm = document.getElementById("predictForm");
    

    // Check if we're on the index page and add logout functionality
    if (window.location.pathname === '/') {
        // Add logout button if not already present
        if (!document.getElementById('logoutBtn')) {
            const body = document.getElementsByTagName('body')[0]

            const logoutBtn = document.createElement('button');
            logoutBtn.id = 'logoutBtn';
            logoutBtn.textContent = '🚪 Logout';
            logoutBtn.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 24px;
                background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                z-index: 1000;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            `;
            body.appendChild(logoutBtn);

            logoutBtn.addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/logout');
                    const result = await response.json();
                    if (result.success) {
                        window.location.href = '/';
                    }
                } catch (err) {
                    console.error('Logout failed:', err);
                }
            });
        }
        return; // Exit if we're on index page
    }

    // Authentication form handling
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const isRegister = !!document.getElementById("name"); // Check if it's register form

        const formData = {
            name: isRegister ? document.getElementById("name").value : undefined,
            email: isRegister ? document.getElementById("regEmail").value : document.getElementById("email").value,
            password: isRegister ? document.getElementById("regPassword").value : document.getElementById("password").value,
            confirmPassword: isRegister ? document.getElementById("confirmPassword").value : undefined
        };

        const endpoint = isRegister ? "/api/register" : "/api/login";

        try {
            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                if (isRegister) {
                    alert("✅ Registration successful! Please login.");
                    window.location.reload(); // Return to login form
                } else {
                    alert("✅ Login successful! Redirecting...");
                    window.location.href = "/"; // Redirect to index.html
                }
            } else {
                alert("❌ " + (result.error || "Something went wrong"));
            }
        } catch (err) {
            alert("❌ Network error");
            console.error(err);
        }
    });

    // Handle form submission from index.html
    const waterTestForm = document.getElementById('waterTestForm');
    if (waterTestForm) {
        waterTestForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Gather form data
            const formData = {};
            const formElements = waterTestForm.elements;
            for (let i = 0; i < formElements.length; i++) {
                if (formElements[i].type !== 'submit') {
                    formData[formElements[i].name] = formElements[i].value;
                }
            }

            try {
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                const result = await response.json();

                if (response.ok) {
                    const { prediction, recommendations } = result;

                    // Update current page with results
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = `
                        <h3>Prediction: ${prediction.status}</h3>
                        ${recommendations.length > 0 ? '<h4>Recommendations:</h4>' : ''}
                        <ul>
                            ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    `;

                } else if (response.status === 401) {
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = "<p>❌ You are not logged in!</p>";
                } else {
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = `<p>❌ Error: ${result.error || 'An unknown error occurred.'}</p>`;
                }
            } catch (error) {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `<p>❌ Error: ${error.message || 'An unknown error occurred.'}</p>`;
            }
        });
    }
});

