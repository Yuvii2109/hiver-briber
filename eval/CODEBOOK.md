# Intent codebook — @AmericanAir

Committed **before** any golden-set labelling, so the annotation rules could not be
retro-fitted to whatever the model happened to do. Any second annotator should be
able to apply this without talking to me.

## How this taxonomy was built

Four independent analysts open-coded the same 400 conversation openers, drawn from
the **train split only**, each from a different angle (action-first, topic-first,
automatability-first, and a deliberate skeptic instructed to assume the standard
airline taxonomy was wrong). Their four taxonomies were then reconciled into one.

**The finding that mattered:** the obvious airline taxonomy — baggage, delay,
refund, seat, loyalty — covers only about 23% of this traffic. Refunds are ~3.5%,
baggage ~2.5%. The two largest masses are things that taxonomy has no bucket for:
social/praise traffic (~22%) and complaint with nothing filable in it (~11.5%).
Roughly **40% of inbound contains no answerable request at all**.

## Decision: venting is a first-class intent

Venting is a FIRST-CLASS INTENT (DIFFUSE_BRAND_VENT, 11.5%), but a strictly residual one: it
gets a message only after every other intent has failed to find an anchor in it. All four
analysts independently reached the first half of this conclusion; the reconciliation work
was in sizing it honestly and in fixing what leaks in and out.

## Precedence

A message gets exactly **one** label. Rules are applied top-down and the first match
wins, which makes the label a deterministic function of the text rather than an
annotator's impression:

1. OTHER (safety route only: anchorless legal-authority or regulator threats, fraud accusations with no described incident, self-harm or violence language, medical-crisis claims — evaluated before everything else so these never receive an automated empathy line)
2. LIVE_TRIP_DISRUPTION
3. BAGGAGE_MISHANDLING
4. RESERVATION_OR_ACCOUNT_ACTION
5. MONEY_CLAIM
6. SERVICE_INCIDENT_REPORT
7. SELF_SERVICE_OR_CHANNEL_FAILURE
8. POLICY_AND_ELIGIBILITY_QUESTION
9. EMPLOYEE_KUDOS
10. PRAISE_AND_TRAVEL_CHATTER
11. DIFFUSE_BRAND_VENT
12. OTHER (residual: advocacy, suggestions, unrecoverable fragments)

## Intents

### PRAISE_AND_TRAVEL_CHATTER  ·  ~22%  ·  risk: **low**

Positive or neutral social posting aimed at the brand in which no problem is asserted and
nothing is asked for, and in which no individual employee, crew, or station team is singled
out for recognition. This covers window-seat and aircraft photos, airport/lounge check-ins,
'headed home' and 'good morning [city]' narration, status-milestone brags, diffuse thanks
for a product or an outcome ('thanks for the upgrade', 'lay-flat beds are clutch'),
aviation-geek observations, memes, ad commentary, and light brand banter. It is the single
largest slice of this corpus at ~22% and the defining feature of an airline social-support
queue: the customer is narrating a trip, not contacting support. The verified human replies
to these are uniformly one warm sentence with no lookup, no record, and no locator request,
which is what makes this bucket action-distinct from every complaint intent and from
EMPLOYEE_KUDOS.

**Support action.** AUTO-HANDLE fully. One warm, specific, on-brand reply referencing what they mentioned, then
close. Do NOT ask for a record locator, do NOT open any record, do NOT route anywhere, do
NOT promise follow-up. Correct handling of this intent is what keeps roughly one in five
inbound messages out of the case queue entirely.

