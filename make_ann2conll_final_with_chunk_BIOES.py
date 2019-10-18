#!/usr/bin/env python
# coding: utf-8

# # yedda로 태깅한 ann 파일을 conll 포맷으로 변환하기
# 
# 191018
# 
# BIOES 포맷(not BIO)
# 
# chunk와 tagging을 합쳐준다
# 
# 2가지 방법으로 conll 포맷을 구하고
# 
# 그래도 오류가 나면 손으로 고쳐준다
# 
# [@AlphaBay Market#Company*] 와 같이 [@~#~*] 식으로 표현되있다
# 
# 입력 문장을 너으면, conll 포맷으로 변형시켜 list로 출력해준다

# In[1]:


## 입력 폴더 지정

folder_path = 'test'


# # 1. ann -> conll, tagging

# In[2]:


import os, re, string
import nltk
from nltk import word_tokenize, pos_tag


# In[3]:


## function
def make_ann2conll(tagedSentence, tagScheme="BIOES", seget_nltk_tokenize=True, entityRe=r'\[[\@\$)].*?\#.*?\*\](?!\#)'):
    ## input  : sentence
    ## output : pairList
#         ['AlphaBay B-Company\n',
#          'Market I-Company\n',
#          ', O\n',
#          'a O\n',

    newSent = tagedSentence.strip('\n')  # \n 떼고

    # filterList : ['[@AlphaBay Market#Company*]', '[@stolen customer account funds#Attack_Objective*]']
    filterList = re.findall(entityRe, newSent)  # '[@~*]' 찾고
    newSentLength = len(newSent)  # 문장 길이 구하고
    chunk_list = []
    start_pos = 0
    end_pos = 0

    # annotation이 없는 문장이면
    if len(filterList) == 0:
        singleChunkList = []
        singleChunkList.append(newSent)
        singleChunkList.append(0)
        singleChunkList.append(len(newSent))
        singleChunkList.append(False)
        # chunk_list : [문장, 0, 문장길이, False]
        chunk_list.append(singleChunkList)
        # 초기화
        singleChunkList = []

    ## annotation이 있는 문장이면
    # filterList : ['[@AlphaBay Market#Company*]', '[@stolen customer account funds#Attack_Objective*]']
    else:
        for pattern in filterList:
            # print pattern
            singleChunkList = []
            start_pos = end_pos + newSent[end_pos:].find(pattern)
            end_pos = start_pos + len(pattern)
            singleChunkList.append(pattern)
            singleChunkList.append(start_pos)
            singleChunkList.append(end_pos)
            singleChunkList.append(True)
            # chunk_list : [패턴, 패턴 시작위치, 패턴 끝위치, True]
            # [['[@AlphaBay Market#Company*]', 0, 27, True],
            # ['[@stolen customer account funds#Attack_Objective*]', 156, 206, True]]
            chunk_list.append(singleChunkList)
            singleChunkList = []

    ## chunk_list format:
    # full_list 형태, 순서대로 이어붙이면 된다
    # [['[@AlphaBay Market#Company*]', 0, 27, True],
    #  [', a popular darknet marketplace has been offline since Tuesday night sparking concerns from users that the site’s operators have ',
    #   27,
    #   156,
    #   False],
    #  ['[@stolen customer account funds#Attack_Objective*]', 156, 206, True],
    #  [' and disappeared.', 206, 223, False]]

    full_list = []
    for idx in range(0, len(chunk_list)):
        if idx == 0:
            if chunk_list[idx][1] > 0:
                full_list.append([newSent[0:chunk_list[idx][1]], 0, chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])
            else:
                full_list.append(chunk_list[idx])

        # annotation이 있으면
        else:
            if chunk_list[idx][1] == chunk_list[idx-1][2]:
                full_list.append(chunk_list[idx])
            elif chunk_list[idx][1] < chunk_list[idx-1][2]:
                print("ERROR: found pattern has overlap!", chunk_list[idx][1], ' with ', chunk_list[idx-1][2])
            else:
                full_list.append([newSent[chunk_list[idx-1][2]:chunk_list[idx][1]], chunk_list[idx-1][2], chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])

        if idx == len(chunk_list) - 1 :
            if chunk_list[idx][2] > newSentLength:
                print("ERROR: found pattern position larger than sentence length!")
            elif chunk_list[idx][2] < newSentLength:
                full_list.append([newSent[chunk_list[idx][2]:newSentLength], chunk_list[idx][2], newSentLength, False])
            else:
                continue

    #######################################################################            
    #######################################################################
    pairList = []
    for eachList in full_list:
        # eachList : [@AlphaBay Market#Company*]', 0, 27, True]
        # eachList[3] : True or False, 어노테이션이냐 아니냐

        # 1. 어노테이션일 때
        if eachList[3]:
            # 쪼개고
            # [@AlphaBay Market#Company*] -> ['AlphaBay Market', 'Company*']
            
            
            # '[$', '[@' 통일, tagging 안에 $가 있는것도 날려서 문제 발생
            contLabelList = eachList[0].strip('[@').rsplit('#', 1)
                
            # 쪼갠 길이가 2가 아니면 에러 표시
            if len(contLabelList) != 2:
                print("Error: sentence format error!")
            # 'Company*' 에서 *를 뗴고 label 선언
            # label : Company
            label = contLabelList[1].strip('*]')

            # 두 단어 이상이 annotation 되있으면 쪼갠다, 'AlphaBay Market' -> ['AlphaBay', 'Market']
            # nltk word tokenize를 이용하여 쪼갠다
            if seget_nltk_tokenize:

                word_tokenized = word_tokenize(contLabelList[0])
                
                ## 'U.S'로 잘못 쪼개진 경우, U.S가 있는 인덱스를 찾고, 그 뒤가 '.' 이면
                ## 합친다!!!
                check_word = ['U.S.', 'U.K.']
                for check in check_word:
                    if check[:-1] in word_tokenized:
                        US_idx = word_tokenized.index(check[:-1])
                        if word_tokenized[US_idx+1] == '.':
                            del word_tokenized[US_idx+1]
                            word_tokenized[US_idx] = word_tokenized[US_idx]+'.'   


                contLabelList[0] = word_tokenized

            # 그냥 빈칸 단위로 쪼갠다
            else:
                contLabelList[0] = contLabelList[0].split()
         
            ## BIO, BMES 관련 태깅함수
            outList = outputWithTagScheme(contLabelList[0], label, tagScheme)

            # pairList : ['AlphaBay B-Company\n', 'Market I-Company\n']
            for eachItem in outList:
                pairList.append(eachItem)

        # 2. 어노테이션일 아닐때
        else:
            # nltk word tokenize를 이용하여 쪼갠다
            if seget_nltk_tokenize:
                eachList[0] = word_tokenize(eachList[0])
            # 그냥 빈칸 단위로 쪼갠다
            else:
                eachList[0] = eachList[0].split()        


            for idx in range(0, len(eachList[0])):
                basicContent = eachList[0][idx]

                # 빈칸이면 마킹 안하고 패스
                if basicContent == ' ':  continue
                # 아무것도 아니니까 O 을 단다
                pair = [basicContent, 'O']
                pairList.append(pair)
                
    return pairList


