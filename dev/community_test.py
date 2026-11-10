# Browser tests for: Union Territory removal, Abol Tabol, Share Your Story, moderation, Voices From Our Readers.
# Runs against the LOCAL MOCK backend (dev/mock-gotrue.mjs + dev/mock-community.mjs). It exercises the UI and the intended
# rules; it is NOT a test of the real Supabase policies in supabase/community.sql.
import json,re,urllib.request,urllib.error
from playwright.sync_api import sync_playwright
BASE='http://localhost:3000/';MOCK='http://localhost:54321'
G=lambda u:json.load(urllib.request.urlopen(MOCK+u))
res=[];errs=[]
def ok(name,cond,extra=''):
    res.append(bool(cond));print(('PASS' if cond else 'FAIL'),'-',name,(extra if not cond else ''))
def rest(path,method='GET',token=None,data=None):
    h={'apikey':'x','Content-Type':'application/json'}
    if token:h['Authorization']='Bearer '+token
    r=urllib.request.Request(MOCK+path,method=method,headers=h,data=json.dumps(data).encode() if data is not None else None)
    try:
        x=urllib.request.urlopen(r);return x.status,json.loads(x.read() or b'null')
    except urllib.error.HTTPError as e:return e.code,None
def signup(pg,name,email):
    pg.evaluate("document.querySelector('#btnSignup').click()");pg.wait_for_selector('#authModal:not(.hidden)')
    pg.fill('#auName',name);pg.fill('#auEmail',email);pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#auLinks button')
    link=[m for m in G('/__mail') if m['to']==email][-1]['link'];pg.goto(link);pg.wait_for_selector('#btnMe',timeout=30000)
def go(pg,h):
    pg.goto(BASE+h);pg.reload();pg.wait_for_load_state()
def new(b,w=1280):
    c=b.new_context(viewport={'width':w,'height':900});pg=c.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)))
    # the existing learning module may open its parent-consent dialog after login; close it so it does not cover the page under test
    pg.add_init_script("let seen=0;setInterval(()=>{const x=document.querySelector('.lm-ov .lm-x');if(!x){seen=0;return}seen=seen||Date.now();if(Date.now()-seen>500){x.click();seen=0}},100)")
    return pg
def token(pg):return pg.evaluate("(async()=>{const s=await KathaaSB.client.auth.getSession();return s.data.session.access_token})()")
def st(pg,sel='#shSt'):return pg.inner_text(sel)
def fill_story(pg,title='The Moon Who Lost His Hat',body='Once upon a time a tiny moon lost his hat in the clouds and looked everywhere for it.',lang='en',state='',pub=False,ok_=True,file=None):
    pg.fill('#shTitle',title);pg.fill('#shBody',body);pg.check(f'input[name=shLang][value={lang}]');pg.select_option('#shState',state)
    pg.set_checked('#shOk',ok_);pg.set_checked('#shPub',pub)
    if file:pg.set_input_files('#shFile',file)
