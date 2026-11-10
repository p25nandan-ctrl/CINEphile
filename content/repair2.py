import json,re,glob,unicodedata
N=lambda s:unicodedata.normalize('NFC',s)
D='/home/claude/content/stories2/'
log=[]
def sub(d,pairs,sid):
    for k in '123':
        L=d['levels'][k]['texts']['hi']
        for i,p in enumerate(L):
            q=N(p)
            for a,b in pairs:
                a=N(a);b=N(b)
                if a in q: q=q.replace(a,b)
            if q!=N(p): log.append((sid,k,i,p,q));L[i]=q
FIX={
'bonobibi-and-shah-jangali':[('सुदरबन','सुंदरबन'),('डरे ं हुए','डरे हुए'),('कि ं जंगल','कि जंगल')],
'chawngtinleri':[('लालचुगनुंगा','लालचुंगनुंगा'),(' ंगनु',''),('हुआ। ं जब','हुआ। जब'),('अपने ं बच्चे','अपने बच्चे')],
'shabrang':[('सुदर बाग़','सुंदर बाग़'),('गुलाबों के बीच ं शाम','गुलाबों के बीच शाम'),
 ('पहुंदरता से मुग्ध होकर राजा ने बिना ँचा, जहाँ एक युवती खड़ी थी। उसकी सु जाने कि','पहुँचा, जहाँ एक युवती खड़ी थी। उसकी सुंदरता से मुग्ध होकर राजा ने बिना जाने कि')],
'the-clever-hare':[('छोड़गा!" ूँ','छोड़ूँगा!"')],
'the-magic-ring':[('चाहता हूँगा।" ँ। मेरे साथ चलो। मैं तुम्हें एक अनमोल वस्तु दू','चाहता हूँ। मेरे साथ चलो। मैं तुम्हें एक अनमोल वस्तु दूँगा।"')],
'the-monkey-and-the-fox':[('छिपती हू।','छिपती हूँ।'),('तब तुम ँ चिल्लाना','तब तुम चिल्लाना'),('दुबकती हू।','दुबकती हूँ।'),('खोआ! ँ अचानक','खोआ! अचानक'),
 ('जंगल होआ और खोआ से ऐसा गूंड टूट पड़ा हो। बाघ या भालू ँजा, मानो जानवरों का पूरा झु के हमले का','जंगल होआ और खोआ से ऐसा गूँज उठा, मानो जानवरों का पूरा झुंड टूट पड़ा हो। बाघ या भालू के हमले का'),
 ('छोड़गा।" ूँ','छोड़ूँगा।"')],
'the-precious-present':[('वहाँ पहुंदर लगती थी, ँचने के दो ही रास्ते थे: पहाड़ की तंग पगडंडियाँ, या फिर झील, जो शांत हो तो बड़ी सु पर हवा चलते ही जानलेवा','वहाँ पहुँचने के दो ही रास्ते थे: पहाड़ की तंग पगडंडियाँ, या फिर झील, जो शांत हो तो बड़ी सुंदर लगती थी, पर हवा चलते ही जानलेवा')],
'the-egotistical-elephant-and-the-praying-pebet':[(' ्',''),('पे्बेट','पेबेट'),('पे ्बेट','पेबेट')]}
for sid,pairs in FIX.items():
    f=D+sid+'.json';d=json.load(open(f,encoding='utf8'));sub(d,pairs,sid)
    json.dump(d,open(f,'w',encoding='utf8'),ensure_ascii=False,indent=1)
json.dump(log,open('/home/claude/content/repair2_log.json','w'),ensure_ascii=False,indent=1)
print(len(log),'paragraphs repaired')
