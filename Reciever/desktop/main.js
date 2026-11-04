const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs/promises');
const readline = require('node:readline');
const root = path.resolve(__dirname, '..');
let child = null;
let windowRef = null;
function stop() {
  if (!child) return;
  const running = child;
  child = null;
  if (process.platform === 'win32') spawn('taskkill', ['/pid', String(running.pid), '/t', '/f'], { windowsHide: true });
  else { try { process.kill(-running.pid, 'SIGTERM'); } catch { running.kill(); } }
}
function createWindow() {
  windowRef = new BrowserWindow({ width: 1440, height: 960, minWidth: 800, minHeight: 650, backgroundColor: '#090d18', title: 'CarView', webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true } });
  windowRef.loadFile(path.join(__dirname, 'index.html'));
  windowRef.on('closed', () => { stop(); windowRef = null; });
}
ipcMain.handle('find-keys', async () => {
  // Prefer a complete pair from one directory; never inspect key contents here.
  const directories = [...new Set([process.cwd(), path.resolve(root, '..'), root].map(dir => path.resolve(dir)))];
  let partial = null;
  for (const dir of directories) {
    const candidates = {
      senderKey: path.join(dir, 'sender_mldsa_pk.bin'),
      receiverKey: path.join(dir, 'receiver_mldsa_sk.bin'),
    };
    const exists = await Promise.all(Object.values(candidates).map(async file => {
      try { return (await fs.stat(file)).isFile(); } catch { return false; }
    }));
    const found = {
      senderKey: exists[0] ? candidates.senderKey : null,
      receiverKey: exists[1] ? candidates.receiverKey : null,
    };
    if (found.senderKey && found.receiverKey) return found;
    if (!partial && (found.senderKey || found.receiverKey)) partial = found;
  }
  return partial || { senderKey: null, receiverKey: null };
});
ipcMain.handle('choose-file', async () => { const result = await dialog.showOpenDialog(windowRef, { properties: ['openFile'] }); return result.canceled ? null : result.filePaths[0]; });
ipcMain.handle('start-receiver', (_, options) => {
  if (child) throw new Error('The receiver is already running.');
  const python = typeof options.python === 'string' && options.python.trim() ? options.python.trim() : 'python3';
  if (!options.senderKey || !options.receiverKey) throw new Error('Choose both key files first.');
  const executable = path.join(root, 'target', 'release', process.platform === 'win32' ? 'reciever.exe' : 'reciever');
  const proc = spawn(executable, [python, path.join(root, 'worker', 'crypto_worker.py'), path.resolve(root, '..'), options.senderKey, options.receiverKey], { detached: process.platform !== 'win32', windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  child = proc;
  const send = payload => { if (windowRef && !windowRef.isDestroyed()) windowRef.webContents.send('receiver-event', payload); };
  readline.createInterface({ input: proc.stdout }).on('line', line => { try { send(JSON.parse(line)); } catch { send({type:'error', message:'Unexpected response from receiver'}); } });
  proc.stderr.on('data', data => send({type:'diagnostic', message: data.toString().slice(0, 1000)}));
  proc.on('error', err => send({type:'error', message: err.message}));
  proc.on('close', code => { if (child === proc) { child = null; send({type:'stopped', message: `Receiver stopped (exit ${code ?? 'unknown'}).`}); } });
  return true;
});
ipcMain.handle('stop-receiver', () => { stop(); return true; });
app.whenReady().then(createWindow);
app.on('window-all-closed', () => { stop(); app.quit(); });
