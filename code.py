import math
import os
import re
import xml.etree.ElementTree as ET
import string
from operator import itemgetter

from stemming.porter2 import stem

def preprocessing(strin, doc_No, need_stop=True, need_stemming=True):
    words_with_index = []
    text_tokenisation = []
    stopwords = []
    text_after_stopping = []
    """
    delete punctuations and form a new list, including text and doc number
    """
    punctuation_string = string.punctuation
    for i in punctuation_string:
        # turning punctuations to ' '
        strin = strin.replace(i, ' ')
    for word in strin.split():
        # splitting words
        text_tokenisation.append(word)
    # text_tokenisation = re.sub("[%s]+" % string.punctuation, " ", str).replace("\n", "")
    if text_tokenisation:
        # form word, document number and position into a list
        words_with_index.extend(
            list(zip(text_tokenisation, [doc_No] * len(text_tokenisation), range(len(text_tokenisation)))))

    """
    Case folding: make all text in to lower case
    """
    text_case_low = [(each[0].lower(), each[1], each[2]) for each in words_with_index]

    """
    if need to remove stop words return new list or do nothing
    """
    if need_stop:
        # read stop words from file
        with open("englishST.txt") as f:
            for stop in f:
                stopwords.append(stop.strip('\n'))
        f.close()
        # remove stop words
        for i in text_case_low:
            if i[0] not in stopwords:
                text_after_stopping.append(i)
    else:
        text_after_stopping = text_case_low

    """
    if need to normalise words return new list or do nothing
    """

    if need_stemming:
        normalisation = [(stem(each[0]), each[1], each[2]) for each in text_after_stopping]
    else:
        normalisation = text_after_stopping

    return normalisation



"""
read xml and get text and doc number to pre-process and form a new lst
"""

preprocessed_list = []
# parse
tree = ET.parse('trec.5000.xml')  # read xml file!!!
root = tree.getroot()
# getting docNo, headline and txt
for child in root:
    doc_No = child.find('DOCNO').text
    txt_strin = child.find('HEADLINE').text + child.find('TEXT').text
    preprocessed_text = preprocessing(txt_strin, int(doc_No), need_stop=True, need_stemming=True)
    preprocessed_list.extend(preprocessed_text)

"""
sort the preprocessed_list
"""
preprocessed_list = sorted(preprocessed_list)

"""
created inverted positional index dictionary (store in memory)
"""

inverted_positional_index = {}
for each in preprocessed_list:
    word_str = each[0]
    docNo_int = each[1]
    pos_int = each[2]
    # check if there is a key existing
    if word_str not in inverted_positional_index.keys():
        inverted_positional_index.update({word_str: {docNo_int: [pos_int]}})
    else:
        # if the key exits , checking the document number
        if docNo_int not in inverted_positional_index[word_str].keys():
            # inverted_positional_index.update(inverted_positional_index[word_str].update({docNo_int: [pos_int]}))
            inverted_positional_index[word_str][docNo_int] = [pos_int]
        else:
            inverted_positional_index[word_str][docNo_int].append(pos_int)

"""
writing to the file 
"""
if not os.path.exists("index.txt"):
    file = open('index.txt', 'w')
    for item in inverted_positional_index:
        # calculate document frequency
        doc_frequency = len(inverted_positional_index[item])
        file.write("%s:%d\n" % (item, doc_frequency))
        for each_DN in inverted_positional_index[item]:
            file.write(f"\t\t{each_DN}: {','.join(str(x) for x in inverted_positional_index[item][each_DN])}\n")
    file.close()


"""
get entire doc 
"""
entire_doc = set()
for k in inverted_positional_index.keys():
    for DocNo in inverted_positional_index[k].keys():
        entire_doc.add(DocNo)
"""
preprocess query 
"""

def preprocess_Bquery(data_path, encoding='utf-8'):
    result = []
    with open(data_path, 'r', encoding=encoding) as f:
        for line in f.readlines():
            result.append(re.sub('[(),"]', ' ', line.strip()).replace('#', '# ').split())
    return result


"""
normalise query including lower case and stemming
"""
def normalise_query(arg):
    arg = [w.lower() for w in arg]
    arg = [stem(wo) for wo in arg]
    return arg

"""
phrase query
"""
def __phrase_Query__(arg):
    doc_pQ = []
    del arg[0]
    arg = normalise_query(arg)
    if len(arg) == 1:
        d1 = inverted_positional_index[arg[0]]
        doc_pQ = list(d1.keys())
    if len(arg) == 2:
        d1 = set(inverted_positional_index[arg[0]].keys())
        d2 = set(inverted_positional_index[arg[1]].keys())
        d3 = d1.intersection(d2)
        for dc in list(d3):
            for ele in inverted_positional_index[arg[0]][dc]:
                if ele + 1 in inverted_positional_index[arg[1]][dc]:
                    doc_pQ.append(dc)
    return sorted(list(set(doc_pQ)))

"""
Proximity Search 
"""

