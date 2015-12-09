#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import gzip
import re
import sys
import unidecode

from collections import defaultdict

# zkusit i CONTEXT_SIZE 4, obcas by to zda se pomohlo..y
CONTEXT_SIZE = 3
TAG = r"N..S4.*"
#VERBS = [verb.strip() for verb in open("../FINAL_VERBS","r")]

#class Matches(object):
#    #one class to contain more Matches
#    def __init__(self):
#        self.matches = []
#
#    def add(self,match):
#        self.matches.append(match)
#
#    def __str__(self):
#        fo
#
#class Match(object):
#    #captured matched verbs, object
#    def __init__(verb,obj,structure):
#        self.verb = verb
#        self.obj = obj
#        self.structure = structure
#
#    def __str__(self):
#        return "%s %s %s" % (self.verb,self.obj,self.structure)
#

class MM(object):
    def __init__(self):
        self.counts = defaultdict(int)

    def add(self,arr):
        for arg in arr:
            self.counts[arg] += 1

    def __str__(self):
        return "\n".join(["%s %s %s %d" % (x[0],x[1],x[2],y) for x,y in self.counts.iteritems()])


class Sentence(object):
    def __init__(self,line):
        self.words = [Word(unit,idx) for idx,unit in enumerate(line.strip().split())]
        self.verbs = filter(lambda x: x.is_verb(), self.words)
        self.verb_object_pairs = [(w,o) for w in self.verbs for o in self.find_objects(w.position)]

    def verb_object_estimate(self):
        return len(self.verb_object_pairs)

    def lemma(self,idx):
        return self.words[idx].shortlemma

    def __str__(self):
        return " ".join([word.word for word in self.words])

    def count(self,matches):
        matches.add(self._query1())
        matches.add(self._query2a())
        matches.add(self._query2b())
        matches.add(self._query2c())
        matches.add(self._query3())
        matches.add(self._query4())
        matches.add(self._query5())
        return matches

    def print_matches(self):
        matches = MM()
        matches.add(self._query1())
        matches.add(self._query2a())
        matches.add(self._query2b())
        matches.add(self._query2c())
        matches.add(self._query3())
        matches.add(self._query4())
        matches.add(self._query5())
        print self.__str__()
        if matches.counts:
            print matches
        else:
            print "Nada"

    def _query1(self):
        #negative pattern
        # type [lemma="dát"&tag="V[^s].*"] positive filter -3, +3 [tag="N..S4.*"]
        # tj. beru to jako ten muj objekt, ale v singularu
        query1 = filter(lambda (x,y): x.is_active() and y.is_singular(), self.verb_object_pairs)
        return [(pair[0].shortlemma, pair[1].shortlemma, "q1")for pair in query1]

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
                        if self.words[y].is_noun("1","S"): # and w.is_singular() and w.is_nominative():
                            found.append((self.lemma(x), self.lemma(y),"q2a"))
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
                        if self.words[y].is_noun("1","S"): # and w.is_singular() and w.is_nominative():
                             found.append((self.lemma(x), self.lemma(y),"q2b"))
        return found

    def _query2c(self):
        #positive pattern
        #[lemma="mít"&tag="V.*"] [lemma!="být"&tag!="Vf."]
        found = []
        #idxs of verbs ="mít", not followed by "být"
        mit_idxs = filter(lambda x: self.words[x+1].shortlemma != "být" \
                          and not self.words[x+1].has_tag("Vf"), \
                         [x.position for x in self.verbs if x.shortlemma == "mít"])
        
        for mit_idx in mit_idxs:
            for x in self.sentence_range(mit_idx+1,mit_idx+6):
                if self.words[x].is_verb() and self.words[x].has_tag("Vs"):
                    for obj in self._find_objects(mit_idx-3,x+3):
                        found.append((self.lemma[x],self.lemma[obj],"q2c"))
        return found

    def _query3(self):
        #positive pattern
        # typ [lemma="dát"&tag="V[^s].*"] positive filter -3, +3 [tag="N..P4.*"]
        query3 = filter(lambda (x,y): x.is_active() and y.is_plural(), self.verb_object_pairs)
        return [(pair[0].shortlemma, pair[1].shortlemma, "q3")for pair in query3]

    def _query4(self):
        #positive pattern
        #[tag="P4.4S.*"][tag="N..S4.*"] positive filter -3, +3 [lemma="dát"&tag="V[^s].*"]
        found = []
        objects = filter(lambda x: x.is_noun("4","S") and self.words[x.position-1].has_tag("P4.4S"), self.words)
        for obj in objects:
            for idx in sentence_range(obj.position-4,obj.position+3):
                if self.words[idx].is_verb() and self.words[idx].is_active():
                    found.append((obj.shortlemma, self.lemma[idx], "q4"))
        return found

    def _query5(self):
        # positive pattern
        # typ [lemma="dát"&tag="V[^s].*"] positive filter -3, +3 [tag="A..S4.*"] [tag="N..S4.*"]
        found = []
        for pair in self.verb_object_pairs:
            obj_idx = pair[1].position
            if self.words[obj_idx-1].has_tag("A..S4"):
                found.append((pair[0].shortlemma,pair[1].shortlemma,"q5"))
        return found

    def sentence_range(self,bottom,top):
        bottom = max(0,bottom)
        top = min(top,len(self.words))
        return range(bottom,top)

#    def _find_objects(self,top,bottom,case="4",number="S"):
#        return filter(lambda x: self.words[x].is_noun(case,number) and 
#                               self.not_follows_preposition(x), \
#                      self.sentence_range(top,bottom))

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

    def is_plural(self):
        return self.number() == "P"
 
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
#     for line in gzip.open("corpora/czeng10","r"):
     matches = MM()
     for line in gzip.open("corps/extracted.gz","r"):
         sentence = Sentence(line)
         import pdb; pdb.set_trace()
         matches = sentence.count(matches)
         sentence.print_matches()
     import pdb; pdb.set_trace()


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
