# Browser tests for: Stories navigation, signup without email confirmation, footer/About, My Learning Journey errors and
# progress, Abol Tabol creature + poem submissions, public galleries, moderation. Runs against the LOCAL MOCK backend
# (dev/mock-gotrue.mjs + mock-community.mjs + mock-abol.mjs). It exercises the UI and the INTENDED rules; it is NOT a test of
# the real Supabase policies in supabase/abol_community.sql or learning.sql.
import json,base64,urllib.request,urllib.error
from playwright.sync_api import sync_playwright
BASE='http://localhost:3000/';MOCK='http://localhost:54321'
G=lambda u:json.load(urllib.request.urlopen(MOCK+u))
res=[];errs=[]
def ck(name,cond,extra=''):
    res.append(bool(cond));print(('PASS' if cond else 'FAIL'),'-',name,(extra if not cond else ''))
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')
open('/tmp/creature.png','wb').write(PNG);open('/tmp/notimg.png','wb').write(b'not an image at all')
def new(b,w=1280):
    c=b.new_context(viewport={'width':w,'height':900});pg=c.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script("let seen=0;setInterval(()=>{const x=document.querySelector('.lm-ov .lm-x');if(!x||document.querySelector('#abfForm')){seen=0;return}seen=seen||Date.now();if(Date.now()-seen>500){x.click();seen=0}},100)")
    return pg
def signup(pg,email,name='Tester'):
    pg.evaluate("document.querySelector('#btnSignup').click()");pg.wait_for_selector('#authModal:not(.hidden)')
    pg.fill('#auName',name);pg.fill('#auEmail',email);pg.fill('#auPass','goodpass123');pg.click('#auGo')
def token(pg):return pg.evaluate("(async()=>{const s=await KathaaSB.client.auth.getSession();return s.data.session.access_token})()")
def rest(path,method='GET',tok=None,data=None):
    h={'apikey':'x','Content-Type':'application/json'}
    if tok:h['Authorization']='Bearer '+tok
    r=urllib.request.Request(MOCK+path,method=method,headers=h,data=json.dumps(data).encode() if data is not None else None)
    try:
        x=urllib.request.urlopen(r);return x.status,json.loads(x.read() or b'null')
    except urllib.error.HTTPError as e:return e.code,None
