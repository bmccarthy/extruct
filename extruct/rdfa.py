"""
HTML Microdata parser

Piece of code extracted form:
* http://blog.scrapinghub.com/2014/06/18/extracting-schema-org-microdata-using-scrapy-selectors-and-xpath/

Ported to lxml
follows http://www.w3.org/TR/microdata/#json

"""

import collections
from six.moves import zip_longest
from six.moves.urllib.parse import urljoin

import lxml.etree
import lxml.html

# from https://www.w3.org/2011/rdfa-context/rdfa-1.1
W3C_PREFIXES = {
    "org": "http://www.w3.org/ns/org#",
    "void": "http://rdfs.org/ns/void#",
    "wdr": "http://www.w3.org/2007/05/powder#",
    "rdfa": "http://www.w3.org/ns/rdfa#",
    "qb": "http://purl.org/linked-data/cube#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "ma": "http://www.w3.org/ns/ma-ont#",
    "xhv": "http://www.w3.org/1999/xhtml/vocab#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "wdrs": "http://www.w3.org/2007/05/powder-s#",
    "rif": "http://www.w3.org/2007/rif#",
    "grddl": "http://www.w3.org/2003/g/data-view#",
    "sd": "http://www.w3.org/ns/sparql-service-description#",
    "prov": "http://www.w3.org/ns/prov#",
    "csvw": "http://www.w3.org/ns/csvw#",
    "rr": "http://www.w3.org/ns/r2rml#",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "skosxl": "http://www.w3.org/2008/05/skos-xl#"
}

WIDELY_USED_PREFIXES = {
    "cc": "http://creativecommons.org/ns#",
    "v": "http://rdf.data-vocabulary.org/#",
    "dc11": "http://purl.org/dc/elements/1.1/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "vcard": "http://www.w3.org/2006/vcard/ns#",
    "dcterms": "http://purl.org/dc/terms/",
    "ical": "http://www.w3.org/2002/12/cal/icaltzd#",
    "rev": "http://purl.org/stuff/rev#",
    "dc": "http://purl.org/dc/terms/",
    "og": "http://ogp.me/ns#",
    "schema": "http://schema.org/",
    "ctag": "http://commontag.org/ns#",
    "gr": "http://purl.org/goodrelations/v1#",
    "sioc": "http://rdfs.org/sioc/ns#"
}

class EvaluationContext(object):
    def __init__(self, base, ctx=None):
        self.base = base
        self.parent_subject = self.base
        self.parent_object = None
        self.incomplete_triples = []
        self.list_mapping = []
        self.language = None
        if ctx and ctx.iri_mappings:
            self.iri_mappings = ctx.iri_mappings
        else:
            self.iri_mappings = []
        if ctx and ctx.term_mappings:
            self.term_mappings = ctx.term_mappings
        else:
            self.term_mappings = []
        if ctx and ctx.default_vocab:
            self.default_vocab = ctx.default_vocab
        else:
            self.default_vocab = None


class LocalValues(object):

    def __init__(self, ctx):
        self.ctx = ctx
        self.skip_element = False
        self.new_subject = None
        self.current_property_value = None
        self.current_object_resource = None
        self.typed_resource = None
        self.iri_mappings = ctx.iri_mappings
        self.incomplete_triples = None
        self.list_mapping = ctx.list_mapping
        self.current_language = ctx.language
        self.term_mappings = ctx.term_mappings
        self.default_vocab = ctx.default_vocab

class BNode(object):
    """a bnode"""

def _grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def _prefixes(prefix):
    return [(p.strip(':'), uri)
            for (p, uri) in _grouper(2, prefix.strip().split())]

def resolve_resource(value, ctx):
    return urljoin(ctx.base, value)

def resolve_iri(value, ctx):
    return urljoin(ctx.base, value)