## 태그 달기
def outputWithTagScheme(input_list, label, tagScheme="BIOES"):
    output_list = []
    list_length = len(input_list)
    if tagScheme=="BIOES":
        if list_length ==1:
            pair = [input_list[0], 'S-'+label]
            output_list.append(pair)
        else:
            for idx in range(list_length):
                if idx == 0:
                    pair = [input_list[idx], 'B-'+label]
                elif idx == list_length -1:
                    pair = [input_list[idx], 'E-'+label]
                else:
                    pair = [input_list[idx], 'I-'+label]
                output_list.append(pair)
    else:
        for idx in range(list_length):
            if idx == 0:
                pair = [input_list[idx], 'B-'+label]
            else:
                pair = [input_list[idx], 'I-'+label]
            output_list.append(pair)
    return output_list

##
def tagging_position_of_sentence(sentence, word_label):
# 문장의 위치별 tagging 구하기
# input : pure한 문장, word_label ex) [('RIG', 'Malware'), ('exploit kit', 'Malware_Category'), ('Amazon Technologies Inc.', 'Company'), ('TimeWeb Ltd.', 'Company')]
# output: 글자별 태깅, ex) ['O', 'O', 'Malware', 'Malware', 'Malware', 'O', 'Malware_Category', ..]

    tag_position = list(['O' for i in range(len(sentence))])
    prev_end = 0, 0
    
    for ii in range(len(word_label)):
        # patter의 시작과 끝을 찾는다
        start = sentence.find(word_label[ii][0])
        end   = start + len(word_label[ii][0])
        
        # 이 전꺼보단 뒤에있으므로, 겹치는 단어를 순서로 구분하기 위해
        if start < prev_end:
            start = prev_end + sentence[prev_end : ].find(word_label[ii][0])
            end   = start + len(word_label[ii][0])

        prev_end   = end
        
