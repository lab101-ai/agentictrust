// DOM Elements - Updated for new layout
const loginSection = document.getElementById('login-section');
const signupSection = document.getElementById('signup-section');
const userInfoSection = document.getElementById('user-info-section'); // New
const displayUsername = document.getElementById('display-username'); // New
const displayRole = document.getElementById('display-role'); // New for role display

// const usernameInput = document.getElementById('username'); // Removed
// const passwordInput = document.getElementById('password'); // Removed
const userSelectDropdown = document.getElementById('user-select-dropdown'); // New
const loginBtn = document.getElementById('login-btn');
// loginError is now created dynamically when needed
const logoutBtn = document.getElementById('logout-btn');

// Signup elements
const signupUsernameInput = document.getElementById('signup-username');
const signupPasswordInput = document.getElementById('signup-password');
const signupBtn = document.getElementById('signup-btn');
const signupMessage = document.getElementById('signup-message');
// const showSignupLink = document.getElementById('show-signup-link'); // De-emphasized
// const showLoginLink = document.getElementById('show-login-link'); // De-emphasized

const ticketListBody = document.getElementById('ticket-list-body'); // Changed from ticketList (ul) to tbody
const publicTicketListBody = document.getElementById('public-ticket-list-body'); // Changed from publicTicketList (ul) to tbody

const chatWindow = document.getElementById('chat-window');
const chatInput = document.getElementById('chat-input');
const sendChatBtn = document.getElementById('send-chat-btn');

// Statistics Display Elements
const overallStatsContent = document.getElementById('overall-stats-content');
const companyStatsList = document.getElementById('company-stats-list');
const userStatsDisplay = document.getElementById('user-stats-display');
const userStatsContent = document.getElementById('user-stats-content');

let authToken = null;
const API_BASE_URL = 'http://0.0.0.0:3002';

// --- UI Visibility --- // 
function updateUIVisibility(isLoggedIn) {
    if (isLoggedIn) {
        loginSection.style.display = 'none';
        signupSection.style.display = 'none';
        userInfoSection.style.display = 'block';
        
        const firstName = localStorage.getItem('firstName');
        const lastName = localStorage.getItem('lastName');
        const storedUsername = localStorage.getItem('username'); // Fallback email
        const storedRole = localStorage.getItem('userRole');

        let nameToShow = '';
        if (firstName && lastName) {
            nameToShow = `${firstName} ${lastName}`;
        } else if (firstName) {
            nameToShow = firstName;
        } else if (lastName) {
            nameToShow = lastName;
        } else {
            nameToShow = storedUsername; // Fallback to email
        }
        
        displayUsername.textContent = nameToShow ? `${nameToShow}!` : 'User!';
        displayRole.textContent = storedRole ? `(${storedRole})` : ''; // Display role in parentheses
        
        userStatsDisplay.style.display = 'block'; // Show user stats section
    } else {
        loginSection.style.display = 'block';
        signupSection.style.display = 'none'; // Default to login form
        userInfoSection.style.display = 'none';
        userStatsDisplay.style.display = 'none'; // Hide user stats section
        userStatsContent.innerHTML = 'Loading...'; // Reset user stats content
        // usernameInput.value = ''; // Removed
        // passwordInput.value = ''; // Removed
        // Remove any error message that might exist
        const existingError = document.getElementById('login-error');
        if (existingError) {
            existingError.remove();
        }
        ticketListBody.innerHTML = ''; // Clear user-specific tickets
        // publicTicketListBody is populated by fetchPublicTickets, called in init
        chatWindow.innerHTML = ''; // Clear chat
    }
}

