"""Short authored Arabic fallback scripts. No claim of reconstructed medieval speech.
Unknown native event tokens fail closed; aliases are explicit semantic decisions.
"""
from __future__ import annotations
import re

SOURCE = 'authored Arabic fallback; historical framing: history.md; native-speaker/audio review pending'
# Identity reflects the actor, not the gender of Arabic occupational nouns.
_ROLES = {
'villager':('عامل','worker','male','earthy, diligent, conversational'),
'scout':('كشاف','scout','male','alert, light, observant'),
 'tuareg':('حارس الصحراء','desert guard','male','dry, restrained, watchful'),
 'trader':('تاجر','merchant','male','warm, measured, shrewd'),
 'mehari':('راكب المهري','camel rider','male','unhurried, resonant'),
 'sanhaja':('حارس صنهاجة','Sanhaja guard','male','low, steadfast'),
 'zenata':('فارس زناتة','Zenata rider','male','quick, incisive'),
 'archer':('رامي','archer','male','precise, clear'),
 'masmuda':('مقاتل مصمودة','Masmuda fighter','male','firm, grounded'),
 'lancer':('حامل الرمح','lancer','male','confident, clipped'),
 'imam':('إمام','imam','male','calm, compassionate, dignified'),
 'handgunner':('رامية','gunner','female','controlled, bright, resolute'),
 'ram':('طاقم الكبش','ram crew','male','rough, coordinated exertion'),
 'siege_tower':('طاقم البرج','tower crew','male','projected, practical'),
 'springald':('طاقم القاذف','springald crew','male','focused, technical'),
 'mangonel':('طاقم المنجنيق','mangonel crew','male','gravelly, deliberate'),
 'trebuchet':('طاقم المنجنيق الكبير','trebuchet crew','male','mature, commanding'),
 'bombard':('طاقم المدفع','bombard crew','male','weighty, disciplined'),
 'fishing_boat':('صياد','fisher','male','easy, weathered'),
 'trade_ship':('تاجر البحر','sea merchant','male','friendly, assured'),
 'transport_ship':('ربان النقل','transport master','male','steady, reassuring'),
 'arrow_ship':('رامي البحر','naval archer','male','crisp, vigilant'),
 'combat_ship':('مقاتل البحر','naval fighter','male','bold, salt-weathered'),
 'fire_ship':('حارس النار','fire-ship crew','male','intense, urgent'),
 'warship':('ربان الحرب','warship captain','male','deep, authoritative'),
 'king':('أمير','ruler','male','mature, restrained authority')}
PERSONAS = {k:dict(role_ar=v[0],role_en=v[1],gender=v[2],direction=v[3]) for k,v in _ROLES.items()}
# Each row contains five short semantic takes, with matching English glosses.
ROWS = {}
def row(key, arabic, english):
    a=arabic.split('|'); e=english.split('|')
    assert len(a)==len(e)==5, key
    ROWS[key]=list(zip(a,e))
