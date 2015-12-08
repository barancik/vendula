#!/usr/bin/python
# -*- coding: utf-8 -*-

import unittest
from counting_frequency import Word,Sentence

class Test_Word(unittest.TestCase):
    def setUp(self):
        self.adj = Word("letecké|letecký|AAFP1----1A----",22)
        self.obj = Word("zobrazení|zobrazení_^(*3it)|NNNS4-----A----",13)
        self.verb = Word("Připoutala|připoutat-:W|VpQW---XR-AA---",1)
        self.prep = Word("v|v-1|RR--6---------",10)

    def test_word(self):
        self.assertEqual(self.obj.word,"zobrazení")
        self.assertEqual(self.verb.word,"Připoutala")

    def test_lemma(self):
        self.assertEqual(self.obj.lemma,"zobrazení_^(*3it)")

    def test_tag(self):
        self.assertEqual(self.obj.tag,"NNNS4-----A----")

    def test_position(self):
        self.assertEqual(self.obj.position,13)

    def test_shortlemma(self):
        self.assertEqual(self.obj.shortlemma,"zobrazení")
        self.assertEqual(self.verb.shortlemma,"připoutat")

    def test_case(self):
        self.assertEqual(self.obj.case(),"4")

    def test_get_lemma(self):
        self.assertEqual(self.obj.get_lemma(),self.obj.shortlemma)

    def test_has_tag(self):
        self.assertTrue(self.obj.has_tag("N..S4"))
        self.assertFalse(self.obj.has_tag("N..P4"))
        self.assertFalse(self.obj.has_tag("N..S2"))
        self.assertTrue(self.verb.has_tag("Vp"))
        self.assertFalse(self.verb.has_tag("N..."))

    def test_is_accusative(self):
        self.assertTrue(self.obj.is_accusative())
        self.assertFalse(self.adj.is_accusative())

    def test_is_adjective(self):
        self.assertTrue(self.adj.is_adjective())
        self.assertFalse(self.obj.is_adjective())

    def test_is_nominative(self):
        self.assertTrue(self.adj.is_nominative())
        self.assertFalse(self.obj.is_nominative())

    def test_is_object(self):
        self.assertTrue(self.obj.is_object())
        self.assertTrue(self.obj.is_object("4","S"))
        self.assertTrue(self.obj.is_object(number="S"))
        self.assertFalse(self.adj.is_object("1","P"))

    def test_is_noun(self):
        self.assertTrue(self.obj.is_noun())
        self.assertFalse(self.adj.is_noun())

    def test_is_preposition(self):
        self.assertTrue(self.prep.is_preposition())
        self.assertFalse(self.adj.is_preposition())
        self.assertFalse(self.obj.is_preposition())

    def test_is_singular(self):
        self.assertTrue(self.obj.is_singular())
        self.assertFalse(self.adj.is_singular())

    def test_is_verb(self):
        self.assertTrue(self.verb.is_verb())
        self.assertFalse(self.prep.is_verb())

    def test_number(self):
        self.assertEqual(self.adj.number(),"P")
        self.assertEqual(self.obj.number(),"S")

    def test_general(self):
        self.assertTrue(self.adj.is_adjective() and self.adj.is_nominative())
        self.assertTrue(self.obj.is_accusative() and self.obj.is_noun("4","S"))
        self.assertTrue(self.verb.is_verb() and self.verb.is_active())
        self.assertTrue(self.prep.is_preposition() and self.prep.case() == "6")


if __name__ == '__main__':
    unittest.main()