#         print(sentence[start : end])

        for idx in range(start, end):
            tag_position[idx] = word_label[ii][1]
    
#     print('tag_position: ', tag_position)
    return tag_position


def chkList(lst): 
    # tagging 들이 일치하면, ex) RIG ['Malware', 'Malware', 'Malware']
    # list가 모두 같은값인지 체크, 다른값이면 다른 조치가 필요함
    # input : list
    # output: list가 모두 같은지, 아닌지
    if len(set(lst)) == 1:
        return True, 0
    else:
#         print('something wrong!! : ', lst)
        return False


def spans(txt):
    # get_token_start_end 에 사용되는 함수
    tokens=nltk.word_tokenize(txt)
    offset = 0
    for token in tokens:
        offset = txt.find(token, offset)
        yield token, offset, offset+len(token)
        offset += len(token)


def get_token_start_end(sentence):
    # 문장을 token 단위로 자르고, 그 token의 시작, 끝 idx를 구한다
    # input : line
    # output: [('The', 0, 3),
    #          ('top', 4, 7),
    #          ('Autonomous', 8, 18), ...
    
    token_start_end = []
    for token in spans(sentence):
        token_start_end.append(token)
        assert token[0]==sentence[token[1]:token[2]]
    return token_start_end


def get_error_information(error_sentence_list, idx):
    ## chunk와 tagging의 길이가 다른 이유를 확인하기 위해
    
    if len(error_sentence_list) > 0:
        print('chunking vs tagging', error_sentence_list[idx][5], error_sentence_list[idx][6])
        print(error_sentence_list[idx][0])

        print(error_sentence_list[idx][1])
        print()
        print(error_sentence_list[idx][2])

        sentence_chunk = [tmp[0] for tmp in error_sentence_list[idx][3]]
        sentence_taging = [tmp[0] for tmp in error_sentence_list[idx][4]]
        print()
        print(sentence_chunk)
        print()
        print(sentence_taging)

        only_chunk = list(set(sentence_chunk) - set(sentence_taging))
        only_taging= list(set(sentence_taging) - set(sentence_chunk))

        only_chunk.reverse()
        only_taging.reverse()

        print(only_chunk)
        print()
        print(only_taging)

        if len(only_taging) > len(only_chunk):
            if ''.join(only_taging) == ''.join(only_chunk):
                print('\n!!!')

        elif len(only_taging) == len(only_chunk):
            print('\n...')
    else:
        print('에러 없음')
        
        