def __Proximity__(arg):
    doc_Pro = []
    distance = int(arg[2])
    sub1 = [1, arg[3]]
    sub2 = [1, arg[4]]
    d1 = set(__phrase_Query__(sub1))
    d2 = set(__phrase_Query__(sub2))
    d3 = d1.intersection(d2)
    for dc in list(d3):
        for ele1 in inverted_positional_index[stem(arg[3].lower())][dc]:
            for ele2 in inverted_positional_index[stem(arg[4].lower())][dc]:
                if abs(ele1-ele2) <= distance:
                    doc_Pro.append(dc)
    return sorted(list(set(doc_Pro)))

"""
And query
"""
def __AND__(arg):
    doc_and=[]
    del arg[0]
    arg.remove('AND')
    arg = normalise_query(arg)
    if len(arg) == 2:
        d1 = set(inverted_positional_index[arg[0]].keys())
        d2 = set(inverted_positional_index[arg[1]].keys())
        d3 = d1.intersection(d2)
        doc_and = sorted(list(d3))
    if len(arg) == 3:
        checking_list = [0, arg[0], arg[1]]
        d1 = set(__phrase_Query__(checking_list))
        d2 = set(inverted_positional_index[arg[2]].keys())
        d3 = d1.intersection(d2)
        doc_and = sorted(list(d3))
    if len(arg) == 4:
        checking_list1 = [0, arg[0], arg[1]]
        checking_list2 = [1, arg[2], arg[3]]
        d1 = set(__phrase_Query__(checking_list1))
        d2 = set(__phrase_Query__(checking_list2))
        d3 = d1.intersection(d2)
        doc_and = sorted(list(d3))
    return doc_and

"""
AND NOT query 
"""
def __ANDNOT__(arg):
    del arg[0]
    arg.remove('AND')
    arg.remove('NOT')
    term1 = [1, arg[0], arg[1]]
    term2 = [1, arg[2]]
    d1 = set(__phrase_Query__(term1))
    d2 = set(__phrase_Query__(term2))
    d3 = entire_doc.difference(d2)
    d4 = d1.intersection(d3)
    return sorted(list(d4))

"""
execute query
"""

Bquery_List = preprocess_Bquery('queries.boolean.txt')
Bq_result = []
for each in Bquery_List:
    Bq_num = each[0]
    if '#' in each:
       e1 = __Proximity__(each)
       e1.insert(0, Bq_num)
       Bq_result.append(e1)
    elif 'AND' and 'NOT' in each:
        e2 = __ANDNOT__(each)
        e2.insert(0, Bq_num)
        Bq_result.append(e2)
    elif 'AND' in each:
        e3 = __AND__(each)
        e3.insert(0, Bq_num)
        Bq_result.append(e3)
    else:
        e4 = __phrase_Query__(each)
        e4.insert(0, Bq_num)
        Bq_result.append(e4)

"""
writing results.boolean.txt
"""
final_results_Bq=[]
for one in Bq_result:
    No_Bq = one[0]
    list_doc_Bq = one[1:]
    for val in list_doc_Bq:
        final_results_Bq.append(No_Bq+','+str(val))
if not os.path.exists("results.boolean.txt"):
    with open('results.boolean.txt', 'w', encoding='utf-8') as f2:
        f2.write("\n".join(final_results_Bq))

"""
based on lecture 7
"""
def weight(tf,df):
    return (1 + math.log(tf, 10)) * math.log(len(entire_doc)/df, 10)

"""
read queries.ranked.txt
"""
def preprocess_Rquery(data_path, encoding='utf-8'):
    result = []
    stoppings = []
    with open("englishST.txt") as f4:
        for stop in f4:
            stoppings.append(stop.strip('\n'))
    f4.close()
    with open(data_path, 'r', encoding=encoding) as f5:
        for line in f5.readlines():
            trans = line.strip().split(" ")
            valid = []
            fial_l = [my.replace('?','') for my in trans]
            for i in fial_l:
                if i not in stoppings:
                    valid.append(i)
                firm = normalise_query(valid)
            result.append(firm)
    return result


"""
dealing with R_queries
"""


score_list = []
l_RQ = preprocess_Rquery('queries.ranked.txt')
for each in l_RQ:
    OR_doc = []
    Rq_num = each[0]
    sub_Rq_list = each[1:]
    # print(sub_Rq_list)
    for wr in sub_Rq_list:
        doc_listRq = list(inverted_positional_index[wr].keys())
        #print(doc_listRq)
        OR_doc.append(doc_listRq)
    #print(OR_doc)
    common_doc = set().union(*OR_doc)
    #print(sorted(common_doc))
    for si in common_doc:
        score = 0
        for term_rq in sub_Rq_list:
            if si in inverted_positional_index[term_rq].keys():
                df1 = len(inverted_positional_index[term_rq])
                tf1 = len(inverted_positional_index[term_rq][si])
                score += weight(tf1,df1)
            else:
                score += 0
        score_list.append((int(Rq_num) , str(si) , score))
#sorted_scores = sorted(score_list, key=itemgetter(0,2), reverse=True)
sorted_scores = sorted(score_list,  key=lambda tup:(tup[0], -tup[2]))



"""
write into results.ranked.txt
"""
if not os.path.exists("results.ranked.txt"):
    fr =open('results.ranked.txt','w')
    for line in sorted_scores:
          fr.write("%s,%s,%.4f\n" % (str(line[0]), line[1], line[2]))
    fr.close()




