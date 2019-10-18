# make_ner_dataset_conll2003_with_yedda
This repository is to make ner dataset(CoNLL2003 format) with chunking from yedda(python ner annoration tool) ann file

Make NER(Named Entity Recognition) dataset
1. annotate with YEDDA(https://github.com/jiesutd/YEDDA). then, you can get a ~.ann file

2. put the ~.ann file to test folder

3. run the make_ann2conll_final_with_chunk_BIOES.py
It automatically add the chunk and pos with nltk.


then, you can get a CoNLL2003 data format

  # example of input : 

Recent [$Katydid#Threat_Actor*] (a.k.a. Operation [@Molerats#Threat_Actor*] or [@Gaza Hacker Team#Threat_Actor*]) 

  # examlt of output : 

Recent	JJ	B-NP	O
Katydid	NNP	E-NP	S-Threat_Actor
(	(	O	O
a.k.a	NN	S-NP	O
.	.	O	O
Operation	NN	B-NP	O
Molerats	NNPS	E-NP	S-Threat_Actor
or	CC	O	O
Gaza	NNP	B-NP	B-Threat_Actor
Hacker	NNP	I-NP	I-Threat_Actor
Team	NNP	E-NP	E-Threat_Actor
)	)	O	O


os, re, string, nltk(word_tokenize, postag) are required. good luck