// --- Authentication --- //
loginBtn.addEventListener('click', async () => {
    const selectedUsername = userSelectDropdown.value;
    const dummyPassword = 'password123'; // Using the same password as in seed.py
    
    // Clear any previous error message
    const existingError = document.getElementById('login-error');
    if (existingError) {
        existingError.remove();
    }

    if (!selectedUsername) {
        // Create error element for the validation message
        const loginError = document.createElement('p');
        loginError.id = 'login-error';
        loginError.className = 'error-message';
        loginError.textContent = 'Please select a user.';
        loginSection.appendChild(loginError);
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/token`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(selectedUsername)}&password=${encodeURIComponent(dummyPassword)}`,
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('username', selectedUsername); // Store selected username
            
            // Fetch user details including role
            try {
                const userDetailsResponse = await fetch(`${API_BASE_URL}/users/me`, {
                    headers: { 'Authorization': `Bearer ${authToken}` }
                });
                if (userDetailsResponse.ok) {
                    const userDetails = await userDetailsResponse.json();
                    localStorage.setItem('userRole', userDetails.role || 'N/A'); // Store role
                    localStorage.setItem('firstName', userDetails.first_name || ''); // Store first name
                    localStorage.setItem('lastName', userDetails.last_name || '');   // Store last name
                } else {
                    console.error('Failed to fetch user details for role');
                    localStorage.setItem('userRole', 'N/A'); // Default if fetch fails
                }
            } catch (error) {
                console.error('Error fetching user details for role:', error);
                localStorage.setItem('userRole', 'N/A'); // Default on error
            }

            updateUIVisibility(true);
            fetchTickets(); // Fetch user-specific tickets
            fetchAndDisplayUserStats(); // Fetch and display user-specific stats
        } else {
            const errorData = await response.json();
            const errorMessage = errorData.detail || `Login failed for ${selectedUsername}. Ensure server is running and user exists with password 'password123'.`;
            
            // Create error element if it doesn't exist, or get existing one
            let loginError = document.getElementById('login-error');
            if (!loginError) {
                loginError = document.createElement('p');
                loginError.id = 'login-error';
                loginError.className = 'error-message';
                loginSection.appendChild(loginError);
            }
            loginError.textContent = errorMessage;
        }
    } catch (error) {
        console.error('Login error:', error);
        
        // Create error element if it doesn't exist, or get existing one
        let loginError = document.getElementById('login-error');
        if (!loginError) {
            loginError = document.createElement('p');
            loginError.id = 'login-error';
            loginError.className = 'error-message';
            loginSection.appendChild(loginError);
        }
        loginError.textContent = 'An error occurred during login.';
    }
});

logoutBtn.addEventListener('click', () => {
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('username'); // Remove stored username
    localStorage.removeItem('userRole'); // Remove stored role
    localStorage.removeItem('firstName'); // Remove stored first name
    localStorage.removeItem('lastName'); // Remove stored last name
    updateUIVisibility(false);
});

// --- Signup --- //
// Signup functionality is kept but less prominent now
signupBtn.addEventListener('click', async () => {
    const username = signupUsernameInput.value.trim();
    const password = signupPasswordInput.value.trim();
    signupMessage.textContent = '';
    signupMessage.className = 'message'; 

    if (!username || !password) {
        signupMessage.textContent = 'Username and password are required.';
        signupMessage.classList.add('error-message');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
            signupMessage.textContent = 'Signup successful! Please login.';
            signupMessage.classList.remove('error-message');
            // Show login form after a brief delay
            setTimeout(() => {
                signupSection.style.display = 'none';
                loginSection.style.display = 'block';
            }, 2000);
        } else {
            signupMessage.textContent = data.detail || 'Signup failed.';
            signupMessage.classList.add('error-message');
        }
    } catch (error) {
        console.error('Signup error:', error);
        signupMessage.textContent = 'An error occurred during signup.';
        signupMessage.classList.add('error-message');
    }
});

