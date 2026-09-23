const API_BASE=(window.API_BASE||new URLSearchParams(location.search).get('api')||'').replace(/\/$/,'');
let authMode='login';
let activeUser=null;
const $=id=>document.getElementById(id);
const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

function toast(message,type='info'){const el=document.createElement('div');el.className=`toast ${type}`;el.textContent=message;$('toasts').appendChild(el);setTimeout(()=>el.style.opacity='0',2600);setTimeout(()=>el.remove(),3000)}
function showAuthMessage(message,type='error'){const el=$('auth-message');el.textContent=message;el.className=`form-message visible ${type}`}
function clearAuthMessage(){$('auth-message').className='form-message';$('auth-message').textContent=''}
function setAuthMode(mode){authMode=mode;const register=mode==='register';$('login-tab').classList.toggle('active',!register);$('register-tab').classList.toggle('active',register);$('name-field').classList.toggle('hidden',!register);$('confirm-field').classList.toggle('hidden',!register);$('login-options').classList.toggle('hidden',register);$('demo-login').classList.toggle('hidden',register);$('auth-title').textContent=register?'Create your account':'Welcome back';$('auth-subtitle').textContent=register?'Start building your personal learning workspace.':'Sign in to continue your learning journey.';$('auth-submit').textContent=register?'Create account':'Log in';$('auth-password').autocomplete=register?'new-password':'current-password';$('auth-name').required=register;$('auth-confirm').required=register;clearAuthMessage()}
function togglePassword(){const input=$('auth-password');input.type=input.type==='password'?'text':'password';document.querySelector('.password-toggle').textContent=input.type==='password'?'Show':'Hide'}
function readAccounts(){try{return JSON.parse(localStorage.getItem('studybot_accounts')||'{}')}catch{return {}}}
function saveSession(user,persistent=true){const store=persistent?localStorage:sessionStorage;store.setItem('studybot_session',JSON.stringify(user));activeUser=user;openApp()}
function submitAuth(event){event.preventDefault();clearAuthMessage();const name=$('auth-name').value.trim();const email=$('auth-email').value.trim().toLowerCase();const password=$('auth-password').value;const accounts=readAccounts();if(authMode==='register'){if(name.length<2)return showAuthMessage('Please enter your full name.');if(password!==$('auth-confirm').value)return showAuthMessage('Passwords do not match.');if(accounts[email])return showAuthMessage('An account with this email already exists.');accounts[email]={name,email,password};localStorage.setItem('studybot_accounts',JSON.stringify(accounts));showAuthMessage('Account created. You can log in now.','success');setAuthMode('login');$('auth-email').value=email;$('auth-password').value='';return}const account=accounts[email];if(!account||account.password!==password)return showAuthMessage('Email or password is incorrect. Register first or use the demo account.');saveSession({name:account.name,email:account.email},$('remember-me').checked)}
function demoLogin(){saveSession({name:'Demo Student',email:'demo@studybot.local'},false)}
function logout(){localStorage.removeItem('studybot_session');sessionStorage.removeItem('studybot_session');activeUser=null;$('app-view').classList.add('hidden');$('auth-view').classList.remove('hidden');setAuthMode('login');toast('You have been logged out.','info')}
function openApp(){$('auth-view').classList.add('hidden');$('app-view').classList.remove('hidden');const first=activeUser.name.split(/\s+/)[0];$('user-name').textContent=activeUser.name;$('user-email').textContent=activeUser.email;$('user-avatar').textContent=activeUser.name.charAt(0).toUpperCase();$('greeting-name').textContent=first;loadStatus();refreshDocuments();loadQueryCount()}
function restoreSession(){for(const store of [localStorage,sessionStorage]){try{const session=JSON.parse(store.getItem('studybot_session'));if(session?.email){activeUser=session;openApp();return}}catch{}}}
function toggleSidebar(){$('sidebar').classList.toggle('open');$('sidebar-scrim').classList.toggle('open')}
function userId(){return activeUser?.email||'test-user-001'}
function logDebug(label,data){const log=$('debug-log');const previous=log.textContent==='No requests yet.'?'':log.textContent;log.textContent=`── ${new Date().toLocaleTimeString()} — ${label} ──\n${JSON.stringify(data,null,2)}\n\n${previous}`.slice(0,12000)}
async function apiCall(path,options={}){options.headers=Object.assign({'X-User-Id':userId()},options.headers||{});try{const response=await fetch(API_BASE+path,options);const text=await response.text();let body;try{body=JSON.parse(text)}catch{body=text}logDebug(`${options.method||'GET'} ${path}`,body);return {ok:response.ok,status:response.status,body}}catch(error){logDebug(`${options.method||'GET'} ${path}`,{error:error.message});return {ok:false,status:0,body:{detail:'Unable to reach the backend.'}}}}
async function loadStatus(){const result=await apiCall('/health');if(!result.ok){$('status-pills').innerHTML='<span class="status-pill offline"><i class="status-dot"></i>Backend offline</span>';$('backend-state').innerHTML='<i class="status-dot offline"></i> Backend offline';return}const localValues=new Set(['local','sqlite']);$('status-pills').innerHTML=Object.entries(result.body.backends).map(([key,value])=>{const mode=localValues.has(value)?'local':'remote';return `<span class="status-pill ${mode}" title="${escapeHtml(value)}"><i class="status-dot"></i>${escapeHtml(key.toUpperCase())}</span>`}).join('');const isLocal=Object.values(result.body.backends).every(value=>localValues.has(value));$('backend-state').innerHTML=isLocal?'<i class="status-dot local"></i> Local development mode':'<i class="status-dot remote"></i> AWS services connected'}

