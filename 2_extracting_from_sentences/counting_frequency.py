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
        self.sentences = []
        self.compute(path_to_corpora)

    def compute(self,path):
        line = list(gzip.open(path,"r"))[1]
        sentence  = Sentence(line)
 #       for line in gzip.open(path,"r"):
#            print line
#            sentence  = Sentence(line)
#            self.sentences.append(sentence) # N
#            for vi in sentence.verb_idxs:
#                verb = sentence.get_lemma(vi)
#                objects = sentence.find_object(vi)
#                for noun in objects:
#                    if verb in self.verbs:
#                        self.LV_N_freq[(verb,noun)] += 1 # LV + N
#                        self.LV_freq[verb] += 1 # LV
#                    self.N_freq[noun] += 1

    def add_noun_counts(self,sentence):
        for noun_idx in sentence.noun_idxs:
            self.N_freq[sentence.get_lemma(noun_idx)] += 1
            print sentence.get_lemma(noun_idx)


class Sentence(object):
    def __init__(self,line):
        self.words = [Word(unit,idx) for idx,unit in enumerate(line.strip().split())]
        self.verbs = filter(lambda x: x.is_verb(), self.words)
        self.verb_object_pairs = [(w,o) for w in self.verbs for o in self.find_objects(w.position)]

    def get_lemma(self,idx):
        return self.words[idx].shortlemma

    def __str__(self):
        return " ".join([word.word for word in self.words])

    def _query1(self):
        #negative pattern
        # type [lemma="dát"&tag="V[^s].*"] positive filter -3, +3 [tag="N..S4.*"]
        # tj. beru to jako ten muj objekt, ale v singularu
        active_verbs = filter(lambda x: x.is_active(), self.verbs)
        query1 = filter(lambda (x,y): x in active_verbs and y.is_singular(), self.verb_object_pairs)
        return self.return_lemma_pairs(query1)

    def sentence_range(self,bottom,top):
        bottom = max(0,bottom)
        top = min(top,len(self.words))
        return range(bottom,top)

    def _query2a(self):
        #positive_pattern
        found = []
        be_verbs = filter(lambda x: x.shortlemma == "být", self.verbs)
        for to_be in be_verbs:
            idx = to_be.position
            for x in self.sentence_range(idx,idx+5):
                # [lemma="dát"&tag="Vs.*"]
                if self.words[x].is_verb() and not self.words[x].is_active():
                    # na výsledek uplatnit další pozitivní filtr -3, +3 [tag="N..S1.*"] (př. rozkaz se dal)
                    for y in self.sentence_range(idx-3,x+3):
                        w = self.words[y]
                        if w.is_noun("1","S"): # and w.is_singular() and w.is_nominative():
                            found.append((self.words[x].shortlemma, w.shortlemma))
        return found

    def _query2b(self):
        #positive_pattern
        # [word="se"&tag!="[PR].*"]
        found = []
        se = filter(lambda x: x.shortlemma == "se" and not x.has_tag("PR"), self.words)
        for s in se:
            s_idx = s.position
            for x in self.sentence_range(s_idx,s_idx+5):
                # verb [lemma="dát"&tag="V[^s].*"]
                if self.words[x].is_verb() and self.words[x].is_active():
                    for y in self.sentence_range(s_idx-3,x+3):
                        w = self.words[y]
                        if w.is_noun("1","S"): # and w.is_singular() and w.is_nominative():
                             found.append((self.words[x].shortlemma, w.shortlemma))
        return found

    def _query2c(self):
        #positive pattern
        #[lemma="mít"&tag="V.*"] [lemma!="být"&tag!="Vf."]
        found = []
        #idxs of verbs ="mít", not followed by "být"
        mit_idxs = filter(lambda x: sentence.words[x+1].shortlemma != "být" \
                          and not sentence.words[x+1].has_tag("Vf"), \
                         [x.position for x in self.verbs if x.shortlemma == "mít"])