**Include when**
- No problem, failure, or grievance is asserted anywhere in the message.
- No request, question, or implied ask is present.
- Any praise present is aimed at the brand, the product, the day, or an outcome — not at a person, crew, or station team.
- Includes neutral/observational travel narration with no evaluative complaint ('DCA > MIA on AA', id 2276251).
- Mild self-deprecating or joking gripes with no ask and no asserted failure stay here (id 1707901 'couldn't get an aisle seat... will I survive?!').

**Exclude when**
- EXCLUDE any message whose literal thanks describes a bad event — sarcasm. Classify on the event described, never on the polarity word (id 393187, id 1185659, id 1342109 all go to SERVICE_INCIDENT_REPORT).
- EXCLUDE if a named person, identified crew, or a specific station team is praised → EMPLOYEE_KUDOS.
- EXCLUDE if any question is asked, even a friendly one → POLICY_AND_ELIGIBILITY_QUESTION.
- EXCLUDE mixed messages where a grievance is asserted alongside the praise; precedence sends those to the grievance intent unless the customer explicitly absolves AA (id 411972 'Safety first!' → EMPLOYEE_KUDOS).

**Real examples**
- Good morning Chicago! 🌆 (id 2725306)
- Thanks for the upgrade to first class! (id 2119619)
- The lay flat beds from LA - NY are so incredibly clutch 😴 (id 1629646)
- You folks are just the best. Done a lot of traveling in the last year, and I've enjoyed my AA flights more than any of the others. (id 2272060)

**Near miss (looks like this, is not).** 'Thanks for delaying my flight not once, not twice, but THREE times. Oh, and cancelling my connecting flight out of LGA as well' (id 393187). It opens with literal thanks and would be caught by any sentiment or keyword router, but the event described is a triple delay plus a cancellation, so it is SERVICE_INCIDENT_REPORT. The verified human reply confirms it: 'Our apologies, we're showing the connection was cancelled due to air traffic.'

### SERVICE_INCIDENT_REPORT  ·  ~15%  ·  risk: **high**

A specific, filable grievance about a completed or unfixable service failure — one that
names at least one thing a human could write into an incident record (flight number, route,
station, gate, date, employee name, or a concretely described episode) — where no
operational action can now change the outcome and the customer has not made an explicit
money ask. It spans two surfaces that were coded separately and then deliberately collapsed
because the support action is identical: (a) employee and staff conduct — rudeness,
shouting, condescension, being lied to, discrimination, refusal to accommodate a disabled or
sick passenger, hostile call-center reps; and (b) the physical and onboard product — broken
IFE and Wi-Fi, a 30-year-old aircraft, catering, cabin and lavatory condition, no ear plugs
or blankets, credit-card pitches over the intercom, lounge and terminal facilities, gate and
bus handling. It also absorbs retrospective disruption complaints (a delay or missed
connection that is over) where the customer wants acknowledgement rather than money. At ~15%
it is the second-largest complaint mass in the corpus.

**Support action.** ESCALATE — never auto-resolve. Apologize without conceding liability, restate the conduct or
product standard, capture the incident anchor (flight, date, station, employee name) and
open one Customer Relations / station-management record with a stated follow-up expectation.
No booking change, no compensation offer, no fix promised. Allegations of discrimination,
assault, safety, or refusal to accommodate a disabled passenger take a priority compliance
route and must bypass any automated reply.

**Include when**
- Message asserts a grievance AND contains at least one recoverable specific: flight number, route, station/gate, date, employee name, or a concretely narrated episode.
- The event is over or otherwise not fixable by an operational action right now (tense test: past, or present-but-unfixable such as a broken seatback screen mid-flight).
- Includes sarcastic-thanks constructions whose underlying event is a failure.
- Includes third-party reports ('Just witnessed ticket staff SCREAMING at a paying customer', id 1874776) — the reporter need not be the victim.
- Includes onboard/terminal product complaints framed as suggestions when a concrete bad experience is narrated (id 936042 seat width, id 2744427 credit-card pitches).

**Exclude when**
- EXCLUDE if the customer is still inside an in-progress or imminent operational problem an ops lookup or station escalation could still fix → LIVE_DISRUPTION.
- EXCLUDE if the message contains an explicit ask for money, miles, a voucher, a refund, or a fee waiver → MONEY_CLAIM.
- EXCLUDE if a correct statement of a published rule would explain or resolve the situation (gate-check, Basic Economy, bag fees, boarding groups) → POLICY_AND_ELIGIBILITY_QUESTION. A rule correctly applied but resented is POLICY; a rule correctly applied and the person treated badly on top of it is SERVICE_INCIDENT_REPORT.
- EXCLUDE if there is no recoverable specific at all — only evaluative language about the brand → DIFFUSE_BRAND_VENT.
- EXCLUDE if the substance is entirely a bag that is lost, damaged, or undelivered → BAGGAGE_MISHANDLING.

**Real examples**
- - had an incredibly terrible experience with customer service agent Sentari at LAX. She was so rude in a stressful situation. (id 1121212)
- Just witnessed ticket staff SCREAMING at a paying customer and her teenage son😳 #whatishappening #nocustomersvc #gatec23 (id 1874776)
- what a shambles! On a 767-300 at JFK + 10 hours to Rio. Aircraft is about 30 yrs old. Generally poor! No screens, chargers etc Classic - anyone for radio! (id 1714473)
- Flt4949 from PHL to CHS is a joke. Your attendant has no clue what she is doing and is too scared to answer questions. 1/2 (id 1542863)

**Near miss (looks like this, is not).** 'Your airline is the absolute worst.' (id 2924898). Identical emotional register and the same underlying dissatisfaction, but there is nothing filable — no flight, no date, no station, no person, no event. An agent cannot write it into an incident record, so it is DIFFUSE_BRAND_VENT. The human reply proves the different action: 'We'd like to change your mind. How can we help?' — a probe, not an apology for something specific.

### POLICY_AND_ELIGIBILITY_QUESTION  ·  ~14%  ·  risk: **medium**

A message whose correct resolution is a statement of a published rule, fee, allowance,
product spec, schedule, or eligibility fact, with no need to open this customer's record. It
covers carry-on size and gate-check rules, checked-bag allowance and fees, Basic Economy
restrictions, boarding groups, seat-fee rules, upgrade and 500-mile-segment eligibility,
award taxes and redemption mechanics, mileage transfer/gifting/purchase/redeposit rules,
elite status cost and benefits, ID for lap infants, breast-milk and pump rules,
accessibility and airport-assistance procedures, catering and Wi-Fi/IFE availability, check-
in desk hours, interline recheck rules, and route/schedule availability. Tone is explicitly
irrelevant: roughly half of these arrive as complaints or sarcasm rather than questions, and
the verified human replies answer them with the rule anyway. At ~14% this is the largest
fully self-servable block in the corpus and the highest-value automation target.

**Support action.** AUTO-HANDLE fully. Answer in one message from the policy knowledge base with the rule stated
plainly and the canonical link. No account lookup, no DM, no case, no discretion. The answer
is identical whether the customer asked politely or furiously.

**Include when**
- TONE-BLIND TEST (primary): if a correct statement of a published rule would explain or resolve the situation, it is POLICY, however angry the wording.
- STRANGER TEST (secondary): would a stranger asking the same thing get the identical correct answer? If yes, POLICY.
- Includes rhetorical and complaint-shaped forms that name a specific rule, fee, product, or eligibility ('Pay seats & still need to pay to check carry on?', id 1304329).
- Includes loyalty questions answerable from published rules (redeposit timelines, status transfer, 500-mile segments, award taxes) — these do not get their own intent.
- Includes route/schedule availability asks ('How about PHL-KEF?', id 2357538); unassisted new-booking sales requests are essentially absent from this data.

**Exclude when**
- EXCLUDE if answering requires opening THIS customer's record or account → RESERVATION_OR_ACCOUNT_ACTION.
- EXCLUDE if the customer asks for the rule to be APPLIED to their booking rather than stated ('waive the change fee for my Sonoma trip', id 763774) → MONEY_CLAIM or RESERVATION_OR_ACCOUNT_ACTION.
- EXCLUDE evaluative brand hostility that names NO specific rule, fee, or product ('your policies are horrible!', id 790744) → DIFFUSE_BRAND_VENT.
- EXCLUDE if the rule was correctly applied and the grievance is about how the person was treated → SERVICE_INCIDENT_REPORT.
- EXCLUDE if a bag is physically lost, damaged, or undelivered → BAGGAGE_MISHANDLING. Bag POLICY disputes outnumber actual mishandling roughly 3:1 in this data.

**Real examples**
- Why do they let guitars on to totally full flights ? They don't fit into the carryon box. (id 1044420)
- If I'm traveling with an infant (under 2) on my lap, can I use their passport for airport ID, or does it have to be birth cert? (id 819631)
- group 9 pays for bags no matter what and yet you ask everyone else to check their bags and offer it for free? (id 1832311)
- . Tell us why our small carryon bags were seized at front of plane?! No tags given &amp; tons of space! This is policy? (id 1566214)

**Near miss (looks like this, is not).** 'your policies are horrible!' (id 790744). Same subject matter, same hostility, and it even uses the word 'policies' — but it names no specific rule, fee, or product, so there is nothing to state back. It is DIFFUSE_BRAND_VENT. The verified reply is the vent script, not a rule: 'What has you feeling this way? We're happy to help however we can.' Contrast id 2518507 above, which also states no question but names Basic Economy, and drew a rule statement: 'You can still purchase a Main Cabin ticket with all the great perks you're used to.'

### LIVE_TRIP_DISRUPTION  ·  ~13%  ·  risk: **medium**

The customer is inside, or hours away from, an in-progress operational problem where a real-
time lookup, a station escalation, or an ops update can still change the outcome: delays,
cancellations, diversions, mechanical and crew and fueling holds, tarmac and gate holds,
missing ground crew or jet bridge, missing flight attendants, unstaffed check-in and
'resolution' lines, oversells and involuntary standby, missed or at-risk connections, denied
check-in at the counter, and being stranded overnight. It collapses the classic 'flight
status', 'delay', 'cancellation', 'missed connection' and 'stuck at the airport' buckets
because they all resolve to the same move. Assignment turns on TENSE AND OPERABILITY, not on
the presence of a flight number: asking for a flight number is a one-token probe the agent
makes anyway, whereas the downstream work (ops lookup and station escalation vs. nothing) is
what actually differs. At ~13% it is the intent where a slow reply makes the answer
worthless.

**Support action.** Real-time flight lookup on flight number or route (probe once for it if absent). Reply with
the actual cause, revised ETD/ETA and gate, or the concrete instruction ('see the gate agent
at D16'), and escalate to the station when the fix is on the ground. Offer proactive
updates. Never promise compensation and never mutate the booking here — if the customer then
asks to be moved, reclassify to RESERVATION_OR_ACCOUNT_ACTION and hand off.

**Include when**
- The operational problem is in progress, imminent, or the customer is still physically inside the journey ('Been sitting in my seat for 80 minutes', id 1622448).
- Applies whether or not a flight number is given — the anchor can be supplied by one probe.
- Includes pure status questions ('any update on AA207?', id 2393651) and furious delay narration with no explicit question.
- Includes being stuck in a line, on a bus, on the tarmac, or at a gate with no information.
- Includes stranding and overnight misconnects where the customer still needs to get somewhere.

**Exclude when**
- EXCLUDE if the disruption is over and the customer is home or past the trip → SERVICE_INCIDENT_REPORT ('Thanks for delaying my flight not once, not twice, but THREE times', id 393187).
- EXCLUDE pattern complaints spanning multiple trips with no single in-progress event ('why has only 1/4 of my flights departed/arrived on time', id 1710242) → DIFFUSE_BRAND_VENT.
- EXCLUDE if the customer explicitly asks for a booking to be CHANGED (rebook me, move me, put me on the next) → RESERVATION_OR_ACCOUNT_ACTION wins by the mutation rule.
- EXCLUDE if the only in-progress problem is a bag (waiting at the belt, undelivered) → BAGGAGE_MISHANDLING.

**Real examples**
- Been sitting in my seat for 80 minutes. And we aren’t airborne yet. Starting to get frustrated. #travel (id 1622448)
- any update on AA207? Flight is scheduled to leave in 4 minutes and boarding hasn’t started. No updates have been given at gate (id 2393651)
- Hi- why is flight 3736 being delayed at 2 PM? (id 2562195)
- American Flight 2259 out of St.Lucia. Crew landed 3 hours ago and refuse to fly us out. $12 food voucher, nowhere to eat. #AAsucks (id 2439956)

**Near miss (looks like this, is not).** 'why has only 1/4 of my flights departed/arrived on time' (id 1710242). It is topically a delay message and would be caught by any delay keyword, but it generalises across many trips and contains no in-progress event, so no lookup can resolve it and no station can be escalated to. It is DIFFUSE_BRAND_VENT — and the human reply is exactly the vent move: 'No one likes delays including us. We're sorry that you've had more than your fair share.'

### DIFFUSE_BRAND_VENT  ·  ~11.5%  ·  risk: **medium**

Hostility, condemnation, despair, or churn declaration aimed at the brand with nothing
recoverable in it: no flight, no date, no station, no named person, no named rule or fee, no
bag, no dollar amount, no question, and no request. This is the residue left after every
other intent has taken what it can anchor. It includes content-free abuse ('why are you the
worst'), break-up and defection statements ('I WILL CRAWL BEFORE I FLY EVER AGAIN. I
QUIT.'), cross-trip pattern complaints with no single event, comparative defections to
competitors, and vague 'your customer service is unacceptable' with nothing attached. At
~11.5% it is a first-class intent because its correct action — say something, resolve
nothing, ask exactly one question — is genuinely different from every other intent's, and
because the verified human replies in this data run that exact script.

**Support action.** One bounded empathetic line plus exactly ONE open qualifying question ('We're here to help —
what's going on?' / 'What has you feeling this way?'), then stop and wait. Do NOT look
anything up, do NOT open a Customer Relations case, do NOT apologize for a specific event
you cannot see, do NOT invent a remedy, and do NOT auto-close. The customer's reply
reclassifies the message into a real intent — VENT is a holding pattern, never a resolution.
Flag churn threats for retention review.

**Include when**
- ZERO-ANCHOR TEST: the message contains no flight/route, no date, no station or gate, no employee name, no specific rule or fee, no dollar amount, no bag, and no prior-contact reference.
- No question is asked and no action is requested.
- Includes churn threats and competitor defections — churn is a priority FLAG for retention review, not a separate intent, because the first action is identical.
- Includes uninterpretable hostile fragments where the opening message carries no recoverable content and the tone is negative.

**Exclude when**
- EXCLUDE if any single anchor exists — one flight number, station, employee name, dollar figure, or named rule routes it topically.
- EXCLUDE if a published rule would explain it, however furious ('Basic Economy is another way to nickel and dime customers for greed', id 2518507) → POLICY_AND_ELIGIBILITY_QUESTION.
- EXCLUDE if it references a prior DM, email, Facebook message, or filed case → SELF_SERVICE_OR_CHANNEL_FAILURE.
- HARD SAFETY CARVE-OUT — these leave VENT regardless of anchor and go to OTHER for human triage: threats to contact a legal authority, regulator, attorney general, or the media; explicit lawsuit or fraud accusations with no describable incident; self-harm-adjacent language; sexual-violence or assault metaphors; and medical-crisis claims (ids 2038469, 1555061, 2309195). A canned empathy line on these is actively harmful.
- EXCLUDE discrimination and assault ALLEGATIONS with a describable episode → SERVICE_INCIDENT_REPORT (they are filable and must be escalated, not soothed).

**Real examples**
- Cheers to the worst airline of all time 🥂 (id 2685605)
- Your airline is the absolute worst. (id 2924898)
- why are you the worst (id 2081079)
- I WILL CRAWL BEFORE I FLY EVER AGAIN. I QUIT. (id 755151)

**Near miss (looks like this, is not).** 'Basic Economy is another way to nickel and dime customers for greed. just as horrid as all the rest.' (id 2518507). It reads as pure brand hatred, asks nothing, and matches the vent lexicon almost word for word — but it names a specific product, so a rule statement is a substantive answer. It is POLICY_AND_ELIGIBILITY_QUESTION, and the verified human reply is a rule, not a probe: 'You can still purchase a Main Cabin ticket with all the great perks you're used to.'

### EMPLOYEE_KUDOS  ·  ~6.5%  ·  risk: **low**

Praise aimed at a routable human target — a named agent or flight attendant, an identified
crew on a named flight, a captain, a mechanic team, or a specific station or lounge team —
such that a recognition record can be filed against somebody. Kept separate from
PRAISE_AND_TRAVEL_CHATTER despite both being positive because the actions genuinely differ:
this one requires detail capture and a downstream forward to station or crew leadership, and
the corpus proves it empirically — kudos are deflected to DM at 23% versus 5% for ambient
chatter, and the deflection reason in the verified replies is always to collect the record
locator so the recognition can be routed (ids 1708777, 418146, 2677510). At ~6.5% it is
small but is the only positive intent with real work attached.

**Support action.** Thank the customer warmly and specifically, then capture what is needed to route the
recognition (employee name, flight number, date, record locator — DM is legitimate here and
only here among the positive intents) and forward it to station or crew leadership as a
kudos record. Auto-send is safe: unlike its negative mirror, praise carries no HR or legal
exposure.

**Include when**
- ROUTABLE-TARGET TEST: the message names or identifies a person, a specific crew, or a specific station/lounge team.
- A named individual ('Natalia from aa5243', 'Lisa', 'Karla', 'Ramie from lost baggage at ELP') always qualifies.
- A specific crew or role on a named flight qualifies ('the pilots on flight 2390 from DFW to EWR', 'the amazing AA gate attendant in Providence').
- A specific recovery attributed to staff qualifies even without a name ('hustled and got us booked on a new flight').
- Mixed messages where a grievance is explicitly absolved and the praise is the point stay here (id 411972, '3 hour delay not good. Safety first! Flight crew ... are awesome!').

**Exclude when**
- EXCLUDE praise of the brand, the product, the day, or an outcome with no person behind it ('Thanks for the upgrade to first class!', id 2119619) → PRAISE_AND_TRAVEL_CHATTER. A flight number alone is not a routable target — a person or crew must be identified.
- EXCLUDE sarcastic praise; classify on the event described → SERVICE_INCIDENT_REPORT.
- EXCLUDE if the message also asks a question or reports a problem — precedence sends it to the working intent.

**Real examples**
- please give a shoutout to Natalia from aa5243. Clt-Cak!! Best flight attendant I have ever had , she made flying #AAwesome (id 1185615)
- Great crew on 595 PHX/DCA. Special shoutout to Lisa. Thanks! (id 1174965)
- Shoutout to the pilots on flight 2390 from DFW to EWR for navigating us through a tropical storm like a boss. (id 2468277)
- Thank you to the amazing AA gate attendant in Providence that hustled and got us booked on a new flight. #greatservice (id 1487857)

**Near miss (looks like this, is not).** 'Thanks for the upgrade to first class!' (id 2119619). Genuine, positive, and it thanks AA for a concrete good thing — but no person, crew, or station is identified, so there is no one to recognize and nothing to file. It is PRAISE_AND_TRAVEL_CHATTER, and the human reply does zero work: 'You bet! We love having you #upfront with us.' Compare id 2677510, praising a named role on a named flight, which was deflected to DM purely to collect the booking code and route it to leadership.

### SELF_SERVICE_OR_CHANNEL_FAILURE  ·  ~5%  ·  risk: **medium**

AA's own tools or contact channels failed this customer, and the substance of the request is
that failure rather than a travel problem. Two families are merged because the support move
is one and the same — take ownership inside this channel rather than bouncing the customer
back to the surface that already failed them. Family (a), broken self-service: aa.com and
booking-engine errors and outages, mobile check-in failing at T-24, electronic boarding
passes that stop working or will not scan, the app showing stale flight data, forms that
will not submit, UI bug reports. Family (b), channel handoff: 'check your DM', 'can I DM
u?', an unanswered Facebook message or email, a filed complaint with no callback, and 'I
guess I'm not that important to answer' — messages whose real content lives in a thread the
agent cannot see from the tweet. At ~5% it is small but is the highest-risk-of-wrong-default
category in the taxonomy, because every other intent's opening move ('how can we help?') is
exactly wrong for family (b): the customer has already explained, elsewhere.

**Support action.** Take ownership in-channel. Family (a): run the scripted troubleshooting ladder (clear cache
/ relaunch browser, the T-24 time-zone explanation, reprint from web), state any known
outage, then Web Support as the single fallback — no account access needed, so this side is
auto-handleable. Family (b): locate the existing DM/email/case thread and resume it there;
if nothing is found, ask ONLY for the case or reference number. Never open a new case, and
never ask 'how can we help?' of a family (b) customer.

**Include when**
- Family (a): the customer names a specific AA digital surface (site, app, mobile check-in, boarding pass, booking form, login) that is not working for them.
- Family (b): the message references a prior contact in another channel (DM, email, Facebook, phone, a filed complaint/case) and restates NO actionable travel substance of its own.
- A bare channel pointer with no topic at all ('Hello Can I DM u?', id 2443025) lands here, not in OTHER — the action is well defined even when the topic is not.
- Family (b) beats tone: complaints about being ignored belong here regardless of how angry they are (id 1514016).

**Exclude when**
- EXCLUDE if repairing the tool is not what they want — if they want the OUTCOME done for them (add my FF number, resend my e-ticket, fix my DOB) → RESERVATION_OR_ACCOUNT_ACTION.
- EXCLUDE if the message restates a full actionable problem in the tweet itself; a passing 'DM me' does not move a substantive message here (id 181673, 'nothing happening gate 50A LAX to CLT as we wait on flt attendant. I DEMAND A REFUND! DM Me' → LIVE_TRIP_DISRUPTION).
- EXCLUDE generic 'your website doesn't work' hostility with no specific blocked task → DIFFUSE_BRAND_VENT.
- EXCLUDE if the prior contact is referenced only alongside a named-employee conduct complaint → SERVICE_INCIDENT_REPORT (id 1122953).

**Real examples**
- is your site not working? Been spinning for minutes (id 245278)
- Is there something wrong with mobile check in? 24 hours till my flight and I'm not able to cehck in. (id 1579972)
- can you please check your dm when you have a chance. (id 2588798)
- Hello! Sent a Facebook private message, but have not heard back. It was a basic inquiry concerning a follow up from customer service. Should I expect a reply or try another source? Thank you for your help. We are very excited about our trip. (id 2434397)

**Near miss (looks like this, is not).** 'your customer service is horrible. Your website doesn’t work, your app doesn’t work and they say they can’t help... smh' (id 1249549). It names the website and the app and would trip any digital keyword, but no specific task is blocked, no error is described, and no prior thread is referenced — there is nothing to troubleshoot and no thread to resume. It is DIFFUSE_BRAND_VENT.

### RESERVATION_OR_ACCOUNT_ACTION  ·  ~4%  ·  risk: **high**

The customer wants something DONE to a specific reservation or AAdvantage account: seats
together for a family or couple, seat reassignment after an equipment swap, upgrade
application, rebooking or cancelling a trip, adding a booking or a frequent-flyer number to
an account, resending a confirmation or e-ticket, producing a checked-bag receipt from the
PNR, correcting a DOB that is blocking TSA PreCheck, redepositing award miles, chasing
partner miles that never posted, and unlocking an account. Seating, upgrades, rebooking and
loyalty-account admin are deliberately merged: despite different surface topics the agent
does one identical thing — verify identity, open the customer's record, and mutate it. This
is the cleanest hard boundary in the taxonomy, because a bot with only public information
can never verify identity or change a PNR. LOYALTY was rejected as a standalone intent
because it splits without residue on the same universal test used everywhere else: state the
rule (POLICY) versus open this person's account (here).

**Support action.** ESCALATE to a human with account access. The bot triages only: confirm exactly what change
is wanted, collect the six-letter record locator (or AAdvantage number) in DM, and hand off
with a filled ticket to Reservations or the AAdvantage service desk. Never confirm that a
change has been made, never quote availability, never mutate anything autonomously.

**Include when**
- OWN-RECORD TEST: answering or acting requires opening THIS customer's booking or AAdvantage account — the answer changes depending on whose account it is.
- An explicit or clearly implied request to change, add, fix, cancel, reissue, or retrieve something on a record.
- MUTATION-WINS: if a message asks for both information and a change, this intent takes it (id 1278285, 'AA2970 is late again... Can you also put me on then next').
- Includes live onboard/at-gate seating fixes where reseating is still possible (id 2443002, 'Flight #2498 right now').

**Exclude when**
- EXCLUDE if the question is about the RULE rather than its application to a booking ('Can I change Basic Economy to premium economy online?', id 2194737) → POLICY_AND_ELIGIBILITY_QUESTION. This is a thin boundary: the test is whether the customer describes a specific trip of their own that must change.
- EXCLUDE if the customer is stuck in an in-progress disruption and asks only for information → LIVE_TRIP_DISRUPTION.
- EXCLUDE if what is wanted is money back rather than a record change → MONEY_CLAIM.
- EXCLUDE if the customer wants the broken tool fixed rather than the outcome done for them → SELF_SERVICE_OR_CHANNEL_FAILURE.

**Real examples**
- Any way I can get my seats together after booking w ? (id 2054306)
- Hi there team! I am unable to add my frequent flyer number to a reservation. Could follow me so I can provide the req. data ? (id 1571204)
- Can you please help me unlock my account. It's been locked since 7/2 by their Revenue Protection department, and I have yet to receive the promised call from them. This is getting absurd!! I want to use the miles I earned to reunite with my family!!!! (id 2414907)
- I haven't been receiving TSA precheck since my DOB on my reservation is 1 day before my real DOB (on AA profile) HELP!! (id 1759394)

**Near miss (looks like this, is not).** 'Hey if I booked a flight on basic economy, could I change it to premium economy online? Or do I have to cancel and rebook?' (id 2194737). It contains 'I booked', 'change it' and 'rebook' and looks like a change request, but the customer is asking what the RULE permits, not asking anyone to touch a specific trip — a published answer serves them. It is POLICY_AND_ELIGIBILITY_QUESTION. This is the thinnest boundary in the codebook: the human agent here routed to Reservations anyway, so annotators should apply the test literally (does the customer describe a specific trip that must be altered?) rather than reasoning about how AA actually replied.

### MONEY_CLAIM  ·  ~3.5%  ·  risk: **high**

An explicit ask for money or its equivalent to move: a refund or refund chase, EU261
compensation, reimbursement of hotel, meal or rebooking costs after a disruption, a change-
or cancellation-fee waiver or reversal, a duplicate or disputed charge, foreign-transaction
fees, a fare-drop rollover, a voucher deemed insulting, or a goodwill gesture demanded
outright ('I want a free drink for dealing with this'). Also covers follow-ups chasing an
already-filed compensation claim. The defining feature is a STATED ASK, not the trigger:
most of these are set off by a delay, but the topic is disruption while the work is a refund
case. At ~3.5% it is genuinely small in this corpus — one of the clearest findings against a
generic airline taxonomy, which would size 'refunds' far larger.

**Support action.** ESCALATE to Refunds / Customer Relations. Do not adjudicate in-channel. The bot may state
the published entitlement rule and a realistic timeline, but must NEVER quote an amount,
promise a waiver, or confirm eligibility — each needs ticket-level authority. Open or look
up the claim, hand off with the claim path. Any mention of EU261, DOT, a chargeback, or a
legal authority takes a compliance-flagged route.

**Include when**
- STATED-ASK TEST: the customer names or plainly demands a monetary remedy — refund, compensation, waiver, reimbursement, miles, voucher, a free drink, or 'what say you?' after itemising losses.
- Includes disputed and duplicated charges even when framed as a rant (id 2362071, a $200 change fee charged twice).
- Includes regulatory compensation claims (EU261, DOT).
- Includes a rejected remedy the customer is pushing back on ('they offered me a 12 dollar meal voucher. R u kidding', id 205521).

**Exclude when**
- EXCLUDE if the customer is still inside a disruption and needs to travel → LIVE_TRIP_DISRUPTION takes precedence, because getting them moving is the action that changes the outcome and the redress is handled downstream (id 181673).
- EXCLUDE general fee grumbling with no claim behind it ('Pay seats & still need to pay to check carry on?', id 1304329) → POLICY_AND_ELIGIBILITY_QUESTION.
- EXCLUDE rhetorical money words with no claim ('they don't give refunds and they're liars too', id 2815290) → DIFFUSE_BRAND_VENT.
- EXCLUDE if the ask is to change a booking rather than to be paid → RESERVATION_OR_ACCOUNT_ACTION.

**Real examples**
- 2 cancelled flights 1000 dollars lost they offered me a 12 dollar meal voucher. R u kidding (id 205521)
- 4 Flights, 2 missed connections from delays, $1200 refund to client, $300 in x-tra hotel stays, 2 very sad kids. What say you? (id 787707)
- all I can get is reservation phone line; trying to get 600 euro I am owed under EU law for delay/compensation for alt travel! (id 1050999)
- Same flight. I don't want a card to call my connecting flight. I want a free drink for dealing with this. (id 2304687)

**Near miss (looks like this, is not).** 'Disagree ( = yep) Pay seats &amp; still need to pay to check carry on? #donotfly #lostcustomer #neveragain #badidea' (id 1304329). It is about fees, uses money language, and is furious — but it asks for nothing back; it disputes that the charge should exist. A rule statement is the correct response, so it is POLICY_AND_ELIGIBILITY_QUESTION, and the human reply was exactly that: 'It sounds like your bag was over the carry on size limitations.'

### BAGGAGE_MISHANDLING  ·  ~2.5%  ·  risk: **medium**

A bag or personal item is physically in the wrong place, damaged, or missing: left behind,
lost, delayed, held on a diverted aircraft, delivery promised and repeatedly missed,
contents soaked or crushed, an item left onboard, or a purse returned with cash missing.
Deliberately narrow — this is mishandling, never baggage rules. It is kept as its own intent
despite being only ~2.5% because it is the one workflow that runs on a different department,
a different system and a different phone line (Baggage Service Office, 800-535-5225, and
third-party delivery vendors), shares nothing with Customer Relations or Reservations, and
is time-boxed: damage and interim-expense windows expire, so an apology-only reply actively
costs the customer money. This is also the boundary a generic 'baggage' bucket destroys —
bag POLICY disputes (carry-on sizers, gate-checking, Group 9 fees, Basic Economy bag
charges) outnumber actual mishandling roughly three to one in this data.

**Support action.** ESCALATE into the baggage workflow. Confirm or start the Bag Service Office file, run a
trace on the file reference, give the delivery vendor's direct number, or set the damage-
claim path (800-535-5225) with its deadline stated. Never route to Customer Relations and
never treat it as a rebooking. The bot may auto-serve only the procedural first step: file a
claim at the airport, and the claim number needed.

**Include when**
- PHYSICAL-SEPARATION TEST: the bag or item is in the wrong place, damaged, or not delivered.
- Includes chasing a delivery vendor on a promised delivery window.
- Includes items left on the aircraft and Lost & Found cases.
- Includes long waits at the belt or jetway when the bag itself is the only unresolved problem.
- Includes damage claims for ruined contents — the claim still starts as a baggage file.

**Exclude when**
- EXCLUDE anything about bag RULES or CHARGES — allowance, weight, carry-on size, gate-check, priority-tag policy, Group 9 fees, Basic Economy bag charges → POLICY_AND_ELIGIBILITY_QUESTION.
- EXCLUDE producing a checked-bag RECEIPT from the booking → RESERVATION_OR_ACCOUNT_ACTION.
- EXCLUDE if the customer is still inside an in-progress flight disruption AND the bag is incidental → LIVE_TRIP_DISRUPTION.
- EXCLUDE if the ask has moved past the bag to compensation for the whole ruined trip → MONEY_CLAIM.

**Real examples**
- So over the phone, online, and via Twitter told me my bag would be delivered at 4 am this morning. It's not 6:58 am &amp; I still haven't gotten it. This is the 3rd time they've lied about the delivery time. (id 2479231)
- Well.My dream guitar has been crushed.Thanks American Airlines!Lost my baggage AND destroyed it. #AmericanAirlines (id 2331205)
- Just blow drying my clothes ... special thanks to for their quality control with checked baggage. #stillSoaked (id 324594)
- Crappy first in all my years flying to DC for next morn Pentagon shuttle to Gitmo: said my Camp Justice suitcase missed flight. (id 2095353)

**Near miss (looks like this, is not).** '. Tell us why our small carryon bags were seized at front of plane?! No tags given &amp; tons of space! This is policy?' (id 1566214). Bags, seizure, no tags — every baggage keyword fires, and a naive 'baggage' bucket swallows it. But nothing is lost or damaged; the customer is disputing the gate-check rule, and the human reply is that rule: 'Agents may ask you to gate check bags to avoid a delay during boarding.' It is POLICY_AND_ELIGIBILITY_QUESTION.

### OTHER  ·  ~3.5%  ·  risk: **high**

A deliberately small, two-part catch-all whose shared property is that no automated reply
should resolve it. Part one is genuine residue: advocacy and campaign traffic aimed at the
brand rather than at support (the animal-trophy transport campaign), unsolicited product and
safety design ideas, route-restoration and boarding-policy opinions with no personal stake,
special onboard requests that fit no workflow, and thread fragments whose opening message
carries no recoverable content at all. Part two is a deliberate, non-residual assignment:
anchorless legal-authority threats, fraud accusations with no describable incident, self-
harm-adjacent language, sexual-violence metaphors, and medical-crisis claims are routed here
rather than to DIFFUSE_BRAND_VENT, because they look exactly like vents but must never
receive a canned empathy line. At ~3.5% the catch-all is honest — its largest coherent group
is advocacy at under 1%, and nothing frequent is hiding in it.

**Support action.** Do not auto-resolve. Advocacy gets the published corporate position with no case opened.
Suggestions get logged as feedback and closed. Fragments get one clarifying probe. Safety-
route items bypass automation entirely to a human, with legal/compliance flagged where a
regulator or attorney is named. If a message reaches OTHER at volume, that is the signal to
reopen the taxonomy — not to widen this bucket.

**Include when**
- Advocacy, campaign, or corporate-position tweets aimed at the brand rather than at support.
- Unsolicited product, route, or safety suggestions with no personal service problem attached.
- Opening messages with no recoverable content — reply-fragments whose context exists only in a thread the annotator cannot see ('Oh come on "favorable location" 🙄', id 2200102).
- SAFETY ROUTE (non-residual): anchorless legal-authority or regulator threats, fraud accusations with no described incident, self-harm or violence language, and medical-crisis claims — these are assigned here on sight, before precedence is applied.
- Special onboard requests that fit no defined workflow (id 1001529, asking crew to announce a honeymoon congratulations).

**Exclude when**
- EXCLUDE anything that lands in a named intent — OTHER is last in precedence and must never be used to avoid a hard call.
- EXCLUDE a channel pointer with no topic ('Hello Can I DM u?') → SELF_SERVICE_OR_CHANNEL_FAILURE; the action there is well defined even though the topic is not.
- EXCLUDE discrimination, assault, or accessibility allegations that describe an actual episode → SERVICE_INCIDENT_REPORT.
- EXCLUDE suggestion-shaped messages that narrate a concrete bad experience → SERVICE_INCIDENT_REPORT.

**Real examples**
- If won’t protect these animals, then and all other international carriers flying into the US should ban animal trophies on their airplanes. Don’t take the #bloodmoney (id 2591058)
- For all Airplane Saftey can't Airlines build where they can drop the fuel tanks and pairshoots or airbags outside that open (id 1553386)
- Oh come on "favorable location" 🙄 (id 2200102)
- This is explicitly fraud. I'll be contacting CA attorney general. (id 2038469)

**Near miss (looks like this, is not).** 'Hi !! Ever thought about making your seats wider so I don't need to feel the hairy sweaty person next to me for 2.5 hours???' (id 936042). It is phrased as an unsolicited product suggestion, which is OTHER's core content — but it narrates a concrete bad onboard experience the customer personally had, which makes it filable product feedback. It is SERVICE_INCIDENT_REPORT. The separator: a suggestion with no personal stake is OTHER; a complaint wearing a suggestion's clothes is not.

## Intents considered and cut

- LOYALTY_AND_MILES / AADVANTAGE (action-first 5%, topic-first 6%) — cut. Splits without residue into POLICY (state the redemption/upgrade/transfer rule) and RESERVATION_OR_ACCOUNT_ACTION (open this person's account). Keeping it would have duplicated two existing support actions on a topical basis.
- SEATING_AND_UPGRADE (topic-first 4%) — cut into RESERVATION_OR_ACCOUNT_ACTION. Seating, upgrades, rebooking and account admin all resolve to one identical move: verify identity, open the record, mutate it. Different surface topic, same desk, same work.
- SERVICE_FAILURE_REDRESS as separate from BOOKING_CHANGE (action-first, 9% + 9%) — cut. Backward- versus forward-looking remedy is a real distinction but not one an opening message reliably carries; the stated ask is the reliable signal, and it produces MONEY_CLAIM at only 3.5%.
- STAFF_CONDUCT_REPORT as separate from SERVICE_FAILURE (action-first 4%) — cut. Same routing destination and, per the verified replies, the same customer-facing move (apologize, capture the anchor, log, promise no fix). Split it again only if real employee-discipline routing is built.
- ONBOARD_PRODUCT_COMPLAINT as separate from STAFF_CONDUCT (topic-first's two 7% codes) — cut by topic-first themselves and confirmed here. The cleanest example in this data of topic-distinct but action-identical.
- CHURN_THREAT / RETENTION (trialled by skeptic on roughly a quarter of vents) — cut. The first action is identical to DIFFUSE_BRAND_VENT (empathize, one probe). Churn becomes a priority flag and a retention-escalation trigger, not an intent.
- DIGITAL_CHANNEL_FAILURE as separate from CHANNEL_HANDOFF (automation-first 3% + skeptic 3%) — merged into SELF_SERVICE_OR_CHANNEL_FAILURE. Both are 'AA's contact surface failed you; take ownership here, open no new case'. Merging them is what kept the taxonomy inside the 10-intent cap without leaving digital breakage in OTHER.
- TOPIC-FIRST'S THREE-WAY DISSOLUTION OF VENTING (fold anchored vents into DISRUPTION and SERVICE_EXPERIENCE, keep only UNSPECIFIED_COMPLAINT at 8%) — partially rejected. The two folds are adopted; the shrinking of the residue to 8% is not. At 11.5% the anchorless remainder is the fifth-largest intent and has a distinct scripted action the human replies run verbatim.
- NEW_BOOKING / SALES — cut. Genuinely near-absent in this corpus; the handful of route-availability asks ('How about PHL-KEF?', id 2357538; 'No direct flights CLT-LIR in late Sept '18?', id 1925444) resolve to a published schedule lookup and live in POLICY.
- FLIGHT_STATUS as separate from IRROPS / REBOOKING (action-first's 6% STATUS) — cut. Same customers, same moment, same first move; the seam is handled by precedence (a request to be moved promotes the message to RESERVATION_OR_ACCOUNT_ACTION), not by a second intent.
- AIRPORT_FACILITY / THIRD-PARTY COMPLAINTS (JFK bathrooms id 2512938, lounge size id 63435, terminal closures id 2531797) — not given a slot. Volume is under 1% and the action (apologize, log as station feedback) is SERVICE_INCIDENT_REPORT's.

## Where the analysts disagreed

- SPLIT OR MERGE THE POSITIVE MASS (action-first and skeptic split kudos from chatter; topic-first and automation-first merged them). RESOLVED: SPLIT, into EMPLOYEE_KUDOS (6.5%) and PRAISE_AND_TRAVEL_CHATTER (22%). The merge advocates were right that both are positive and safe, but the deciding test is the support action, and the corpus settles it empirically rather than by argument: in my coding, kudos were deflected to DM at 23% versus 5% for ambient chatter, and the verified deflection reason is always detail capture for routing — id 2677510 got 'We'd love to share your praises for her with our leadership team. Please DM your 6-letter booking code', id 1708777 and id 418146 the same. Chatter got zero-work replies ('You bet! We love having you #upfront with us.'). One intent requires a data-capture step and a downstream leadership record; the other requires nothing. That is action-distinct.
- SIZE AND SCOPE OF VENTING (action-first 23%, skeptic 14%, automation-first 13%, topic-first 8% after a three-way split). RESOLVED: 11.5%, closest to automation-first and skeptic. Action-first's 23% was inflated by pulling in-the-moment misery narration ('been sitting in my seat for 80 minutes', id 1622448) into VENT on the grounds that no flight number is present. I reject the flight-number test: asking for a flight number is a one-token probe the agent makes anyway, and id 1622448's actual human reply was an ops lookup ('We're glad to see that you've departed with an estimated arrival time of 2:13p'), not a probe. Topic-first's 8% is too low because it dissolved anchored vents into topical intents, which is right, but also drained borderline cases the replies show were handled with the vent script.
- SIZE OF THE POLICY BUCKET (automation-first 19%, skeptic 17%, action-first 12%, topic-first 4%). RESOLVED: 14%, and — more importantly — the tone-blind rule that automation-first and skeptic proposed is ADOPTED IN FULL, against my own initial instinct to send purely evaluative policy gripes to VENT. The human replies decided it. Id 2518507 ('Basic Economy is another way to nickel and dime customers for greed') asks no question and reads as pure hatred, yet the agent answered with the rule: 'You can still purchase a Main Cabin ticket with all the great perks you're used to.' Same for id 1167649 and id 1863623. Topic-first's 4% is the single largest miss in the four submissions: it routed the angry-but-answerable half of this mass into complaint buckets, which converts the most automatable block in the corpus into escalations.
- WHAT SEPARATES DISRUPTION FROM VENTING (automation-first: presence of a lookup-able flight number; skeptic: tense plus operability). RESOLVED: skeptic's tense-and-operability test, because it survives the probe argument above and because it correctly separates the two failure modes that matter — apologizing to someone who needs rebooking, versus rebooking someone whose trip ended yesterday. Under it, LIVE_TRIP_DISRUPTION lands at 13.3% (vs. action-first's 6%, which is far too low, and topic-first's 18%, which absorbed retrospective delay complaints that belong in SERVICE_INCIDENT_REPORT).
- LOYALTY AS AN INTENT (action-first 5% and topic-first 6% kept it; automation-first and skeptic dissolved it). RESOLVED: DISSOLVED. Loyalty splits without residue on the same universal test the taxonomy already applies everywhere: 'how long should it take to redeposit my AAdvantage miles' (id 827646), 'can I transfer my miles/status from Latam' (id 371226) and '500-mile segments to upgrade an int'l flight' (id 1455834) are rule statements → POLICY; 'help me unlock my account' (id 2414907), 'my rental miles don't show up' (id 2983742) and 'unable to add my frequent flyer number to a reservation' (id 1571204) require opening this person's record → RESERVATION_OR_ACCOUNT_ACTION. Keeping LOYALTY would have created two intents with the same support action as two existing ones, purely on topic.
- STAFF CONDUCT VERSUS ONBOARD PRODUCT VERSUS RETROSPECTIVE DISRUPTION (action-first split conduct out at 4%; topic-first merged conduct and product at 14%; automation-first kept a narrow 6% incident bucket; skeptic merged at 16%). RESOLVED: ONE intent at 15%. Topic-first's own note is the strongest argument in the four submissions — they coded conduct and product as separate 7% topics and collapsed them because the agent does exactly the same thing for both. The verified replies confirm it: id 1874776 (staff screaming) and id 1714473 (30-year-old aircraft, no screens) both got apologize-plus-log with no fix promised. Action-first's 4% conduct bucket only survives if you build genuine employee-discipline routing, which is not what an opening-message classifier decides.
- BACKWARD-LOOKING REDRESS VERSUS FORWARD-LOOKING BOOKING CHANGE (action-first split these into SERVICE_FAILURE_REDRESS 9% and BOOKING 9%). RESOLVED: REJECTED as a primary split. The distinction is real but it is not what an opening message reliably carries; the reliable signal is the stated ask. MONEY_CLAIM is keyed on an explicit demand for money and comes out at only 3.5% — much lower than any analyst estimated, because most 'redress' messages in this corpus itemise a grievance without ever naming a remedy, and those are filable incidents, not claims. This is a real finding, not a rounding difference: a generic airline taxonomy would size refunds several times larger than this data supports.
- DIGITAL BREAKAGE AND CHANNEL FOLLOW-UP (action-first dumped digital in OTHER and regretted it; automation-first kept DIGITAL 3% and put channel pings in OTHER; skeptic kept CHANNEL_HANDOFF 3% and folded digital into SELF_SERVICE_BLOCKED; topic-first merged both at 5%). RESOLVED: topic-first's merge, at 5%, which my independent count reproduces exactly (10 digital + 9 channel of 400). The shared action is 'take ownership in-channel and do not bounce them back to the surface that already failed them', and both share the same critical anti-pattern of never opening a new case. This merge is what freed the eleventh slot; action-first explicitly named digital breakage as its structural regret, and this resolves it without breaking the cap.
- WHETHER ANCHORLESS LEGAL THREATS AND SELF-HARM LANGUAGE BELONG IN VENT (automation-first carved them out to a human but left them inside the VENT intent as a flag; skeptic left them in VENT; the others did not address it). RESOLVED: they are ASSIGNED TO OTHER, evaluated before precedence. A flag inside an auto-handled intent is a configuration that can be lost; an intent assignment is part of the frozen codebook. Id 2038469 ('This is explicitly fraud. I'll be contacting CA attorney general') and id 1555061 ('Flying is basically aerial rape, thx for being the worst') are structurally indistinguishable from vents and would otherwise receive the canned empathy probe. This is the one place the codebook deliberately uses OTHER non-residually, and it is why OTHER carries a high risk tier.
- PRECEDENCE PHILOSOPHY: mutation-wins (automation-first) versus escalation-wins (skeptic biases ties toward escalation). RESOLVED: mutation-wins for the operational intents, escalation-wins only via the pre-precedence safety route. Rationale: the escalation must happen regardless of whether the information answer was also given, so putting RESERVATION_OR_ACCOUNT_ACTION above LIVE_TRIP_DISRUPTION for id 1278285 loses nothing, while the reverse loses the rebooking. The one place I overrode mutation-wins is MONEY_CLAIM losing to LIVE_TRIP_DISRUPTION (id 181673, 'I DEMAND A REFUND' while waiting for a flight attendant): getting the customer moving is the action that changes the outcome, and the redress survives downstream.