row('select','أنا {role}|{role} حاضر|{role} مستعد|{role} يسمعك|هنا {role}', 'I am the {role}|The {role} is here|The {role} is ready|The {role} hears you|Here is the {role}')
row('acknowledge','سمعا|حاضر|كما تأمر|أفعل ذلك|أمرك مطاع','Understood|At your service|As you command|I will do it|Your order is obeyed')
row('move','نتقدم|نسير|إلى هناك|في الطريق|نتحرك','We advance|We march|Over there|On the way|We move')
row('attack','اضربوا|على العدو|هاجموا|إلى القتال|لا تتراجعوا','Strike|Against the enemy|Attack|Into battle|Do not retreat')
row('hold','اثبتوا|الزموا المكان|هنا نبقى|احفظوا الصف|لا تتحركوا','Stand firm|Hold this place|We stay here|Keep the line|Do not move')
row('stop','قفوا|توقفوا|كفى مسيرا|نقف هنا|توقفوا هنا','Halt|Stop|Enough marching|We halt here|Stop here')
row('garrison','إلى الحصن|ادخلوا|نحتمي هنا|إلى الداخل|وراء الجدران','To the fort|Enter|We shelter here|Inside|Behind the walls')
row('formation','انتظموا|رصوا الصف|غيروا الصفوف|إلى مواقعكم|احفظوا النظام','Form up|Close the line|Change ranks|To your positions|Keep formation')
row('brace','ثبتوا الرماح|استعدوا للصدمة|اثبتوا أمامهم|الرماح للأمام|لا تهتزوا','Brace spears|Brace for impact|Stand against them|Spears forward|Do not waver')
row('enemy','العدو أمامنا|أرى العدو|خصم قريب|حذار من العدو|ظهر العدو','Enemy ahead|I see the enemy|Foe nearby|Beware the enemy|The enemy appears')
row('underattack','نتعرض لهجوم|احمونا|العدو يضربنا|نحتاج العون|إلينا يا رجال','We are attacked|Protect us|The enemy strikes us|We need help|To us, men')
row('victory','لنا النصر|ظفرنا|الحمد لله|انكسر العدو|أحسنتم','Victory is ours|We prevailed|Praise God|The enemy is broken|Well done')
row('destroyed','سقط الهدف|انتهى أمره|دمرناه|أصبناه|قضينا عليه','Target down|It is finished|We destroyed it|We hit it|We finished it')
row('idle','نحفظ الطريق|ننتظر الأمر|ما زلنا نسير|الصف ثابت|الطريق أمامنا','We guard the road|Awaiting orders|Still marching|The line is steady|The road lies ahead')
row('build','نضع الأساس|نبني هنا|إلى البناء|نرفع الجدران|نبدأ البناء','Lay foundations|We build here|To construction|Raise the walls|Begin building')
row('repair','نصلح الضرر|إلى الإصلاح|نرمم هذا|نسد الخلل|نصلحه الآن','Repair damage|To repairs|Restore this|Mend the break|Repair it now')
row('hunt','إلى الصيد|نتبع الطريدة|أرى الصيد|نصطاد هنا|نقتفي الأثر','To the hunt|Follow the quarry|I see game|We hunt here|Follow the tracks')
row('wood','نقطع الخشب|إلى الحطب|نحتطب هنا|إلى الأشجار|نجمع الخشب','Cut wood|To firewood|Gather wood here|To the trees|Collect wood')
row('food','نجمع الطعام|إلى الثمار|نجني القوت|نحصد هنا|نأتي بالطعام','Gather food|To the fruit|Gather provisions|Harvest here|Bring food')
row('gold','نستخرج الذهب|إلى الذهب|نحفر هنا|نجمع الذهب|نطلب الذهب','Extract gold|To the gold|Dig here|Gather gold|Seek gold')
row('stone','نقطع الحجر|إلى المحجر|نجمع الحجر|نقتلع الصخور|نحمل الحجر','Cut stone|To the quarry|Collect stone|Break rocks|Carry stone')
row('fish','نلقي الشباك|نصيد السمك|إلى الصيد|نسحب الشباك|نطلب الرزق','Cast nets|Catch fish|To fishing|Pull nets|Seek our livelihood')
row('farm','نحرث الأرض|نزرع هنا|إلى الحقول|نروي الزرع|نعمل في الحقل','Plough land|Plant here|To the fields|Water crops|Work the field')
row('trade','إلى السوق|نسلك طريق التجارة|نحمل البضاعة|نطلب الربح|نبيع ونشتري','To market|Take trade route|Carry goods|Seek profit|Buy and sell')
row('heal','أداوي الجرح|هون عليك|أعالج المصاب|إليك الدواء|ارفقوا بالجرحى','Tend the wound|Take heart|Treat the wounded|Here is medicine|Care for the wounded')
row('convert','إلى الهدى|اسمعوا الدعوة|اهتدوا|أقبلوا بسلام|استجيبوا للدعوة','Toward guidance|Hear the call|Find guidance|Come in peace|Answer the call')
row('relic','نحمل الأمانة|نحفظ الأثر|إلى الموضع الآمن|نصون الأمانة|نحمل الأثر','Carry the trust|Preserve the relic|To safety|Safeguard the trust|Carry the relic')
row('embark','اصعدوا السفينة|إلى المركب|اركبوا|نحمل الركاب|الجميع إلى السفينة','Board the ship|To the boat|Embark|Take passengers|All aboard')
row('unload','انزلوا هنا|إلى البر|أنزلوا الركاب|بلغنا الشاطئ|اخرجوا إلى البر','Disembark here|To land|Unload passengers|Reached shore|Go ashore')
row('navalmove','ارفعوا الشراع|نبحر الآن|إلى البحر|وجهوا المركب|نسلك هذا المجرى','Raise sail|Sail now|To sea|Steer the vessel|Take this channel')

ALIASES={}
def aliases(semantic,tokens):
    for token in tokens.split(): ALIASES[token]=semantic