def re_organize_list(tag_name_idx_list):
    # 연속된 것들끼리 뭉치게 list 만들기
    # input : [[9, 10, 11, 12, 15, 16, 17, 18], [6], [1, 2, 3, 4]]
    # output: [[1, 2, 3, 4], [6], [9, 10, 11, 12], [15, 16, 17, 18]]
    # list 안의 list들을 다 풀어서 처리
    queue = []
    for idx_tag_name in tag_name_idx_list: 
        queue += idx_tag_name
    queue.sort()


    re_tag_name_idx_list = []
    tmp = []
    v = queue.pop(0)
    tmp.append(v)
    # print(v)

    while(len(queue)>0):
        vv = queue.pop(0)
    #     print(vv)
        if v+1 == vv:
            tmp.append(vv)
            v = vv
        else:
            re_tag_name_idx_list.append(tmp)
            tmp = []
            tmp.append(vv)
            v = vv
    re_tag_name_idx_list.append(tmp)

    return re_tag_name_idx_list


def make_BIOES_tagging(new_tagging_token):
#    input : BIOES 고려되지 않은 list
#     [['DeepSight', 'O'],
#      ['hdrfth', 'baby'],
#      ['asd', 'baby'],
#      ['TRYGHJIK', 'baby'],
#      ['JKTGHD', 'baby'],
#      ['afsdfba', 'O'],
# output : BIOES 고려한 list

    # BIOES 를 붙이기 위해 TAG 들만 LIST를 만든다
    tag_sequence = [tmp[1] for tmp in new_tagging_token]
    
    # ex) tag_set : ['Malware']
    tag_set = list(set(tag_sequence))
    if 'O' in tag_set:  tag_set.remove('O')  # 'O' 는 제거

    tag_name_idx_list = []
    for tag_name in tag_set:
        tag_name_idx = [i for i,x in enumerate(tag_sequence) if x==tag_name]
        tag_name_idx_list.append(tag_name_idx)

#     print(tag_name_idx_list)

    # 같은 tag 여도 연속된것들끼리 묶어주는 코드 
    re_tag_name_idx_list = re_organize_list(tag_name_idx_list)

    for re_tag_name_idx in re_tag_name_idx_list:
#         print(re_tag_name_idx)
        if len(re_tag_name_idx) == 1:
            new_tagging_token[re_tag_name_idx[0]][-1] = 'S-' + new_tagging_token[re_tag_name_idx[0]][-1]
        elif len(re_tag_name_idx) == 2:
            new_tagging_token[re_tag_name_idx[0]][-1] = 'B-' + new_tagging_token[re_tag_name_idx[0]][-1]
            new_tagging_token[re_tag_name_idx[-1]][-1] = 'E-' + new_tagging_token[re_tag_name_idx[-1]][-1]

        elif len(re_tag_name_idx) > 2:
            new_tagging_token[re_tag_name_idx[0]][-1] = 'B-' + new_tagging_token[re_tag_name_idx[0]][-1]
            new_tagging_token[re_tag_name_idx[-1]][-1] = 'E-' + new_tagging_token[re_tag_name_idx[-1]][-1]
            # 중간 Interm
            for ii_tmp in range(re_tag_name_idx[1], re_tag_name_idx[-1]):
                new_tagging_token[ii_tmp][-1] = 'I-' + new_tagging_token[ii_tmp][-1]       
    # BIOES가 고려된 출력
    return new_tagging_token    


def get_tagging_token(sentence):
    # yedda의 태깅된 문장으로 부터 token별 출력 얻기
    # input : tagged line, ex) [@Amazon Technologies Inc. #Company*] and [$TimeWeb Ltd.#Company*] (see Figure 7).
    # output: token tagging lilst
    #         ['Amazon', 'Company'],
    #         ['Technologies', 'Company'],
    #         ['Inc.', 'Company'],
    #         ['and', 'O'],
    #         ['TimeWeb', 'Company'],
    #         ['Ltd.', 'Company'],
    pure_line, pattern_list, word_label, tag_position, token_start_end = '', [], [], [], []
    
    ## 1. 원래 문장 복원
    pure_line = make_pure_sentence_from_tagged(sentence)
