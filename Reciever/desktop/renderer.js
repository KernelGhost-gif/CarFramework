const $ = id => document.getElementById(id);
let frames = 0;
let running = false;
let errors = 0;
let collapsedOnConnect = false;

function setConnectionPanel(open) {
  const panel = $('connection-panel');
  const toggle = $('connection-toggle');
  if (!open && panel.contains(document.activeElement)) toggle.focus();
  panel.inert = !open;
  $('connection-shell').classList.toggle('collapsed', !open);
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', open ? 'Hide connection panel' : 'Show connection panel');
  toggle.title = open ? 'Hide connection panel' : 'Show connection panel';
}
$('connection-toggle').addEventListener('click', () => {
  setConnectionPanel($('connection-toggle').getAttribute('aria-expanded') !== 'true');
});

function setStatus(title, detail, state = '') {
  $('receiver-status').textContent = title;
  $('receiver-detail').textContent = detail;
  $('status-dot').className = `status-dot ${state}`;
}
function setRunning(value) {
  running = value;
  $('start').disabled = value;
  $('stop').disabled = !value;
  for (const id of ['sender-select', 'receiver-select', 'python']) $(id).disabled = value;
}
function clearFeed() {
  $('frame').hidden = true;
  $('placeholder').hidden = false;
  $('feed-tag').textContent = 'OFFLINE';
}
for (const name of ['sender', 'receiver']) {
  $(`${name}-select`).addEventListener('click', async () => {
    const selected = await window.receiver.chooseFile();
    if (selected) $(`${name}-key`).value = selected;
  });
}
// Do not overwrite a key the user selected while discovery was running.
window.receiver.findKeys().then(keys => {
  if (keys.senderKey && !$('sender-key').value) $('sender-key').value = keys.senderKey;
  if (keys.receiverKey && !$('receiver-key').value) $('receiver-key').value = keys.receiverKey;
  if (keys.senderKey && keys.receiverKey && !running) setStatus('Offline', 'Keys detected · ready to connect');
}).catch(() => {});

$('start').addEventListener('click', async () => {
  try {
    setRunning(true);
    frames = 0; errors = 0; collapsedOnConnect = false;
    $('frame-count').textContent = 'No frames received';
    setStatus('Starting', 'Preparing connection');
    await window.receiver.start({ senderKey: $('sender-key').value, receiverKey: $('receiver-key').value, python: $('python').value });
  } catch (error) { setRunning(false); setStatus('Error', error.message, 'error'); }
});
$('stop').addEventListener('click', async () => {
  await window.receiver.stop();
  setRunning(false); clearFeed(); setStatus('Offline', 'Stopped by user'); setConnectionPanel(true);
});
window.receiver.onEvent(event => {
  if (event.type === 'frame') {
    frames++;
    $('frame').src = 'data:image/avif;base64,' + event.data;
    $('frame').hidden = false; $('placeholder').hidden = true;
    $('feed-tag').textContent = 'LIVE';
    $('frame-count').textContent = `${frames} frame${frames === 1 ? '' : 's'} received`;
    setStatus('Connected', 'Receiving video frames', 'connected');
  } else if (event.type === 'status') {
    const connected = event.message.startsWith('Connected');
    setStatus(connected ? 'Connected' : 'Listening', event.message, connected ? 'connected' : '');
    if (connected && !collapsedOnConnect) { collapsedOnConnect = true; setConnectionPanel(false); }
  } else if (event.type === 'frame_error') {
    errors++;
    setStatus('Frame error', `${event.message} (${errors} failed)`, 'error');
  } else if (event.type === 'error') {
    setStatus('Error', event.message, 'error'); setConnectionPanel(true);
  } else if (event.type === 'diagnostic') {
    setStatus('Receiver', event.message, 'error');
  } else if (event.type === 'stopped' && running) {
    setRunning(false); clearFeed(); setConnectionPanel(true);
    if ($('receiver-status').textContent !== 'Error') setStatus('Offline', event.message);
  }
});
$('frame').addEventListener('error', () => { $('feed-tag').textContent = 'ERROR'; setStatus('Decode error', 'The received frame could not be displayed as AVIF.', 'error'); });
