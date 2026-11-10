import json,re,sys
def devan(s): return bool(re.search(r'[ऀ-ॿ]',s))
def latin(s): return re.findall(r'[A-Za-z]+',s)
def check(path):
    e=[];w=[]
    try: d=json.load(open(path,encoding='utf8'))
    except Exception as x: return ['invalid JSON: %s'%x],[]
    for k in ['id','state','title','titleHi','summary','summarySource','genre','from','origLevel','levelReason','levels','pages','scenes','artStyle','imagine','create','about','sources','reviewFlags']:
        if k not in d: e.append('missing '+k)
    if e: return e,w
    L=d['levels']
    if set(L)!={'1','2','3'}: e.append('levels must be 1,2,3'); return e,w
    n=len(L['1']['texts']['en'])
    for lv in '123':
        t=L[lv]['texts']
        for lang in ('en','hi'):
            if len(t[lang])!=n: e.append(f'L{lv} {lang}: {len(t[lang])} paragraphs, expected {n}')
        for i,p in enumerate(t['hi']):
            if not devan(p): e.append(f'L{lv} hi para {i} has no Devanagari')
            bad=latin(p)
            if bad: e.append(f'L{lv} hi para {i} has Latin letters: {bad[:3]}')
        for i,p in enumerate(t['en']):
            if devan(p): e.append(f'L{lv} en para {i} contains Devanagari')
        v=L[lv]['vocab']
        if not 8<=len(v)<=12: e.append(f'L{lv} vocab count {len(v)} (need 8-12)')
        en=' '.join(t['en'])
        for x in v:
            if not re.search(r'\b'+re.escape(x['w'])+r'\b',en,re.I): e.append(f'L{lv} vocab "{x["w"]}" not found in English text')
            if not devan(x['hi']) or latin(x['hi']): e.append(f'L{lv} vocab "{x["w"]}" Hindi must be Devanagari only')
            if not x['en'].strip(): e.append(f'L{lv} vocab "{x["w"]}" empty meaning')
        q=L[lv]['questions']
        if len(q)!=5: e.append(f'L{lv} needs 5 questions, has {len(q)}')
        words=len(en.split()); sents=max(1,len(re.findall(r'[.!?]+(?:\s|$)',en)))
        w.append(f'L{lv}: {words} words, {words/sents:.1f} words/sentence, vocab {len(v)}')
    flat=[i for pg in d['pages'] for i in pg]
    if flat!=list(range(n)): e.append('pages must list every paragraph index 0..%d once, in order'%(n-1))
    if len(d['scenes'])!=len(d['pages']): e.append('scenes (%d) must equal pages (%d)'%(len(d['scenes']),len(d['pages'])))
    for i,s in enumerate(d['scenes']):
        for k in ('t','th','p'):
            if not s.get(k): e.append(f'scene {i} missing {k}')
        if s.get('th') and (not devan(s['th']) or latin(s['th'])): e.append(f'scene {i} th must be Devanagari only')
    for pi,pg in enumerate(d['pages']):
        wc=len(' '.join(L['3']['texts']['en'][i] for i in pg).split())
        if wc>150: e.append(f'spread {pi} has {wc} words at level 3 (max ~150)')
    if not devan(d['titleHi']) or latin(d['titleHi']): e.append('titleHi must be Devanagari only')
    for k in ('where','community','tradition','shared','matters','links'):
        if k not in d['about']: e.append('about.'+k+' missing')
    if d['origLevel'] not in (1,2,3): e.append('origLevel')
    if len(d['summary'].split())>45: w.append('summary long')
    return e,w
if __name__=='__main__':
    bad=0
    for p in sys.argv[1:]:
        e,w=check(p); print(p); [print('  ERROR',x) for x in e]; [print('  info',x) for x in w]; bad+=bool(e)
    sys.exit(1 if bad else 0)