#     print('tagged: ',sentence, '\n')
#     print('pure  : ',pure_line, '\n')

    ## 3. 패턴 리스트를 찾기
    pattern_list = re.findall(r'\[[\@\$)].*?\#.*?\*\](?!\#)', sentence)
#     print('pattern : ', pattern_list,'\n')

    ## 4. word, label 세트 찾기
    word_label = [get_word_label(pattern) for pattern in pattern_list]
#     print('word_label: ',word_label)
    
    ## 5. tagging 위치 찾기
    tag_position = tagging_position_of_sentence(pure_line, word_label)
    
    ## 6. 문장을 token 단위로 자르고, 그 token의 시작, 끝 idx를 구한다
    token_start_end = get_token_start_end(pure_line)
    
    ## 7. token 단위 태깅하기
    new_tagging_token = []
    token, tag_list = '', []
    for iiii in range(len(token_start_end)):
        token = token_start_end[iiii][0]
        tag_list = tag_position[token_start_end[iiii][1] : token_start_end[iiii][2]]
    #     print(token, tag_list)
        # ['Victim_product', 'O']
        tag_set = list(set(tag_list))
        tag_set.reverse()

        if len(set(tag_list)) == 1:
            new_tagging_token.append([token, tag_list[0]])
            
        elif len(set(tag_list)) > 1:
            print('한 토큰에 %d 개의 태깅이 있다\n'%(len(set(tag_list))))

            split_idx = tag_list.index(tag_set[1])
            # 띄어쓰기 추가!!
            new_token = token.split(token[split_idx])[0] + ' ' + token[split_idx:]

            print(sentence)
            sentence = sentence.replace(token, new_token)
            print(sentence)

            print(token)
            print(new_token)
    
    # BIOES 추가하기
    new_tagging_token = make_BIOES_tagging(new_tagging_token)
    
    return new_tagging_token


# In[ ]:





# # 2. chunking

# In[4]:


## chunk function
def traverse(t, chunk_list):
    try:
        if t.label() == 'S':
            current_label = 'O'
        else:
            current_label = t.label()
    except AttributeError:
        chunk_list.append(t)
    else:
        for idx, child in enumerate(t):
            if current_label == 'O':
                chunk_list.append(current_label)
            else:
                if len(t) == 1:
                    chunk_list.append('S-'+current_label)
                else:
                    if idx == 0:
                        chunk_list.append('B-'+current_label)
                    elif idx == len(t)-1:
                        chunk_list.append('E-'+current_label)
                    else:
                        chunk_list.append('I-'+current_label)              

            traverse(child, chunk_list)
    
    return chunk_list


## detokenize, inverse tokenize
def detokenize(tokens):
    return "".join([" "+i if not i.startswith("'") and i not in string.punctuation else i for i in tokens]).strip()


# pure 문장으로 되돌리기
# 문장 안의 indexing text 제거, '[@AlphaBay Market#Company*] -> AlphaBay Market
# ex) pure_line = re.sub(r'\[[\@\$)].*?\#.*?\*\](?!\#)', back2pure_line, line)
def back2pure_line(pattern):
    string = str(pattern.group())
    
    # 두가지 패턴을 하나로 통일, '[$' -> '[@'
    string = string.replace('[$', '[@')
    
    # [@ 인 경우와 [$ 인 경우, 2가지가 있다!!
    if '[@' in string:
        if len(string.split('[@')[1].split('#')) > 2:
            return '#'.join(string.split('[@')[1].split('#')[:-1])  # '#'이 word에 있으면 구분이 제대로 안되므로, 맨뒤 빼고 앞은 word
        elif len(string.split('[@')[1].split('#')) == 2:
            return string.split('[@')[1].split('#')[0]

        