aliases('select','select selectgc selectsu selectsametypegc')
aliases('acknowledge','acknowledge acknowledgegmr')
aliases('move','move movegc movesu movesametypegc')
aliases('attack','attack attackmovegc attackmovesu attacksametypegc engage ambientcombat')
aliases('formation','changeformation'); aliases('brace','brace'); aliases('hold','hold'); aliases('stop','stop')
aliases('garrison','garrison'); aliases('enemy','enemyspotted'); aliases('underattack','underattack')
aliases('victory','celebrate reactproud'); aliases('destroyed','targetdestroyed'); aliases('idle','marchingidle')
aliases('build','structurebuild build'); aliases('repair','structurerepair repair')
aliases('hunt','resourcehunt'); aliases('wood','resourcewood resourcechop'); aliases('food','resourcefood resourcegather resourceforage resourceharvest')
aliases('gold','resourcegold'); aliases('stone','resourcestone'); aliases('fish','resourcefish fishing fish')
aliases('farm','resourcefarm farm'); aliases('trade','trade traderoute resourcetrade')
aliases('heal','heal healing'); aliases('convert','convert conversion'); aliases('relic','relic relicpickup relicdropoff')
aliases('embark','embark load transportload'); aliases('unload','disembark unload transportunload')
EFFORTS={
'effortattack':'[short forceful grunt]', 'effortattackbig':'[forceful attack grunt]',
'effortcough':'[brief cough]', 'effortdeath':'[dying gasp]',
'effortexertion':'[short exertion grunt]', 'effortexertionbig':'[strained exertion grunt]',
'effortfear':'[startled gasp]', 'efforthealed':'[relieved exhale]',
'effortincomingprojectile':'[sharp startled gasp]', 'effortinspired':'[energized breath]',
'effortpain':'[brief pain grunt]', 'effortpainbig':'[sharp pain cry]',
'effortpanic':'[panicked gasp]', 'effortstretch':'[stretching exhale]',
'effortthroatclear':'[throat clearing]', 'effortwarcry':'[wordless battle cry]'}
AGES={'lowest':'early age: plain, alert, modest assurance', 'low':'second age: purposeful, practiced assurance', 'med':'third age: seasoned, controlled confidence', 'high':'fourth age: veteran, measured authority', 'none':'age-neutral established character'}
AGE_INDEX={age:i for i,age in enumerate(AGES)}
DELIVERIES={'norm':'conversational, crisp','normal':'conversational, crisp','high':'projected over combat, urgent','combat':'projected over combat, urgent','stealth':'hushed, controlled, intelligible','none':'neutral'}
NAVAL={x for x in _ROLES if x.endswith('_ship')}|{'fishing_boat'}
def line_text(family,event,age,take,delivery):
    """Take is 1-based, 1..5 (3 frequent + 2 rare); no silent unknown fallback."""
    result=dict(family=family,event=event,age=age,take=take,delivery=delivery,text='',english='',language='Arabic',phonetics=None,source=SOURCE,review_status='unresolved',nonverbal=False)
    key=re.sub(r'[_\-\s]','',str(event).lower())
    if family not in PERSONAS or age not in AGES or delivery not in DELIVERIES or not isinstance(take,int) or not 1<=take<=5:
        result['missing_reason']='unknown family/age/delivery or take outside 1..5'; return result
    if key in EFFORTS:
        result.update(text=EFFORTS[key],english=EFFORTS[key],language='nonverbal',review_status='performance_review_pending',nonverbal=True,effort=True,performance_direction=DELIVERIES[delivery],variation=f'age {age}; take {take}; natural distinct performance')
        return result
    semantic=ALIASES.get(key)
    if semantic is None:
        result['missing_reason']='unmapped native event: semantic review required'; return result
    if semantic=='move' and family in NAVAL: semantic='navalmove'
    ar,en=ROWS[semantic][(take-1+AGE_INDEX[age])%5]
    p=PERSONAS[family]
    ar=ar.format(role=p['role_ar']); en=en.format(role=p['role_en'])
    if p['gender']=='female' and semantic=='select':
        ar=ar.replace('حاضر','حاضرة').replace('مستعد','مستعدة').replace('يسمعك','تسمعك')
    # Role callouts make common selections identity-specific. Other events retain
    # their native semantic meaning, with family-specific vocal performance.
    result.update(text=ar,english=en,review_status='arabic_fallback_native_review_pending',semantic=semantic,effort=False,persona=p,performance_direction=DELIVERIES[delivery]+'; '+AGES[age]+'; '+p['direction'],recording_identity=f'{family}/{event}/{age}/{delivery}/{take}',target_duration_seconds=[1,3],fallback_reason='Amazigh/Tuareg provider support and pronunciation unverified')
    return result

