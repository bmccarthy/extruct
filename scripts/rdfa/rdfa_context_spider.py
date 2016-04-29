import scrapy


class RDFaCoreInitContextSpider(scrapy.Spider):
    name = "rdfacoreinitctx"

    def start_requests(self):
        yield scrapy.Request("https://www.w3.org/2011/rdfa-context/rdfa-1.1",
                             callback=self.parse_core)
        yield scrapy.Request("https://www.w3.org/2011/rdfa-context/xhtml-rdfa-1.1",
                             callback=self.parse_xhtml)

    def parse_core(self, response):
        # prefixes
        for cap in ["Vocabulary Prefixes of W3C Documents",
                    "Widely used Vocabulary prefixes"]:
            yield {
                'prefixes': dict(row.xpath('td[position()<=2]/text()').extract()
                            for row in response.xpath('''
                                //table[re:test(caption, "{caption}")]
                                    /tbody/tr'''.format(caption=cap)))
            }
        # terms
        for cap in ["Terms defined by W3C Documents"]:
            yield {
                'terms': dict(row.xpath('td[position()<=2]/text()').extract()
                            for row in response.xpath('''
                                //table[re:test(caption, "{caption}")]
                                    /tbody/tr'''.format(caption=cap)))
            }

    def parse_xhtml(self, response):
        # terms
        for cap in ["Terms Defined by XHTML Vocabulary"]:
            yield {
                'terms': dict(row.xpath('td[position()<=2]/text()').extract()
                            for row in response.xpath('''
                                //table[re:test(caption, "{caption}")]
                                    /tbody/tr'''.format(caption=cap)))
            }