## chunk 만드는 함수
def make_chunk(pure_line):
    ## input : 함수
    ## output: chunk가 고려된 list
    #  [['AlphaBay', 'NNP', 'B-NP'],
    #   ['Market', 'NNP', 'E-NP'],
    #   [',', ',', 'O'],    
    
    ## chunk 규칙
    grammar = r"""
      NP: {<DT|JJ|NN.*>+}          # Chunk sequences of DT, JJ, NN
      PP: {<IN><NP>}               # Chunk prepositions followed by NP
      VP: {<VB.*><NP|PP|CLAUSE>+$} # Chunk verbs and their arguments
      # CLAUSE: {<NP><VP>}         # Chunk NP, VP
      """
    chunk_grammer = nltk.RegexpParser(grammar)
    
    word_tokenized = word_tokenize(pure_line)
    
    ## 'U.S'로 잘못 쪼개진 경우, U.S가 있는 인덱스를 찾고, 그 뒤가 '.' 이면
    ## 합친다!!!
    check_word = ['U.S.', 'U.K.']
    for check in check_word:
        if check[:-1] in word_tokenized:
            US_idx = word_tokenized.index(check[:-1])
            if word_tokenized[US_idx+1] == '.':
                del word_tokenized[US_idx+1]
                word_tokenized[US_idx] = word_tokenized[US_idx]+'.'   
            
            
            
    sentence = pos_tag(word_tokenized)
    # print('chunk_grammer.parse(sentence)', chunk_grammer.parse(sentence))

    ## !!, 괄호가 에러가 나므로, 괄호를 임시로 다른 이상한 문자로 치환, 나중에 다시 복구
    # replace '(/(' -> '_/@*#*@' & ')/)' -> '_/@*#*#*@'
    _sentence = []
    for sent in sentence:
        w, p = sent[0], sent[1]
        _sentence.append((w.replace('(', '_').replace(')', '_'), p.replace('(', '@*#*@').replace(')', '@*#*#*@')))
    sentence = _sentence
    
    t = nltk.Tree.fromstring(str(chunk_grammer.parse(sentence)))
    chunk_list = []
    chunk_list = traverse(t, chunk_list)
    # print(chunk_list)

    current_label = ''

    chunking = []
    for idx, value in enumerate(chunk_list):
        if '/' not in value:
            current_label = value
            if (idx+2) < len(chunk_list):
                if chunk_list[idx+2] == 'E-PP':
                    current_label = current_label.replace('B-', 'S-')
                elif chunk_list[idx+2] == 'I-PP':
                    if len(idx+3) < len(chunk_list) and chunk_list[idx+3].startswith('B-'):
                        current_label = current_label.replace('M-', 'E-')
                    else:
                        print('Not Implemented..')
                        break
        else:
            word, pos = value.split('/')[0], value.split('/')[1]
            
            # 괄호가 에러가 나므로, 괄호를 임시로 다른 이상한 문자로 치환, 나중에 다시 복구
            # replace '@*#*@' -> '(' & '@*#*#*@' -> ')'
            if pos == '@*#*@':
                word, pos = '(', '('
            elif pos == '@*#*#*@':
                word, pos = ')', ')'
            
            chunking.append([word, pos, current_label])
    
    return chunking


# ann format line을 입력으로 chunk + tagging 두개를 합쳐서 최종 conll 포맷을 만드는 함수
def make_line_conll(line):
    ## line 단위
    ## input : ann format line
    ## output: conll format with chunking
    #[['AlphaBay', 'NNP', 'B-NP', 'B-Company'],
    # ['Market', 'NNP', 'E-NP', 'E-Company'],
    # [',', ',', 'O', 'O'],
    ##############################################
    ## 1. conll tagging 형식 만들기
    conll_format = make_ann2conll(line)
    ##############################################
    ## 2. chunk 형식 만들기
    ## 2.1 원래 문장으로 복원
    pure_line = re.sub(r'\[[\@\$)].*?\#.*?\*\](?!\#)', back2pure_line, line)
    ## 2.2 chunk 생성
    chunking     = make_chunk(pure_line)
    ##############################################
    ## 3. 두개의 길이가 다른지 체크하고 합쳐서 최종 결과물 만들기
    assert len(chunking) == len(conll_format), 'chunking과 tagging의 길이가 다르다'

    conll_with_chunking = []
    for i in range(len(chunking)):
        conll_with_chunking.append(chunking[i] + [conll_format[i][-1]])

    return conll_with_chunking