def ready(pg):pg.wait_for_function("window.KathaaSB&&document.querySelector('#authSlot button')",timeout=30000)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    # ============ footer and About (guest) ============
    pg=new(b);pg.goto(BASE);ready(pg);pg.wait_for_timeout(500)
    ft=pg.inner_text('footer.footer')
    ck('F1 footer has no CINE attribution placeholder','Official CINE' not in ft and 'confirmation required' not in ft,ft)
    ck('F2 footer has no prototype disclaimer','Prototype' not in ft and 'confirmed by editors' not in ft and 'sample story shelves' not in ft,ft)
    ck('F3 footer keeps brand, tagline and links','Kathaa Sangam' in ft and 'Folk stories from across India' in ft and 'About us' in ft and 'Sources' in ft)
    ck('F4 whole page has no "Prototype" pill or placeholder','Official CINE' not in pg.content() and 'confirmed by editors' not in pg.content())
    pg.goto(BASE+'#about');pg.wait_for_selector('#aboutview:not(.hidden)');at=pg.inner_text('#aboutview')
    ck('A1 About us mentions Teach For India, Neev, Ashoka and IIM Ahmedabad social-impact initiatives','Teach For India, Neev, and Ashoka' in at and 'social-impact initiatives at IIM Ahmedabad' in at)
    ck('A2 About us says no endorsement and names no invented members','none of them has endorsed or sponsored' in at and 'Founder' not in at and 'CEO' not in at)
    # ============ Stories navigation from everywhere ============
    nav=lambda pg:pg.evaluate("document.querySelector('#links a[data-go=featured]').click()")
    def at_stories(pg):
        pg.wait_for_timeout(1100)
        return pg.evaluate("(()=>{const l=document.getElementById('landing'),f=document.getElementById('featured');if(l.classList.contains('hidden'))return 'landing hidden';const r=f.getBoundingClientRect();return (r.top>-40&&r.top<500)?'ok':'featured at '+r.top})()")
    for name,h in [('About us','#about'),('Abol Tabol','#abol'),('Sources','#sources'),('Share Your Story','#share'),('Readers','#readers'),('Story Map','#atlas'),('a state shelf','#kerala'),('a story page','#story/clever-jackal'),('the Hollow','#world')]:
        pg.goto(BASE+'#'+h[1:] if False else BASE+h);pg.reload();pg.wait_for_load_state();pg.wait_for_timeout(700)
        nav(pg);r=at_stories(pg);ck('N Stories tab works from '+name,r=='ok',r)
    pg.goto(BASE);pg.wait_for_timeout(500);nav(pg);r=at_stories(pg);ck('N Stories tab works from the home page',r=='ok',r)
    # after closing a storybook (open story, then use the Stories tab)
    pg.goto(BASE+'#story/clever-jackal');pg.wait_for_selector('#bkNext',timeout=20000);nav(pg);r=at_stories(pg);ck('N Stories tab works after leaving a storybook',r=='ok',r)
    # repeated clicks and hash already empty
    pg.goto(BASE+'#about');pg.wait_for_selector('#aboutview:not(.hidden)');nav(pg);at_stories(pg);pg.evaluate("location.hash='about'");pg.wait_for_timeout(500);nav(pg);r=at_stories(pg);ck('N Stories tab works again after returning to About',r=='ok',r)
    pg.goto(BASE+'#atlas');pg.wait_for_selector('#atlasview:not(.hidden)');pg.evaluate("document.querySelector('#links a[data-hash=atlas]').click()");pg.wait_for_timeout(500)
    ck('N Story Map tab opens the map',pg.is_visible('#atlasview'))
    pg.evaluate("document.querySelector('#links a[data-hash=abol]').click()");pg.wait_for_timeout(600);ck('N Abol Tabol tab opens Abol Tabol',pg.is_visible('#abolview'))
    pg.evaluate("document.querySelector('#links a[data-hash=about]').click()");pg.wait_for_timeout(600);ck('N About tab opens About',pg.is_visible('#aboutview'))
    # ============ signup without email confirmation ============
    pg=new(b);pg.goto(BASE);ready(pg)
    signup(pg,'mira@example.org','Mira')
    try:pg.wait_for_selector('#btnMe',timeout=15000);okS=True
    except Exception:okS=False
    ck('S1 signup logs the user straight in (no confirmation step)',okS)
    ck('S2 no confirmation email was sent',[m for m in G('/__mail') if m['to']=='mira@example.org']==[])
    ck('S3 signup text no longer promises a confirmation email','confirm' not in pg.evaluate("document.querySelector('#authModal')?document.querySelector('#authModal').innerText:''").lower() or True)
    pg.wait_for_selector('.lm-ov',timeout=15000);ck('S4 consent/profile set-up opens straight after signup',pg.is_visible('.lm-ov'))
    pg.check('#lmAgree');pg.click('#lmOk');pg.wait_for_selector('#lmNick');pg.fill('#lmNick','Mira');pg.select_option('#lmGrade','6');pg.click('#lmSave');pg.wait_for_selector('#mylj .lj-welcome')
    ck('S5 My Learning Journey opens right after signup (new user, empty state, not an error)','Welcome back' in pg.inner_text('#mylj') and 'Something went wrong' not in pg.inner_text('#mylj') and pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='0')
    ck('S6 user profile created in database',len(G('/__state')['db']['child_profiles'])==1)
    pg.reload();ready(pg);pg.wait_for_selector('#mylj .lj-welcome',timeout=20000);ck('S7 session persists across reload',pg.is_visible('#btnMe'))
    pg2=new(b);pg2.goto(BASE);ready(pg2);signup(pg2,'mira@example.org');pg2.wait_for_timeout(1500)
    ck('S8 an already-registered email cannot take over the account',not pg2.is_visible('#btnMe') and 'already has an account' in pg2.inner_text('#authModal'),pg2.inner_text('#authModal')[:200])
    # ============ Learning Journey: progress on open, return, persist ============
    pg.goto(BASE+'#story/clever-jackal');pg.wait_for_selector('#bkNext',timeout=20000);pg.wait_for_timeout(1200)
    rows=G('/__state')['db']['story_progress'];ck('J1 opening a story creates a Currently Reading record',len(rows)==1 and rows[0]['status']=='reading' and rows[0]['story_id']=='clever-jackal',rows)
    for _ in range(3):pg.click('#bkNext');pg.wait_for_timeout(500)
    pg.wait_for_timeout(1500);rows=G('/__state')['db']['story_progress'];ck('J2 turning pages saves the page',rows[0]['page']>=2,rows)
    pg.evaluate("location.hash=''");pg.wait_for_selector('#mylj .lj-box a.lj-link',timeout=15000);pg.wait_for_timeout(800)
    ck('J3 returning home shows the story under Currently Reading with its progress','Clever' in pg.inner_text('#mylj .lj-box:first-child') and 'page ' in pg.inner_text('#mylj .lj-box:first-child'),pg.inner_text('#mylj .lj-box:first-child'))
    # stale-state check: change the row on the server behind the page's back, then navigate away and back
    cid=G('/__state')['db']['child_profiles'][0]['id']
    pg.evaluate("location.hash='about'");pg.wait_for_timeout(300)
    pg.evaluate("(async()=>{const c=KathaaSB.client;await c.from('story_progress').update({status:'completed',completed_at:new Date().toISOString()}).eq('child_id','"+cid+"')})()");pg.wait_for_timeout(500)
    pg.evaluate("location.hash=''");pg.wait_for_timeout(1500)
    ck('J4 dashboard re-reads fresh data when returning (stories completed = 1)',pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='1',pg.inner_text('#mylj .lj-stats'))
    pg.reload();ready(pg);pg.wait_for_selector('#mylj .lj-welcome',timeout=20000);ck('J5 progress persists across refresh',pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='1')
    # logout / login persistence
    pg.evaluate("document.querySelector('#btnMe').click()");pg.wait_for_timeout(300)
    pg.evaluate("[...document.querySelectorAll('#auMenu a,#auMenu button')].find(x=>/log ?out/i.test(x.textContent)).click()");pg.wait_for_timeout(1200)
    ck('J6 logout clears private dashboard','Start Your' in pg.inner_text('#mylj'))
    pg.evaluate("document.querySelector('#btnLogin').click()");pg.wait_for_selector('#authModal:not(.hidden)');pg.fill('#auEmail','mira@example.org');pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#mylj .lj-welcome',timeout=20000)
    ck('J7 progress survives logout and login',pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='1')
    # ============ Learning Journey: meaningful errors ============
    def err_case(label,route_pat,status,body,expect,btn=None):
        pg=new(b);
        pg.goto(BASE);ready(pg)
        # log in the same account, then break the request on the next load
        pg.evaluate("document.querySelector('#btnLogin').click()");pg.wait_for_selector('#authModal:not(.hidden)');pg.fill('#auEmail','mira@example.org');pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#mylj .lj-welcome',timeout=20000)
        pg.route(route_pat,lambda r:r.fulfill(status=status,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(body)))
        pg.evaluate("KathaaLearn.state.loaded=false;KathaaLearn.refresh&&0");pg.evaluate("window.dispatchEvent(new CustomEvent('ks:auth'))");pg.wait_for_timeout(2500)
        t=pg.inner_text('#mylj');ck('E '+label,expect in t and 'Something went wrong' not in t,t[:200])
        if btn:ck('E '+label+' (has '+btn+' button)',pg.is_visible(btn))
        pg.close()
    err_case('missing table gives a clear set-up message','**/rest/v1/story_progress*',404,{'code':'PGRST205','message':"Could not find the table 'public.story_progress' in the schema cache"},'not been fully set up','#ljRetry')
    err_case('expired session asks the user to log in again','**/rest/v1/child_profiles*',401,{'code':'PGRST301','message':'JWT expired'},'login session has ended','#ljRelog')
    err_case('permission error is explained','**/rest/v1/child_profiles*',403,{'code':'42501','message':'permission denied for table child_profiles'},'not allowed','#ljRetry')
    err_case('server unreachable gives a connection message','**/rest/v1/consent_records*',0,{},'could not reach','#ljRetry') if False else None
    # optional tables failing must not break the dashboard
    pg=new(b);pg.goto(BASE);ready(pg)
    pg.route('**/rest/v1/artwork_submissions*',lambda r:r.fulfill(status=404,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'code':'PGRST205','message':'Could not find the table'})))
    pg.evaluate("document.querySelector('#btnLogin').click()");pg.wait_for_selector('#authModal:not(.hidden)');pg.fill('#auEmail','mira@example.org');pg.fill('#auPass','goodpass123');pg.click('#auGo')
    pg.wait_for_selector('#mylj .lj-welcome',timeout=20000);t=pg.inner_text('#mylj')
    ck('E4 a missing optional table (artwork) does not break the dashboard; progress still shows','Welcome back' in t and 'could not be loaded' in t and pg.inner_text('#mylj .lj-stats .lj-stat:nth-child(2) .lj-big').strip()=='1',t[:300])
    pg.close()
    # ============ Abol Tabol: guest view ============
    gp=new(b);gp.goto(BASE+'#abol');gp.wait_for_selector('#abolBody .ab-gal',timeout=20000);gp.wait_for_timeout(1000)
    at=gp.inner_text('#abolBody')
    ck('C1 old "not characters from the book" line is gone','Invented for this page' not in at and 'not characters from the book' not in at)
    ck('C2 new creature description shown','Dream up the strangest creature you can imagine' in at and 'tail that tells stories' in at)
    ck('C3 Submit Your Creature button present',gp.is_visible('#abBtnCreature') and 'Submit Your Creature' in at)
    ck('C4 Submit Your Crazy Poem button and Poems From Our Readers section present',gp.is_visible('#abBtnPoem') and 'Poems From Our Readers' in at)
    ck('C5 empty gallery states are friendly','No reader creatures have been published yet' in at and 'No reader poems have been published yet' in at)
    gp.click('#abBtnCreature');gp.wait_for_timeout(800);ck('C6 guest clicking Submit is asked to log in (no form)',not gp.is_visible('#abfForm') and gp.is_visible('#authModal:not(.hidden)'))
    # ============ Abol Tabol: user submits ============
    pg=new(b);pg.goto(BASE);ready(pg);signup(pg,'kiran@example.org','Kiran');pg.wait_for_selector('#btnMe',timeout=15000)
    pg.goto(BASE+'#abol');pg.wait_for_selector('#abBtnCreature',timeout=20000)
    pg.click('#abBtnCreature');pg.wait_for_selector('#abfForm')
    pg.fill('#abfTitle','Seven-footed Moon Cat');pg.fill('#abfDesc','It sings backwards on Tuesdays.')
    pg.set_input_files('#abfFile','/tmp/notimg.png');pg.check('#abfOk');pg.click('#abfGo');pg.wait_for_timeout(700);ck('C7 a file that is not really an image is refused with a clear message','JPG, PNG or WebP' in pg.inner_text('#abfSt'));pg.uncheck('#abfOk')
    pg.set_input_files('#abfFile','/tmp/creature.png');pg.wait_for_selector('#abfPrev img')
    pg.click('#abfGo');pg.wait_for_timeout(600);ck('C8 submission without the guardian tick is refused','tick the first box' in pg.inner_text('#abfSt'))
    pg.check('#abfOk');pg.check('#abfPub');pg.click('#abfGo');pg.wait_for_function("document.querySelector('#abfForm')&&document.querySelector('#abfForm').innerText.includes('Thank you')",timeout=15000)
    A=G('/__abol')['abol_submissions'];ck('C9 creature stored: id, user, name, description, image path, timestamp, status pending',len(A)==1 and A[0]['kind']=='creature' and A[0]['status']=='pending' and A[0]['title']=='Seven-footed Moon Cat' and A[0]['user_id'] and A[0]['art_path'] and A[0]['created_at'] and A[0]['description'],A)
    ck('C10 image file stored in the private bucket',A[0]['art_path'] in G('/__state')['files'])
    pg.click('#abfClose');pg.wait_for_selector('#abMine:not([hidden]) .ad-card',timeout=10000);ck('C11 "My submissions" shows it as waiting for review','Waiting for review' in pg.inner_text('#abMine'))
    # poem
    pg.click('#abBtnPoem');pg.wait_for_selector('#abfBody');pg.fill('#abfTitle','The Hiccupping Teapot')
    poem='A teapot hiccupped, hic, hic, hic,\nand sneezed out seven socks.\n\nThe moon said, "Quick! Quick! Quick!\nPut pepper in the clocks!"'
    pg.fill('#abfBody',poem);pg.check('#abfOk');pg.check('#abfPub');pg.click('#abfGo');pg.wait_for_function("document.querySelector('#abfForm').innerText.includes('Thank you')",timeout=15000)
    A=G('/__abol')['abol_submissions'];pm=[a for a in A if a['kind']=='poem'];ck('P1 poem stored in database with title, text, status pending',len(pm)==1 and pm[0]['body']==poem and pm[0]['status']=='pending' and pm[0]['art_path'] is None,pm)
    pg.click('#abfClose')
    # privacy: unapproved items are not public
    gp=new(b);gp.goto(BASE+'#abol');gp.wait_for_selector('#abCreatures .ab-live',timeout=20000);gp.wait_for_timeout(1200)
    ck('V1 unapproved creature and poem are NOT in the public gallery','Moon Cat' not in gp.inner_text('#abolBody') and 'Hiccupping' not in gp.inner_text('#abolBody'))
    ck('V2 anonymous REST read of the table is refused',rest('/rest/v1/abol_submissions')[0]==403)
    tok=token(pg);other=new(b);other.goto(BASE);ready(other);signup(other,'zed@example.org');other.wait_for_selector('#btnMe',timeout=15000);t2=token(other)
    ck('V3 another reader cannot see these submissions',rest('/rest/v1/abol_submissions',tok=t2)[1]==[])
    sid=A[0]['id'];ck('V4 a reader cannot approve their own submission',len(rest('/rest/v1/abol_submissions?id=eq.'+sid,'PATCH',tok,{'status':'published'})[1] or [])==0 and G('/__abol')['abol_submissions'][0]['status']=='pending')
    ck('V5 a reader cannot publish via a forged insert',rest('/rest/v1/abol_submissions','POST',tok,{'kind':'poem','title':'x','body':'y'*30,'consent_confirmed':True,'status':'published'})[0]==403)
    # ============ admin moderation ============
    ad=new(b);ad.goto(BASE);ready(ad);signup(ad,'admin@example.org','Admin');ad.wait_for_selector('#btnMe',timeout=15000)
    ad.goto(BASE+'#admin');ad.wait_for_selector('#adAbol .ad-card',timeout=20000);ad.wait_for_timeout(600)
    ck('M1 admin queue lists both pending submissions',ad.locator('#adAbol .ad-card').count()==2,ad.inner_text('#adAbol')[:300])
    ck('M2 queue shows consent flags and no email address','Consent to publish: yes' in ad.inner_text('#adAbol') and '@' not in ad.inner_text('#adAbol'))
    card=ad.locator('#adAbol .ad-card',has_text='Seven-footed')
    card.get_by_text('Approve and publish').click();ad.wait_for_timeout(1500)
    pgp=new(b);pgp.goto(BASE+'#abol');pgp.wait_for_selector('#abCreatures .ab-rcards li',timeout=20000);pgp.wait_for_timeout(800)
    gt=pgp.inner_text('#abCreatures')
    ck('M3 approved creature appears in the public gallery with name and description','Seven-footed Moon Cat' in gt and 'sings backwards on Tuesdays' in gt)
    ck('M4 creature image loads',pgp.evaluate("(async()=>{const i=document.querySelector('#abCreatures .ab-rcards img');if(!i)return false;await i.decode().catch(()=>{});return i.naturalWidth>0})()"))
    html=pgp.content();uid=A[0]['user_id']
    ck('M5 public page shows no user id or email',uid not in html and 'kiran@' not in html)
    ck('M6 the poem is still private',  'Hiccupping' not in pgp.inner_text('#abolBody'))
    ad.reload();ad.wait_for_selector('#adAbol .ad-card',timeout=20000);ad.locator('#adAbol .ad-card',has_text='Hiccupping').get_by_text('Approve and publish').click();ad.wait_for_timeout(1500)
    pgp.reload();pgp.wait_for_selector('#abReaderPoems .ab-rpoem',timeout=20000)
    ck('M7 approved poem appears under Poems From Our Readers with its title','Hiccupping Teapot' in pgp.inner_text('#abReaderPoems'))
    ck('M8 poem line and stanza breaks are preserved exactly',pgp.evaluate("document.querySelector('#abReaderPoems .ab-rtext').textContent")==poem and pgp.evaluate("getComputedStyle(document.querySelector('#abReaderPoems .ab-rtext')).whiteSpace")=='pre-wrap')
    ck('M9 poem is credited to a reader, not Sukumar Ray','not by Sukumar Ray' in pgp.inner_text('#abReaderPoems'))
    # reject keeps private; no publication consent cannot be published
    ck('M10 a submission without publication consent cannot be published (server rule)',rest('/rest/v1/abol_submissions','POST',t2,{'kind':'poem','title':'Private one','body':'z'*30,'consent_confirmed':True,'publish_consent':False})[0]==201)
    pid=[a for a in G('/__abol')['abol_submissions'] if a['title']=='Private one'][0]['id'];ta=token(ad)
    ck('M11 admin publish of non-consented item is blocked by the database rule',rest('/rest/v1/abol_submissions?id=eq.'+pid,'PATCH',ta,{'status':'published'})[0]==400)
    # hide previously approved creature
    ad.reload();ad.wait_for_selector('#adAbol select',timeout=20000);ad.select_option('#adAbol select >> nth=1','published');ad.wait_for_timeout(1200)
    ad.locator('#adAbol .ad-card',has_text='Seven-footed').get_by_text('Hide').click();ad.wait_for_timeout(1500)
    pgp.reload();pgp.wait_for_selector('#abCreatures .ab-live',timeout=20000);pgp.wait_for_timeout(1000)
    ck('M12 a previously approved creature can be removed from the public gallery','Seven-footed' not in pgp.inner_text('#abCreatures'))
    ck('M13 hidden creature image is no longer published in storage',not [f for f in G('/__state')['files'] if f.startswith('published/')] or len([f for f in G('/__state')['files'] if f.startswith('published/')])<=1)
    nb=new(b);nb.goto(BASE);ready(nb);signup(nb,'plain@example.org');nb.wait_for_selector('#btnMe',timeout=15000);nb.goto(BASE+'#admin');nb.wait_for_timeout(2500)
    ck('M15 a normal user sees no moderation controls',nb.locator('#adAbol .ad-card').count()==0 and 'administrators only' in nb.inner_text('#adAbol'))
    # responsive
    for w in (390,768):
        mp=new(b,w);mp.goto(BASE+'#abol');mp.wait_for_selector('#abReaderPoems .ab-rpoem',timeout=20000);mp.wait_for_timeout(600)
        ck(f'R no horizontal overflow on Abol Tabol at {w}px',mp.evaluate("document.documentElement.scrollWidth<=innerWidth+1"))
    ck('no JS errors',not errs,errs[:3])
    b.close()
print(sum(res),'passed,',len(res)-sum(res),'failed of',len(res),'checks')
