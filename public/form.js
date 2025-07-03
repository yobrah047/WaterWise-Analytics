document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("authForm");

    // Function to handle fullscreen toggle
    function toggleFullScreen() {
        if (!document.fullscreenElement) {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            } else if (document.documentElement.mozRequestFullScreen) {
                document.documentElement.mozRequestFullScreen();
            } else if (document.documentElement.webkitRequestFullscreen) {
                document.documentElement.webkitRequestFullscreen();
            } else if (document.documentElement.msRequestFullscreen) {
                document.documentElement.msRequestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
    }

    // Add fullscreen button if not on auth page
    if (window.location.pathname !== '/auth.html') {
        if (!document.getElementById('fullscreenBtn')) {
            const body = document.getElementsByTagName('body')[0];

            const fullscreenBtn = document.createElement('button');
            fullscreenBtn.addEventListener("error", (e) => console.error("Error with Fullscreen button: ", e));
            fullscreenBtn.id = 'fullscreenBtn';
            fullscreenBtn.textContent = 'Fullscreen';

            fullscreenBtn.classList.add('fullscreen-button');
            fullscreenBtn.onclick = toggleFullScreen;
            body.appendChild(fullscreenBtn);
        }
    }

    // Add logout button and functionality to index page
    if (window.location.pathname === '/') {
        if (!document.getElementById('logoutBtn')) {
            const body = document.getElementsByTagName('body')[0];

            const nav = document.createElement('nav');
            nav.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
            `;
            body.insertBefore(nav, body.firstChild);

            // Logout Button
            
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
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            `;
            nav.appendChild(logoutBtn);

            logoutBtn.addEventListener('click', async () => {
                try {                   
                    const response = await fetch('/api/logout');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const result = await response.json();
                    if (result.success) {
                        window.location.href = '/';
                    } else {
                        console.error("Logout failed: ", result.error);
                        alert("❌ Error: " + (result.error || "Logout failed"));
                    }
                } catch (err) {
                    console.error('Logout failed:', err);
                    alert("❌ Network error: " + err.message);                }
            });
        }
        return; // Exit if we're on index page
    }
    // Authentication form handling (login/register)
    if(form){
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

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();

            if (response.ok) {
                if (isRegister) {
                    alert("✅ Registration successful! Please login.");
                    window.location.reload(); // Return to login form
                } else {
                    alert("✅ Login successful! Redirecting...");
 if (result.redirectUrl) {
                        window.location.href = result.redirectUrl; // Redirect to specified URL
                    } else {
 window.location.href = "/"; // Default redirect to index.html if no redirectUrl
                    }
                }
            } else {
                alert("❌ " + (result.error || "Something went wrong"));

            }
        } catch (err) {
            alert("❌ Network error: " + err.message);
        }
    });
    }

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
                if(!formData){
                    throw new Error("Form data is empty!");
                }
                const response = await fetch('/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (response.ok) {
                    const result = await response.json();
                    localStorage.setItem('predictionResult', JSON.stringify(result));
                    window.location.href = '/results.html'; // Redirect to results page

                } else if (response.status === 401) {
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = "<p>❌ You are not logged in! </p>";
                } else {
                    const result = await response.json();
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = `<p>❌ Error: ${result.error || 'An unknown error occurred.'}</p>`;
                }
            }
             catch (error) {
                const resultsDiv = document.getElementById('results');
                console.error('Fetch error:', error);
                resultsDiv.innerHTML = `<p>❌ Error: ${error.message || 'An unknown error occurred.'}</p>`;
            }
        });
    }
    // Toggle between login and register forms in auth.html
    const switchToRegister = document.getElementById("switchToRegister");
    const switchToLogin = document.getElementById("switchToLogin");
    

    if (switchToRegister) {
        switchToRegister.addEventListener("click", function (e) {
            e.preventDefault();
            const form = document.getElementById("authForm");
            form.innerHTML = `
                <div>
                    <label for="name">👤 Full Name:</label>
                    <input type="text" id="name" name="name" placeholder="Enter your full name" required>
                </div>
                <div>
                    <label for="regEmail">📧 Email:</label>
                    <input type="email" id="regEmail" name="email" placeholder="Enter your email" required>
                </div>
                <div>
                    <label for="regPassword">🔒 Password:</label>
                    <input type="password" id="regPassword" name="password" placeholder="Create a password" required>
                </div>
                <div>
                    <label for="confirmPassword">🔐 Confirm Password:</label>
                    <input type="password" id="confirmPassword" name="confirmPassword" placeholder="Confirm your password" required>
                </div>
                <button type="submit" class="btn-submit">Register</button>
                <div class="auth-switch">
                    Already have an account? <a href="#" id="switchToLogin">Sign In</a>
                </div>
            `;
            // Reattach the listener to the newly created switchToLogin link
            const newSwitchToLogin = document.getElementById("switchToLogin");
            if (newSwitchToLogin) {
                newSwitchToLogin.addEventListener("click", function (e) {
                    e.preventDefault();
                    window.location.reload();
                });
            }
            // Reset the form's event listener
            const newForm = document.getElementById("authForm");
            newForm.addEventListener("submit", async function (e) {
                // Call the function handling the form submission
                e.preventDefault();
                const isRegister = !!document.getElementById("name"); 
                const formData = {
                    name: isRegister ? document.getElementById("name").value : undefined,
                    email: isRegister ? document.getElementById("regEmail").value : document.getElementById("email").value,
                    password: isRegister ? document.getElementById("regPassword").value : document.getElementById("password").value,
                    confirmPassword: isRegister ? document.getElementById("confirmPassword").value : undefined
                };
                const endpoint = isRegister ? "/api/register" : "/api/login";
                
            });
            
        });
    }
    
    
});
