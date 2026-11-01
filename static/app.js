(() => {
'use strict';
const $ = (s,scope=document)=>scope.querySelector(s);
const $$ = (s,scope=document)=>[...scope.querySelectorAll(s)];
const els = {overlay:$('#overlay'), modal:$('#modalBody'), form:$('#createForm'), btn:$('#submitBtn')};
const titles = {violet:'THE VISIONARY',navy:'THE EXECUTIVE',forest:'THE NATURAL',coral:'THE CREATIVE'};
let chosenType = 'cv', chosenTheme = 'violet', currentOrder = null, config = null;
const escapeHtml = (s) => String(s??'').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function formData(){return Object.fromEntries(new FormData(els.form).entries());}
function fail(s){const e=$('#formError');e.textContent=s;e.hidden=false;e.scrollIntoView({block:'nearest',behavior:'smooth'});}
function clearFail(){$('#formError').hidden=true;}
async function call(path, init={}){
 const resp=await fetch(path, {headers:{'Content-Type':'application/json',...(init.headers||{})}, ...init});
 let data;try{data=await resp.json();}catch{throw new Error('The server did not respond correctly.');}
 if(!resp.ok)throw new Error(data.error||'Something went wrong.');return data;
}
function openModal(markup){els.modal.innerHTML=markup;els.overlay.hidden=false;document.body.style.overflow='hidden';$('#closeModal').focus();}
function closeModal(){els.overlay.hidden=true;document.body.style.overflow='';els.modal.innerHTML='';}
$('#closeModal').addEventListener('click',closeModal);
els.overlay.addEventListener('click',e=>{if(e.target===els.overlay)closeModal();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!els.overlay.hidden)closeModal();});
function setType(type){chosenType=type;$('#cvFields').hidden=type!=='cv';$('#letterFields').hidden=type!=='letter';$('#cvTab').classList.toggle('active',type==='cv');$('#letterTab').classList.toggle('active',type==='letter');updatePreview();}
$('#cvTab').addEventListener('click',()=>setType('cv'));$('#letterTab').addEventListener('click',()=>setType('letter'));
$$('[data-theme]').forEach(b=>b.addEventListener('click',()=>{
 chosenTheme=b.dataset.theme;
 $$('[data-theme]').forEach(b2=>b2.classList.toggle('selected',b===b2));
 $('#livePreview').className='live-paper '+chosenTheme;
 $('#previewTheme').textContent=titles[chosenTheme];
 updatePreview();
}));
function updatePreview(){
 const d=formData();const get=(v,fall)=>v?.trim()||fall;
 $('#lpName').textContent=get(d.fullName,'YOUR NAME').toUpperCase();
 $('#lpHeadline').textContent=chosenType==='cv'?get(d.headline,'Your professional headline'):'APPLICATION LETTER · '+get(d.jobTitle,'Your next opportunity');
 $('#lpContact').textContent=[get(d.email,'you@example.com'),d.phone,d.location].filter(Boolean).join('  ·  ');
 const sections=$$('.lp-section');
 if(chosenType==='cv'){
   sections[0].textContent='PROFILE'; sections[1].textContent='EXPERIENCE';sections[2].textContent='SKILLS & EDUCATION';
   $('#lpSummary').textContent=get(d.summary,'Your story belongs here. Add your details to bring this design to life.');
   $('#lpExperience').innerHTML=d.experience?`<p>${escapeHtml(d.experience.slice(0,350)).replace(/\n/g,'<br>')}</p>`:'<span></span><span></span><span></span>';
   $('#lpSkills').innerHTML=(d.skills||d.education)?`<p>${escapeHtml((d.skills+'\n'+d.education).trim().slice(0,230)).replace(/\n/g,'<br>')}</p>`:'<span></span><span></span>';
 } else {
   sections[0].textContent='APPLICATION FOR '+get(d.jobTitle,'YOUR NEXT ROLE').toUpperCase();sections[1].textContent='YOUR STRENGTHS';sections[2].textContent='MOTIVATION';
   $('#lpSummary').textContent=get(d.letterBody,`Dear ${get(d.hiringManager,'Hiring Manager')},\nI am applying for the ${get(d.jobTitle,'advertised')} position${d.company?' at '+d.company:''}.`).slice(0,430);
   $('#lpExperience').innerHTML=d.strengths?`<p>${escapeHtml(d.strengths.slice(0,340)).replace(/\n/g,'<br>')}</p>`:'<span></span><span></span><span></span>';
   $('#lpSkills').innerHTML=d.motivation?`<p>${escapeHtml(d.motivation.slice(0,250)).replace(/\n/g,'<br>')}</p>`:'<span></span><span></span>';
 }
}
els.form.addEventListener('input',updatePreview);
els.form.addEventListener('submit',async e=>{
 e.preventDefault();clearFail();
 const d=formData();
 if(!d.fullName||d.fullName.trim().length<2)return fail('Please enter your full name.');
 if(!d.email||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(d.email))return fail('Please enter a valid email address.');
 if(chosenType==='cv'&&!(d.summary||d.experience||d.education))return fail('Please add a profile, experience or education.');
 if(chosenType==='letter'&&!d.jobTitle?.trim())return fail('Please enter the job title you are applying for.');
 if(!config?.ready)return fail('The owner is finishing bank payment setup. You can prepare your document, but checkout will open once payment details are confirmed.');
 els.btn.disabled=true;els.btn.textContent='Preparing your order...';
 try{currentOrder=await call('/api/orders',{method:'POST',body:JSON.stringify({type:chosenType,theme:chosenTheme,details:d})});sessionStorage.setItem('hired_last_order',JSON.stringify({id:currentOrder.id,token:currentOrder.token}));showCheckout();}
 catch(ex){fail(ex.message);}finally{els.btn.disabled=false;els.btn.innerHTML='Continue to bank payment <span>↗</span>';}
});
function copyButton(value,label='Copy') {return `<button type="button" class="copy-btn" data-copy="${escapeHtml(value)}">${escapeHtml(label)}</button>`;}
function detail(label,value,copy=false){return `<div class="payment-detail"><small>${escapeHtml(label)}</small><div class="copyline"><strong>${escapeHtml(value||'Not provided')}</strong>${copy?copyButton(value):''}</div></div>`;}
function attachCopies(){ $$('[data-copy]',els.modal).forEach(el=>el.addEventListener('click',async()=>{
 try{await navigator.clipboard.writeText(el.dataset.copy);const was=el.textContent;el.textContent='Copied!';setTimeout(()=>{if(el.isConnected)el.textContent=was;},1500);}catch{el.textContent='Select to copy';}
 }));}
function showCheckout(){const bank=currentOrder.bank||config?.bank||{};
 openModal(`<span class="modal-label">02 / PAYMENT</span><h2>Your next chapter is close. ✨</h2><p>Transfer the exact amount below to FNB and use your unique reference so your payment can be identified.</p>
 ${detail('BANK',bank.name||'FNB Eswatini')}${detail('ACCOUNT HOLDER',bank.accountName)}${detail('ACCOUNT NUMBER',bank.accountNumber,true)}${bank.branch?detail('BRANCH',bank.branch):''}${bank.accountType?detail('ACCOUNT TYPE',bank.accountType):''}${bank.swift?detail('SWIFT / BIC (international)',bank.swift,true):''}
 ${detail('AMOUNT TO TRANSFER','US$'+currentOrder.amount+' USD',true)}${detail('PAYMENT REFERENCE',currentOrder.reference,true)}
 <div class="info-line"><b>Before paying:</b> Hired serves customers worldwide, but accepts FNB bank transfers only. Overseas SWIFT transfers can be expensive and may take days; some banks require additional receiving-bank details. Confirm your bank supports the transfer and check all fees before sending money. Send US$0.60 only if your bank can send such a small USD payment and our FNB account is able to receive it. Extra bank fees are your responsibility and may exceed the document price. A receipt does not prove the funds arrived; Hired checks the actual bank credit before approving your PDF.</div>
 <label>Upload payment proof (PDF, JPG or PNG · max 3MB)<input class="file-input" id="proofFile" type="file" accept="application/pdf,image/jpeg,image/png"></label>
 <div id="proofMsg" role="alert"></div><button class="primary" id="uploadProof" type="button">Submit payment proof <span>↗</span></button><button class="subtle-link" id="goStatus" type="button">I've paid — check my order status</button>`);
 attachCopies();$('#uploadProof').addEventListener('click',sendProof);$('#goStatus').addEventListener('click',()=>showStatus(currentOrder.id,currentOrder.token));
}
function binaryBase64(bytes){let s='';for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(s);}
async function sendProof(){const input=$('#proofFile'),file=input.files?.[0],message=$('#proofMsg');
 if(!file){message.textContent='Choose the payment receipt first.';message.className='error';return;}
 const match={'application/pdf':'pdf','image/png':'png','image/jpeg':'jpg'};const ext=match[file.type];
 if(!ext){message.textContent='Please choose a PDF, JPG or PNG.';message.className='error';return;}
 if(file.size>3*1024*1024||file.size<100){message.textContent='File must be between 100 bytes and 3 MB.';message.className='error';return;}
 const button=$('#uploadProof');button.disabled=true;button.textContent='Uploading...';
 try{const bytes=new Uint8Array(await file.arrayBuffer());await call(`/api/orders/${currentOrder.id}/proof`,{method:'POST',body:JSON.stringify({token:currentOrder.token,extension:ext,content:binaryBase64(bytes)})});showStatus(currentOrder.id,currentOrder.token);}
 catch(e){message.textContent=e.message;message.className='error';button.disabled=false;button.textContent='Submit payment proof';}
}
async function showStatus(id,token){
 openModal('<span class="modal-label">YOUR ORDER</span><h2>Looking up your order...</h2>');
 try{const data=await call(`/api/orders/${encodeURIComponent(id)}?token=${encodeURIComponent(token)}`);
 const statuses={pending_payment:['Awaiting your transfer','Transfer to FNB using your unique reference, then upload your payment proof.'],awaiting_review:['Payment proof received','Your receipt has been submitted. The owner will check the actual FNB account credit and then approve the order. Depending on your bank, international transfer charges and delays can be substantial.'],approved:['Payment confirmed!','Your document is ready to download. Good luck on your next opportunity!'],rejected:['Payment needs attention','The submitted payment could not be verified. Please contact the owner and include your order reference.']};
 const [title,description]=statuses[data.status]||[data.status,'Please check again.'];
 openModal(`<span class="modal-label">ORDER ${escapeHtml(data.id)}</span><h2>${escapeHtml(title)}</h2><span class="order-status ${escapeHtml(data.status)}">${escapeHtml(data.status.replaceAll('_',' '))}</span><p>${escapeHtml(description)}</p>${detail('YOUR REFERENCE',data.reference,true)}${detail('AMOUNT','US$'+data.amount+' USD')}
 ${data.ready?'<button id="downloadOrder" class="primary">Download my PDF ↗</button>':`<button id="refreshOrder" class="primary">Refresh payment status ↻</button>`}
 <button id="saveOrderLink" class="subtle-link" type="button">Copy a private order-status link</button>`);
 attachCopies();
 $('#downloadOrder')?.addEventListener('click',()=>{window.location.href=`/api/orders/${encodeURIComponent(id)}/download?token=${encodeURIComponent(token)}`;});
 $('#refreshOrder')?.addEventListener('click',()=>showStatus(id,token));
 $('#saveOrderLink').addEventListener('click',async()=>{const url=`${location.origin}/#order=${encodeURIComponent(id)}&token=${encodeURIComponent(token)}`;await navigator.clipboard.writeText(url);$('#saveOrderLink').textContent='Private link copied!';});
 }catch(e){openModal(`<span class="modal-label">TRACK AN ORDER</span><h2>Could not retrieve order</h2><p>${escapeHtml(e.message)}</p><button class="primary" id="backTrack">Try again</button>`);$('#backTrack').onclick=trackPrompt;}
}
function trackPrompt(){const recent=JSON.parse(sessionStorage.getItem('hired_last_order')||'null');
 openModal(`<span class="modal-label">TRACK YOUR DOCUMENT</span><h2>Where's my Hired PDF?</h2><p>Enter the order number and private access token received at checkout. You can also use the private link saved after payment.</p>
 <label>Order ID<input id="trackOrderId" placeholder="A1B2C3D4E5F6" value="${escapeHtml(recent?.id||'')}"></label>
 <label>Private access token<input id="trackToken" placeholder="Paste your access token" value="${escapeHtml(recent?.token||'')}"></label><button class="primary" id="lookupOrder">Find my order ↗</button><div id="trackError" role="alert"></div>`);
 $('#lookupOrder').onclick=()=>{const id=$('#trackOrderId').value.trim().toUpperCase(),token=$('#trackToken').value.trim();if(!id||!token){$('#trackError').textContent='Both fields are required.';return;}showStatus(id,token);};
}
$('#trackBtn').addEventListener('click',trackPrompt);$('#footerTrack').addEventListener('click',trackPrompt);
$('#year').textContent=new Date().getFullYear();
(async()=>{try{config=await call('/api/config');}catch{config={ready:false};}const hash=location.hash;
 if(hash.startsWith('#order=')){const p=new URLSearchParams(hash.substring(1));let id=p.get('order'),token=p.get('token');if(id&&token)showStatus(id,token);history.replaceState(null,'',location.pathname);}
 updatePreview();})();
})();