#        mit = [self.words[x] for x in mit_idxs \
#                                 if self.words[x+1].shortlemma != "být" \
#                                 if not self.words[x+1].has_tag("Vf")]
        for mit_idx in mit_idxs:
            for x in self.sentence_range(mit_idx+1,mit_idx+6):
                if self.words[x].is_verb() and self.words[x].has_tag("Vs"):
                    for obj in self._find_objects(mit_idx-3,x+3):
                        found.append((self.words[x].shortlemma,self.words[obj].shortlemma))
#                    for o in self.sentence_range(mit_idx-3,x+3):
#                        if self.words[o].is_object() and self.not_follows_preposition(o):
#                               found.append((self.words[x].shortlemma,self.words[o].shortlemma))
        return found
        #TODO - tu jsem nekde asi prestala
        #ilter(lambda x: x.shortlemma == "mít" and x.is_verb() and /

    def _find_objects(self,top,bottom,case="4",number="S"):
        return filter(lambda x: self.words[x].is_noun(case,number) and 
                               self.not_follows_preposition(x), \
                      self.sentence_range(top,bottom))

    def find_objects(self,idx,context_size=CONTEXT_SIZE):
        # Get verb idx and return array with  its objects.
        bottom = max(0,idx-context_size)
        top = min(idx+context_size+1,len(self.words))
        return [self.words[x] for x in range(bottom,top) if self.words[x].is_noun(case="4") \
                                                         if self.not_follows_preposition(x)]
        
    def not_follows_preposition(self,idx):
        if idx == 0:
            return True
        if self.words[idx-1].is_preposition():
            return False
        if self.words[idx-1].is_adjective():
            return self.not_follows_preposition(idx-1)
        return True

    def print_objects(self):
        print ", ".join(["%s - %s" % (v.shortlemma,o.shortlemma) for v,o in self.verb_object_pairs])

    def return_lemma_pairs(self,arr):
        return [(x.shortlemma,y.shortlemma) for x,y in arr]

class Word(object):
    def __init__(self, unit, position):
        parts = unit.split("|")
        self.word = parts[0]
        self.lemma = parts[1]
        self.tag = parts[2]
        self.position = position
        self.shortlemma = self._shortlemma()

    def __str__(self):
        return self.word

    def case(self):
        return self.tag[4]

    def get_lemma(self):
        return self.shortlemma

    def has_tag(self,tag):
        return re.match(tag,self.tag)
  
    def is_accusative(self):
        return self.case() == "4"

    def is_active(self):
        return self.tag[1] != "s"

    def is_adjective(self):
        return self.tag.startswith("A")
 
    def is_nominative(self):
        return self.case() == "1"

    def is_object(self,case="4",number="S"):
        return self.is_noun() and self.case() == case and self.number() == number

    def is_noun(self, case=None, number=None):
        return_value = self.tag.startswith("N")
        if case is not None:
             return_value &= self.case() == case
        if number is not None:
            return_value &= self.number() == number
        return return_value

    def is_preposition(self):
        return self.tag.startswith("R")

    def is_singular(self):
        return self.number() == "S"
 
    def is_verb(self):
        return self.tag.startswith("V")

    def number(self):
        #whether it is singular or plural
        return self.tag[3]

    def _shortlemma(self):
        if len(self.lemma) < 2 or self.lemma[0] in ["^","_",";","`","-"]:
            return self.lemma
        return re.match("[^_;`-]+",self.lemma).group(0)

#verbex = re.escape(verb) + r"[:_]?"
#nsgacc = r"N..S4.*"
if __name__ == "__main__":
#    Corpus(sys.argv[1])
     i = 0
     for line in gzip.open("corpora/czeng10","r"):
         i += 1
#     for line in gzip.open("corps/extracted.gz","r"):
         sentence = Sentence(line)

         rrr =  sentence._query2c()
         if rrr:
             print i
             import pdb; pdb.set_trace()
#         print "---------"


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
