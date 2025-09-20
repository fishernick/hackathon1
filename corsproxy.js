const express = require('express');
const fetch = require('node-fetch');
const app = express();
const PORT = 25480;
const puppeteer = require('puppeteer');
const TARGET = 'https://purdue.brightspace.com'; 
app.use(express.json());
let sesVal = 1

app.post('/recieve-cookies', (req, res) => {
 sesVal = req.get('d2lSessionVal');
 console.log(`recieved ${sesVal}`)
});

app.post("/login", (req, res) => {
  const { username, password } = req.body;
  (async () => {
  const browser = await puppeteer.launch({
    headless: true, // set false if you want to watch the browser
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Step 1: Open the page with the login link
  await page.goto('https://purdue.brightspace.com', { waitUntil: 'networkidle2' });

  // Step 2: Click the Purdue West Lafayette / Indianapolis login link
  await page.evaluate(() => {
    const link = document.querySelector('a[title="Purdue West Lafayette Login"]');
    if (link) link.click();
  });

  // Step 3: Wait for redirect to login page with username/password fields
  await page.waitForSelector('input#username', { timeout: 30000 });

  // Step 4: Type username and password
  await page.type('input#username', username);
  await page.type('input#password', password);

  // Submit form (press Enter in password field)
  await page.keyboard.press('Enter');

  // Step 5: Wait for redirect after login
  await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 60000 });

  // Step 6: Wait for the verification code div to appear
  await page.waitForSelector('div.verification-code', { timeout: 60000 });

  // Step 7: Extract and log the code
  const code = await page.$eval('div.verification-code', el => el.innerText.trim());
  console.log('Verification code:', code);

  await browser.close();
})();
  
});

app.get('/proxy/*path', async (req, res) => {
  try {
    const pathPart = Array.isArray(req.params.path)
    ? req.params.path.join('/')
    : req.params.path || '';
    const query = req.originalUrl.includes('?') ? req.originalUrl.slice(req.originalUrl.indexOf('?')) : '';
    const pathAndQuery = pathPart + query;
    
    const targetUrl = `${TARGET}/${pathAndQuery}`;
    
    
    console.log(`Proxying: ${targetUrl}`);
    
    const upstreamRes = await fetch(targetUrl, {
      method: 'GET',
      // If you need to forward cookies from the browser to the proxy, do it explicitly.
      // e.g. headers: { Cookie: req.get('Cookie') }
      headers: {
        accept: 'application/json',
        cookie: `d2lSameSiteCanaryA=1; d2lSameSiteCanaryB=1; d2lSessionVal=vxlsiYVwKr3tchPv8O47vRUUG53T8avpCVtt; d2lSecureSessionVal=InDGPhQu9Hn6qS9URLiZAxiPcCIKplDl7pbR`
      },
    });
    
    // copy status
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
    res.status(502).json({ error: 'bad gateway', details: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Proxy listening at http://xennick.com:${PORT}`);
});