# Compact occupational order responses; overrides preserve event semantics.
_ATTACK = {
'villager':('ندافع عن أهلنا','Defend our people'), 'scout':('أضرب وأعود','Strike and return'),
 'tuareg':('نضرب من الصحراء','Strike from the desert'), 'trader':('احموا القافلة','Protect the caravan'),
 'mehari':('إلى الأمام يا مهري','Forward, my camel'), 'sanhaja':('صنهاجة تثبت','Sanhaja stands firm'),
 'zenata':('زناتة تغير','Zenata charges'), 'archer':('أطلقوا السهام','Loose arrows'),
 'masmuda':('مصمودة تتقدم','Masmuda advances'), 'lancer':('بالرماح','With spears'),
 'imam':('احموا الضعيف','Protect the weak'), 'handgunner':('أشعل الفتيل','Light the match'),
 'ram':('اكسروا الباب','Break the gate'), 'siege_tower':('إلى الأسوار','To the walls'),
 'springald':('أرسلوا السهم','Release the bolt'), 'mangonel':('ارموا الحجارة','Hurl stones'),
 'trebuchet':('أطلقوا الثقل','Release the weight'), 'bombard':('أطلقوا المدفع','Fire the cannon'),
 'fishing_boat':('احموا الشباك','Protect the nets'), 'trade_ship':('احموا الحمولة','Protect the cargo'),
 'transport_ship':('احموا الركاب','Protect the passengers'), 'arrow_ship':('سهامنا عليهم','Our arrows upon them'),
 'combat_ship':('اضربوا مركبهم','Strike their vessel'), 'fire_ship':('أضرموا النار','Kindle the fire'),
 'warship':('حطموا سفنهم','Smash their ships'), 'king':('دافعوا عن البلاد','Defend the land')}
# Additional contexts observed in the 26 actual stock profile inventories.
row('mine','نحفر المعدن|إلى المنجم|نضرب الصخر|نستخرج الخام|نطلب المعدن','Dig ore|To the mine|Strike rock|Extract ore|Seek metal')
row('dropoff','نضع الحمولة|نسلم القوت|نفرغ الحمل|إلى المخزن|نوصل المتاع','Set down cargo|Deliver provisions|Unload burden|To storage|Deliver goods')
row('arm','نحمل السلاح|إلى السلاح|نستعد للدفاع|نأخذ السلاح|السلاح جاهز','Take arms|To arms|Prepare to defend|Pick up weapons|Weapons ready')
row('unarm','نضع السلاح|نعود للعمل|إلى أدواتنا|نترك السلاح|العمل ينتظر','Put down arms|Return to work|To our tools|Leave weapons|Work awaits')
row('help','نحتاج النجدة|أعينونا|أدركونا|إلينا بالعون|النجدة','Need rescue|Help us|Come to our aid|Bring help|Help')
row('charge','اندفعوا|أغيروا عليهم|إلى الصدمة|اهجموا بقوة|حملة واحدة','Charge|Raid them|Into the clash|Attack hard|One charge')
row('carcass','نحمل الطريدة|نرفع الصيد|نأخذ الطريدة|الصيد معنا|نحمل الصيد','Carry the quarry|Lift the game|Take the quarry|Game with us|Carry the game')
row('herd','نجمع القطيع|إلى الحظيرة|نسوق الماشية|نحفظ القطيع|نسوقها هنا','Gather the herd|To the pen|Drive livestock|Keep the herd|Drive them here')
row('aim','نصوب الآن|ثبتوا الهدف|خذوا التصويب|نرقب الهدف|استعدوا للرمي','Aim now|Fix the target|Take aim|Watch the target|Prepare to shoot')
row('fire','أطلقوا|ارموا الآن|إلى الهدف|الرمي الآن|أرسلوا الرمية','Fire|Shoot now|At the target|Shoot now|Release the shot')
row('paling','نثبت الأوتاد|نغرس الخشب|إلى الأوتاد|نسد الطريق|نقيم الحاجز','Set stakes|Plant timber|To stakes|Block the road|Raise barrier')
row('setup','نثبت الآلة|نهيئ للرمي|نقيم الآلة|إلى موضع الرمي|ننصب هنا','Fix the engine|Prepare to shoot|Erect the engine|To firing position|Set up here')
row('teardown','نفك الآلة|نتهيأ للرحيل|نطوي العدة|نحزم العدة|نرفع الآلة','Dismantle engine|Prepare to leave|Pack equipment|Bind equipment|Lift the engine')
row('incendiary','نجهز النار|إلى الرمي بالنار|الحمولة نارية|نحمل النار|هيئوا الحريق','Prepare fire|Use fire shots|Fire payload|Load fire|Prepare burning')
row('standard','نعود للرمي المعتاد|الحمولة المعتادة|بدلوا الحمولة|نترك النار|الرمي المعتاد','Return to ordinary shots|Ordinary payload|Change payload|Leave fire|Ordinary shots')
row('detonate','أضرموا المركب|النار جاهزة|أشعلوها|إلى الحريق|النار عليهم','Ignite the vessel|Fire ready|Light it|Into the blaze|Fire upon them')
aliases('select','selectcart selectram selectseigetower selectmangonel selectribauldequin selectspringald selecttrebuchet')
aliases('idle','ambientidle workingidle')
aliases('mine','resourcemine'); aliases('dropoff','dropoff dropoffcarcass')
row('carcassdropoff','أضع الصيد هنا|نسلم الطريدة|إلى مخزن الطعام|جئت بالصيد|نضع الطريدة','Set the game here|Deliver the quarry|To the food store|I brought the game|Set down the quarry')
ALIASES['dropoffcarcass']='carcassdropoff'
aliases('arm','armvillager'); aliases('unarm','unarmvillager'); aliases('help','reacthelp')
aliases('trade','sethomemarket setuptraderoute traderouteset')
aliases('charge','charge'); aliases('carcass','pickupcarcass'); aliases('herd','dropoffherd')
aliases('aim','weaponaim'); aliases('fire','weaponfire attackground')
aliases('paling','placepailings'); aliases('relic','pickuprelic dropoffrelic'); aliases('heal','healorder'); aliases('convert','wololo')
aliases('embark','garrisonunits'); aliases('unload','unloadunits')
aliases('setup','setup'); aliases('teardown','teardown'); aliases('incendiary','swaptoincendary'); aliases('standard','swaptostandard'); aliases('detonate','detonate')

