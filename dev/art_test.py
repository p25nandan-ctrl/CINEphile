import json,urllib.request
from playwright.sync_api import sync_playwright
G=lambda u:json.load(urllib.request.urlopen('http://localhost:54321'+u))
def signup(pg,name,email):
    pg.evaluate("document.querySelector('#btnSignup').click()");pg.wait_for_selector('#authModal:not(.hidden)')
    pg.fill('#auName',name);pg.fill('#auEmail',email);pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#auLinks button')
    link=[m for m in G('/__mail') if m['to']==email][-1]['link'];pg.goto(link);pg.wait_for_selector('#btnMe',timeout=30000)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    ctx=b.new_context(viewport={'width':1280,'height':900});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:3000/#story/clever-jackal');pg.wait_for_selector('#btnLogin',timeout=30000);pg.wait_for_selector('#stArt h2')
    print('logged out:',pg.inner_text('#stArt').replace('\n',' | ')[:200])
    signup(pg,'Kid','kid@test.com');pg.goto('http://localhost:3000/#story/clever-jackal');pg.reload();pg.wait_for_selector('#artForm',timeout=20000);print('form shown after login')
    # no consent
    pg.set_input_files('#artFile','/tmp/art.png');pg.fill('#artTitle','My jackal');pg.click('#artGo');pg.wait_for_function("document.querySelector('#artSt').textContent.length>3");print('no consent ->',pg.inner_text('#artSt'),'| state',G('/__state'))
    # wrong type (fake png) and too big
    pg.set_input_files('#artFile','/tmp/fake.png');pg.check('#artOk');pg.click('#artGo');pg.wait_for_timeout(500);print('fake image ->',pg.inner_text('#artSt'),'| files',len(G('/__state')['files']))
    pg.set_input_files('#artFile','/tmp/big.png');pg.wait_for_timeout(300);print('big ->',pg.inner_text('#artSt'))
    # insert fails: file must be cleaned up and no success message
    G('/__failinsert?on=1');pg.set_input_files('#artFile','/tmp/art.png');pg.check('#artOk');pg.click('#artGo');pg.wait_for_timeout(800)
    s=G('/__state');print('insert fails ->',pg.inner_text('#artSt'),'| files',len(s['files']),'rows',len(s['rows']))
    G('/__failinsert?on=0');G('/__failupload?on=1');pg.click('#artGo');pg.wait_for_timeout(800);s=G('/__state');print('upload fails ->',pg.inner_text('#artSt'),'| files',len(s['files']),'rows',len(s['rows']));G('/__failupload?on=0')
    # success
    pg.click('#artGo');pg.wait_for_function("document.querySelector('#artSt').textContent.startsWith('Thank')");s=G('/__state');print('success ->',pg.inner_text('#artSt'),'| files',len(s['files']),'rows',len(s['rows']),s['rows'][0]['story_id'],s['rows'][0]['status'],s['rows'][0]['storage_path'][-12:]);pg.screenshot(path='/tmp/art_form.png',full_page=False)
    # child cannot open admin page
    pg.goto('http://localhost:3000/#admin');pg.wait_for_selector('#adBody p',timeout=15000);print('child at #admin ->',pg.inner_text('#adBody'))
    # admin
    a=b.new_context(viewport={'width':1280,'height':900}).new_page();a.on('pageerror',lambda e:errs.append(str(e)))
    a.goto('http://localhost:3000/');a.wait_for_selector('#btnLogin',timeout=30000);signup(a,'Admin','admin@test.com')
    a.evaluate("location.hash='admin'");a.wait_for_selector('.ad-card',timeout=20000);print('admin sees:',a.inner_text('.ad-card').replace('\n',' | '));a.screenshot(path='/tmp/admin.png')
    a.click('text=✅ Approve');a.wait_for_function("document.querySelectorAll('.ad-card').length===0");print('after approve, pending list empty; state',G('/__state')['rows'][0]['status'])
    a.select_option('.lis-bar select','approved');a.wait_for_selector('.ad-card');print('approved list shows',len(a.query_selector_all('.ad-card')),'| img src has signed token:', 'token=' in a.get_attribute('.ad-img img','src'))
    print('errors',errs)
    b.close()
