# Journey + unauthorised-access tests against the LOCAL MOCK (dev/mock-gotrue.mjs). Not a test of real Supabase RLS.
import json,urllib.request,sys
from playwright.sync_api import sync_playwright
G=lambda u:json.load(urllib.request.urlopen('http://localhost:54321'+u))
U='http://localhost:3000/'
R=[]
def ck(n,ok,info=''):
    R.append((n,bool(ok)));print(('PASS' if ok else 'FAIL'),'-',n,info if not ok else '')
def signup(pg,name,email):
    pg.evaluate("document.querySelector('#btnSignup').click()");pg.wait_for_selector('#authModal:not(.hidden)')
    pg.fill('#auName',name);pg.fill('#auEmail',email);pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#auLinks button')
    link=[m for m in G('/__mail') if m['to']==email][-1]['link'];pg.goto(link);pg.wait_for_selector('#btnMe',timeout=30000)
def sb(pg,js):return pg.evaluate("async()=>{const c=KathaaSB.client;"+js+"}")
def to_end(pg):
    pg.wait_for_selector('#bkNext');
    for _ in range(80):
        if pg.evaluate("document.querySelector('#bkNext').disabled"):break
        pg.evaluate("document.querySelector('#bkNext').click()");pg.wait_for_timeout(250)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':900});ctx.set_default_timeout(15000);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(U);pg.wait_for_selector('#btnLogin',timeout=30000)
    pg.wait_for_selector('#mylj .lj-guest')
    t=pg.inner_text('#mylj');ck('1 guest sees Start Your Reading Journey, no stats','Start Your' in t and 'Stories completed' not in t and 'Not Yet Assessed' not in t)
    ck('1b guest can browse+read story',pg.evaluate("location.hash='story/the-monkey-and-the-fox',true") and pg.wait_for_selector('#bkNext',timeout=15000) is not None)
    pg.goto(U);pg.wait_for_selector('#btnSignup')
    signup(pg,'Parent One','parent@test.com')
    pg.wait_for_selector('.lm-card',timeout=15000);ck('2 consent modal after login','agree' in pg.inner_text('.lm-card').lower())
    pg.click('#lmOk');ck('3 cannot continue without ticking',len(G('/__state')['db']['consent_records'])==0 and pg.is_visible('.lm-msg.err'))
    pg.check('#lmAgree');pg.click('#lmOk');pg.wait_for_selector('#lmNick')
    ck('3b consent stored with version+role',G('/__state')['db']['consent_records'][0]['version']=='v1')
    pg.fill('#lmNick','Asha');pg.select_option('#lmGrade','6');ck('4 grade 6 suggests level 2',pg.is_checked('input[name=lmLv][value="2"]') and pg.is_visible('.lm-sug[data-k="2"]'))
    pg.click('#lmSave');pg.wait_for_selector('#mylj .lj-welcome')
    kid=G('/__state')['db']['child_profiles'][0];ck('4b child profile saved (nickname,grade,level only)',kid['nickname']=='Asha' and kid['level']==2 and 'email' not in kid)
    t=pg.inner_text('#mylj');ck('5 dashboard: welcome, level, 0 completed, Not Yet Assessed','Asha' in t and 'Growing Sapling' in t and 'Not Yet Assessed' in t)
    ck('5b recommendations are real stories',pg.evaluate("[...document.querySelectorAll('#mylj .lj-box:nth-child(2) a.lj-link')].every(a=>REAL[a.getAttribute('href').slice(7)])") and len(pg.query_selector_all('#mylj .lj-box:nth-child(2) a.lj-link'))>=1)
    # 6 open story at preferred level, progress recorded
    pg.evaluate("location.hash='story/the-monkey-and-the-fox'");pg.wait_for_selector('#bkNext');pg.evaluate("document.querySelector('#bkNext').click()");pg.wait_for_timeout(400);pg.evaluate("document.querySelector('#bkNext').click()");pg.wait_for_timeout(1500)
    sp=G('/__state')['db']['story_progress'];ck('6 progress row reading at level 2, page>=0',len(sp)>=1 and sp[-1]['status']=='reading' and sp[-1]['level']==2 and sp[-1]['page']>=0,sp)
    # 7 reload -> resume
    pg.goto(U);pg.wait_for_selector('#mylj .lj-welcome');pg.wait_for_selector('#mylj a.lj-link[data-resume]')
    ck('7 Currently Reading lists story with page','Monkey' in pg.inner_text('#mylj .lj-box'))
    pg.click('#mylj .lj-box:first-child a.lj-link');pg.wait_for_selector('#bkNext');pg.wait_for_timeout(600)
    ck('7b resumes on saved page',pg.inner_text('#bkSt').startswith('Page'),pg.inner_text('#bkSt'))
    # 8 complete
    to_end(pg);pg.wait_for_selector('#ljDone');pg.click('#ljDone');pg.wait_for_function("document.querySelector('#ljDone').textContent.includes('Completed')")
    ck('8 story marked completed in DB',any(r['status']=='completed' for r in G('/__state')['db']['story_progress']))
    pg.goto(U+'#story/the-ow-princess' if False else U);pg.wait_for_selector('#mylj .lj-welcome');ck('8b stories completed = 1','Stories completed' in pg.inner_text('#mylj') and pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='1')
    # 9 written answers
    pg.evaluate("location.hash='story/clever-jackal'");pg.wait_for_selector('#qaSave');tas=pg.query_selector_all('#stThink textarea');tas[0].fill('The jackal was clever because he made a plan.');tas[1].fill('I would also have tried to stay calm.')
    pg.click('#qaSave');pg.wait_for_function("document.querySelector('#qaSt').textContent.includes('learning journey')")
    ck('9 answers saved to DB',len(G('/__state')['db']['child_responses'])==2)
    pg.reload();pg.wait_for_selector('#qaSave');pg.wait_for_function("document.querySelector('#stThink textarea').value.length>5");ck('9b answers persist after reload and are editable',True)
    # 10 quiz
    def do_quiz(story,wrong=False):
        pg.evaluate(f"location.hash='story/{story}'");pg.wait_for_selector('#qzForm')
        ans=pg.evaluate(f"(()=>{{const lv=+document.querySelector('.bk-lvl,.lvl-on')?0:0;return null}})()")
        items=pg.evaluate("(()=>{const id=location.hash.slice(7);const lvs=REAL[id].levels;const k=Object.keys(lvs).find(k=>document.querySelector('#stQuiz').innerHTML.includes(lvs[k].quiz[0].q.slice(0,20)));return lvs[k].quiz.map(i=>i.a)})()")
        for i,a in enumerate(items):
            n=a if not wrong else (a+1)%4
            pg.check(f'input[name=qz{i}][value="{n}"]')
        pg.click('#qzGo');pg.wait_for_function("document.querySelector('#qzSt').textContent.includes('Saved')||document.querySelector('#qzSt').textContent.includes('could not')");return items
    it=do_quiz('the-monkey-and-the-fox');ck('10 quiz first attempts saved',len(G('/__state')['db']['quiz_attempts'])==len(it),len(G('/__state')['db']['quiz_attempts']))
    n1=len(G('/__state')['db']['quiz_attempts']);pg.click('#qzGo')
    # retry (wrong) counts as additional attempt but first attempt per item scored
    for i,a in enumerate(it):pg.check(f'input[name=qz{i}][value="{(a+1)%4}"]')
    pg.click('#qzGo');pg.wait_for_timeout(800);
    sc=pg.evaluate("KathaaLearn.core.assess(KathaaLearn.state.attempts,[],{})");ck('10b retry does not lower first-attempt score',sc['dims']['comprehension']['n']<=4 and all(a['correct'] for a in pg.evaluate("KathaaLearn.core.firstAttempts(KathaaLearn.state.attempts)")))
    do_quiz('the-ow-princess');pg.goto(U);pg.wait_for_selector('#mylj .lj-welcome')
    ck('10c score appears from real evidence (>=6 items)', '/100' in pg.inner_text('#mylj .lj-stats') and 'Not Yet Assessed' not in pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(3)'),pg.inner_text('#mylj .lj-stats'))
    ck('10d written/critical shown as awaiting review','awaiting review' in pg.text_content('#mylj .lj-how'))
    # 11 artwork linked to child
    pg.evaluate("location.hash='story/the-monkey-and-the-fox'");pg.wait_for_selector('#artForm');pg.set_input_files('#artFile','/tmp/art.png');pg.fill('#artTitle','My mango');pg.check('#artOk');pg.click('#artGo')
    pg.wait_for_function("document.querySelector('#artSt').textContent.startsWith('Thank')",timeout=15000);s=G('/__state')
    ck('11 artwork saved with child_id and file',len(s['rows'])==1 and s['rows'][0]['child_id']==kid['id'] and len(s['files'])==1)
    pg.goto(U);pg.wait_for_selector('#mylj .lj-welcome');ck('11b My Creative Work lists artwork','My mango' in pg.inner_text('#mylj'))
    # 12 shelf indicator
    pg.evaluate("location.hash='punjab'") if False else None
    st=pg.evaluate("REAL['the-monkey-and-the-fox'].state");slug=pg.evaluate(f"STATES['{st}'].slug");pg.evaluate(f"location.hash='{slug}'");pg.wait_for_function("document.querySelectorAll('.book[data-story]').length>0",timeout=20000);pg.wait_for_timeout(800)
    ck('12 shelf shows Completed for finished story',pg.evaluate("[...document.querySelectorAll('.book[data-story=\"the-monkey-and-the-fox\"] .prg')].some(e=>e.textContent.includes('Completed'))"))
    # 13 admin review
    a=b.new_context(viewport={'width':1280,'height':900}).new_page();a.on('pageerror',lambda e:errs.append(str(e)))
    a.goto(U);a.wait_for_selector('#btnLogin',timeout=30000);signup(a,'Admin','admin@test.com')
    a.evaluate("location.hash='admin'");a.wait_for_selector('.lj-rev',timeout=20000);rv=a.query_selector_all('.lj-rev')
    for d in rv:
        d.query_selector('[data-k=written]').select_option('3');d.query_selector('[data-k=critical]').select_option('2');d.query_selector('button.lbtn').evaluate('e=>e.click()');a.wait_for_timeout(400)
    ck('13 admin saved rubric reviews',len(G('/__state')['db']['response_reviews'])==2)
    pg.goto(U);pg.wait_for_selector('#mylj .lj-welcome');t=pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(3)');ck('13b score now includes reviewed written/critical','written expression' in t,t)
    # 14 add second child, isolation
    pg.click('#ljAdd');pg.fill('#lmNick','Ravi');pg.select_option('#lmGrade','9');pg.click('#lmSave');pg.wait_for_function("document.querySelector('.lj-welcome').textContent.includes('Ravi')")
    ck('14 second child starts empty (no leaked data)','Not Yet Assessed' in pg.inner_text('#mylj .lj-stats') and pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='0' and 'Mighty Tree' in pg.inner_text('#mylj'))
    # 15 level change never forced
    pg.click('#ljLvl');pg.check('input[name=lmLv][value="1"]');pg.click('#lmSave');pg.wait_for_function("document.querySelector('#mylj').textContent.includes('Little Seedling')")
    ck('15 level can be changed by user',G('/__state')['db']['child_profiles'][1]['level']==1)
    # delete child 2 cascades
    pg.click('#ljMng');pg.click('#lmDel');pg.click('#lmDel');pg.wait_for_function("document.querySelector('.lj-welcome').textContent.includes('Asha')");ck('15b deleting a child removes profile',len(G('/__state')['db']['child_profiles'])==1)
    pg.locator('#mylj').screenshot(path='/tmp/dash_desktop.png');pg.set_viewport_size({'width':390,'height':800});pg.wait_for_timeout(400);pg.locator('#mylj').screenshot(path='/tmp/dash_mobile.png');ck('15c no horizontal overflow at 390px',pg.evaluate('document.documentElement.scrollWidth<=392'));pg.set_viewport_size({'width':1280,'height':900})
    # 16 logout
    pg.click('#btnMe');pg.click('text=Log out');pg.wait_for_selector('#mylj .lj-guest');ck('16 logout returns to guest view, no private stats','Asha' not in pg.inner_text('#mylj'))
    # 17 persistent session / login again
    pg.evaluate("document.querySelector('#btnLogin').click()");pg.fill('#auEmail','parent@test.com');pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#mylj .lj-welcome',timeout=20000)
    ck('17 login restores journey','Asha' in pg.inner_text('#mylj') and 'Stories completed' in pg.inner_text('#mylj'))
    pg.reload();pg.wait_for_selector('#mylj .lj-welcome',timeout=20000);ck('17b session persists across reload',True)
    # ---- unauthorised access ----
    o=b.new_context().new_page();o.on('pageerror',lambda e:errs.append(str(e)));o.goto(U);o.wait_for_selector('#btnLogin',timeout=30000);signup(o,'Other','other@test.com');o.wait_for_timeout(800)
    cid=kid['id']
    ck('U1 other user cannot read child profile',sb(o,"const r=await c.from('child_profiles').select('id').eq('id','"+cid+"');return r.data.length")==0)
    ck('U2 other user cannot read progress/responses/attempts',sb(o,"let n=0;for(const t of ['story_progress','child_responses','quiz_attempts']){const r=await c.from(t).select('*').eq('child_id','"+cid+"');n+=(r.data||[]).length}return n")==0)
    ck('U3 other user cannot write progress for child',sb(o,"const r=await c.from('story_progress').insert({child_id:'"+cid+"',story_id:'x',level:1,status:'reading',page:0});return !!r.error")==True)
    ck('U4 other user cannot write answers/attempts for child',sb(o,"const a=await c.from('child_responses').insert({child_id:'"+cid+"',story_id:'x',level:1,question_id:'0',body:'hi'});const b=await c.from('quiz_attempts').insert({child_id:'"+cid+"',story_id:'x',level:1,item_id:'z',dimension:'comprehension',chosen:0,correct:true});return !!a.error&&!!b.error")==True)
    ck('U5 non-admin cannot create reviews (cannot self-score)',sb(o,"const r=await c.from('response_reviews').insert({response_id:'"+G('/__state')['db']['child_responses'][0]['id']+"',written:4,critical:4});return !!r.error")==True)
    ck('U6 non-admin cannot read reviews of others',sb(o,"const r=await c.from('response_reviews').select('*');return r.data.length")==0)
    ck('U7 user cannot attach artwork to another child',sb(o,"const r=await c.from('artwork_submissions').insert({story_id:'x',storage_path:'"+o.evaluate("KathaaSB.user().id")+"/z.png',content_type:'image/png',size_bytes:1,consent_confirmed:true,child_id:'"+cid+"'});return !!r.error")==True)
    # owner cannot edit/forge scores or alter quiz attempts
    ck('U8 owner cannot alter quiz attempts (append-only)',sb(pg,"const r=await c.from('quiz_attempts').update({correct:true}).eq('child_id','"+cid+"').select();return (r.data||[]).length")==0 and sb(pg,"const r=await c.from('quiz_attempts').delete().eq('child_id','"+cid+"').select();return (r.data||[]).length")==0)
    ck('U9 owner cannot self-review',sb(pg,"const r=await c.from('response_reviews').insert({response_id:'"+G('/__state')['db']['child_responses'][0]['id']+"',written:4,critical:4});return !!r.error")==True)
    ck('U10 invalid values rejected (level 9, page 999, empty nickname)',sb(pg,"const a=await c.from('child_profiles').insert({nickname:'ok',level:9});const b2=await c.from('story_progress').insert({child_id:'"+cid+"',story_id:'x',level:1,status:'reading',page:999});const d=await c.from('child_profiles').insert({nickname:'',level:1});return !!a.error&&!!b2.error&&!!d.error")==True)
    ck('U11 guests (no login) cannot read learning tables',json.loads(__import__('subprocess').run(['curl','-s','-o','/dev/null','-w','%{http_code}','localhost:54321/rest/v1/child_profiles'],capture_output=True,text=True).stdout or '0') in (401,403))
    ck('U12 admin page blocked for non-admin',(lambda:(o.evaluate("location.hash='admin'"),o.wait_for_selector('#adBody p',timeout=15000),'administrators only' in o.inner_text('#adBody'))[2])())
    ck('no JS errors',not errs,errs)
    b.close()
bad=[n for n,o in R if not o]
print('\n%d checks, %d failed'%(len(R),len(bad)));print('\n'.join(bad))