# Spoken battle observations are separate from issued attack orders.
row('battlechatter','العدو يتقدم|ثبتنا أمامهم|سهام حولنا|القتال يشتد|نحن صامدون','The enemy advances|We stand against them|Arrows around us|The fighting grows fierce|We hold firm')
aliases('battlechatter','ambientcombat')
_SELECT_AGE={
'lowest':('أنا {role}|هنا {role}|{role} معك|{role} في خدمتك|هل تطلب {role}', 'I am the {role}|Here is the {role}|The {role} is with you|The {role} at your service|Do you need the {role}'),
'low':('{role} مستعد|{role} حاضر|أنا {role}، تفضل|{role} رهن أمرك|{role} يصغي','The {role} is ready|The {role} is here|I am the {role}, speak|The {role} awaits your order|The {role} listens'),
'med':('{role} ينتظر أمرك|{role} يعرف واجبه|{role} على أهبة|أنا {role}، أسمعك|{role} على العهد','The {role} awaits orders|The {role} knows the duty|The {role} is prepared|I am the {role}, I hear you|The {role} keeps faith'),
'high':('{role} ثابت العزم|{role} لا يتأخر|{role} يحفظ العهد|أنا {role}، مرني|{role} يقظ','The {role} is resolute|The {role} will not delay|The {role} keeps the pledge|I am the {role}, command me|The {role} is vigilant'),
'none':('{role} يسمعك|{role} ينتظر|{role} هنا|ماذا تطلب من {role}|{role} بالخدمة','The {role} hears you|The {role} waits|The {role} is here|What do you ask of the {role}|The {role} at your service')}
_ATTACK_AGE={
'lowest':('إلى العدو|اضربوا الآن|نهجم معا|لنبدأ القتال|ها نحن قادمون','To the enemy|Strike now|Attack together|Begin the fight|Here we come'),
'low':('عليهم يا رجال|أحكموا الهجوم|لا تمهلوهم|تقدموا للقتال|نضرب صفوفهم','At them, men|Make the attack count|Give them no respite|Advance to battle|Strike their ranks'),
'med':('اكسروا صفهم|اضربوا بحزم|نضغط عليهم|لنحسم القتال|لا تدعوهم يفلتون','Break their line|Strike firmly|Press them|Decide the battle|Do not let them escape'),
'high':('أتموا الهجوم|اسحقوا مقاومتهم|ضربة فاصلة|احسموا المعركة|ليكن النصر لنا','Complete the attack|Crush their resistance|A decisive blow|Decide the battle|Let victory be ours'),
'none':('اضربوا|على العدو|هاجموا|إلى القتال|لا تتراجعوا','Strike|Against the enemy|Attack|Into battle|Do not retreat')}
_SIEGE={'ram','siege_tower','springald','mangonel','trebuchet','bombard'}
_base_line_text=line_text