// --- Tickets --- //
async function fetchTickets() { // User-specific tickets
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE_URL}/tickets`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (response.ok) {
            const tickets = await response.json();
            renderTickets(tickets, ticketListBody, false); // My Tickets table
        } else {
            console.error('Failed to fetch user tickets');
            ticketListBody.innerHTML = '<tr><td colspan="7">Failed to load your tickets.</td></tr>';
        }
    } catch (error) {
        console.error('Error fetching user tickets:', error);
        ticketListBody.innerHTML = '<tr><td colspan="7">Error loading your tickets.</td></tr>';
    }
}

async function fetchPublicTickets() {
    try {
        const response = await fetch(`${API_BASE_URL}/public_tickets`);
        if (response.ok) {
            const tickets = await response.json();
            renderTickets(tickets, publicTicketListBody, true); // Public Tickets table
        } else {
            console.error('Failed to fetch public tickets');
            publicTicketListBody.innerHTML = '<tr><td colspan="6">Failed to load public tickets.</td></tr>';
        }
    } catch (error) {
        console.error('Error fetching public tickets:', error);
        publicTicketListBody.innerHTML = '<tr><td colspan="6">Error loading public tickets.</td></tr>';
    }
}

function renderTickets(tickets, tableBodyElement, isPublicTable) {
    tableBodyElement.innerHTML = ''; // Clear existing tickets

    const numColumns = isPublicTable ? 6 : 7; // Public: 6 cols, My Tickets: 7 cols

    if (!tickets || tickets.length === 0) {
        const tr = document.createElement('tr');
        const td = document.createElement('td');
        td.textContent = 'No tickets found.';
        td.colSpan = numColumns;
        tr.appendChild(td);
        tableBodyElement.appendChild(tr);
        return;
    }

    tickets.forEach(ticket => {
        const tr = document.createElement('tr');

        const tdId = document.createElement('td');
        tdId.textContent = ticket.id;
        tr.appendChild(tdId);

        const tdTitle = document.createElement('td');
        tdTitle.textContent = ticket.title;
        tr.appendChild(tdTitle);

        const tdDescription = document.createElement('td');
        tdDescription.textContent = ticket.description;
        tr.appendChild(tdDescription);

        const tdStatus = document.createElement('td');
        tdStatus.textContent = ticket.status;
        tr.appendChild(tdStatus);

        if (!isPublicTable) { // Only show 'Public' column for 'My Tickets'
            const tdPublic = document.createElement('td');
            tdPublic.textContent = ticket.public ? 'Yes' : 'No';
            tr.appendChild(tdPublic);
        }

        const tdOwner = document.createElement('td');
        tdOwner.textContent = ticket.owner_name || 'N/A';
        tr.appendChild(tdOwner);

        const tdCompany = document.createElement('td');
        tdCompany.textContent = ticket.owner_company || 'N/A';
        tr.appendChild(tdCompany);

        // Removed Owner ID as we now show Owner Name and Company
        // if (isPublicTable) {
        //     const tdOwnerId = document.createElement('td');
        //     tdOwnerId.textContent = ticket.owner_id;
        //     tr.appendChild(tdOwnerId);
        // }

        tableBodyElement.appendChild(tr);
    });
}

// --- Statistics Functions ---
async function fetchAndDisplayOverallStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats/overall_tickets`);
        if (response.ok) {
            const stats = await response.json();
            overallStatsContent.innerHTML = 
                `Total Tickets: <strong>${stats.total_tickets}</strong><br>
                 Public Tickets: <strong>${stats.public_tickets}</strong><br>
                 Private Tickets: <strong>${stats.private_tickets}</strong>`;
        } else {
            console.error('Failed to fetch overall stats');
            overallStatsContent.textContent = 'Failed to load overall stats.';
        }
    } catch (error) {
        console.error('Error fetching overall stats:', error);
        overallStatsContent.textContent = 'Error loading overall stats.';
    }
}

async function fetchAndDisplayCompanyStats() {
    companyStatsList.innerHTML = '<li>Loading...</li>';
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats/company_tickets`);
        if (response.ok) {
            const stats = await response.json();
            companyStatsList.innerHTML = ''; // Clear loading/previous
            if (stats.length === 0) {
                companyStatsList.innerHTML = '<li>No company data available.</li>';
            } else {
                stats.forEach(companyStat => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${companyStat.company_name}:</strong> ${companyStat.ticket_count} tickets`;
                    companyStatsList.appendChild(li);
                });
            }
        } else {
            console.error('Failed to fetch company stats');
            companyStatsList.innerHTML = '<li>Failed to load company stats.</li>';
        }
    } catch (error) {
        console.error('Error fetching company stats:', error);
        companyStatsList.innerHTML = '<li>Error loading company stats.</li>';
    }
}

