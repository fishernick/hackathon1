const express = require('express');
const app = express();
const PORT = 25480;
const path = require("path");
const puppeteer = require('puppeteer');
const { exec, execFile } = require("child_process");
const TARGET = 'https://purdue.brightspace.com'; 
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
    //exec("/Users/nick/PycharmProjects/ItDoesntMatterIDontCare/.venv/lib/python3.13 /ItDoesntMatterIDontCare/main.py", (error, stdout, stderr) => {
    exec("python3 /Users/nick/Documents/hacky/ItDoesntMatterIDontCare/main.py", (error, stdout, stderr) => {
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

app.post('/food', async (req, res) => {
  const userInput = req.body;
  
  // Pass input as command line argument using execFile to avoid shell escaping issues on Windows
  const inputArg = JSON.stringify(userInput);

  // Use the 'py' launcher on Windows to run the script; pass the JSON as a single argument
  execFile('py', ['C:\\Users\\Nick Fisher\\Desktop\\hacky\\DiningDecider.py', inputArg], (error, stdout, stderr) => {
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