def line_text(family,event,age,take,delivery):
    result=_base_line_text(family,event,age,take,delivery)
    semantic=result.get('semantic')
    if semantic=='select':
        ar,en=_SELECT_AGE[age]; ar=ar.split('|')[take-1];en=en.split('|')[take-1]
        ar=ar.format(role=PERSONAS[family]['role_ar']);en=en.format(role=PERSONAS[family]['role_en'])
        if PERSONAS[family]['gender']=='female':
            for a,b in [('مستعد','مستعدة'),('حاضر','حاضرة'),('يصغي','تصغي'),('ينتظر','تنتظر'),('يعرف','تعرف'),('يحفظ','تحفظ'),('يسمعك','تسمعك'),('ثابت العزم','ثابتة العزم'),('لا يتأخر','لا تتأخر'),('يقظ','يقظة')]: ar=ar.replace(a,b)
        result.update(text=ar,english=en)
    elif semantic=='attack':
        ar,en=_ATTACK_AGE[age];ar=ar.split('|')[(take-1)%5];en=en.split('|')[(take-1)%5]
        # All ages keep a recognizable occupational bark; later takes vary naturally.
        if take==1:
            ar,en=_ATTACK[family]
            if age=='low': ar+=' الآن';en+=' now'
            elif age=='med': ar+=' معا';en+=' together'
            elif age=='high': ar+=' بحزم';en+=' firmly'
            elif age=='none': ar+=' هيا';en+=', come on'
        elif family in _SIEGE:
            ar,en=ROWS['fire' if family not in {'ram','siege_tower'} else 'attack'][(take-1+AGE_INDEX[age])%5]
            if family=='ram': ar,en=('إلى الباب','To the gate') if take==2 else (ar,en)
            if family=='siege_tower': ar,en=ROWS['embark'][(take-1+AGE_INDEX[age])%5]
        elif family in NAVAL:
            naval=[('إلى سفنهم','To their ships'),('اضربوا المركب','Strike the vessel'),('حاصروا سفنهم','Surround their ships'),('لا تدعوهم يبحرون','Do not let them sail'),('أحكموا الهجوم البحري','Press the sea attack')]
            ar,en=naval[(take-1+AGE_INDEX[age])%5]
        result.update(text=ar,english=en)
    return result

# Engines carry crews; embark/disembark here must not mention ships.
row('siegeembark','إلى البرج|ادخلوا الآلة|اصعدوا البرج|الطاقم إلى الداخل|نحمل الرجال','To the tower|Enter the engine|Climb the tower|Crew inside|Take the men aboard')
row('siegeunload','انزلوا هنا|اخرجوا من البرج|الرجال إلى الخارج|إلى الأرض|أنزلوا الرجال','Disembark here|Leave the tower|Men outside|To the ground|Unload the men')
_age_line_text=line_text

def line_text(family,event,age,take,delivery):
    result=_age_line_text(family,event,age,take,delivery)
    if not result['text']: return result
    result['recording_identity']=f'{family}/{event}/{age}/{delivery}/{take}'
    if result['nonverbal']:
        result['performance_direction']+='; '+AGES[age]+'; '+PERSONAS[family]['direction']
    if family in _SIEGE and result.get('semantic') in {'embark','unload'}:
        sem='siegeembark' if result['semantic']=='embark' else 'siegeunload'
        result['text'],result['english']=ROWS[sem][(take-1+AGE_INDEX[age])%5]
    if family=='siege_tower' and result.get('semantic')=='attack' and take!=1:
        result['text'],result['english']=ROWS['siegeembark'][(take-1+AGE_INDEX[age])%5]
    if family=='handgunner' and not result['nonverbal']:
        result['text']=result['text'].replace('رامية','رَامِيَةٌ').replace('أشعل الفتيل','أُشْعِلُ الْفَتِيلَ')
        result['pronunciation_note']='Vowel marks on gunner identity and match-lighting phrase after pilot ASR ambiguity; listening still separate.'
    return result
