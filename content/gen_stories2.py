import json,glob,re,sys
sys.path.insert(0,'/home/claude/g2')
D='/home/claude/content/stories2/'
IMGM=json.load(open('/home/claude/g2/imgmeta.json'))
ALT={
'the-crow-and-the-sparrow':'Red-and-white folk-art illustration of a crow and a sparrow with their nests in a tree, beside thatched huts, a river and a snake.',
'the-magic-ring':'Red-and-white folk-art illustration of a man, a pig, a tiger, a cat, a dog and mice, with a glowing ring passing between them among huts and trees.',
'the-clever-hare':'Folk-art illustration of a tiger crouching by a pond, looking at a white hare sitting on a rock, with a hornbill in the tree above and deer behind.',
'the-egotistical-elephant-and-the-praying-pebet':'Folk-art illustration of a decorated elephant standing in the rain by a pond, with a small creature sitting on a lily pad in front of it.',
'chawngtinleri':'Folk-art illustration of a woman in traditional dress sitting on a hillside with a deer, a hornbill and small animals, while a young man with a basket looks up at her.',
'chemtatrawta':'Folk-art illustration of a young man holding up a prawn beside a stream, with a dog, a cat, a pig and a goat running toward him and a woman on the hillside behind.',
'the-tiger-and-the-man':'Folk-art illustration of a man sitting under a tree with a tiger and a clay pot, with smaller scenes of a man walking through the forest and fleeing a tiger.',
'licha-ba':'Folk-art illustration of a bamboo house on a terraced hillside, with an old traveller standing near a pot of rice while villagers harvest and carry rice.',
'dharmapada':'Folk-art illustration in several panels: craftsmen at work on a great stone temple, a boy studying plans, and a figure flying above the sunlit sea beside the temple’s stone wheel.',
'sivai-santara':'Folk-art illustration in several panels: craftsmen building a temple, an old woman serving a bowl of rice, and the finished temple with its stone wheel beside the sea.',
'raja-rasalu':'Folk-art illustration of a prince on a white horse before a fort, with smaller scenes of a hermit under a tree, a snake and a kneeling figure.',
'puran-bhagat':'Folk-art illustration in several panels: a royal couple and courtiers, a man looking down a well, and a robed yogi seated under a tree.',
'dhola-maru':'Folk-art illustration of travellers on camels and horses crossing desert dunes toward a palace, with a tiger and a wedding scene.',
'panna-dhai':'Folk-art illustration of a white palace at night with a woman and a child sleeping inside, and a camel cart travelling across the desert below.',
'children-of-the-snowy-peaks':'Folk-art illustration of two figures cupping water that falls from the sky between two heavenly figures among clouds, with a red panda, a sheep and villagers below the snowy mountains.',
'the-race-between-teesta-and-rangeet':'Folk-art illustration of two women racing as rivers through the mountains, with flowers, snowy peaks and a village below.',
'sammakka':'Folk-art illustration in several panels: a child lying in a forest beside a deer, a man and women, a woman with a spear, and a crowd gathered around decorated shrines.',
'sammakka-and-saralamma':'Folk-art illustration in several panels: a warrior woman with a spear, a king on a horse with his soldiers, a golden light in the forest, and a crowd gathered around decorated shrines.',
'nwai':'Illustration in six panels showing village scenes: a family outside a bamboo house, women cooking, a girl in the forest at night, an old person and a girl, and a woven cloth.',
'chethuang':'Illustration in four panels showing village life: farmers in a field, two young people on a porch, villagers on a path, and two young people beside a tree.',
'the-four-fairies':'Folk-art illustration in several panels: a woman beside a man in bed, four fairies under a tree at night, a pot of rice and a cow, a man carrying a sack, and a man in the water.',
'the-clever-jackal-up':'Folk-art illustration in several panels: jackals resting in a cave, a tiger approaching the cave, jackals calling out, and the tiger running away.',
'fyoli':'Illustration in six panels: a girl beside a lake with deer, a prince on horseback, a girl carried in a palanquin, a girl alone in a room, a prince at her side, and a yellow flower growing on a hillside.',
'ghughutiya':'Illustration of a couple sitting with a small boy under a tree where a crow is perched, with smaller panels of a man carrying a child at night, a child in a cave with a crow and a necklace, and villagers with crows.',
'bonobibi-and-shah-jangali':'Folk-art illustration in several panels: villagers in a boat, a woman and a man standing with a tiger, a king, and a boat on the river.',
'the-match-making-jackal':'Folk-art illustration in several panels: jackals with a lion and a lioness, a wedding of two lions, deer, an elephant, a rabbit and other forest animals.',
'ka-pah-syntiew':'Illustration in several panels: a woman in a cave, a woman offering flowers, villagers in the hills, standing stones, and a spirit in the clouds.',
'the-legend-of-mount-sophet-bneng':'Illustration in several panels: figures in the sky above a great tree on a mountain, villagers felling the tree, and families in the hill country with a basket of grain.',
'the-precious-present':['Wular Lake villagers in a boat, gathering water-nuts, with mountains behind.','An old villager holds up a shiny silver coin while others look on.','Villagers gather round the headman, who speaks to them about the coin.','A palanquin carried by boat across the lake.','The ruler and his courtiers in the palace, with the open palanquin.','The ruler holds up a matchbox while the villagers stand before him.','The villagers receive a sack of grain from the ruler.'],
'shabrang':['A king on his throne, with his neglected daughter Shabrang looking sad.','Shabrang in a hooded shawl walks away from the palace toward the mountains.','Shabrang learns from a thief who holds a bag of gold.','Shabrang, in disguise, walks back into the city.','At the royal court, the king and the disguised Shabrang speak across a table.','Shabrang speaks to the king, revealing who she is.','The king and Shabrang smile at one another.'],
'the-monkey-and-the-fox':['A monkey and a fox sit side by side in the forest.','Men carry baskets of bananas and sweets for a wedding.','The fox hides in the bushes while the men run away.','The monkey in the tree eats the food, while banana peels fall to the fox below.','The monkey is stung by hornets.','The monkey eats a burning arum plant.','The monkey sits on a cobweb-covered well.'],
'the-ow-princess':['A queen lies beside a large ow fruit.','A princess steps out of the ow fruit.','A prince in a boat sees the princess by the river.','The princess eats alone at night while the prince sleeps.','The prince talks with an old woman.','The prince burns the ow shell while the princess lies nearby.','The prince and princess in wedding garlands.']}
GENRE={}
PANEL={'the-precious-present','shabrang','the-monkey-and-the-fox','the-ow-princess'}
def cuts(w,N):
    tot=sum(w);cum=[0]
    for x in w:cum.append(cum[-1]+x)
    out=[];prev=0
    for k in range(1,N):
        lo=prev+1;hi=len(w)-(N-k)
        j=min(range(lo,hi+1),key=lambda j:abs(cum[j]-tot*k/N));out.append(j);prev=j
    return out
