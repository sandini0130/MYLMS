// Initialize active tab based on user role
window.onload = function () {
  const userRole = document.body.dataset.userRole;

  if (userRole === 'admin') {
      showTab('admin-home');
  } else if (userRole === 'instructor') {
      showTab('instructor-home');
  } else if (userRole === 'student') {
      showTab('student-home');
  }

  // Add active class to the default tab link
  const defaultTab = `${userRole}-home`;
  const defaultLink = document.querySelector(`[onclick="showTab('${defaultTab}')"]`);
  if (defaultLink) {
      defaultLink.classList.add('active');
  }

  // Load saved quizzes from localStorage on page load
  loadQuizzesFromLocalStorage();
};

// Function to switch between tabs
function showTab(tabName) {
  // Hide all tabs
  const tabs = document.querySelectorAll('.tab-content');
  tabs.forEach(tab => {
      tab.classList.remove('active');
      tab.classList.add('hidden');
  });

  // Show selected tab
  const selectedTab = document.getElementById(tabName);
  if (selectedTab) {
      selectedTab.classList.add('active');
      selectedTab.classList.remove('hidden');
  }

  // Update active state of navigation links
  const links = document.querySelectorAll('.tab-link');
  links.forEach(link => {
      link.classList.remove('active');
  });

  // Add active class to clicked link
  const selectedLink = document.querySelector(`[onclick="showTab('${tabName}')"]`);
  if (selectedLink) {
      selectedLink.classList.add('active');
  }

  // Handle special logic for specific tabs
  handleTabSpecificLogic(tabName);
}

// Handle tab-specific logic
function handleTabSpecificLogic(tabName) {
  if (tabName === 'student-messages') {
      initializeMessagesTab(); // Load messaging features
      document.querySelector('#student-messages').style.display = 'block';
  } else {
      // Hide messaging features when not in the Messages tab
      document.querySelector('#student-messages').style.display = 'none';
  }
}

// Messaging Feature

let selectedUserId = null;

// Initialize the Messages tab logic
function initializeMessagesTab() {
  fetchUsers(); // Fetch users when the Messages tab is loaded
  const sendButton = document.getElementById('chat-send');
  if (sendButton) {
      sendButton.addEventListener('click', sendMessage);
  }
}

// Fetch users for the messaging feature
async function fetchUsers() {
  try {
      const response = await fetch('/get_users');
      const users = await response.json();

      const userList = document.getElementById('user-list');
      userList.innerHTML = '';

      users.forEach(user => {
          const li = document.createElement('li');
          li.textContent = `${user.first_name} ${user.last_name}`;
          li.classList.add('user-list-item');
          li.addEventListener('click', () => {
              selectedUserId = user.user_id;
              highlightSelectedUser(li);
              loadChat();
          });
          userList.appendChild(li);
      });
  } catch (error) {
      console.error('Error fetching users:', error);
  }
}

// Highlight the selected user
function highlightSelectedUser(selectedLi) {
  const userListItems = document.querySelectorAll('.user-list li');
  userListItems.forEach(item => {
      item.classList.remove('selected'); // Remove highlight from all users
  });
  selectedLi.classList.add('selected'); // Highlight the clicked user
}

// Load chat history for the selected user
async function loadChat() {
  if (!selectedUserId) return;

  try {
      const response = await fetch(`/get_chat?receiver_id=${selectedUserId}`);
      const messages = await response.json();

      const chatHistory = document.getElementById('chat-history');
      chatHistory.innerHTML = '';

      messages.forEach(msg => {
          const div = document.createElement('div');
          div.className = msg.sender_id === parseInt(document.body.dataset.userId) ? 'sender' : 'receiver';
          div.textContent = msg.message_text;
          chatHistory.appendChild(div);
      });

      chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll to the latest message
  } catch (error) {
      console.error('Error loading chat:', error);
  }
}

// Send a message to the selected user
async function sendMessage() {
  const chatInput = document.getElementById('chat-input');
  const messageText = chatInput.value.trim();

  if (!messageText || !selectedUserId) return;

  try {
      await fetch('/send_message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ receiver_id: selectedUserId, message_text: messageText })
      });

      chatInput.value = '';
      loadChat();
  } catch (error) {
      console.error('Error sending message:', error);
  }
}
