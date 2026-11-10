import json,urllib.request,re
from playwright.sync_api import sync_playwright
def mails(): return json.load(urllib.request.urlopen('http://localhost:54321/__mail'))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    pg=b.new_context(viewport={'width':1280,'height':800}).new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:3000/');pg.wait_for_selector('#btnLogin',timeout=30000)
    print('slot ok');pg.screenshot(path='/tmp/a0.png')
    pg.evaluate("document.querySelector('#btnSignup').click()");pg.wait_for_selector('#authModal:not(.hidden)')
    pg.fill('#auName','Asha');pg.fill('#auEmail','asha@test.com');pg.fill('#auPass','short');pg.click('#auGo')
    print('short pw msg:',pg.inner_text('#auMsg'))
    pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_selector('#auLinks button')
    print('after signup:',pg.inner_text('#authTitle'),'|',pg.inner_text('#auSub'));pg.screenshot(path='/tmp/a1.png')
    # login before confirm
    pg.click('text=Back to log in');pg.fill('#auEmail','asha@test.com');pg.fill('#auPass','goodpass123');pg.click('#auGo')
    pg.wait_for_function("document.querySelector('#authTitle').textContent==='Check your email'");print('unconfirmed ->',pg.inner_text('#auSub'))
    # wrong password
    pg.click('text=Back to log in');pg.fill('#auEmail','asha@test.com');pg.fill('#auPass','wrongpass99');pg.click('#auGo');pg.wait_for_function("document.querySelector('#auMsg').textContent.length>0")
    print('invalid:',pg.inner_text('#auMsg'));pg.screenshot(path='/tmp/a2.png')
    # existing email signup => same generic
    pg.click('#tabSignup');pg.fill('#auEmail','asha@test.com');pg.fill('#auPass','goodpass123');pg.click('#auGo');pg.wait_for_function("document.querySelector('#authTitle').textContent==='Check your email'");print('dup signup generic ok')
    # verify via email link
    link=[m for m in mails() if m['kind']=='signup'][0]['link'];print('link redirect',link[-60:])
    pg.keyboard.press('Escape');pg.goto(link);pg.wait_for_selector('#btnMe',timeout=30000)
    print('verified, url:',pg.url,'| chip:',pg.inner_text('#btnMe'),'| toast:',pg.inner_text('#toast'));pg.screenshot(path='/tmp/a3.png')
    # persistence
    pg.reload();pg.wait_for_selector('#btnMe',timeout=30000);print('persist after reload ok')
    # account page
    pg.evaluate("location.hash='account'");pg.wait_for_selector('.acv-top',timeout=15000);print('account:',pg.inner_text('.acv-top').replace('\n',' '));pg.screenshot(path='/tmp/a4.png')
    # logout
    pg.evaluate("document.querySelector('#btnMe').click()");pg.evaluate("document.querySelector('#btnLogout').click()");pg.wait_for_selector('#btnLogin');print('logout ok, hash=',repr(pg.evaluate('location.hash')))
    pg.reload();pg.wait_for_selector('#btnLogin');print('stays logged out after reload')
    # direct #account when logged out
    pg.goto('http://localhost:3000/#account');pg.wait_for_selector('#authModal:not(.hidden)',timeout=15000);print('protected: login modal opened')
    pg.keyboard.press('Escape')
    # forgot
    pg.evaluate("document.querySelector('#btnLogin').click()");pg.click('text=Forgot password?');pg.fill('#auEmail','asha@test.com');pg.click('#auGo');pg.wait_for_function("document.querySelector('#authTitle').textContent==='Check your email'");print('forgot generic:',pg.inner_text('#auSub'))
    rl=[m for m in mails() if m['kind']=='recovery'][0]['link']
    pg.goto(rl);pg.wait_for_selector('#authModal:not(.hidden)',timeout=30000);print('reset view title:',pg.inner_text('#authTitle'))
    pg.fill('#auPass','newpass12345');pg.fill('#auPass2','different123');pg.click('#auGo');print('mismatch:',pg.inner_text('#auMsg'))
    pg.fill('#auPass2','newpass12345');pg.click('#auGo');pg.wait_for_selector('#authModal.hidden',state='attached');print('reset ok toast:',pg.inner_text('#toast'),'| url',pg.url)
    # expired link
    pg.goto('http://localhost:54321/auth/v1/verify?c=nope&redirect_to=http%3A%2F%2Flocalhost%3A3000%2F%3Fauth%3Dverified');pg.wait_for_selector('#authModal:not(.hidden)',timeout=30000);print('expired link:',pg.inner_text('#auMsg'))
    print('errors:',errs)
    # mobile
    m=b.new_context(viewport={'width':390,'height':844}).new_page();m.goto('http://localhost:3000/');m.wait_for_selector('#btnLogin',timeout=30000);m.screenshot(path='/tmp/m0.png')
    m.evaluate("document.querySelector('#btnLogin').click()");m.wait_for_selector('#authModal:not(.hidden)');m.screenshot(path='/tmp/m1.png')
    print('mobile overflow:',m.evaluate("document.documentElement.scrollWidth>innerWidth"))
    b.close()