def grp(n,c):
    b=[0]+c+[n];return [list(range(b[i],b[i+1])) for i in range(len(b)-1)]
def pages(en,hi,N):
    if len(en)==len(hi):
        c=cuts([len(a)+len(b) for a,b in zip(en,hi)],N);g=grp(len(en),c);return g,g
    return grp(len(en),cuts([len(x) for x in en],N)),grp(len(hi),cuts([len(x) for x in hi],N))
fn=lambda s:s.replace('पे्बेट','पेबेट')  # stray virama in the supplied Hindi (logged in INTERNAL report)
out=[];META={}
for f in sorted(glob.glob(D+'*.json')):
    d=json.load(open(f,encoding='utf8'))
    sid=d['id'];L=d['levels']
    N=7 if sid in PANEL else max(3,min(7,min(min(len(L[k]['texts']['en']),len(L[k]['texts']['hi'])) for k in L)))
    lv={}
    for k in '123':
        en=L[k]['texts']['en'];hi=[fn(x) for x in L[k]['texts']['hi']]
        pe,ph=pages(en,hi,N)
        e={'texts':{'en':en,'hi':hi},'vocab':[],'questions':[],'pages':{'en':pe,'hi':ph}}
        lt=d['levelTitles'][k]
        if lt.get('en'):e['title']=lt['en'];e['titleHi']=fn(lt.get('hi') or d['titleHi'])
        lv[k]=e
    heading=d['title'];title=heading.split(' — ')[0].strip()
    sub=fn(d['levelTitles']['1'].get('hi') or d['titleHi'])
    if sid in PANEL:
        imgs=IMGM[sid];alts=ALT[sid];scenes=[{'t':'','th':'','p':alts[i]} for i in range(N)];simg=imgs;salt=alts;cover=imgs[0]
    else:
        path,size=IMGM[sid];scenes=[{'t':'','th':'','p':ALT[sid]} for _ in range(N)];simg=[path]+[None]*(N-1);salt=[ALT[sid]]+['']*(N-1);cover=path
    r={'id':sid,'state':d['state'],'title':title,'titleHi':sub,'genre':d['genre'],'lv':2,'levelNote':'',
       'texts':lv['2']['texts'],'vocab':[],'questions':[],'levels':lv,'imagine':'','create':'','scenes':scenes,'pages':lv['2']['pages'],
       'sceneImages':simg,'sceneAlt':salt,'cover':cover,'artCredit':'Illustrations supplied with the story repository.',
       'about':d['about'],'sources':d['sources']}
    r['about']['links']=[];out.append(r)
    META[sid]={'summary':d['about']['tradition'],'from':d['about']['where'],'match':{'puran-bhagat':'Puran Bhagat','dhola-maru':'Dhola and Maru','panna-dhai':'Panna Dhai','sammakka-and-saralamma':'Sammakka and Saralamma'}.get(sid)}
js=['/* generated by /home/claude/content/gen_stories2.py from content/stories2/*.json: do not edit by hand */','(function(){','const GEN=%s;'%json.dumps(out,ensure_ascii=False),'const META=%s;'%json.dumps(META,ensure_ascii=False),
'const MOT=["sun","moon","wave","hills","flower","fort"];',
'GEN.forEach((r,n)=>{REAL[r.id]=r;const st=STATES[r.state];if(!st)return;const m=META[r.id];',
' const ex=st.books.find(b=>b.t===(m.match||r.title));',
' const book={t:r.title,sub:r.titleHi,lv:r.lv,th:st.ico||"📖",m:MOT[n%MOT.length],d:m.summary,from:m.from,story:r.id,texts:r.texts};',
' if(ex){Object.assign(ex,{story:r.id,texts:r.texts,lv:r.lv,sub:r.titleHi});r.ico=st.ico}else{st.books.unshift(book);r.ico=st.ico}});',
'})();']
open('/home/claude/site/stories_gen2.js','w',encoding='utf8').write('\n'.join(js))
print(len(out),'stories')
