#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import gzip
import re
import sys
import unidecode

from collections import defaultdict

#tohle nebude uplne fungovat, potreba jeste vyresit cesty
CONTEXT_SIZE = 3
TAG = r"N..S4.*"
#VERBS = [verb.strip() for verb in open("../FINAL_VERBS","r")]

class Corpus(object):
    def __init__(self,path_to_corpora):
        # The verbs I am interested in.
        self.verbs = [verb.strip() for verb in open("../FINAL_VERBS","r")]
        # Light Verb frequency
        self.LV_freq = defaultdict(int)
        # Noun frequency
        self.N_freq = defaultdict(int)
        # Light Verb + Noun frequency
        self.LV_N_freq = defaultdict(int)
        # Light Verb + Noun + Pattern Set frequency
        self.LV_N_PS_freq = defaultdict(int)
        # Noun + Pattern Set frequency
        self.N_PS_freq = defaultdict(int)
        self.compute(path_to_corpora)

    def compute(self,path):
        for line in gzip.open(path,"r"):
            sentence  = Sentence(line)
#            self.add_noun_counts(sentence) # N
            for vi in sentence.verb_idxs:
                verb = sentence.get_lemma(vi)
#                if verb in self.verbs:
#                    self.LV_freq[verb] += 1 # LV
                #musim najit objekt
                objects = sentence.find_object(vi)
                for noun in objects:
                    if verb in self.verbs:
                        self.LV_N_freq[(verb,lemma)] += 1 # LV + N
                        self.LV_freq[verb] += 1 # LV
                    self.N_freq[noun] += 1
                   
#                    import pdb; pdb.set_trace()
#                    self.LV_N_freq[(verb,lemma)] += 1 # LV + N
#                for lemma in sentence._query1(vi):
#                    self.N_PS_freq[(lemma,1)] += 1 # N + PS
#                    if LV:
#                        self.LV_N_PS_freq[(verb,lemma,1)] += 1
#            import pdb; pdb.set_trace()

    def add_noun_counts(self,sentence):
        for noun_idx in sentence.noun_idxs:
            self.N_freq[sentence.get_lemma(noun_idx)] += 1
            print sentence.get_lemma(noun_idx)


class Sentence(object):
    def __init__(self,line):
        self.words = []
        self.verb_idxs = []
        self.noun_idxs = []
        self.initiate(line)

    def get_lemma(self,idx):
        return self.words[idx].shortlemma

    def initiate(self,line):
        for position, unit in enumerate(line.strip().split()):
            word = Word(unit,position)
            self.words.append(word)
            if word.is_noun():
                self.noun_idxs.append(position)
            elif word.is_verb():
                self.verb_idxs.append(position)
        self.words = [Word(unit,idx) for idx,unit in enumerate(line.strip().split())]

    def __str__(self):
        return " ".join([word.word for word in self.words])

    def _query1(self,verb_idx):
        #positive pattern
        # type [lemma="dát"&tag="V[^s].*"] positive filter -3, +3 [tag="N..S4.*"]
        if not self.words[verb_idx].is_active():
            return []
        return [x.word for x in self.find_it(verb_idx)]

    def find_it(self,idx,it=TAG,context_size=CONTEXT_SIZE):
        bottom = max(0,idx-context_size)
        top = min(idx+context_size+1,len(self.words))
        return [w for w in self.words if w.position in range(bottom,top) if w.has_tag(it)]

    def find_object(self,idx,context_size=CONTEXT_SIZE):
        bottom = max(0,idx-context_size)
        top = min(idx+context_size+1,len(self.words))
        return [self.get_lemma(x) for x in range(bottom,top) if self.words[x].is_noun() if self.words[x].is_accusative() if not self.follows_preposition(x)]

    def follows_preposition(self,idx):
        if idx == 0:
            return False
        if self.words[idx-1].is_preposition():
            return True
        if self.words[idx-1].is_adjective():
            return self.follows_preposition(idx-1)
        return False

class Word(object):
    def __init__(self, unit, position):
        parts = unit.split("|")
        self.word = parts[0]
        self.lemma = parts[1]
        self.tag = parts[2]
        self.position = position
        self.shortlemma = self.shortlemma()

    def __str__(self):
        return self.word

    def case(self):
        return self.tag[4]

    def has_tag(self,tag):
        return re.match(tag,self.tag)
  
    def is_accusative(self):
        return self.case() == "4"

    def is_active(self):
        return self.tag[1] != "s"

    def is_adjective(self):
        return self.tag.startswith("A")
 
    def is_noun(self):
        return self.tag.startswith("N")

    def is_preposition(self):
        return self.tag.startswith("R")
 
    def is_verb(self):
        return self.tag.startswith("V")

    def number(self):
        #whether it is singular or plural
        return self.tag[3]

    def shortlemma(self):
        if len(self.lemma) < 2 or self.lemma[0] in ["^","_",";","`","-"]:
            return self.lemma
        return re.match("[^_;`-]+",self.lemma).group(0)
#
##def print_arount(words,idx,context_size=CONTEXT_SIZE):
##    a = max(0,idx-CONTEXT_SIZE)
##    b = min(idx+CONTEXT_SIZE+1,len(words))
##    print " ".join([get_word(words[i]) for i in range(a,b)])            

#def process_sentence(line):
    # takes lines from input and creates list of Word objects

    

#def query1(position,words)

#
#def find_it(words,idx,it=TAG,context_size=CONTEXT_SIZE):
#    a = max(0,idx-CONTEXT_SIZE)
#    b = min(idx+CONTEXT_SIZE+1,len(words))
#    return [shortlemma(words[i]) for i in range(a,b) if has_tag(words[i],TAG)]
#
#
#def verb_nouns(verbs=VERBS):
#    nouns = set()
#    for verb in verbs:
#        verb_no_punct = unidecode.unidecode(verb.decode(utf-8))
#        for line in open("distinguishing/nouns/"+verb_no_punct,"r"):
#            nouns.add(
#

#verbex = re.escape(verb) + r"[:_]?"
#nsgacc = r"N..S4.*"
if __name__ == "__main__":
    Corpus(sys.argv[1])

#for fil in glob.glob("extracted_sentences/%s.*" % verb):
#    corpus = re.search("\.(.*)\.gz",fil).group(1)
#    for line in gzip.open(fil,"r"):
#        words = line.strip().split()
#        verb_idxs = find_verb(words,verb)
# #       print verb_idxs
#        if not verb_idxs:
#            continue
#        for idx in verb_idxs:
#            nouns = find_it(words,idx) 
#            if nouns:
#                print "\n".join(nouns)
##            import pdb; pdb.set_trace()
#
#    for idx in range(len(words)):
#        if re.search(verbex,words[idx].split("|")[1]):
#            d = max(0,idx-3)
#            u = min(idx+3,len(words))
#            for idx2 in range(d,u):
#                if has_tag(words[idx2],nsgacc):
#                    print get_lemma(words[idx2])
