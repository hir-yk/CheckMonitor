const express = require('express');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// 状態管理
let monitorProcess = null;
let lastOutputs = []; // recent stdout/stderr
const MAX_LOG_LINES = 200;

// Helper: push log line (keep bounded length)
function pushLog(line) {
  lastOutputs.push(line);
  if (lastOutputs.length > MAX_LOG_LINES) lastOutputs.shift();
}

// Helper: find a Python executable on Windows
function findPythonCommand() {
  // prefer 'py' launcher on Windows, fallback to 'python', 'python3'
  return process.env.PYTHON || 'py' || 'python' || 'python3';
}

// Start monitoring. body: { continuous, directory, change_threshold, prefix, interval, confirm_area }
// returns 409 if already running
app.post('/api/start', (req, res) => {
  if (monitorProcess) {
    return res.status(409).json({ error: 'monitor already running', pid: monitorProcess.pid });
  }

  const args = [];
  const body = req.body || {};

  // Map allowed options to CheckMonitor.py CLI args
  if (body.continuous) args.push('-c');
  if (body.directory) {
    args.push('-d', String(body.directory));
  }
  if (body.change_threshold !== undefined) {
    args.push('-t', String(body.change_threshold));
  }
  if (body.prefix) {
    args.push('-p', String(body.prefix));
  }
  if (body.interval !== undefined) {
    args.push('-i', String(body.interval));
  }
  if (body.confirm_area) args.push('-ca');

  // Prefer using 'py' on Windows; allow override by env PYTHON
  const pythonCmd = findPythonCommand();

  // Spawn python process with CheckMonitor.py; ensure cwd is repo root
  const scriptPath = path.join(__dirname, 'CheckMonitor.py');

  // Ensure Python stdout/stderr use UTF-8 to avoid console encoding errors on Windows
  const spawnEnv = Object.assign({}, process.env, { PYTHONIOENCODING: 'utf-8' });

  try {
    monitorProcess = spawn(pythonCmd, [scriptPath, ...args], {
      cwd: __dirname,
      windowsHide: false,
      env: spawnEnv
    });
  } catch (e) {
    monitorProcess = null;
    return res.status(500).json({ error: 'failed to spawn process', detail: String(e) });
  }

  monitorProcess.stdout.on('data', (buf) => {
    const text = buf.toString();
    text.split(/\r?\n/).forEach(line => { if (line) pushLog({ t: Date.now(), src: 'out', text: line }); });
  });
  monitorProcess.stderr.on('data', (buf) => {
    const text = buf.toString();
    text.split(/\r?\n/).forEach(line => { if (line) pushLog({ t: Date.now(), src: 'err', text: line }); });
  });
  monitorProcess.on('exit', (code, signal) => {
    pushLog({ t: Date.now(), src: 'sys', text: `process exited code=${code} signal=${signal}` });
    monitorProcess = null;
  });

  pushLog({ t: Date.now(), src: 'sys', text: `started process pid=${monitorProcess.pid}` });

  return res.json({ ok: true, pid: monitorProcess.pid });
});

// Stop monitoring
app.post('/api/stop', (req, res) => {
  if (!monitorProcess) return res.status(409).json({ error: 'not running' });

  try {
    // On Windows, child.kill() will send SIGTERM equivalent; fallback to taskkill if necessary
    monitorProcess.kill();
    pushLog({ t: Date.now(), src: 'sys', text: 'requested kill to monitor process' });
    return res.json({ ok: true });
  } catch (e) {
    return res.status(500).json({ error: 'failed to stop', detail: String(e) });
  }
});

// Status and recent logs
app.get('/api/status', (req, res) => {
  return res.json({
    running: !!monitorProcess,
    pid: monitorProcess ? monitorProcess.pid : null,
    logs: lastOutputs.slice(-MAX_LOG_LINES)
  });
});

// List snapshots in a directory. Query: ?dir=<relative_dir>
// If no dir provided, try to read monitor_config.json last_directory; otherwise default to current timestamp dir name
app.get('/api/snapshots', (req, res) => {
  let dir = req.query.dir;
  if (!dir) {
    // try to read monitor_config.json
    try {
      const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, 'monitor_config.json')));
      if (cfg && cfg.last_directory) dir = cfg.last_directory;
    } catch (e) {
      // ignore
    }
  }
  if (!dir) dir = ''; // root if not found
  const fullDir = path.resolve(__dirname, dir);
  if (!fullDir.startsWith(path.resolve(__dirname))) {
    return res.status(400).json({ error: 'invalid directory' });
  }
  if (!fs.existsSync(fullDir) || !fs.statSync(fullDir).isDirectory()) {
    return res.json({ files: [] });
  }
  const items = fs.readdirSync(fullDir).filter(f => \/\.(png|jpg|jpeg|gif)$/i.test(f)).map(f => ({
    name: f,
    url: `/snapshots/${encodeURIComponent(path.relative(__dirname, fullDir))}/${encodeURIComponent(f)}`
  }));
  return res.json({ dir: path.relative(__dirname, fullDir), files: items });
});

// Serve snapshot files: /snapshots/:dir/:file
app.get('/snapshots/:dir/:file', (req, res) => {
  const relDir = req.params.dir || '';
  const file = req.params.file;
  const fullDir = path.resolve(__dirname, relDir);
  if (!fullDir.startsWith(path.resolve(__dirname))) return res.status(400).send('invalid path');
  const fullPath = path.join(fullDir, file);
  if (!fs.existsSync(fullPath)) return res.status(404).send('not found');
  return res.sendFile(fullPath);
});

app.listen(port, () => {
  console.log(`CheckMonitor Web UI server running at http://localhost:${port}`);
});