UT_NAMES=['Delhi','Chandigarh','Puducherry','Lakshadweep','Ladakh','Andaman','Jammu','Dadra','Daman']
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    G('/__resetcommunity')
    # ======================= 4. UNION TERRITORIES =======================
    pg=new(b);pg.goto(BASE);pg.wait_for_function("typeof STATES!=='undefined'&&document.querySelectorAll('#msvg .ms').length>0",timeout=30000);pg.wait_for_timeout(800)
    names=pg.evaluate("Object.values(STATES).map(s=>s.name)")
    ok('U1 exactly 28 states in the public data',len(names)==28,len(names))
    ok('U2 no Union Territory name among them',not [n for n in names if any(u in n for u in UT_NAMES)],names)
    ok('U3 the 28 expected states are all present',set(names)=={'Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh','Uttarakhand','West Bengal'},names)
    quick=pg.inner_text('#quick');chips=pg.inner_text('#chips')
    ok('U4 home state list and filter chips show no Union Territory',not any(u in quick+chips for u in UT_NAMES))
    ok('U5 home state list says "All 28 states"','All 28 states' in quick)
    ok('U6 map: 28 selectable states and 9 non-selectable UT outlines',pg.evaluate("[document.querySelectorAll('#msvg .ms.live').length,document.querySelectorAll('#msvg .ms.ut').length]")==[28,9])
    ok('U7 UT outlines are inert (no role/tabindex, pointer-events none)',pg.evaluate("[...document.querySelectorAll('#msvg .ms.ut')].every(p=>!p.getAttribute('role')&&!p.hasAttribute('tabindex')&&getComputedStyle(p).pointerEvents==='none')"))
    h0=pg.evaluate("location.hash");pg.evaluate("document.querySelector('#msvg .ms.ut').dispatchEvent(new MouseEvent('click',{bubbles:true}))");pg.wait_for_timeout(300)
    ok('U8 clicking a UT outline does nothing',pg.evaluate("location.hash")==h0)
    ok('U9 every state tile on the map opens a shelf',pg.evaluate("[...document.querySelectorAll('#msvg .ms.live')].every(p=>STATES[p.dataset.id]&&bySlug[STATES[p.dataset.id].slug]===p.dataset.id)"))
    ok('U10 featured-story rail and search index contain no UT story',pg.evaluate("ALLB.every(x=>!UT.has(x.sid))&&Object.values(REAL).every(r=>!UT.has(r.state))"))
    arch=pg.evaluate("[Object.keys(UT_ARCHIVE.states).sort(),Object.keys(UT_ARCHIVE.stories).sort()]")
    ok('U11 UT records are archived, not deleted',arch[0]==['an','ch','dd','dl','dn','jk','ld','py'] and arch[1]==['shabrang','the-precious-present'],arch)
    pg.goto(BASE+'#atlas');pg.wait_for_selector('#achips .atl-chip',timeout=20000)
    ok('U12 story map page: 28 selectable regions and 28 list chips',pg.evaluate("[document.querySelectorAll('#asvg .as-s').length,document.querySelectorAll('#achips .atl-chip').length]")==[28,28])
    ok('U13 story map still draws all 37 outlines (geography kept)',pg.evaluate("document.querySelectorAll('#asvg path.as-s,#asvg path.as-u').length")==37)
    pg.fill('#asq','Delhi');pg.wait_for_timeout(300)
    ok('U14 searching "Delhi" finds nothing',pg.evaluate("document.querySelectorAll('#achips .atl-chip').length")==0)
    pg.fill('#asq','Jammu');pg.wait_for_timeout(300)
    ok('U15 searching "Jammu" finds nothing',pg.evaluate("document.querySelectorAll('#achips .atl-chip').length")==0)
    pg.goto(BASE+'#jammu-and-kashmir');pg.wait_for_timeout(800)
    ok('U16 old Jammu & Kashmir shelf link shows the home page, not a shelf',pg.evaluate("!document.querySelector('#landing').classList.contains('hidden')&&document.querySelector('#shelfview').classList.contains('hidden')"))
    pg.goto(BASE+'#story/shabrang');pg.wait_for_timeout(800)
    ok('U17 old link to a Kashmir story shows the home page (record kept, not browsable)',pg.evaluate("!document.querySelector('#landing').classList.contains('hidden')"))
    pg.goto(BASE+'#story/clever-jackal');pg.wait_for_selector('#bkNext',timeout=20000)
    ok('U18 existing stories still open',pg.evaluate("document.querySelector('#storyview h1, #stMeta h2, #stMeta')!==null"))
    pg.goto(BASE+'#world');pg.wait_for_timeout(2500)
    hl=pg.evaluate("(()=>{try{mkList();return document.querySelectorAll('#sgrid button').length}catch(e){return 'err '+e.message}})()")
    ok('U19 3D world jump list has 28 entries (list only; 3D scene not rendered in this check)',hl==28,hl)
    pg.close()
    # ======================= 1. ABOL TABOL =======================
    pg=new(b);pg.goto(BASE);pg.wait_for_selector('#links');
    ok('A1 main navigation has Abol Tabol and Share Your Story',pg.evaluate("[...document.querySelectorAll('#links a')].map(a=>a.textContent).join('|')")=='Stories|Story Map|Abol Tabol|Share Your Story|About')
    ok('A2 home has an Abol Tabol section with a working link',pg.evaluate("!!document.querySelector('#abolHome a[href=\"#abol\"]')&&document.querySelector('#abolHome h2').textContent==='Abol Tabol'"))
    ok('A3 home section order: journey < Abol Tabol < Share Your Story < footer',pg.evaluate("(()=>{const o=['journey','abolHome','shareHome'].map(i=>document.getElementById(i).getBoundingClientRect().top+scrollY);return o[0]<o[1]&&o[1]<o[2]&&o[2]<document.querySelector('.footer').getBoundingClientRect().top+scrollY})()"))
    pg.click('#links a[href="#abol"]');pg.wait_for_selector('#abolBody .ab-hero')
    t=pg.inner_text('#abolBody')
    ok('A4 collection page opens with the explanation',all(s in t for s in ['What is Abol Tabol?','Sukumar Ray','nonsense','Why play with words?']))
    ok('A5 date facts are the verified ones','19 September 1923' in t and '10 September 1923' in t)
    ok('A6 no poem is published and the page says so honestly','No poems are published here yet' in t and pg.evaluate("document.querySelectorAll('.ab-pcard').length")==0)
    ok('A7 no claim that a translation exists',not re.search(r'translated by|our translation|English translation by',t,re.I))
    ok('A8 illustrations have alt text and load',pg.evaluate("[...document.querySelectorAll('#abolBody img')].every(i=>i.alt.length>10&&i.complete&&i.naturalWidth>0)"))
    ok('A9 poem validator rejects unverified or incomplete records',pg.evaluate("""(()=>{const base={id:'t1',verified:true,title:{en:'T'},stanzas:{en:[['a']]},source:{work:'w',author:'a',firstPublished:'f',textFrom:'t',versionBy:'v',rights:'r',verifiedBy:'b',verifiedOn:'2026-01-01'}};
      const bad=[{...base,verified:false},{...base,source:{...base.source,rights:''}},{...base,stanzas:{en:[]}},{...base,title:{}},null];
      return Community.usablePoem(base)&&bad.every(x=>!Community.usablePoem(x))})()"""))
    # TEST FIXTURE ONLY (clearly fake text, never shipped): checks the reader keeps line and stanza structure
    pg.evaluate("""ABOL_POEMS.push({id:'zz-test',verified:true,title:{en:'TEST FIXTURE POEM',hi:'परीक्षण'},
      stanzas:{en:[['TEST line one,','  TEST line two (indented),','TEST line three.'],['TEST second verse, line one','TEST second verse, line two']],hi:[['परीक्षण पंक्ति एक','परीक्षण पंक्ति दो','परीक्षण पंक्ति तीन'],['परीक्षण दूसरा छंद']]},
      vocab:[{w:'testword',m:'a word for testing'}],
      source:{work:'TEST',author:'TEST',firstPublished:'TEST',textFrom:'TEST',versionBy:'TEST',rights:'TEST',verifiedBy:'TEST',verifiedOn:'2026-01-01'}},
      {id:'zz-unverified',verified:false,title:{en:'UNVERIFIED SHOULD NOT SHOW'},stanzas:{en:[['x']]},source:{}})""")
    pg.goto(BASE+'#abol');pg.wait_for_selector('#abolBody .ab-hero');pg.evaluate("Community.show('abol')");pg.wait_for_selector('.ab-pcard')
    ok('A10 only the verified record appears as a poem card',pg.evaluate("[...document.querySelectorAll('.ab-pcard')].map(a=>a.textContent)")==['✨TEST FIXTURE POEMपरीक्षण'])
    pg.click('.ab-pcard');pg.wait_for_selector('.ab-read .stz')
    ok('A11 poem lines are kept as separate lines (not merged into prose)',pg.evaluate("document.querySelectorAll('.ab-read .stz .ln').length")==3 and pg.evaluate("getComputedStyle(document.querySelector('.stz .ln')).display")=='block')
    ok('A12 indentation preserved (white-space pre-wrap)',pg.evaluate("[...document.querySelectorAll('.stz .ln')][1].textContent.startsWith('  ')&&getComputedStyle(document.querySelector('.stz .ln')).whiteSpace==='pre-wrap'"))
    pg.click('.ab-nav button:has-text("Next")');pg.wait_for_timeout(200)
    ok('A13 page navigation moves to verse 2 with its own stanza break',pg.evaluate("document.querySelectorAll('.stz .ln').length")==2 and 'Verse 2 of 2' in pg.inner_text('.ab-nav'))
    pg.click('.ab-read .chip:has-text("Side by side")');pg.wait_for_timeout(200)
    ok('A14 side-by-side shows English and Hindi stanzas',pg.evaluate("document.querySelectorAll('.ab-spread.two .stz').length")==2 and pg.evaluate("document.querySelector('.ab-spread.two .stz[lang=hi]')!==null"))
    ok('A15 vocabulary help and source/credit panels exist',pg.evaluate("[...document.querySelectorAll('.ab-det summary')].map(s=>s.textContent)")==['Word help','Source and credits'])
    ok('A16 listen button present (enabled only when the device has a voice)',pg.evaluate("[...document.querySelectorAll('.ab-read .lbtn')].some(b=>b.textContent.includes('Listen'))"))
    pg.close()
    # ======================= 2. SHARE YOUR STORY =======================
    anon=new(b);anon.goto(BASE+'#share');anon.wait_for_selector('#shareBody .cm-rules');anon.wait_for_timeout(1500)
    ok('S1 logged-out visitor sees a login prompt and no form',anon.evaluate("!document.querySelector('#shForm')&&!![...document.querySelectorAll('#shareBody button')].find(b=>b.textContent.includes('Log in'))"))
    ok('S2 child-safety rules are shown (private, no personal data, labelled by reader)',all(s in anon.inner_text('#shareBody') for s in ['private','full name','by a reader']))
    s,_=rest('/rest/v1/user_stories');ok('S3 anonymous cannot read the stories table',s in (401,403),s)
    s,_=rest('/rest/v1/user_stories','POST',None,{'title':'x'});ok('S4 anonymous cannot insert a story',s in (401,403),s)
    anon.close()
    kid=new(b);kid.goto(BASE);kid.wait_for_selector('#btnLogin',timeout=30000);signup(kid,'Kid One','kid1@test.com')
    go(kid,'#share');kid.wait_for_selector('#shForm',timeout=20000)
    ok('S5 logged-in user sees the form with all fields',kid.evaluate("['#shTitle','#shBody','input[name=shLang]','#shState','#shInsp','#shFile','#shOk','#shPub'].every(s=>document.querySelector(s))"))
    ok('S6 state list has 28 states plus the "no particular state" choice',kid.evaluate("document.querySelectorAll('#shState option').length")==29 and 'imagination' in kid.inner_text('#shState'))
    fill_story(kid,ok_=False);kid.click('#shGo');kid.wait_for_timeout(500)
    ok('S7 missing permission tick is refused, nothing stored','parent, guardian or teacher' in st(kid) and len(G('/__community')['user_stories'])==0)
    fill_story(kid,body='too short');kid.click('#shGo');kid.wait_for_timeout(400)
    ok('S8 too-short story refused, nothing stored','short' in st(kid) and len(G('/__community')['user_stories'])==0)
    fill_story(kid,title='   ');kid.click('#shGo');kid.wait_for_timeout(400)
    ok('S9 empty title refused','title' in st(kid).lower() and len(G('/__community')['user_stories'])==0)
    G('/__failinsert?on=1');fill_story(kid,file='/tmp/art.png');kid.click('#shGo');kid.wait_for_timeout(900)
    s=G('/__state');ok('S10 database failure: error shown, no success message','Nothing was sent' in st(kid) and 'Thank you' not in st(kid))
    ok('S10b ...nothing saved and the uploaded picture was cleaned up (no orphan file)',len(G('/__community')['user_stories'])==0 and len(s['files'])==0,s['files'])
    G('/__failinsert?on=0');G('/__failupload?on=1');kid.click('#shGo');kid.wait_for_timeout(700)
    ok('S11 picture upload failure: nothing saved, no success message','Thank you' not in st(kid) and len(G('/__community')['user_stories'])==0)
    G('/__failupload?on=0');kid.click('#shGo');kid.wait_for_function("document.querySelector('#shSt').textContent.startsWith('Thank')",timeout=10000)
    rows=G('/__community')['user_stories'];uid=kid.evaluate("KathaaSB.user().id")
    ok('S12 valid story saved as pending with the author\'s ID, language and no publish consent',len(rows)==1 and rows[0]['status']=='pending' and rows[0]['user_id']==uid and rows[0]['language']=='en' and rows[0]['publish_consent']==False and rows[0]['state_id'] is None and rows[0]['art_path'].startswith(uid+'/'),rows)
    ok('S13 confirmation appears only after storage and says it is private','private' in st(kid) and kid.evaluate("document.querySelector('#shForm #shTitle').value")=='')
    kid.wait_for_selector('#shList .ad-card');ok('S14 "My stories" shows it as waiting for review',('Waiting for review' in kid.inner_text('#shList')) and 'The Moon Who Lost His Hat' in kid.inner_text('#shList'))
    fill_story(kid,title='चाँद की टोपी',body='एक बार की बात है, एक छोटे चाँद की टोपी बादलों में खो गई और वह उसे ढूँढता रहा।',lang='hi',state='ka',pub=True);kid.click('#shGo');kid.wait_for_function("document.querySelectorAll('#shList .ad-card').length==2",timeout=10000)
    rows=G('/__community')['user_stories'];hi=[r for r in rows if r['language']=='hi'][0]
    ok('S15 Hindi story with a state and publish consent saved',hi['state_id']=='ka' and hi['publish_consent'] is True and hi['status']=='pending',hi)
    for i in range(3):
        fill_story(kid,title=f'Extra story {i}');kid.click('#shGo');kid.wait_for_timeout(500)
    fill_story(kid,title='One too many');kid.click('#shGo');kid.wait_for_timeout(600)
    ok('S16 more than 5 waiting stories is refused politely','5 stories waiting' in st(kid) and len(G('/__community')['user_stories'])==5)
    kid2=new(b);kid2.goto(BASE);kid2.wait_for_selector('#btnLogin',timeout=30000);signup(kid2,'Kid Two','kid2@test.com')
    n=kid2.evaluate("(async()=>{const r=await KathaaSB.client.from('user_stories').select('id');return r.data.length})()")
    ok('S17 another reader cannot see these stories',n==0,n)
    go(kid2,'#share');kid2.wait_for_selector('#shList');kid2.wait_for_timeout(600)
    ok('S18 another reader\'s "My stories" is empty','not sent a story' in kid2.inner_text('#shList'))
    t2=token(kid2);sid=rows[0]['id'];s,_=rest('/rest/v1/user_stories?id=eq.'+sid,'PATCH',t2,{'status':'published'});
    ok('S19 another reader cannot change someone else\'s story',G('/__community')['user_stories'][0]['status']=='pending')
    t1=token(kid);s,r=rest('/rest/v1/user_stories?id=eq.'+sid,'PATCH',t1,{'status':'published','admin_note':'x'});
    ok('S20 the author cannot publish or approve their own story',G('/__community')['user_stories'][0]['status']=='pending',s)
    s,_=rest('/rest/v1/user_stories','POST',t1,{'title':'Sneaky','body':'x'*30,'language':'en','consent_confirmed':True,'status':'published'});
    ok('S21 a new story cannot be inserted already published',s==403 and all(r['status']=='pending' for r in G('/__community')['user_stories']),s)
    # edit
    go(kid,'#share');kid.wait_for_selector('#shList .ad-card');kid.click('#shList .ad-card:has-text("चाँद की टोपी") button:has-text("Edit")');kid.wait_for_timeout(300)
    ok('S22 Edit fills the form with the story',kid.input_value('#shTitle')=='चाँद की टोपी' and kid.is_checked('#shPub'))
    kid.fill('#shTitle','चाँद की नई टोपी');kid.click('#shGo');kid.wait_for_function("document.querySelector('#shSt').textContent.startsWith('Thank')",timeout=10000)
    rows=G('/__community')['user_stories'];ok('S23 editing updates the same record, not a duplicate',len(rows)==5 and any(r['title']=='चाँद की नई टोपी' for r in rows),len(rows))
    # withdraw
    kid.wait_for_timeout(500);kid.once('dialog',lambda d:d.accept());kid.click('#shList .ad-card:has-text("Extra story 2") button:has-text("Withdraw")');kid.wait_for_timeout(900)
    ok('S24 withdrawing deletes the story',len(G('/__community')['user_stories'])==4)
    # ======================= moderation =======================
    adm=new(b);adm.goto(BASE);adm.wait_for_selector('#btnLogin',timeout=30000);signup(adm,'Admin','admin@test.com')
    go(kid2,'#admin');kid2.wait_for_timeout(1500)
    ok('M1 a normal user sees "administrators only" and no review list','administrators only' in kid2.inner_text('#adStories') and kid2.evaluate("document.querySelectorAll('#adStories .ad-card').length")==0)
    go(adm,'#admin');adm.wait_for_selector('#adStories .ad-card',timeout=20000)
    ok('M2 admin sees submitted stories with text, consent flags and picture',adm.evaluate("document.querySelectorAll('#adStories .ad-card').length")==4 and 'Consent to publish' in adm.inner_text('#adStories'))
    info=adm.evaluate("(async()=>{const im=document.querySelector('#adStories .ad-img img');if(!im)return 'noimg: '+document.querySelector('#adStories .ad-img').textContent;im.scrollIntoView();await new Promise(r=>setTimeout(r,1200));return [im.src,im.complete,im.naturalWidth]})()")
    ok('M3 admin picture preview loads (signed URL)',isinstance(info,list) and info[1] and info[2]>0,info)
    # request changes needs a note
    card=lambda title:adm.locator('#adStories .ad-card',has_text=title)
    card('The Moon Who Lost His Hat').locator('button:has-text("Request changes")').click();adm.wait_for_timeout(300)
    ok('M4 requesting changes without a note is refused','note' in adm.inner_text('#adStories .lis-st').lower() and G('/__community')['user_stories'][0]['status']=='pending')
    card('The Moon Who Lost His Hat').locator('textarea').fill('Lovely start! Please add what happens at the end.');card('The Moon Who Lost His Hat').locator('button:has-text("Request changes")').click();adm.wait_for_timeout(600)
    r0=[r for r in G('/__community')['user_stories'] if r['title']=='The Moon Who Lost His Hat'][0]
    ok('M5 changes requested: status and note stored',r0['status']=='revision_requested' and 'what happens' in r0['admin_note'])
    go(kid,'#share');kid.wait_for_selector('#shList .ad-card');kid.wait_for_timeout(400)
    ok('M6 the author sees the note and can edit',('Note from the team' in kid.inner_text('#shList')) and kid.evaluate("!![...document.querySelectorAll('#shList .ad-card')].find(c=>c.textContent.includes('Moon Who')&&c.textContent.includes('Edit'))"))
    kid.click('#shList .ad-card:has-text("Moon Who") button:has-text("Edit")');kid.fill('#shBody','Once upon a time a tiny moon lost his hat. At the end a kind star found it and gave it back.');kid.click('#shGo');kid.wait_for_function("document.querySelector('#shSt').textContent.startsWith('Thank')",timeout=10000)
    ok('M7 resubmitting sends it back to pending',[r for r in G('/__community')['user_stories'] if r['title']=='The Moon Who Lost His Hat'][0]['status']=='pending')
    # approve and check not public
    go(adm,'#admin');adm.wait_for_selector('#adStories .ad-card');adm.wait_for_timeout(400)
    card('The Moon Who Lost His Hat').locator('button:has-text("Approve")').click();adm.wait_for_timeout(700)
    pub=lambda:rest('/rest/v1/published_user_stories')[1]
    ok('M8 approved (but not published) stories are NOT publicly visible',pub()==[])
    ok('M9 Publish is disabled when the author gave no publish permission',adm.evaluate("(()=>{const c=[...document.querySelectorAll('#adStories .ad-card')].find(c=>c.textContent.includes('Moon Who'));return c?[...c.querySelectorAll('button')].find(b=>b.textContent.includes('Publish'))===undefined||[...c.querySelectorAll('button')].find(b=>b.textContent.includes('Publish')).disabled:true})()"))
    adm.select_option('#adStories select','all');adm.wait_for_timeout(600)
    card('चाँद की नई टोपी').locator('button:has-text("Publish")').click();adm.wait_for_timeout(900)
    pubs=pub();ok('M10 a story with permission can be published by an admin',len(pubs)==1 and pubs[0]['title']=='चाँद की नई टोपी',pubs)
    ok('M11 the public record contains no author ID, note or review data',pubs and not ({'user_id','admin_note','reviewed_by','status','consent_confirmed'}&set(pubs[0].keys())),pubs and list(pubs[0].keys()))
    ok('M12 other (pending/approved) stories remain private',len(pubs)==1 and len([r for r in G('/__community')['user_stories'] if r['status']!='published'])==3)
    # public readers page
    pa=new(b);pa.goto(BASE+'#readers');pa.wait_for_selector('#readersBody .cm-card',timeout=20000)
    ok('M13 public "Stories From Our Readers" shows only the published story',pa.evaluate("document.querySelectorAll('#readersBody .cm-card').length")==1 and 'by a reader' in pa.inner_text('#readersBody'))
    ok('M14 the collection says these are not traditional folktales','not traditional folktales' in pa.inner_text('#readersBody'))
    pa.click('#readersBody .cm-card');pa.wait_for_selector('.cm-story .cm-text')
    ok('M15 story page shows text, "by a reader" label and permission note',all(s in pa.inner_text('.cm-story') for s in ['A story by a Kathaa Sangam reader','Shared with permission','not a traditional folktale','Karnataka']) and pa.evaluate("document.querySelector('.cm-story .cm-text').lang")=='hi')
    ok('M16 no author identity shown','kid1' not in pa.inner_text('body') and 'Kid One' not in pa.inner_text('body'))
    s,_=rest('/rest/v1/user_stories');ok('M17 public still cannot read the private table',s in (401,403))
    # unpublish
    go(adm,'#admin');adm.wait_for_selector('#adStories .ad-card');adm.select_option('#adStories select','all');adm.wait_for_timeout(600)
    card('चाँद की नई टोपी').locator('button:has-text("Unpublish")').click();adm.wait_for_timeout(800)
    ok('M18 unpublishing removes it from the public collection',pub()==[])
    # reject & delete
    adm.select_option('#adStories select','all');adm.wait_for_timeout(500)
    card('Extra story 0').locator('button:has-text("Reject")').click();adm.wait_for_timeout(600)
    ok('M19 reject works',[r for r in G('/__community')['user_stories'] if r['title']=='Extra story 0'][0]['status']=='rejected')
    adm.once('dialog',lambda d:d.accept());card('Extra story 1').locator('button:has-text("Delete")').click();adm.wait_for_timeout(800)
    ok('M20 admin can delete a submission',not any(r['title']=='Extra story 1' for r in G('/__community')['user_stories']))
    pa.close()
    # ======================= 3. TESTIMONIALS =======================
    pv=new(b);pv.goto(BASE);pv.wait_for_selector('#links');pv.wait_for_timeout(1800)
    ok('V1 with no approved testimonials the section is hidden (no fake reviews)',pv.evaluate("document.querySelector('#voices').hidden===true&&document.querySelectorAll('#voicesList li').length===0"))
    ok('V2 page contains no invented quotation text',not re.search(r'loved it|my students|great app|5 stars',pv.inner_text('body'),re.I))
    s,_=rest('/rest/v1/testimonials');ok('V3 the testimonials table is not publicly readable',s in (401,403))
    s,_=rest('/rest/v1/testimonials','POST',t1,{'quote':'Fake quote here please','role':'student'});ok('V4 a normal user cannot add testimonials',s==403 and G('/__community')['testimonials']==[],s)
    ok('V5 admin testimonial panel is visible only to admins','administrators only' in kid2.inner_text('#adTesti'))
    adm.reload();adm.wait_for_selector('#adTesti form',timeout=20000)
    def addt(q,role='teacher',name='',child=False,perm=False,src=''):
        adm.fill('#tmQ',q);adm.select_option('#tmR',role);adm.fill('#tmN',name);adm.set_checked('#tmC',child);adm.set_checked('#tmP',perm);adm.fill('#tmS',src);adm.click('#tmGo');adm.wait_for_timeout(600)
    addt('TEST QUOTE written for the automated test only.','student','',True,False,'test note');
    ok('V6 draft saved but not public',len(G('/__community')['testimonials'])==1 and rest('/rest/v1/published_testimonials')[1]==[])
    tcard=lambda txt:adm.locator('#adTesti .ad-card',has_text=txt)
    tcard('TEST QUOTE').locator('button:has-text("Approve")').click();adm.wait_for_timeout(500)
    ok('V7 a child\'s testimonial cannot be approved without permission',G('/__community')['testimonials'][0]['status']=='draft' and 'permission' in adm.inner_text('#tmSt').lower())
    addt('TEST QUOTE two from a teacher, for the test only.','teacher','Test T.',False,False,'')
    tcard('TEST QUOTE two').locator('button:has-text("Approve")').click();adm.wait_for_timeout(500)
    ok('V8 approval needs a recorded source note',[t for t in G('/__community')['testimonials'] if 'two' in t['quote']][0]['status']=='draft')
    tcard('TEST QUOTE two').locator('button:has-text("Edit")').click();adm.fill('#tmS','Told to the team by email on 2026-11-01 (test)');adm.click('#tmGo');adm.wait_for_timeout(500)
    tcard('TEST QUOTE two').locator('button:has-text("Approve")').click();adm.wait_for_timeout(600)
    ok('V9 with a source note the testimonial can be approved',[t for t in G('/__community')['testimonials'] if 'two' in t['quote']][0]['status']=='approved')
    pv.reload();pv.wait_for_selector('#voicesList li',timeout=15000)
    vt=pv.inner_text('#voices');ok('V10 only the approved testimonial shows on the home page, with role and chosen name','TEST QUOTE two' in vt and 'Test T., Teacher' in vt and 'TEST QUOTE written' not in vt)
    ok('V11 the private source note and IDs are not public',all(k not in json.dumps(rest('/rest/v1/published_testimonials')[1]) for k in ['source_note','is_child','created_by','status']))
    adm.reload();adm.wait_for_selector('#adTesti .ad-card');tcard('TEST QUOTE written').locator('button:has-text("Edit")').click();adm.set_checked('#tmP',True);adm.fill('#tmS','Parent permission by email (test)');adm.click('#tmGo');adm.wait_for_timeout(500)
    tcard('TEST QUOTE written').locator('button:has-text("Approve")').click();adm.wait_for_timeout(600)
    ok('V12 a child\'s testimonial with permission and source can be approved',[t for t in G('/__community')['testimonials'] if 'written' in t['quote']][0]['status']=='approved')
    tcard('TEST QUOTE two').locator('button:has-text("Hide")').click();adm.wait_for_timeout(600)
    pv.reload();pv.wait_for_selector('#voicesList li',timeout=15000);ok('V13 hiding removes it from the home page',pv.evaluate("document.querySelectorAll('#voicesList li').length")==1 and 'TEST QUOTE two' not in pv.inner_text('#voices'))
    adm.once('dialog',lambda d:d.accept());tcard('TEST QUOTE written').locator('button:has-text("Delete")').click();adm.wait_for_timeout(700)
    pv.reload();pv.wait_for_timeout(1800);ok('V14 deleting removes it and the section hides again',pv.evaluate("document.querySelector('#voices').hidden===true"))
    # ======================= responsiveness =======================
    for w in (390,768):
        m=new(b,w);m.goto(BASE);m.wait_for_selector('#links',state='attached');m.wait_for_timeout(1200)
        ov=lambda:m.evaluate("document.documentElement.scrollWidth>innerWidth+2")
        ok(f'R{w}a home has no horizontal overflow',not ov())
        for h in ('abol','readers','share'):
            m.goto(BASE+'#'+h);m.wait_for_timeout(1200);ok(f'R{w} #{h} has no horizontal overflow',not ov())
        if w==390:
            m.goto(BASE);m.click('#burger');ok('R390 menu lists the new links',m.evaluate("[...document.querySelectorAll('#links.open a')].map(a=>a.textContent).includes('Abol Tabol')"))
        m.close()
    ok('E no JavaScript errors during the whole run',not errs,errs[:3])
    b.close()
print(f'\n{sum(res)} passed, {len(res)-sum(res)} failed of {len(res)} checks')