class RDFaExtractor(object):

    def __init__(self, parser='lxml'):
        self.parser = parser

    def extract(self, htmlstring, url='http://www.example.com/', encoding="UTF-8"):

        # https://www.w3.org/TR/rdfa-core/#s_sequence
        # 7.5 Sequence
        # At the beginning of processing, an initial evaluation context is created

        self.ctx = EvaluationContext(base=url)

        # 1. First, the local values are initialized
        local_values = LocalValues(self.ctx)
        if self.parser == 'lxml':
            parser = lxml.html.HTMLParser(encoding=encoding)
            lxmldoc = lxml.html.fromstring(htmlstring, parser=parser)
        elif self.parser == 'html5lib':
            from lxml.html import html5parser
            lxmldoc = html5parser.fromstring(htmlstring)

        return {'tuples': list(self.extract_tuples(lxmldoc, local_values))}

    def extract_tuples(self, node, local_values):
        print("extract_tuples(%r)" % node)
        # 2. Next the current element is examined for any change to the default vocabulary via @vocab
        vocab = node.get("vocab")
        print("vocab=%r" % vocab)
        if vocab is not None:
            local_values.default_vocab = vocab
            yield (local_values.ctx.base,
                   "http://www.w3.org/ns/rdfa#usesVocabulary",
                   local_values.default_vocab)
        # TODO: If the value is empty, then the local default vocabular
        # must be reset to the Host Language defined default (if any).
        elif not vocab:
            #local_values.default_vocab = hostvocab
            pass

        # 3. Next, the current element is examined for IRI mappings
        prefix = node.get("prefix")
        print(prefix)
        if prefix:
            prefixes = _prefixes(prefix)
            print(prefixes)

        # 4. The current element is also parsed for any language information
        # TODO: this is now skipped

        # 5. If the current element contains no @rel or @rev attribute,
        # then the next step is to establish a value for new subject.
        rel_attr = node.get("rel")
        rev_attr = node.get("rev")
        property_attr = node.get("property")
        content_attr = node.get("content")
        datatype_attr = node.get("datatype")

        if not (rel_attr or rev_attr):

            # 5.1 If the current element contains the @property attribute,
            # but does not contain either the @content or @datatype attributes
            if property_attr and not (content_attr or datatype_attr):

                # new subject?

                about_attr = node.get("about")
                if about_attr:
                    local_values.new_subject = resolve_resource(about_attr, local_values.ctx)
                #TODO: check for root node
                #elif node == root
                elif False:
                    local_values.new_subject = resolve_resource("", local_values.ctx)
                elif local_values.ctx.parent_object:
                    local_values.new_subject = local_values.ctx.parent_object

                # typed resource?

                typeof_attr = node.get("typeof")
                if typeof_attr:
                    local_values.typed_resource = resolve_resource(typeof_attr, local_values.ctx)
                #TODO: check for root node
                #elif node == root
                #    local_values.typed_resource = ""
                else:
                    found = False
                    for aname, resfun in (
                            ("resource", resolve_resource),
                            ("href", resolve_iri),
                            ("src", resolve_iri),
                        ):
                        avalue = node.get(aname)
                        if avalue:
                            local_values.typed_resource = resfun(avalue, local_values.ctx)
                            found = True
                            break
                    if not found:
                        local_values.typed_resource = BNode()
                    local_values.current_object_resource = local_values.typed_resource

            else:
        # 5.2 otherwise:
                found = False
                for aname, resfun in (
                        ("about", resolve_resource),
                        ("resource", resolve_resource),
                        ("href", resolve_iri),
                        ("src", resolve_iri),
                    ):
                    avalue = node.get(aname)
                    if avalue:
                        local_values.new_subject = resfun(avalue, local_values.ctx)
                        found = True
                        break

                if not found:

                    typeof_attr = node.get("typeof")
                    # TODO: test root element
                    if False:
                        # consider empty @about value
                        local_values.new_subject = resfun("", local_values.ctx)
                    else:
                        if typeof_attr:
                            local_values.new_subject = BNode()
                        elif local_values.ctx.parent_object:
                            local_values.new_subject = local_values.ctx.parent_object
                            if not node.get("property"):
                                local_values.skip_element = True

                    if typeof_attr:
                        local_values.typed_resource = local_values.new_subject

        # 6. If the current element does contain a @rel or @rev attribute,
        # then the next step is to establish both a value for new subject
        # and a value for current object resource:
        about_attr = node.get("about")
        typeof_attr = node.get("typeof")
        if about_attr:
            local_values.new_subject = resolve_resource(about_attr, local_values.ctx)
            if typeof_attr:
                local_values.typed_resource = local_values.new_subject
        else:
            # TODO: test root node
            if False:
                local_values.new_subject = resolve_resource("", local_values.ctx)
                if typeof_attr:
                    local_values.typed_resource = local_values.new_subject
            else:
                local_values.new_subject = local_values.ctx.parent_object

        found = False
        for aname, resfun in (
                ("resource", resolve_resource),
                ("href", resolve_iri),
                ("src", resolve_iri),
            ):
            avalue = node.get(aname)
            if avalue:
                local_values.current_object_resource = resfun(avalue, local_values.ctx)
                found = True
                break
        if not found:
            if typeof_attr and not about_attr:
                local_values.current_object_resource = BNode()

        if typeof_attr and not about_attr:
            local_values.typed_resource = local_values.current_object_resource

        # 7. If in any of the previous steps a typed resource was set
        # to a non-null value, it is now used to provide a subject for type values;
        if typeof_attr:
            for iri in typeof_attr.split():
                yield (local_values.typed_resource,
                       'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
                       iri)

        # 8. If in any of the previous steps a new subject was set
        # to a non-null value different from the parent object;

        # 9. If in any of the previous steps a current object resource was set
        # to a non-null value, it is now used to generate triples
        # and add entries to the local list mapping:

        # If the element contains both the @inlist and the @rel attributes the @rel may contain one or more resources
        # TODO: this is skipped for now

        if local_values.current_object_resource is not None:
            if rel_attr and not node.get("inlist"):
                for iri in rel_attr.split():
                    yield (local_values.new_subject,
                           resolve_iri(iri, local_values.ctx),
                           local_values.current_object_resource)
            if rev_attr:
                for iri in rev_attr.split():
                    yield (local_values.current_object_resource,
                           resolve_iri(iri, local_values.ctx),
                           local_values.new_subject)

        # 10. If however current object resource was set to null,
        # but there are predicates present, then they must be stored as incomplete triples
        # TODO: this is skipped for now

        # 11. The next step of the iteration is to establish any current property value;

        # TODO: skipping the part on @datatype

        content_attr = node.get("content")
        if content_attr:
            local_values.current_property_value = content_attr
        else:
            local_values.current_property_value = lxml.html.tostring(node, method="text", encoding="unicode")

        # TODO: we skip the @inlist thing
        if property_attr:
            for iri in property_attr.split():
                yield (local_values.new_subject,
                       resolve_iri(iri, local_values.ctx),
                       local_values.current_property_value)

        # 12. If the skip element flag is 'false',
        # and new subject was set to a non-null value,
        # then any incomplete triples within the current context should be completed:

        # 13. Next, all elements that are children of the current element
        # are processed using the rules described here, using a new evaluation
        # context
        for child in node.getchildren():
            for t in self.extract_tuples(child, local_values):
                yield t
