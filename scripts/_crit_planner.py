import pandas as pd, re, collections
df = pd.read_csv('data/raw/twcs.csv', usecols=['tweet_id','author_id','inbound','text','in_response_to_tweet_id'], dtype={'text':str})
b='Uber_Support'
out = df[(df.author_id==b)]
# brand replies whose parent is an inbound customer msg
inb = df[df.inbound==True][['tweet_id','text']].rename(columns={'tweet_id':'pid','text':'ctext'})
m = out.merge(inb, left_on='in_response_to_tweet_id', right_on='pid')
print('brand replies to a customer msg:', len(m))
t = m.text.fillna('')
q = t.str.contains(r'\?')
print('reply contains a question mark: %.1f%%' % (100*q.mean()))
dm = t.str.contains(r'(?i)\b(DM|direct message|private message|send us a (?:dm|message))\b')
print('reply asks to DM: %.1f%%' % (100*dm.mean()))
print('question AND not dm: %.1f%%' % (100*(q&~dm).mean()))
pats = {
 'email': r'(?i)\bemail\b',
 'phone/number on account': r'(?i)\b(phone number|number associated|mobile number)\b',
 'trip/ride details': r'(?i)\b(trip|ride|fare)\b.{0,20}\b(date|details|id|link|receipt)\b|\b(which|what) (trip|ride)\b',
 'location/city': r'(?i)\b(city|location|where)\b',
 'item description (lost)': r'(?i)\b(item|left behind|lost)\b',
 'screenshot': r'(?i)\bscreenshot\b',
 'driver name': r'(?i)\bdriver\'?s? (name|first name)\b',
 'account/username': r'(?i)\b(account|username|handle) (email|name)?\b',
 'more detail (open)': r'(?i)\b(more (info|information|details)|tell us more|elaborate|what happened|can you (share|provide|tell))\b',
}
qs = t[q]
print('\nAmong replies containing a question (n=%d), what is asked for:'%len(qs))
for k,p in pats.items():
    print('  %-26s %5.1f%%' % (k, 100*qs.str.contains(p).mean()))
print('\n--- 15 sample brand replies containing a question ---')
for s in qs.sample(15, random_state=0):
    print(' *', s[:190].replace('\n',' '))
