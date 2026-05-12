const express = require('express');
const basicAuth = require('express-basic-auth');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Basic auth - change these credentials
const users = {};
const userList = (process.env.DASHBOARD_USERS || 'admin:nutriobox2026').split(',');
userList.forEach(u => {
  const [user, pass] = u.split(':');
  if (user && pass) users[user] = pass;
});

// Apply basic auth
app.use(basicAuth({
  users: users,
  challenge: true,
  realm: 'Nutriobox Dashboard'
}));

// Serve static files from public folder
app.use(express.static(path.join(__dirname, 'public')));

// Default route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Nutriobox Dashboard running on port ${PORT}`);
});