async function fetchAndDisplayUserStats() {
    if (!authToken) {
        userStatsDisplay.style.display = 'none';
        return;
    }
    userStatsContent.innerHTML = 'Loading...';
    userStatsDisplay.style.display = 'block'; 

    try {
        const response = await fetch(`${API_BASE_URL}/api/stats/user_ticket_status`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (response.ok) {
            const stats = await response.json();
            userStatsContent.innerHTML = 
                `Open: <strong>${stats.open_tickets}</strong><br>
                 In Progress: <strong>${stats.in_progress_tickets}</strong><br>
                 Closed: <strong>${stats.closed_tickets}</strong>`;
        } else {
            console.error('Failed to fetch user stats');
            userStatsContent.textContent = 'Failed to load your ticket stats.';
        }
    } catch (error) {
        console.error('Error fetching user stats:', error);
        userStatsContent.textContent = 'Error loading your ticket stats.';
    }
}

// --- Chat --- //
sendChatBtn.addEventListener('click', sendChatMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

async function sendChatMessage() {
    const messageText = chatInput.value.trim();
    if (!messageText) return;

    appendMessage(messageText, 'user-message'); // Use 'user-message' class
    chatInput.value = '';
    chatInput.focus();

    try {
        // Display a thinking indicator for the bot
        appendMessage('Bot is thinking...', 'bot-message thinking'); // Use 'bot-message' and 'thinking'

        // Set up headers - include auth token if logged in
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ query: messageText })
        });

        // Remove the thinking indicator
        const thinkingMessage = chatWindow.querySelector('.thinking');
        if (thinkingMessage) {
            chatWindow.removeChild(thinkingMessage);
        }

        if (response.ok) {
            const data = await response.json();
            appendMessage(data.response, 'bot-message'); // Use 'bot-message' class
        } else {
            const errorData = await response.json();
            appendMessage(`Error: ${errorData.detail || 'Failed to get response'}`, 'bot-message'); // Use 'bot-message' class
        }
    } catch (error) {
        console.error('Chat error:', error);
        appendMessage('Error connecting to the chat service.', 'bot-message'); // Use 'bot-message' class
    }
}

function appendMessage(message, className) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message'); // Add base class
    if (className) {
        className.split(' ').forEach(cls => messageDiv.classList.add(cls)); // Add specific classes like 'user-message' or 'bot-message' and 'thinking'
    }
    messageDiv.textContent = message;
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to bottom
}

// --- Initialization --- //
async function fetchAndPopulateUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/users`);
        if (!response.ok) {
            console.error('Failed to fetch users for dropdown');
            userSelectDropdown.innerHTML = '<option value="">Error loading users</option>';
            return;
        }
        const users = await response.json();
        userSelectDropdown.innerHTML = '<option value="">-- Select a User --</option>'; // Default option
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.username;
            option.textContent = user.username;
            userSelectDropdown.appendChild(option);
        });
    } catch (error) {
        console.error('Error fetching users:', error);
        userSelectDropdown.innerHTML = '<option value="">Error loading users</option>';
    }
}

function init() {
    authToken = localStorage.getItem('authToken');
    fetchPublicTickets(); // Always fetch public tickets on load
    fetchAndPopulateUsers(); // Fetch and populate users for the dropdown

    if (authToken) {
        updateUIVisibility(true);
        fetchTickets(); // Fetch user-specific tickets if logged in
        // Role should already be set by login logic if authToken exists
        fetchAndDisplayUserStats(); // Fetch user-specific stats
    } else {
        updateUIVisibility(false);
    }
    fetchAndDisplayOverallStats(); // Fetch overall stats
    fetchAndDisplayCompanyStats(); // Fetch company stats
}

init();
