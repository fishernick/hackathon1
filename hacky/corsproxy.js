const express = require('express');
const app = express();
const PORT = 25480;
const path = require("path");
const puppeteer = require('puppeteer');
const { exec } = require("child_process");
const TARGET = 'https://purdue.brightspace.com'; 
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./people.db');
app.use(express.static(path.join(__dirname, "public")));

// Store active sessions
const activeSessions = new Map();

// Global cookie storage for proxy
let globalCookies = {
  d2lSessionVal: null,
  d2lSecureSessionVal: null
};

app.use(express.static(path.join(__dirname, "public")));

// Disable CORS for all routes
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, d2lSessionVal');
  res.header('Access-Control-Allow-Credentials', 'true');
  
  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

app.use(express.json());

// Generate unique session ID
function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Dashboard route - serve thea HTML file
app.get("/dashboard.html", (req, res) => {
  res.sendFile(path.join(__dirname, "dashboard.html"));
});

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "LoginPage.html"));
});

app.post("/login", async (req, res) => {
  const { username, password } = req.body;
  
  if (!username || !password) {
    return res.status(400).json({ success: false, error: 'Username and password required' });
  }

  const sessionId = generateSessionId();
  let browser = null;
  let page = null;

  try {
    browser = await puppeteer.launch({
      headless: true, 
      args: ['--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-features=WebAuthn,WebAuth',
    '--disable-webauthn']
    });

    page = await browser.newPage();

    // Step 1: Open the page with the login link
    await page.goto('https://purdue.brightspace.com/d2l/lp/auth/saml/initiate-login?entityId=https://idp.purdue.edu/idp/shibboleth&target=%2fd2l%2fhome%2f6824', { waitUntil: 'networkidle2' });

    // Step 2: Wait for redirect to login page with username/password fields
    await page.waitForSelector('input#username', { timeout: 30000 });
 
    // Step 3: Type username and password
    await page.type('input#username', username, { delay: 3 });
    await page.type('input#password', password, { delay: 3 });

    // Submit form (press Enter in password field)
    await page.keyboard.press('Enter');

    // Step 4: Wait for redirect after login
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 60000 });

    // Step 5: Wait for the verification code div to appear
    await page.waitForSelector('div.verification-code', { timeout: 60000 });

    // Step 6: Extract the code
    const code = await page.$eval('div.verification-code', el => el.innerText.trim());

    // Store the session data
    activeSessions.set(sessionId, {
      browser,
      page,
      code,
      timestamp: Date.now(),
      username
    });
    console.log(`Login successful for user ${username}, session ID: ${sessionId}`);

    // Step 7: Send the code and session ID back to the client
    res.json({ 
      success: true, 
      code, 
      sessionId 
    });

    // After successful login, update the crime map
    exec("python3 /Users/nick/Documents/hacky/CrimeMap/main.py", (error, stdout, stderr) => {
      if (error) {
        console.error(`Crime map update error: ${error}`);
      } else {
      }
    });

    // Wait for authentication to complete in the background
    page.waitForSelector('body.d2l-body', { timeout: 60000 }).then(async () => {
      try {
        const cookies = await page.cookies();
        const d2lSessionCookie = cookies.find(cookie => cookie.name === 'd2lSessionVal');
        const d2lSecureSessionCookie = cookies.find(cookie => cookie.name === 'd2lSecureSessionVal');
        
        if (d2lSessionCookie && d2lSecureSessionCookie) {
          // Store cookies globally for proxy use
          globalCookies.d2lSessionVal = d2lSessionCookie.value;
          globalCookies.d2lSecureSessionVal = d2lSecureSessionCookie.value;
        }
      } catch (error) {
        console.error('Error extracting cookies:', error);
      }
    }).catch(console.error);

  } catch (error) {
    console.error('Login error:', error);
    
    // Clean up browser if there was an error
    if (browser) {
      try {
        await browser.close();
      } catch (closeError) {
        console.error('Error closing browser:', closeError);
      }
    }
    
    res.status(500).json({ 
      success: false, 
      error: error.message 
    });
  }
});

