// Pull x.com cookies (incl. httpOnly auth_token) from a running Chrome started with
// --remote-debugging-port. Needs Node 22+ (native WebSocket).
//
// Strategy:
//   1) Browser endpoint  ws://127.0.0.1:<port>/devtools/browser  -> Storage.getCookies
//      (works for a normal user whose debug port isn't held by another CDP client)
//   2) Fallback: if the browser endpoint is occupied (e.g. a long-running CDP proxy holds
//      it), grab a page target id from a local proxy's /targets and connect to that page's
//      ws -> Network.getCookies (page-level connections can run concurrently).
//
// Env: CDP_PORT (default 9222), PROXY_PORT (default 3456, for the fallback target list).

const CDP_PORT = process.env.CDP_PORT || '9222';
const PROXY_PORT = process.env.PROXY_PORT || '3456';
const X_DOMAIN = /(^|\.)(x|twitter)\.com$/;

function emit(cookies) {
  const list = cookies.filter(c => X_DOMAIN.test(c.domain));
  const pick = {};
  for (const c of list) pick[c.name] = c.value;
  if (!pick.auth_token || !pick.ct0) {
    console.error('未拿到 auth_token/ct0(Chrome 是否已登录 x.com?)');
    process.exit(1);
  }
  console.log(JSON.stringify({
    auth_token: pick.auth_token,
    ct0: pick.ct0,
    all_names: [...new Set(list.map(c => c.name))],
    cookieHeader: list.map(c => `${c.name}=${c.value}`).join('; '),
  }));
  process.exit(0);
}

function cdp(wsUrl, method, params, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    const t = setTimeout(() => { try { ws.close(); } catch {} reject(new Error('timeout')); }, timeoutMs);
    ws.addEventListener('open', () => ws.send(JSON.stringify({ id: 1, method, params })));
    ws.addEventListener('message', ev => {
      clearTimeout(t);
      const m = JSON.parse(ev.data);
      if (m.error) reject(new Error(JSON.stringify(m.error)));
      else resolve(m.result);
      try { ws.close(); } catch {}
    });
    ws.addEventListener('error', e => { clearTimeout(t); reject(new Error(e.message || 'ws error')); });
  });
}

async function viaBrowser() {
  const r = await cdp(`ws://127.0.0.1:${CDP_PORT}/devtools/browser`, 'Storage.getCookies', {}, 5000);
  return r.cookies || [];
}

async function viaPage() {
  // discover a page target id from the local proxy's target list
  const res = await fetch(`http://localhost:${PROXY_PORT}/targets`);
  const targets = await res.json();
  const page = (Array.isArray(targets) ? targets : targets.targets || []).find(t => t.type === 'page');
  if (!page) throw new Error('no page target available');
  const r = await cdp(`ws://127.0.0.1:${CDP_PORT}/devtools/page/${page.targetId}`,
                      'Network.getCookies', { urls: ['https://x.com', 'https://twitter.com'] }, 5000);
  return r.cookies || [];
}

try {
  let cookies;
  try { cookies = await viaBrowser(); }
  catch (e) { cookies = await viaPage(); }
  emit(cookies);
} catch (e) {
  console.error('cookie 抠取失败:', e.message);
  process.exit(1);
}
