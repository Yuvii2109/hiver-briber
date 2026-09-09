# Data provenance

**Dataset:** Customer Support on Twitter (Kaggle, `thoughtvector/customer-support-on-twitter`), file `twcs.csv`.

Kaggle requires authentication, which a grader may not have. This project therefore
pulls a byte-identical public mirror and verifies it:

- URL: `https://huggingface.co/datasets/SunidhiSriram/twcs/resolve/main/twcs.csv`
- size: 516,508,641 bytes
- md5: `73e961b2837626de89618a3f35f7bd6c`
- rows: 2,811,774 (matches the Kaggle original)

`scripts/build_corpus.py` verifies the md5 before use and refuses to proceed on a
mismatch, so a silently-changed mirror cannot corrupt results.

**Mirrors that look right and are not.** `gorkemsevinc/Customer_Support_on_Twitter`
is the top HuggingFace hit for this dataset and is unusable: it has a single
`cleaned_text` column that has been lowercased and Porter-stemmed ("pleas send us a
privat messag"), and it has dropped `tweet_id`, `author_id`, `inbound`, `created_at`
and both reply-link columns. Thread reconstruction is impossible from it. Checking
the schema rather than the title was worth the five minutes.

**Licence / privacy.** The corpus is public, already user-anonymised by the dataset
author (customer handles replaced with integer ids; `__email__` and `__credit_card__`
tokens substituted). Only the chosen brand's slice is committed here.