app.get("/dblogin", async (req, res) => {
  try {
    let cookieHeader = req.headers.cookie || '';
    if (cookieHeader) {
      cookieHeader += '; d2lSameSiteCanaryA=1; d2lSameSiteCanaryB=1';
    } else {
      cookieHeader = 'd2lSameSiteCanaryA=1; d2lSameSiteCanaryB=1';
    }

    const response = await fetch(
      "http://localhost:25480/proxy/d2l/api/lp/1.32/users/whoami",
      { credentials: 'include', headers: { 'cookie': cookieHeader } }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch whoami: ${response.status}`);
    }

    const userData = await response.json();

    // Insert or update user in DB
    const user = await ensureUser(userData);

    res.json({ success: true, user });
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ success: false, error: error.message });
  }
});
// Fixed proxy route
app.get('/proxy/*path', async (req, res) => {
  try {
    // Extract the path after /proxy/
    const pathPart = req.originalUrl.substring(7) || '';
    
    const targetUrl = `${TARGET}/${pathPart}`;
    console.log(`Proxying: ${targetUrl}`);
    
    // Always use cookies from the incoming request
    let cookieHeader = req.headers.cookie || '';
    // Always add SameSiteCanary headers
    if (cookieHeader) {
      cookieHeader += '; d2lSameSiteCanaryA=1; d2lSameSiteCanaryB=1';
    } else {
      cookieHeader = 'd2lSameSiteCanaryA=1; d2lSameSiteCanaryB=1';
    }
    
    
    const upstreamRes = await fetch(targetUrl, {
      method: req.method,
      headers: {
        'accept': 'application/json',
        'cookie': cookieHeader,
        'user-agent': req.get('user-agent') || 'Mozilla/5.0 (compatible; proxy-server)',
        'content-type': req.get('content-type') || 'application/json'
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined
    });
    
    res.status(upstreamRes.status);
    
    // copy safe headers
    upstreamRes.headers.forEach((v, k) => {
      if (!['transfer-encoding', 'connection', 'content-encoding'].includes(k.toLowerCase())) {
        res.set(k, v);
      }
    });
    
    const body = await upstreamRes.text();
    res.send(body);
  } catch (err) {
    console.error('Proxy error:', err);
    res.status(502).json({ error: 'Bad gateway', details: err.message });
  }
});

app.get('/get-cookies/:sessionId', async (req, res) => {
  const sessionId = req.params.sessionId;
  
  if (!sessionId || !activeSessions.has(sessionId)) {
    return res.status(404).json({ success: false, error: 'Session not found' });
  }

  try {
    const session = activeSessions.get(sessionId);
    const { page } = session;

    // Check if we're on the Brightspace page (after successful auth)
    const url = page.url();
    if (!url.includes('brightspace.com') || !url.includes('/d2l/')) {
      return res.json({ success: false, ready: false, message: 'Authentication not complete yet' });
    }

    // Get cookies from the page
    const cookies = await page.cookies();
    const d2lSessionCookie = cookies.find(cookie => cookie.name === 'd2lSessionVal');
    const d2lSecureSessionCookie = cookies.find(cookie => cookie.name === 'd2lSecureSessionVal');

    if (d2lSessionCookie && d2lSecureSessionCookie) {
      console.log(`Cookies retrieved for session ${sessionId}`);
      
      // Store cookies globally for proxy use
      globalCookies.d2lSessionVal = d2lSessionCookie.value;
      globalCookies.d2lSecureSessionVal = d2lSecureSessionCookie.value;
      
      return res.json({
        success: true,
        ready: true,
        cookies: {
          d2lSessionVal: d2lSessionCookie.value,
          d2lSecureSessionVal: d2lSecureSessionCookie.value,
          domain: d2lSessionCookie.domain,
          path: d2lSecureSessionCookie.path
        }
      });
    } else {
      return res.json({ success: false, ready: false, message: 'Cookies not available yet' });
    }

  } catch (error) {
    console.error('Error retrieving cookies:', error);
    return res.status(500).json({ success: false, error: error.message });
  }
});

function ensureUser(userData) {
  return new Promise((resolve, reject) => {
    db.get(
      "SELECT * FROM users WHERE id = ?",
      [userData.Identifier],
      (err, row) => {
        if (err) return reject(err);

        if (row) {
          // User already exists
          return resolve(row);
        }

        // Insert new user
        db.run(
          `INSERT INTO users (id, first_name, last_name, pronouns, unique_name, profile_identifier)
           VALUES (?, ?, ?, ?, ?, ?)`,
          [
            userData.Identifier,
            userData.FirstName,
            userData.LastName,
            userData.Pronouns || null,
            userData.UniqueName,
            userData.ProfileIdentifier,
          ],
          function (err) {
            if (err) return reject(err);
            resolve({
              id: userData.Identifier,
              ...userData,
            });
          }
        );
      }
    );
  });
}

app.post('/cleanup-session/:sessionId', async (req, res) => {
  const sessionId = req.params.sessionId;
  
  if (activeSessions.has(sessionId)) {
    const session = activeSessions.get(sessionId);
    if (session.browser) {
      await session.browser.close();
    }
    activeSessions.delete(sessionId);
    console.log(`Session ${sessionId} cleaned up`);
  }
  
  res.json({ success: true });
});

// Get all friends for a user
app.get('/get-friends', async (req, res) => {
  try {
    const { user_id } = req.query;
    
    if (!user_id) {
      return res.status(400).json({ success: false, error: 'user_id is required' });
    }
    
    const query = `
      SELECT CASE 
        WHEN user_id_1 = ? THEN user_id_2 
        ELSE user_id_1 
      END as friend_id 
      FROM friendships 
      WHERE (user_id_1 = ? OR user_id_2 = ?) 
      AND status = 'accepted'
    `;
    
    const friends = await db.query(query, [user_id, user_id, user_id]);
    res.json({ success: true, friends });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});
// Search users by query (first name, last name, or unique_name)
app.get('/search-users', (req, res) => {
  const query = req.query.query?.trim();
  
  if (!query || query.length < 2) {
    return res.json({ success: true, users: [] }); // keep parity with frontend behavior
  }

  const sql = `
    SELECT id, first_name, last_name, unique_name, profile_identifier 
    FROM users
    WHERE first_name LIKE ? 
       OR last_name LIKE ? 
       OR unique_name LIKE ?
    LIMIT 20
  `;

  const likeQuery = `%${query}%`;
  db.all(sql, [likeQuery, likeQuery, likeQuery], (err, rows) => {
    if (err) {
      console.error("Search error:", err);
      return res.status(500).json({ success: false, error: "Database error" });
    }

    if (!rows || rows.length === 0) {
      return res.json({ success: true, users: [] });
    }

    res.json({ success: true, users: rows });
  });
});

// Check if two users are friends
app.post('/check-friends', async (req, res) => {
  try {
    const { user_id_1, user_id_2 } = req.body;
    
    if (!user_id_1 || !user_id_2) {
      return res.status(400).json({ success: false, error: 'user_id_1 and user_id_2 are required' });
    }
    
    const query = `
      SELECT 1 
      FROM friendships 
      WHERE ((user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)) 
      AND status = 'accepted'
    `;
    
    const result = await db.query(query, [user_id_1, user_id_2, user_id_2, user_id_1]);
    const areFriends = result.length > 0;
    
    res.json({ success: true, are_friends: areFriends });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// Add friendship request
app.post('/add-friends', async (req, res) => {
  try {
    const { user_id_1, user_id_2 } = req.body;
    console.log(`Add friend request from ${user_id_1} to ${user_id_2}`);
    if (!user_id_1 || !user_id_2) {
      return res.status(400).json({ success: false, error: 'user_id_1 and user_id_2 are required' });
    }
    
    if (user_id_1 === user_id_2) {
      return res.status(400).json({ success: false, error: 'Cannot add yourself as friend' });
    }
    
    // Order user IDs to maintain consistency (smaller ID first)
    const minUserId = Math.min(user_id_1, user_id_2);
    const maxUserId = Math.max(user_id_1, user_id_2);
    
    const query = `
      INSERT INTO friendships (user_id_1, user_id_2, status) 
      VALUES (?, ?, 'pending')
    `;
    
    await db.query(query, [minUserId, maxUserId]);
    res.json({ success: true, message: 'Friend request sent' });
  } catch (error) {
    // Handle duplicate friendship attempts
    if (error.code === 'ER_DUP_ENTRY' || error.code === '23000') {
      return res.status(409).json({ success: false, error: 'Friendship already exists' });
    }
    res.status(500).json({ success: false, error: error.message });
  }
});



app.post('/food', async (req, res) => {
  const userInput = req.body;
  
  // Pass input as command line argument
  const inputArgs = JSON.stringify(userInput).replace(/"/g, '\\"');
  
  exec(`python3 /Users/nick/Documents/hacky/DiningDecider.py "${inputArgs}"`, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error}`);
      return res.status(500).json({ error: 'Script execution failed' });
    }
    
    if (stderr) {
      console.error(`Python stderr: ${stderr}`);
    }
    
    // stdout contains your string - just trim whitespace
    const result = stdout.trim();
    
    res.json({ 
      success: true, 
      message: result,
      cookies: globalCookies 
    });
  });
});
// Clean up expired sessions (every 10 minutes)
setInterval(() => {
  const now = Date.now();
  const expiredSessions = [];
  
  for (const [sessionId, session] of activeSessions.entries()) {
    // Sessions expire after 15 minutes
    if (now - session.timestamp > 15 * 60 * 1000) {
      expiredSessions.push(sessionId);
    }
  }
  
  for (const sessionId of expiredSessions) {
    const session = activeSessions.get(sessionId);
    if (session && session.browser) {
      session.browser.close().catch(console.error);
    }
    activeSessions.delete(sessionId);
    console.log(`Cleaned up expired session: ${sessionId}`);
  }
}, 10 * 60 * 1000);

app.listen(PORT, () => {
  console.log(`Server listening at http://localhost:${PORT}`);
  console.log(`Dashboard: http://localhost:${PORT}/dashboard.html`);
  console.log(`Login: http://localhost:${PORT}/`);
});