const fileInput = $('file');
fileInput.addEventListener('change', event => {
    if (event.target.files[0]) uploadFile(event.target.files[0]);
});

document.querySelector('.chat-input-container').addEventListener('dragover', e => e.preventDefault());
document.querySelector('.chat-input-container').addEventListener('drop', e => {
    e.preventDefault();
    if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
});

async function uploadFile(file) {
    const allowed = ['pdf', 'txt', 'md'];
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (!allowed.includes(ext)) return toast('Only PDF, TXT, and Markdown files are supported.', 'warn');
    if (file.size > 10 * 1024 * 1024) return toast('File is larger than 10 MB.', 'warn');
    
    const chipId = 'chip-' + Date.now();
    const chips = $('upload-chips');
    if(chips) chips.insertAdjacentHTML('beforeend', `
        <div id="${chipId}" class="upload-chip uploading">
            <i class="spinner"></i>
            <span>${escapeHtml(file.name)} — indexing…</span>
        </div>
    `);
    
    const form = new FormData();
    form.append('file', file);
    const result = await apiCall('/upload', { method: 'POST', body: form });
    
    const chip = document.getElementById(chipId);
    if (!result.ok) {
        if(chip) {
            chip.className = 'upload-chip error';
            chip.innerHTML = `<span>${escapeHtml(file.name)} — failed</span><button class="close" onclick="this.parentElement.remove()">×</button>`;
        }
        return toast('Upload failed.', 'error');
    }
    
    const item = result.body;
    if(chip) {
        chip.className = 'upload-chip success';
        chip.innerHTML = `
            <span>✓ ${escapeHtml(item.filename)} · ${Number(item.chars_extracted || 0).toLocaleString()} chars</span>
            <button class="close" onclick="this.parentElement.remove()">×</button>
        `;
    }
    toast(`${item.filename} added.`, 'success');
    fileInput.value = '';
    refreshDocuments();
}
async function ask(){
    const question=$('question').value.trim();
    if(!question)return toast('Enter a question first.','warn');
    
    // Add user message to stream
    const stream = $('chat-stream');
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user';
    userMsg.innerHTML = `<div class="message-bubble">${escapeHtml(question)}</div>`;
    stream.appendChild(userMsg);
    
    // Clear input and show loading
    $('question').value = '';
    $('ask-btn').disabled=true;
    
    const botMsg = document.createElement('div');
    botMsg.className = 'chat-message bot';
    botMsg.innerHTML = `<div class="message-bubble"><i class="spinner"></i> Reading your notes…</div>`;
    stream.appendChild(botMsg);
    stream.scrollTop = stream.scrollHeight;

    const result=await apiCall('/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});
    $('ask-btn').disabled=false;
    
    if(!result.ok){
        botMsg.innerHTML = `<div class="message-bubble upload-error">${escapeHtml(result.body.detail||'The request failed.')}</div>`;
        return;
    }
    
    const data = result.body.data || result.body;
    const status = result.body.status || 'success';
    const citations = data.citations||[];
    
    let badge = '';
    if (status === 'acceptance' || status === 'success') {
        badge = '<span class="status-badge status-acceptance">✓ Grounded</span>';
    } else if (status === 'ambiguous') {
        badge = '<span class="status-badge status-ambiguous">⚠️ Ambiguous</span>';
    } else if (status === 'rejection') {
        badge = '<span class="status-badge status-rejection">❌ Rejection</span>';
    }
    
    let citationsHtml = '';
    if (citations.length > 0) {
        citationsHtml = '<div class="citations">' + citations.map((citation,index)=>`<article class="citation"><div class="citation-head"><span>Source ${citation.citation_id || index+1}</span><span class="score">score ${Number(citation.score||0).toFixed(1)}</span></div><div>${escapeHtml(citation.text||'Source reference')}</div></article>`).join('') + '</div>';
    }
    
    botMsg.innerHTML = `<div class="message-bubble">${badge}<div class="answer-text">${escapeHtml(data.answer)}</div>${citationsHtml}</div>`;
    stream.scrollTop = stream.scrollHeight;
    loadQueryCount();
}
$('question').addEventListener('keydown',event=>{if(event.key==='Enter'&&(event.ctrlKey||event.metaKey)){event.preventDefault();ask()}});
async function refreshDocuments(){const result=await apiCall('/docs/list');const docs=result.ok&&Array.isArray(result.body.docs)?result.body.docs:[];$('document-count').textContent=docs.length;$('docs').innerHTML=docs.length?docs.map(doc=>`<article class="doc-item"><span class="doc-icon">▤</span><strong title="${escapeHtml(doc.filename||doc.doc_id)}">${escapeHtml(doc.filename||doc.doc_id)}</strong><small>${Number(doc.chars||0).toLocaleString()} characters · ${Number(doc.size||0).toLocaleString()} bytes</small></article>`).join(''):'<div class="empty-state"><strong>Your library is empty</strong><span>Upload a document to start learning.</span></div>'}
async function loadQueryCount(){
    const result=await apiCall('/queries/recent?limit=100');
    const queries = result.ok&&Array.isArray(result.body.queries)?result.body.queries:[];
    $('query-count').textContent=queries.length;
    
    // Add to sidebar
    let navList = document.querySelector('.nav-list');
    let historyContainer = document.getElementById('chat-history');
    if (!historyContainer) {
        historyContainer = document.createElement('div');
        historyContainer.id = 'chat-history';
        historyContainer.className = 'chat-history-list';
        navList.appendChild(historyContainer);
    }
    
    if (queries.length > 0) {
        // Simple deduplication for the UI based on query text
        const seen = new Set();
        const deduplicated = [];
        for (const q of queries) {
            if (!seen.has(q.query)) {
                seen.add(q.query);
                deduplicated.push(q);
            }
        }
        
        historyContainer.innerHTML = '<div style="font-size:10px; font-weight:800; color:#94a3b8; text-transform:uppercase; margin: 10px 0 5px 8px; letter-spacing:0.5px;">Recent Chats</div>' + 
            deduplicated.slice(0, 15).map(q => `<div class="chat-history-row">
                <button class="chat-history-item" onclick="loadConversation('${q.id}')" title="${escapeHtml(q.query)}">💬 ${escapeHtml(q.query)}</button>
                <button class="chat-history-delete" onclick="deleteConversation('${q.id}', event)" title="Delete this conversation">×</button>
            </div>`).join('');
    } else {
        historyContainer.innerHTML = '';
    }
}

async function loadConversation(id) {
    const result = await apiCall('/queries/recent?limit=100');
    if (!result.ok) return;
    const queries = result.body.queries || [];
    const found = queries.find(q => String(q.id) === String(id));
    if (found) {
        const stream = $('chat-stream');
        const messages = stream.querySelectorAll('.chat-message:not(.system-message)');
        messages.forEach(m => m.remove());
        
        const userMsg = document.createElement('div');
        userMsg.className = 'chat-message user';
        userMsg.innerHTML = `<div class="message-bubble">${escapeHtml(found.query)}</div>`;
        stream.appendChild(userMsg);
        
        const botMsg = document.createElement('div');
        botMsg.className = 'chat-message bot';
        botMsg.innerHTML = `<div class="message-bubble"><div class="answer-text">${escapeHtml(found.answer)}</div></div>`;
        stream.appendChild(botMsg);
        
        stream.scrollTop = stream.scrollHeight;
    }
}

async function deleteConversation(id, event) {
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
        setTimeout(() => {
            if (!btn.parentElement) return;
            btn.dataset.confirm = "";
            btn.innerHTML = oldHtml;
            btn.style.fontSize = "";
            btn.style.color = "";
            btn.style.width = "";
            btn.style.padding = "";
        }, 3000);
        return;
    }
    
    const result = await apiCall(`/queries/${id}`, {method: 'DELETE'});
    if (result.ok) {
        toast('Conversation deleted', 'success');
        loadQueryCount();
    } else {
        toast('Failed to delete', 'error');
    }
}
restoreSession();
