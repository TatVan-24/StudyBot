const queryApiBase = new URLSearchParams(location.search).get('api');

if (queryApiBase) {
    sessionStorage.setItem('api_base', queryApiBase);
}

const API_BASE = (
    window.API_BASE ||
    queryApiBase ||
    sessionStorage.getItem('api_base') ||
    ''
).replace(/\/$/, '');

const COGNITO_CONFIG = {
    domain: window.STUDYBOT_CONFIG.cognitoDomain,
    clientId: window.STUDYBOT_CONFIG.clientId,
    redirectUri: window.location.origin + window.location.pathname,
    scope: 'openid email profile'
};

function base64UrlEncode(buffer) {
    return btoa(String.fromCharCode(...new Uint8Array(buffer)))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

function generateRandomString(length = 64) {
    const characters =
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';

    const randomValues = new Uint8Array(length);
    crypto.getRandomValues(randomValues);

    return Array.from(
        randomValues,
        value => characters[value % characters.length]
    ).join('');
}

async function loginWithCognito() {
    const state = generateRandomString();
    const codeVerifier = generateRandomString();

    const hash = await crypto.subtle.digest(
        'SHA-256',
        new TextEncoder().encode(codeVerifier)
    );

    const codeChallenge = base64UrlEncode(hash);

    sessionStorage.setItem('oauth_state', state);
    sessionStorage.setItem('oauth_code_verifier', codeVerifier);

    const params = new URLSearchParams({
        client_id: COGNITO_CONFIG.clientId,
        response_type: 'code',
        scope: COGNITO_CONFIG.scope,
        redirect_uri: COGNITO_CONFIG.redirectUri,
        state: state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256'
    });

    const authorizeUrl =
        `https://${COGNITO_CONFIG.domain}.auth.ap-southeast-2.amazoncognito.com/oauth2/authorize?${params}`;

    window.location.href = authorizeUrl;
}

async function handleCognitoCallback() {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const returnedState = params.get('state');

    // Không phải OAuth callback
    if (!code && !returnedState) {
        return;
    }

    if (!code || !returnedState) {
        console.error('Missing OAuth code or state');
        return;
    }

    const savedState = sessionStorage.getItem('oauth_state');
    const codeVerifier = sessionStorage.getItem('oauth_code_verifier');

    // 1. Verify state
    if (!savedState || returnedState !== savedState) {
        console.error('OAuth state mismatch');
        return;
    }

    // 2. PKCE verifier phải tồn tại
    if (!codeVerifier) {
        console.error('Missing PKCE code verifier');
        return;
    }

    try {
        const tokenUrl =
            `https://${COGNITO_CONFIG.domain}.auth.ap-southeast-2.amazoncognito.com/oauth2/token`;

        const body = new URLSearchParams({
            grant_type: 'authorization_code',
            client_id: COGNITO_CONFIG.clientId,
            code: code,
            redirect_uri: COGNITO_CONFIG.redirectUri,
            code_verifier: codeVerifier
        });

        const response = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: body.toString()
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Token exchange failed: ${response.status} ${errorText}`);
        }

        const tokens = await response.json();

        console.log('Cognito tokens received');

        // Lưu token tạm thời
        sessionStorage.setItem(
            'cognito_access_token',
            tokens.access_token
        );

        sessionStorage.setItem(
            'cognito_id_token',
            tokens.id_token
        );

        if (tokens.refresh_token) {
            sessionStorage.setItem(
                'cognito_refresh_token',
                tokens.refresh_token
            );
        }

        // Không cần code/state nữa
        sessionStorage.removeItem('oauth_state');
        sessionStorage.removeItem('oauth_code_verifier');

        // Xóa ?code=...&state=... khỏi URL
        window.history.replaceState(
            {},
            document.title,
            COGNITO_CONFIG.redirectUri
        );

        // Tạm thời tạo active user từ ID token
        const payload = JSON.parse(
            atob(
                tokens.id_token
                    .split('.')[1]
                    .replace(/-/g, '+')
                    .replace(/_/g, '/')
            )
        );

        activeUser = {
            id: payload.sub,
            name: payload.name || (payload.email ? payload.email.split('@')[0] : 'Student'),
            email: payload.email,
            username: payload['cognito:username'] || payload.email
        };

        console.log('Authenticated user:', activeUser);

        openApp();

    } catch (error) {
        console.error('Cognito callback failed:', error);
    }
}

let authMode='login';
let activeUser=null;
const $=id=>document.getElementById(id);
const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

// ═══════════════════════════════════════════════════════════
// [Phase 5] Session State + localStorage
// ═══════════════════════════════════════════════════════════
const SESSION_KEY = 'studybot_current_session';
let currentSessionId = null;

// [Security] Debug chỉ bật khi chạy local
const IS_LOCAL = ['localhost', '127.0.0.1'].includes(location.hostname);

if (!IS_LOCAL) {
    // Production: xóa debug panel khỏi DOM
    document.addEventListener('DOMContentLoaded', () => {
        const panel = document.getElementById('debug-panel');
        if (panel) panel.remove();
    });
}


function getStoredSessionId() {
    return localStorage.getItem(SESSION_KEY);
}

function saveSessionId(sessionId) {
    if (!sessionId) return;
    currentSessionId = sessionId;
    localStorage.setItem(SESSION_KEY, sessionId);
}

function clearSessionId() {
    currentSessionId = null;
    localStorage.removeItem(SESSION_KEY);
}

function toast(message,type='info'){const el=document.createElement('div');el.className=`toast ${type}`;el.textContent=message;$('toasts').appendChild(el);setTimeout(()=>el.style.opacity='0',2600);setTimeout(()=>el.remove(),3000)}
function showAuthMessage(message,type='error'){const el=$('auth-message');el.textContent=message;el.className=`form-message visible ${type}`}
function clearAuthMessage(){$('auth-message').className='form-message';$('auth-message').textContent=''}
function setAuthMode(mode){authMode=mode;const register=mode==='register';$('login-tab').classList.toggle('active',!register);$('register-tab').classList.toggle('active',register);$('name-field').classList.toggle('hidden',!register);$('confirm-field').classList.toggle('hidden',!register);$('login-options').classList.toggle('hidden',register);$('demo-login').classList.toggle('hidden',register);$('auth-title').textContent=register?'Create your account':'Welcome back';$('auth-subtitle').textContent=register?'Start building your personal learning workspace.':'Sign in to continue your learning journey.';$('auth-submit').textContent=register?'Create account':'Log in';$('auth-password').autocomplete=register?'new-password':'current-password';$('auth-name').required=register;$('auth-confirm').required=register;clearAuthMessage()}
function togglePassword(){const input=$('auth-password');input.type=input.type==='password'?'text':'password';document.querySelector('.password-toggle').textContent=input.type==='password'?'Show':'Hide'}
function readAccounts(){try{return JSON.parse(localStorage.getItem('studybot_accounts')||'{}')}catch{return {}}}
function saveSession(user,persistent=true){const store=persistent?localStorage:sessionStorage;store.setItem('studybot_session',JSON.stringify(user));activeUser=user;openApp()}
function submitAuth(event){event.preventDefault();clearAuthMessage();const name=$('auth-name').value.trim();const email=$('auth-email').value.trim().toLowerCase();const password=$('auth-password').value;const accounts=readAccounts();if(authMode==='register'){if(name.length<2)return showAuthMessage('Please enter your full name.');if(password!==$('auth-confirm').value)return showAuthMessage('Passwords do not match.');if(accounts[email])return showAuthMessage('An account with this email already exists.');accounts[email]={name,email,password};localStorage.setItem('studybot_accounts',JSON.stringify(accounts));showAuthMessage('Account created. You can log in now.','success');setAuthMode('login');$('auth-email').value=email;$('auth-password').value='';return}const account=accounts[email];if(!account||account.password!==password)return showAuthMessage('Email or password is incorrect. Register first or use the demo account.');saveSession({name:account.name,email:account.email},$('remember-me').checked)}
function demoLogin(){saveSession({name:'Demo Student',email:'demo@studybot.local'},false)}
function logout(){
    localStorage.removeItem('studybot_session');
    sessionStorage.removeItem('studybot_session');
    clearSessionId();
    activeUser=null;
    $('app-view').classList.add('hidden');
    $('auth-view').classList.remove('hidden');
    setAuthMode('login');
    toast('You have been logged out.','info');
}
async function openApp(){
    if (IS_LOCAL) document.body.classList.add('is-local');

    $('auth-view').classList.add('hidden');
    $('app-view').classList.remove('hidden');
    const first=activeUser.name.split(/\s+/)[0];
    $('user-name').textContent=activeUser.name;
    $('user-email').textContent=activeUser.email;
    $('user-avatar').textContent=activeUser.name.charAt(0).toUpperCase();
    $('greeting-name').textContent=first;

    currentSessionId = getStoredSessionId();

    loadStatus();
    refreshDocuments();
    loadSessions();

    if (currentSessionId) {
        loadSession(currentSessionId);
    } else {
        await createSession();
        showWelcomeCard();
    }
}
function restoreSession(){for(const store of [localStorage,sessionStorage]){try{const session=JSON.parse(store.getItem('studybot_session'));if(session?.email){activeUser=session;openApp();return}}catch{}}}
function toggleSidebar(){$('sidebar').classList.toggle('open');$('sidebar-scrim').classList.toggle('open')}
function userId(){return activeUser?.email||'test-user-001'}
function logDebug(label,data){
    if (!IS_LOCAL) return;
    const log=$('debug-log');const previous=log.textContent==='No requests yet.'?'':log.textContent;log.textContent=`── ${new Date().toLocaleTimeString()} — ${label} ──\n${JSON.stringify(data,null,2)}\n\n${previous}`.slice(0,12000)
}

async function apiCall(path, options = {}) {
    const accessToken = sessionStorage.getItem('cognito_access_token');

    options.headers = Object.assign(
        {
            'Content-Type': 'application/json',
            ...(accessToken
                ? { 'Authorization': `Bearer ${accessToken}` }
                : {})
        },
        options.headers || {}
    );

    try {
        const response = await fetch(API_BASE + path, options);
        const text = await response.text();

        let body;
        try {
            body = JSON.parse(text);
        } catch {
            body = text;
        }

        logDebug(`${options.method || 'GET'} ${path}`, body);

        return {
            ok: response.ok,
            status: response.status,
            body
        };
    } catch (error) {
        logDebug(`${options.method || 'GET'} ${path}`, {
            error: error.message
        });

        return {
            ok: false,
            status: 0,
            body: {
                detail: 'Unable to reach the backend.'
            }
        };
    }
}

async function loadStatus() {
    const result = await apiCall('/sessions');

    if (!result.ok) {
        $('status-pills').innerHTML =
            '<span class="status-pill offline">' +
            '<i class="status-dot"></i>Backend offline</span>';

        $('backend-state').innerHTML =
            '<i class="status-dot offline"></i> Backend offline';

        return;
    }

    $('status-pills').innerHTML =
        '<span class="status-pill remote">' +
        '<i class="status-dot"></i>AWS API</span>';

    $('backend-state').innerHTML =
        '<i class="status-dot remote"></i> AWS services connected';
}

async function createSession() {
    const result = await apiCall('/sessions', {
        method: 'POST',
        body: JSON.stringify({
            title: 'New Session'
        })
    });

    if (!result.ok) {
        console.error('Failed to create session:', result.status, result.body);
        toast('Failed to create a new session.', 'error');
        return null;
    }

    const session = result.body;
    const sessionId = session.session_id || session.session?.session_id;

    if (!sessionId) {
        console.error('Session ID missing from response:', result.body);
        toast('Invalid session response.', 'error');
        return null;
    }

    saveSessionId(sessionId);
    return sessionId;
}

const fileInput = $('file');
fileInput.addEventListener('change', event => {
    if (event.target.files.length) enqueueFiles(Array.from(event.target.files));
    fileInput.value = '';
});

document.querySelector('.chat-input-container').addEventListener('dragover', e => e.preventDefault());
document.querySelector('.chat-input-container').addEventListener('drop', e => {
    e.preventDefault();
    if (e.dataTransfer.files.length) enqueueFiles(Array.from(e.dataTransfer.files));
});

// ═══════════════════════════════════════════════════════════
// Upload Queue — serialize uploads, sort by size
// ═══════════════════════════════════════════════════════════
const MAX_FILES_PER_SESSION = 10;
let uploadQueue = [];
let isUploading = false;

function enqueueFiles(files) {
    const allowed = ['pdf', 'txt', 'md'];
    const valid = [];

    for (const f of files) {
        const ext = (f.name.split('.').pop() || '').toLowerCase();
        if (!allowed.includes(ext)) {
            toast(`Skipped ${f.name}: only PDF, TXT, MD are supported.`, 'warn');
            continue;
        }
        if (f.size > 10 * 1024 * 1024) {
            toast(`Skipped ${f.name}: exceeds 10 MB.`, 'warn');
            continue;
        }
        valid.push(f);
    }

    if (valid.length === 0) return;

    // Đếm slot còn lại (bao gồm cả file đang chờ trong queue)
    const currentCount = parseInt($('document-count').textContent || '0', 10);
    const pendingCount = uploadQueue.length + (isUploading ? 1 : 0);
    const remaining = MAX_FILES_PER_SESSION - currentCount - pendingCount;

    if (remaining <= 0) {
        toast(`Session is full (${MAX_FILES_PER_SESSION} docs). Create a new session to upload more.`, 'warn');
        return;
    }

    if (valid.length > remaining) {
        toast(`Only ${remaining} slots left in this session. Processing first ${remaining} files.`, 'warn');
        valid.length = remaining;
    }

    // Sort nhỏ trước để phản hồi nhanh
    valid.sort((a, b) => a.size - b.size);

    uploadQueue.push(...valid);

    if (!isUploading) {
        processUploadQueue();
    }
}

async function processUploadQueue() {
    if (isUploading) return;
    isUploading = true;

    while (uploadQueue.length > 0) {
        const file = uploadQueue.shift();
        try {
            await uploadFile(file);
        } catch (err) {
            console.error('Queue item failed', file.name, err);
        }
    }

    isUploading = false;
}

async function uploadFile(file) {
    const allowed = ['pdf', 'txt', 'md'];
    const ext = (file.name.split('.').pop() || '').toLowerCase();

    if (!allowed.includes(ext)) {
        return toast('Only PDF, TXT, and Markdown files are supported.', 'warn');
    }

    if (file.size > 10 * 1024 * 1024) {
        return toast('File is larger than 10 MB.', 'warn');
    }

    const contentTypes = {
        pdf: 'application/pdf',
        txt: 'text/plain',
        md: 'text/markdown',
    };

    const contentType = contentTypes[ext];

    const chipId = 'chip-' + Date.now();
    const chips = $('upload-chips');

    if (chips) {
        chips.insertAdjacentHTML('beforeend', `
            <div id="${chipId}" class="upload-chip uploading">
                <i class="spinner"></i>
                <span>${escapeHtml(file.name)} — uploading…</span>
            </div>
        `);
    }

    try {
        // ------------------------------------------------------------
        // Step 1: Ask API Gateway/Lambda for a presigned S3 POST
        // ------------------------------------------------------------
        const prepareResult = await apiCall('/documents/uploads', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: file.name,
                content_type: contentType,
            }),
        });

        const chip = document.getElementById(chipId);

        if (!prepareResult.ok) {
            if (chip) {
                chip.className = 'upload-chip error';
                chip.innerHTML = `
                    <span>❌ ${escapeHtml(file.name)} — failed</span>
                    <button class="close" onclick="this.parentElement.remove()">×</button>
                `;
            }

            const detail =
                (prepareResult.body && (
                    prepareResult.body.error ||
                    prepareResult.body.detail
                )) ||
                'Failed to prepare upload.';

            toast(detail, 'error');
            return false;
        }

        const uploadInfo = prepareResult.body;

        // ------------------------------------------------------------
        // Step 2: Upload the actual file directly to S3
        // ------------------------------------------------------------
        const s3Form = new FormData();

        Object.entries(uploadInfo.fields || {}).forEach(([key, value]) => {
            s3Form.append(key, value);
        });

        s3Form.append('file', file);

        if (chip) {
            chip.innerHTML = `
                <i class="spinner"></i>
                <span>${escapeHtml(file.name)} — uploading to S3…</span>
            `;
        }

        const s3Response = await fetch(uploadInfo.upload_url, {
            method: 'POST',
            body: s3Form,
        });

        if (!s3Response.ok) {
            if (chip) {
                chip.className = 'upload-chip error';
                chip.innerHTML = `
                    <span>❌ ${escapeHtml(file.name)} — S3 upload failed</span>
                    <button class="close" onclick="this.parentElement.remove()">×</button>
                `;
            }

            toast('File upload to S3 failed.', 'error');
            return false;
        }

        // ------------------------------------------------------------
        // Step 3: Poll document lifecycle
        // ------------------------------------------------------------
        const documentId = uploadInfo.document_id;

        if (chip) {
            chip.innerHTML = `
                <i class="spinner"></i>
                <span>${escapeHtml(file.name)} — processing…</span>
            `;
        }

        const finalDocument = await pollDocumentStatus(documentId, chipId);

        if (!finalDocument) {
            return false;
        }

        if (finalDocument.status === 'ACTIVE') {
            if (chip) {
                chip.className = 'upload-chip success';
                chip.innerHTML = `
                    <span>✓ ${escapeHtml(file.name)} — ready</span>
                `;
            }

            if (currentSessionId) {
                const attachResult = await apiCall(
                    `/sessions/${encodeURIComponent(currentSessionId)}/documents/${encodeURIComponent(documentId)}`,
                    {
                        method: 'POST'
                    }
                );

                if (!attachResult.ok) {
                    console.error(
                        'Failed to attach document to session:',
                        attachResult.status,
                        attachResult.body
                    );
                    toast('Document is ready, but could not attach it to the session.', 'error');
                    return false;
                }
            }

            refreshDocuments();
            loadSessions();
            return true;
        }

        // FAILED
        if (chip) {
            chip.className = 'upload-chip error';
            chip.innerHTML = `
                <span>❌ ${escapeHtml(file.name)} — processing failed</span>
                <button class="close" onclick="this.parentElement.remove()">×</button>
            `;
        }

        toast(`${file.name} processing failed.`, 'error');
        return false;

    } catch (err) {
        console.error('Upload failed:', err);

        const chip = document.getElementById(chipId);

        if (chip) {
            chip.className = 'upload-chip error';
            chip.innerHTML = `
                <span>❌ ${escapeHtml(file.name)} — failed</span>
                <button class="close" onclick="this.parentElement.remove()">×</button>
            `;
        }

        toast('Upload failed. Please try again.', 'error');
        return false;
    }
}

function renderAnswer(text) {
    let html = escapeHtml(text);
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    html = html.replace(/\n\n+/g, '</p><p>');
    if (!html.startsWith('<')) html = '<p>' + html + '</p>';
    html = html.replace(/<p><ul>/g, '<ul>').replace(/<\/ul><\/p>/g, '</ul>');
    return html;
}

function showWelcomeCard() {
    const el = document.getElementById('welcome-message');
    if (el) el.style.display = 'flex';
}

function hideWelcomeCard() {
    const el = document.getElementById('welcome-message');
    if (el) el.style.display = 'none';
}

function clearChatStream() {
    const stream = $('chat-stream');
    const messages = stream.querySelectorAll('.chat-message:not(.system-message)');
    messages.forEach(m => m.remove());
}

function getStatusBadge(status) {
    if (status === 'acceptance' || status === 'success') {
        return '<span class="status-badge status-acceptance">✓ Grounded</span>';
    } else if (status === 'ambiguous') {
        return '<span class="status-badge status-ambiguous">⚠️ Ambiguous</span>';
    } else if (status === 'rejection') {
        return '<span class="status-badge status-rejection">❌ Rejection</span>';
    } else if (status === 'refusal') {
        return '<span class="status-badge status-refusal">⊘ Refusal</span>';
    }
    return '';
}

function newChat() {
    clearSessionId();
    clearChatStream();
    showWelcomeCard();
    const input = $('question');
    if (input) {
        input.value = '';
        input.focus();
    }
    loadSessions();
    toast('New chat ready. Upload a document to start.', 'info');
}

const JOB_STATES = {
    POLLING: 'POLLING',
    SUCCESS: 'SUCCESS',
    FAILED: 'FAILED',
    HTTP_ERROR: 'HTTP_ERROR',
    TIMEOUT: 'TIMEOUT'
};

function getJobState(response) {
    // API request itself failed: 4xx / 5xx / unexpected HTTP status
    if (!response.ok) {
        return {
            state: JOB_STATES.HTTP_ERROR,
            response
        };
    }

    const job = response.body;

    if (!job || !job.status) {
        return {
            state: JOB_STATES.HTTP_ERROR,
            error: 'Invalid job response: missing status'
        };
    }

    // Job completed successfully
    if (job.result) {
        return {
            state: JOB_STATES.SUCCESS,
            job
        };
    }

    // Job completed with an error
    if (job.error_message) {
        return {
            state: JOB_STATES.FAILED,
            job
        };
    }

    // Any valid non-terminal job state
    return {
        state: JOB_STATES.POLLING,
        job
    };
}

async function pollJob(jobId, {
    intervalMs = 2000,
    timeoutMs = 60000
} = {}) {
    const startedAt = Date.now();

    while (Date.now() - startedAt < timeoutMs) {
        const response = await apiCall(
            `/jobs/${encodeURIComponent(jobId)}`
        );

        const result = getJobState(response);

        if (result.state === JOB_STATES.SUCCESS) {
            return result;
        }

        if (result.state === JOB_STATES.FAILED) {
            return result;
        }

        if (result.state === JOB_STATES.HTTP_ERROR) {
            return result;
        }

        await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    return {
        state: JOB_STATES.TIMEOUT,
        error: `Job ${jobId} timed out after ${timeoutMs}ms`
    };
}

async function ask(){
    const question = $('question').value.trim();
    if (!question) return toast('Enter a question first.', 'warn');

    if (!currentSessionId) {
        return toast('Please upload your documents before asking.', 'warn');
    }

    hideWelcomeCard();

    const stream = $('chat-stream');

    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user';
    userMsg.innerHTML = `<div class="message-bubble">${escapeHtml(question)}</div>`;
    stream.appendChild(userMsg);

    $('question').value = '';
    $('ask-btn').disabled = true;

    const botMsg = document.createElement('div');
    botMsg.className = 'chat-message bot';
    botMsg.innerHTML = `
        <div class="message-bubble">
            <i class="spinner"></i> Reading your notes…
        </div>
    `;
    stream.appendChild(botMsg);
    stream.scrollTop = stream.scrollHeight;

    // Step 1: Create async answer job
    const result = await apiCall(
        `/sessions/${encodeURIComponent(currentSessionId)}/questions`,
        {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: question
            })
        }
    );

    if (!result.ok) {
        $('ask-btn').disabled = false;

        botMsg.innerHTML = `
            <div class="message-bubble upload-error">
                ${escapeHtml(result.body?.detail || 'The request failed.')}
            </div>
        `;
        return;
    }

    const jobId = result.body?.job_id;

    if (!jobId) {
        $('ask-btn').disabled = false;

        botMsg.innerHTML = `
            <div class="message-bubble upload-error">
                The server did not return a job ID.
            </div>
        `;
        return;
    }

    // Step 2: Poll job until it reaches a terminal state
    const jobResult = await pollJob(jobId);

    $('ask-btn').disabled = false;

    // Step 3: Handle polling/request failure
    if (jobResult.state === JOB_STATES.HTTP_ERROR) {
        const detail =
            jobResult.response?.body?.detail ||
            jobResult.error ||
            'Failed to check the job status.';

        botMsg.innerHTML = `
            <div class="message-bubble upload-error">
                ${escapeHtml(detail)}
            </div>
        `;
        return;
    }

    if (jobResult.state === JOB_STATES.FAILED) {
        const errorMessage =
            jobResult.job?.error_message ||
            'The request could not be completed.';

        botMsg.innerHTML = `
            <div class="message-bubble upload-error">
                ${escapeHtml(errorMessage)}
            </div>
        `;
        return;
    }

    if (jobResult.state === JOB_STATES.TIMEOUT) {
        botMsg.innerHTML = `
            <div class="message-bubble upload-error">
                The request is taking longer than expected. Please try again later.
            </div>
        `;
        return;
    }

    // Step 4: Job completed successfully
    const metadata = jobResult.job.result || {};

    const status = metadata.status || 'acceptance';
    const answer = metadata.answer || '';
    const citations = metadata.citations || [];
    const reason = metadata.reason || '';

    if (
        status === 'rejection' &&
        reason.toLowerCase().includes('session')
    ) {
        clearSessionId();
        toast('Session has expired. Please upload again.', 'warn');
        showWelcomeCard();
        botMsg.remove();
        return;
    }

    // Step 5: Existing rendering logic
    const badge = getStatusBadge(status);

    let citationsHtml = '';

    if (citations.length > 0) {
        citationsHtml =
            '<div class="citations">' +
                citations.map((citation, index) => {
                // Chỉ hiển thị score nếu Backend thực sự trả về
                const scoreHtml = (citation.score != null)
                    ? `<span class="score">score ${Number(citation.score).toFixed(2)}</span>`
                    : '';

                return `
                <article class="citation">
                    <div class="citation-head">
                        <span>
                            Source ${citation.citation_id || index + 1}
                        </span>
                        ${scoreHtml}
                    </div>
                    <div>
                        ${escapeHtml(citation.text || 'Source reference')}
                    </div>
                </article>
                `;
            }).join('') +
            '</div>';
    }

    botMsg.innerHTML = `
        <div class="message-bubble">
            ${badge}
            <div class="answer-text">${renderAnswer(answer)}</div>
            ${citationsHtml}
        </div>
    `;

    stream.scrollTop = stream.scrollHeight;
    loadSessions();
}
$('question').addEventListener('keydown',event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();ask()}});
let allDocs = [];

async function refreshDocuments() {
    const result = await apiCall('/documents');
    allDocs = result.ok && Array.isArray(result.body.documents) ? result.body.documents : [];
    $('document-count').textContent = allDocs.length;
    renderDocs(allDocs);
}

function renderDocs(docsToRender) {
    if (!docsToRender.length) {
        $('docs').innerHTML = '<div class="empty-state"><strong>Your library is empty</strong><span>Upload a document to start learning.</span></div>';
        return;
    }
    $('docs').innerHTML = docsToRender.map(doc => `
        <article class="doc-item" style="position: relative; padding-right: 140px;">
            <span class="doc-icon">▤</span>
            <strong title="${escapeHtml(doc.filename || doc.doc_id)}">${escapeHtml(doc.filename || doc.doc_id)}</strong>
            <small>${Number(doc.chars || 0).toLocaleString()} characters · ${Number(doc.size || 0).toLocaleString()} bytes</small>
            <div style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); display: flex; gap: 8px;">
                <button onclick="detachDoc('${doc.document_id}')" class="button compact" style="background: #fef08a; color: #854d0e; border: 1px solid #fde047;" title="Detach from session">Detach</button>
                <button onclick="deleteDocGlobal('${doc.document_id}')" class="button compact" style="background: #fee2e2; color: #991b1b; border: 1px solid #fecaca;" title="Delete permanently">Delete</button>
            </div>
        </article>
    `).join('');
}

function filterDocs() {
    const q = $('doc-search').value.toLowerCase();
    const filtered = allDocs.filter(d => (d.filename || d.doc_id).toLowerCase().includes(q));
    renderDocs(filtered);
}

async function detachDoc(docId) {
    if (!confirm('Detach this document from the current session? (It will not be deleted from the system)')) return;
    if (!currentSessionId) return toast('No active session.', 'error');
    const res = await apiCall(
        '/sessions/' + encodeURIComponent(currentSessionId) +
        '/documents/' + encodeURIComponent(docId),
        { method: 'DELETE' }
    );
    if (res.ok) {
        toast('Document detached from session.', 'success');
        refreshDocuments();
    } else {
        toast('Error: ' + (res.body?.detail || res.body?.reason || ''), 'error');
    }
}

async function deleteDocGlobal(docId) {
    if (!confirm('Permanently delete this document from the system? (SQLite, Vector DB, Disk)')) return;
    const res = await apiCall(
        '/documents/' + encodeURIComponent(docId),
        { method: 'DELETE' }
    );
    if (res.ok) {
        toast('Document permanently deleted.', 'success');
        refreshDocuments();
    } else {
        toast('Error: ' + (res.body?.detail || res.body?.reason || ''), 'error');
    }
}

function showPanel(panelName) {
    const chatEls = document.querySelectorAll('.hero-panel, .chat-stream, .upload-chips, .chat-input-container');
    const libPanel = document.querySelector('.library-panel');
    const progPanel = document.querySelector('.progress-panel');

    chatEls.forEach(el => el.style.display = (panelName === 'workspace' ? '' : 'none'));
    if (libPanel) libPanel.style.display = (panelName === 'library' ? 'block' : 'none');
    if (progPanel) progPanel.style.display = (panelName === 'progress' ? 'block' : 'none');

    document.querySelectorAll('.nav-list .nav-item').forEach(el => el.classList.remove('active'));
    const btn = document.getElementById('nav-' + panelName);
    if (btn) btn.classList.add('active');

    if (panelName === 'library') refreshDocuments();
    if (panelName === 'progress') loadProgress();
}

let statusChartInstance = null;

async function loadProgress() {
    const res = await apiCall('/progress/summary');
    if (!res.ok) return toast('Failed to load progress', 'error');
    const data = res.body;

    $('prog-queries').textContent = data.total_queries || 0;
    $('prog-sessions').textContent = data.total_sessions || 0;
    $('prog-p50').textContent = data.latency_p50 || 0;
    $('prog-p95').textContent = data.latency_p95 || 0;

    const rqList = $('recent-queries-list');
    rqList.innerHTML = (data.recent_queries || []).map(q => 
        `<li style="padding: 10px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
            <div style="font-weight: 600; font-size: 13px;">${escapeHtml(q.query)}</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(q.answer)}</div>
        </li>`
    ).join('') || '<li style="color: #64748b; font-size: 13px;">No recent queries</li>';

    const ctx = document.getElementById('statusChart');
    if (statusChartInstance) statusChartInstance.destroy();
    if (ctx && window.Chart) {
        const dist = data.status_distribution || {};
        statusChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Acceptance', 'Ambiguous', 'Rejection', 'Refusal'],
                datasets: [{
                    label: 'Status Distribution (%)',
                    data: [dist.acceptance || 0, dist.ambiguous || 0, dist.rejection || 0, dist.refusal || 0],
                    backgroundColor: ['rgba(34, 197, 94, 0.2)', 'rgba(234, 179, 8, 0.2)', 'rgba(239, 68, 68, 0.2)', 'rgba(59, 130, 246, 0.2)'],
                    borderColor: ['rgb(34, 197, 94)', 'rgb(234, 179, 8)', 'rgb(239, 68, 68)', 'rgb(59, 130, 246)'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });
    }
}

async function loadSessions() {
    const result = await apiCall('/sessions');
    const sessions = result.ok && Array.isArray(result.body.sessions) ? result.body.sessions : [];

    $('query-count').textContent = sessions.length;

    let navList = document.querySelector('.nav-list');
    let container = document.getElementById('chat-history');
    if (!container) {
        container = document.createElement('div');
        container.id = 'chat-history';
        container.className = 'chat-history-list';
        navList.appendChild(container);
    }

    if (sessions.length === 0) {
        container.innerHTML = `
            <div class="session-empty">
                <span>No sessions yet</span>
                <small>Upload a document to start</small>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="session-header">
            <span>SESSIONS</span>
        </div>
        ${sessions.map(s => {
            const isActive = s.session_id === currentSessionId;
            const title = s.title || 'Untitled';
            return `
                <div class="session-row ${isActive ? 'active' : ''}">
                    <button class="session-item"
                            onclick="loadSession('${s.session_id}')"
                            title="${escapeHtml(title)}">
                        <span class="session-icon">📄</span>
                        <span class="session-title">${escapeHtml(title)}</span>
                    </button>
                    <button class="session-delete"
                            onclick="deleteSession('${s.session_id}', event)"
                            title="Delete session">×</button>
                </div>
            `;
        }).join('')}
    `;
}

async function loadSession(sessionId) {
    if (!sessionId) return;

    const result = await apiCall(`/sessions/${sessionId}`);

    if (!result.ok) {
        clearSessionId();
        toast('Session does not exist. Reset.', 'warn');
        showWelcomeCard();
        loadSessions();
        return;
    }

    saveSessionId(sessionId);
    clearChatStream();

    const turns = result.body.turns || [];

    if (turns.length === 0) {
        showWelcomeCard();
    } else {
        const stream = $('chat-stream');
        turns.forEach(turn => {
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-message user';
            userMsg.innerHTML = `<div class="message-bubble">${escapeHtml(turn.query)}</div>`;
            stream.appendChild(userMsg);

            const botMsg = document.createElement('div');
            botMsg.className = 'chat-message bot';
            const badge = getStatusBadge(turn.status);
            botMsg.innerHTML = `
                <div class="message-bubble">
                    ${badge}
                    <div class="answer-text">${renderAnswer(turn.answer || '')}</div>
                </div>
            `;
            stream.appendChild(botMsg);
        });
        stream.scrollTop = stream.scrollHeight;
    }

    loadSessions();
}

async function deleteSession(sessionId, event) {
    if (event) event.stopPropagation();
    const btn = event.currentTarget;

    if (!btn.dataset.confirm) {
        btn.dataset.confirm = "true";
        const oldHtml = btn.innerHTML;
        btn.innerHTML = "Sure?";
        btn.style.fontSize = "10px";
        btn.style.color = "#b91c1c";
        btn.style.width = "auto";
        btn.style.padding = "0 8px";
        btn.style.opacity = "1";

        setTimeout(() => {
            if (!btn.parentElement) return;
            btn.dataset.confirm = "";
            btn.innerHTML = oldHtml;
            btn.style.fontSize = "";
            btn.style.color = "";
            btn.style.width = "";
            btn.style.padding = "";
            btn.style.opacity = "";
        }, 3000);
        return;
    }

    const result = await apiCall(`/sessions/${sessionId}`, {method: 'DELETE'});

    if (!result.ok) {
        toast('Failed to delete session', 'error');
        return;
    }

    toast('Session deleted', 'success');

    if (sessionId === currentSessionId) {
        clearSessionId();
        clearChatStream();
        showWelcomeCard();
    }

    loadSessions();
}

async function pollDocumentStatus(documentId, chipId) {
    const POLL_INTERVAL_MS = 2000;
    const MAX_WAIT_MS = 5 * 60 * 1000;

    const startedAt = Date.now();

    while (Date.now() - startedAt < MAX_WAIT_MS) {
        try {
            const result = await apiCall(`/documents/${encodeURIComponent(documentId)}`, {
                method: 'GET',
            });

            const chip = document.getElementById(chipId);

            if (!result.ok) {
                console.error(
                    'Failed to get document status:',
                    result.status,
                    result.body
                );

                if (chip) {
                    chip.className = 'upload-chip error';
                    chip.innerHTML = `
                        <span>❌ Failed to check ${escapeHtml(documentId)}</span>
                        <button class="close" onclick="this.parentElement.remove()">×</button>
                    `;
                }

                toast('Failed to check document status.', 'error');
                return null;
            }

            const documentData = result.body && result.body.document;

            if (!documentData) {
                console.error('Document response missing document:', result.body);
                toast('Invalid document status response.', 'error');
                return null;
            }

            const status = documentData.status;

            // --------------------------------------------------------
            // Terminal state: ingestion succeeded
            // --------------------------------------------------------
            if (status === 'ACTIVE') {
                return documentData;
            }

            // --------------------------------------------------------
            // Terminal state: ingestion failed
            // --------------------------------------------------------
            if (status === 'FAILED') {
                console.error('Document processing failed:', documentData);

                return documentData;
            }

            // --------------------------------------------------------
            // Non-terminal states
            // --------------------------------------------------------
            if (
                status === 'UPLOADING' ||
                status === 'INGEST_QUEUED' ||
                status === 'PROCESSING'
            ) {
                if (chip) {
                    const statusText = {
                        UPLOADING: 'uploading…',
                        INGEST_QUEUED: 'queued for processing…',
                        PROCESSING: 'processing…',
                    }[status];

                    chip.innerHTML = `
                        <i class="spinner"></i>
                        <span>${escapeHtml(documentData.filename)} — ${statusText}</span>
                    `;
                }

                await new Promise(resolve =>
                    setTimeout(resolve, POLL_INTERVAL_MS)
                );

                continue;
            }

            // --------------------------------------------------------
            // Unknown state
            // --------------------------------------------------------
            console.error('Unknown document status:', status);
            toast(`Unknown document status: ${status}`, 'error');
            return null;

        } catch (err) {
            console.error('Error polling document status:', err);
            toast('Failed to check document status.', 'error');
            return null;
        }
    }

    // ------------------------------------------------------------
    // Timeout
    // ------------------------------------------------------------
    console.error(
        `Document ${documentId} did not become terminal within 5 minutes.`
    );

    const chip = document.getElementById(chipId);

    if (chip) {
        chip.className = 'upload-chip error';
        chip.innerHTML = `
            <span>⚠ ${escapeHtml(documentId)} — processing timeout</span>
            <button class="close" onclick="this.parentElement.remove()">×</button>
        `;
    }

    toast('Document processing is taking too long.', 'warn');

    return null;
}

// restoreSession();

(async function initApp() {
    const params = new URLSearchParams(window.location.search);

    if (params.has('code') || params.has('state')) {
        await handleCognitoCallback();
        return;
    }

    restoreSession();
})();