# *] 뒤 띄어쓰기 추가
# [@ 바로 앞 뭐 있으면 띄어쓰기 추가
def _split(pattern):
    string = str(pattern.group())    
    # 앞뒤로 바로 붙어있는거 떼기
    if '[@' in string:
        return string.split('[')[0] + ' ' + '[@'
    elif '[$' in string:
        return string.split('[')[0] + ' ' + '[$'
    elif '*]' in string:
        return '*]' + ' ' + string.split(']')[1]


# 패턴에 '.' 있으면 앞에 단어와 띄어주기
def _split_comma(pattern):
    string = str(pattern.group())    
    # 앞뒤로 바로 붙어있는거 떼기
    if '.' in string:
        return string.split('.')[0]

    
## 태깅 지우고 원래 문장으로 복원
def make_pure_sentence_from_tagged(taged_sentence_filtered):
    return re.sub(r'\[[\@\$)].*?\#.*?\*\](?!\#)', back2pure_line, taged_sentence_filtered)


def get_word_label(pattern):
    # tagging 패턴에서 단어, 라벨을 추출해서 반환
    # input : '[@RIG#Malware*]'
    # output : word = RIG
    #          label= Malware
    
    pattern = pattern.replace('[$', '[@')  # 통일
    if '[@' in pattern:
        if len(pattern.split('[@')[1].split('#')) > 2:
            word  = '#'.join(pattern.split('[@')[1].split('#')[:-1])
            label = pattern.split('[@')[1].split('#')[-1].split('*]')[0]

        elif len(pattern.split('[@')[1].split('#')) == 2:
            word  = pattern.split('[@')[1].split('#')[0]
            label = pattern.split('[@')[1].split('#')[-1].split('*]')[0]
    
    return word, label    


# In[ ]:





# # Tagging!!!

# In[5]:


