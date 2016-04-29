# -*- coding: utf-8 -*-
import json
import unittest

from extruct.rdfa import RDFaExtractor
from tests import get_testdata

class TestRDFa(unittest.TestCase):

    maxDiff = None

    def test_rdfalite_001(self):
        prefix = 'rdfalite.2.1.example003'
        body = get_testdata('w3c', '{}.html'.format(prefix))
        expected = json.loads(
            get_testdata('w3c', '{}.json'.format(prefix)).decode('UTF-8')
        )
        rdfae = RDFaExtractor()
        data = rdfae.extract(body)
        self.assertDictEqual(data, expected)

    def test_rdfalite_002(self):
        prefix = 'rdfalite.2.2.example004'
        body = get_testdata('w3c', '{}.html'.format(prefix))
        expected = json.loads(
            get_testdata('w3c', '{}.json'.format(prefix)).decode('UTF-8')
        )
        rdfae = RDFaExtractor()
        data = rdfae.extract(body)
        self.assertDictEqual(data, expected)

    def test_rdfalite_003(self):
        prefix = 'rdfalite.2.3.example005'
        body = get_testdata('w3c', '{}.html'.format(prefix))
        expected = json.loads(
            get_testdata('w3c', '{}.json'.format(prefix)).decode('UTF-8')
        )
        rdfae = RDFaExtractor()
        data = rdfae.extract(body)
        self.assertDictEqual(data, expected)

    def test_003(self):
        prefix = 'rdfa1.1.primer.2.1.5.example028'
        body = get_testdata('w3c', '{}.html'.format(prefix))
        expected = json.loads(
            get_testdata('w3c', '{}.json'.format(prefix)).decode('UTF-8')
        )
        rdfae = RDFaExtractor(parser='html5lib')
        data = rdfae.extract(body)
        self.assertDictEqual(data, expected)