file_list = os.listdir(folder_path)
print('doc %d 개' % (len(file_list)))
# 저장할 ~_conll 폴더 만들기
conll_folder_path = folder_path + '_conll'
if not os.path.isdir(conll_folder_path): os.mkdir(conll_folder_path)

    
error_sentence_list = []  # error sentence 저장
for file_path in file_list:
#     filename = 'test.ann'
    
    ## 1. load
    sentences = []
    with open(os.path.join(folder_path, file_path), 'r', encoding='UTF-8') as f:
        for line in f.readlines():
            line = line.strip()
            sentences.append(line)
        
    conll_document = []
    ## 2. line 단위로 수행
    for sentence in sentences:
        conll_sentence_with_chunking = []
        sentence = sentence.replace(" '", " ' ")
        
        if sentence != '':
            ##############################################################################
            ## 1) 데이터 전처리
            ##############################################################################
            ## 1. '.' 토크나이즈 문제 해결, 패턴 안에 . 앞뒤는 다 띄어준다
            # 1.1. pattern을 찾는다
            pattern_list = re.findall(r'\[[\@\$)].*?\#.*?\*\](?!\#)', sentence)
            for pattern in pattern_list:
                if '.' in pattern:
                    no_comma_pattern = pattern.replace('.', ' . ')
            # 1.2. 그 안에 .가 있으면 앞듸 모두 띄어쓴다
                    sentence = sentence.replace(pattern, no_comma_pattern)
            # 위에서 pattern이 갱신되서 다시 pattern을 구한다
            pattern_list = re.findall(r'\[[\@\$)].*?\#.*?\*\](?!\#)', sentence)
            for pattern in pattern_list:
                if '[$' in pattern:
                    no_comma_pattern = pattern.replace('[$', '[@')
                    sentence = sentence.replace(pattern, no_comma_pattern)      
            ##############################################################################
            ## 2. tag 바로 앞, 뒤에 뭐가 있으면 띄어준다. 토크나이즈 문제 해결
            ## 2.1. tag 바로 뒤('*]')에 빈칸이 아니면 띄어주기
            taged_sentence_back     = re.sub(r'\*\][^\ ]', _split, sentence)
            # 2.2. tag  바로 앞('[@' or '[$')에 빈칸이 아니면 띄어주기
            taged_sentence_filtered = re.sub(r'[^\ ]\[[\@\$]', _split, taged_sentence_back)            
            ##############################################################################
            
            
            ##############################################################################
            ## 2) conll tagging
            ##############################################################################
            ## 1. conll tagging 형식 만들기
            conll_format = make_ann2conll(taged_sentence_filtered)
            ##############################################################################
            ## 2. chunk 형식 만들기
            ## 2.1 원래 문장으로 복원
            
            #  'asd' -> 'asd, ' 로 잘못 분리되므로, ', asd, ' 로 하기 위하 앞에 공란 삽입
            pure_line = re.sub(r'\[[\@\$)].*?\#.*?\*\](?!\#)', back2pure_line, taged_sentence_filtered)
            ## 2.2 chunk 생성
            chunking     = make_chunk(pure_line)
            ##############################################################################
            ## 3. 두개의 길이가 다른지 체크하고 합쳐서 최종 결과물 만들기
            ## 3.1. 길이가 같으면 chunk와 tagging 합침
            if len(chunking) == len(conll_format):
                
                for i in range(len(chunking)):
                    conll_sentence_with_chunking.append(chunking[i] + [conll_format[i][-1]])
                # 문장 끝 빈칸 추가
                conll_sentence_with_chunking.append([''])
            
            ## 3.2. 길이가 다르면
            else:
                try:
                    if len(chunking) != len(conll_format):
                        print('!!! - 1방법으론 안됨')

                        conll_format1 = make_ann2conll(sentence)
                        conll_format2 = get_tagging_token(sentence)
                        ##############################################################################
                        ## 2. chunk 형식 만들기
                        ## 2.1 원래 문장으로 복원
                        pure_line = make_pure_sentence_from_tagged(sentence)
                        ## 2.2 chunk 생성
                        chunking     = make_chunk(pure_line)
                        print('chunk : %d / conll1 : %d / conll1 : %d'%(len(chunking), len(conll_format1), len(conll_format2)))                    

                        if len(chunking) != len(conll_format2):
                            print('!!! - 2방법으론 안됨, 직접 수정!!')
                            error_sentence_list.append([file_path, sentence, pure_line, chunking, conll_format, len(chunking), len(conll_format)])
                        else:
                            print('!!!!! - 2방법으로 수정 완료')
                            conll_format = conll_format2
                            # 수정 완료, 합친다
                            for i in range(len(chunking)):
                                conll_sentence_with_chunking.append(chunking[i] + [conll_format[i][-1]])
                            # 문장 끝 빈칸 추가
                            conll_sentence_with_chunking.append([''])
                except:
                    print('직접 수정하자.....')
                    error_sentence_list.append([file_path, sentence, pure_line, chunking, conll_format, len(chunking), len(conll_format)])

        # 문장이 끝나면 문단에 추가
        conll_document.append(conll_sentence_with_chunking)
    
    ####################################################################
    ## save
    ####################################################################
    ## 문서단위 저장
    fila_name = file_path.split('.ann')[0]
    fw = open(os.path.join(conll_folder_path, fila_name  + '.conll'), 'w')
    # 문서 시작
    fw.write('<<doc>> ' + fila_name +'\n\n')
    for conll_line in conll_document:
        for conll_token in conll_line:
            if len(conll_token) > 0:
                try:
                    fw.write('\t'.join(conll_token) + '\n')
                except:
                    pass
    fw.close()
    ####################################################################
    ####################################################################
print('Done, error : %d'%(len(error_sentence_list)))


# In[6]:


print(len(error_sentence_list))
error_sentence_list


# In[7]:


idx = 0
get_error_information(error_sentence_list, idx)


