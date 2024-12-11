from bs4 import BeautifulSoup

from scripts.extract import ZhWikiQuoteCrawler


def test_crawler_wikiquote_zh():
    testcases = [
        (
            """
<li>这种争斗我，也看得够了，由他去吧！<sup id="cite_ref-1" class="reference"><a href="#cite_note-1"><span class="cite-bracket">[</span>1<span class="cite-bracket">]</span></a></sup></li>
""",
            "li",
            "这种争斗我，也看得够了，由他去吧！",
            "",
        ),
        (
            """<li>岂有豪情似旧时，花开花落两由之。
<dl><dd>——七言绝句《悼杨铨》（1933年）</dd></dl></li>""",
            "li",
            "岂有豪情似旧时，花开花落两由之。",
            "七言绝句《悼杨铨》（1933年）",
        ),
        (
            """<li><a href="/wiki/%E4%BA%BA" title="人">人</a>必<a href="/wiki/%E7%94%9F%E6%B4%BB" title="生活">生活</a>着，<a href="/wiki/%E6%84%9B" class="mw-redirect" title="爱">爱</a>才有所附丽。
<dl><dd>——鲁迅唯一一部爱情小说《伤逝》（1925年）</dd></dl></li>""",
            "li",
            "人必生活着，爱才有所附丽。",
            "鲁迅唯一一部爱情小说《伤逝》（1925年）",
        ),
        (
            """<li><b>其实地上本没有路；走的人多了，也便成了路。</b></li>""",
            "li",
            "其实地上本没有路；走的人多了，也便成了路。",
            "",
        ),
        (
            """<li><b>寄意寒星荃不察，我以我血荐轩辕。</b> （鲁迅·自题小像）</li>""",
            "li",
            "寄意寒星荃不察，我以我血荐轩辕。",
            "鲁迅·自题小像",
        ),
        (
            """<ul><li>凡是愚弱的国民，即使体格如何健全，如何茁壮，也只能做毫无意义的示众的材料和看客，病死多少是不必以为不幸的。
<dl><dd>——《<a href="https://zh.wikisource.org/wiki/%E5%90%B6%E5%96%8A" class="extiw" title="s:呐喊">呐喊自序</a>》（1922年）</dd>
<dd><b>注：</b> 鲁迅在成为作家以前曾是一名留学日本的医学生，一次观看日本用十万牺牲攻陷旅顺的日俄战争影片，拍到中国同胞对侵吞中国东北的沙俄协力（翻译）被日本人处决。回忆看片的其他中国人欢呼，鲁迅写道自己转而认为挽救灵魂比肉身更重要，乃弃学回国从事笔耕。</dd></dl></li></ul>""",
            "li",
            "凡是愚弱的国民，即使体格如何健全，如何茁壮，也只能做毫无意义的示众的材料和看客，病死多少是不必以为不幸的。",
            "《呐喊自序》（1922年）",
        ),
        (
            """<ul><li>中国各处是壁，然而无形，像‘鬼打墙’一般，使你随时能‘碰’，能打这墙的，能碰而不感到痛苦的，是胜利者。</li></ul><dl><dd><i>出自《碰壁之后》一九二五年</i></dd></dl>""",
            "li",
            "中国各处是壁，然而无形，像‘鬼打墙’一般，使你随时能‘碰’，能打这墙的，能碰而不感到痛苦的，是胜利者。",
            "《碰壁之后》一九二五年",
        ),
        (
            """<ul><li>愿中国青年都摆脱冷气，只是向上走，不必听自暴自弃者流的话。能做事的做事，能发声的发声。有一分热，发一分光。就令萤火一般，也可以在黑暗里发一点光，不必等候炬火。</li></ul><p><i>出自《热风•四十一》一九二五年十一月，北京北新书局初版</i>
</p>""",
            "li",
            "愿中国青年都摆脱冷气，只是向上走，不必听自暴自弃者流的话。能做事的做事，能发声的发声。有一分热，发一分光。就令萤火一般，也可以在黑暗里发一点光，不必等候炬火。",
            "《热风•四十一》一九二五年十一月，北京北新书局初版",
        ),
        (
            """<li>旧社会那种<a href="https://zh.wikipedia.org/wiki/%E7%A7%81%E6%9C%89%E5%88%B6" class="extiw" title="w:私有制">私有制</a>，使兄弟间也不顾情义。我父亲和你父亲是<a href="https://zh.wikipedia.org/wiki/%E5%A0%82%E5%85%84%E5%BC%9F" class="extiw" title="w:堂兄弟">堂兄弟</a>，买你家那七亩田时，就只顾自己发财，全无兄弟之情，什么劝说都听不进去。我后来思考这些事，认识到这不光是个人与家庭问题，还是<a href="https://zh.wikipedia.org/wiki/%E7%A4%BE%E6%9C%83%E5%88%B6%E5%BA%A6" class="extiw" title="w:社会制度">社会制度</a>问题；认清只有彻底改造这个社会，才能根绝这类事情，于是下决心寻找一条解救穷苦<a href="https://zh.wikipedia.org/wiki/%E8%BE%B2%E6%B0%91" class="extiw" title="w:农民">农民</a>的<a href="https://zh.wikipedia.org/wiki/%E9%81%93%E8%B7%AF" class="extiw" title="w:道路">道路</a>。<sup id="cite_ref-青_1-0" class="reference"><a href="#cite_note-青-1"><span class="cite-bracket">[</span>1<span class="cite-bracket">]</span></a></sup><sup class="reference" style="white-space:nowrap;">:39-40</sup>
<dl><dd>——<a href="https://zh.wikipedia.org/wiki/%E4%B8%AD%E8%8F%AF%E4%BA%BA%E6%B0%91%E5%85%B1%E5%92%8C%E5%9C%8B%E6%88%90%E7%AB%8B" class="extiw" title="w:中华人民共和国成立">中华人民共和国成立</a>后，多次与堂弟毛泽连谈及父亲毛顺生向毛泽连父亲毛菊生买进其赖以活命的7亩田，认为是极不道德</dd></dl></li>""",
            "li",
            "旧社会那种私有制，使兄弟间也不顾情义。我父亲和你父亲是堂兄弟，买你家那七亩田时，就只顾自己发财，全无兄弟之情，什么劝说都听不进去。我后来思考这些事，认识到这不光是个人与家庭问题，还是社会制度问题；认清只有彻底改造这个社会，才能根绝这类事情，于是下决心寻找一条解救穷苦农民的道路。",
            "中华人民共和国成立后，多次与堂弟毛泽连谈及父亲毛顺生向毛泽连父亲毛菊生买进其赖以活命的7亩田，认为是极不道德",
        ),
        (
            """<li>日本帝国主义想把蒋介石完全控制在自己手下，“党对时局应有表示，发表文件，在部队中宣传，反对日本”，这是“最能动员群众”<sup id="cite_ref-毛一_4-2" class="reference"><a href="#cite_note-毛一-4"><span class="cite-bracket">[</span>4<span class="cite-bracket">]</span></a></sup><sup class="reference" style="white-space:nowrap;">:345</sup>。
<dl><dd>——在中共中央常委会议上的发言记录，1935年6月29日</dd></dl></li>""",
            "li",
            "日本帝国主义想把蒋介石完全控制在自己手下，“党对时局应有表示，发表文件，在部队中宣传，反对日本”，这是“最能动员群众”。",
            "在中共中央常委会议上的发言记录，1935年6月29日",
        ),
        (
            """<li>我方对于政治会议的方针是，继续坚持和平政策，坚持通过谈判协商和平解决朝鲜问题，并进一步争取和平解决<a href="https://zh.wikipedia.org/wiki/%E9%81%A0%E6%9D%B1" class="extiw" title="w:远东">远东</a>其他问题，以缓和<a href="https://zh.wikipedia.org/wiki/%E5%9C%8B%E9%9A%9B" class="extiw" title="w:国际">国际</a>的紧张局势。<sup id="cite_ref-毛四_12-18" class="reference"><a href="#cite_note-毛四-12"><span class="cite-bracket">[</span>12<span class="cite-bracket">]</span></a></sup><sup class="reference" style="white-space:nowrap;">:85</sup>
<ul><li>致电金日成，提出中国对双方分别派代表召开政治会议之意见，1953年8月15日</li></ul></li>""",
            "li",
            "我方对于政治会议的方针是，继续坚持和平政策，坚持通过谈判协商和平解决朝鲜问题，并进一步争取和平解决远东其他问题，以缓和国际的紧张局势。",
            "致电金日成，提出中国对双方分别派代表召开政治会议之意见，1953年8月15日",
        ),
        (
            """<li>“俄国政府两年前实行的政策，其原则与方针与我政府是完全不同的。但是俄国政府的现行政策——新经济政策，其主要点与应在中国实行的我的《建国方略》如出一辙。”
<dl><dd>——与日本广州新闻社记者的谈话，1924年3月<sup id="cite_ref-qj9_39-2" class="reference"><a href="#cite_note-qj9-39"><span class="cite-bracket">[</span>39<span class="cite-bracket">]</span></a></sup><sup class="reference" style="white-space:nowrap;">:671</sup></dd></dl></li>""",
            "li",
            "“俄国政府两年前实行的政策，其原则与方针与我政府是完全不同的。但是俄国政府的现行政策——新经济政策，其主要点与应在中国实行的我的《建国方略》如出一辙。”",
            "与日本广州新闻社记者的谈话，1924年3月",
        ),
        (
            """<li>我们的梦醒了，我们知道就要上岸了；我们心里充满了幻灭的情思。
<ul><li>《<a href="https://zh.wikisource.org/wiki/%E6%A1%A8%E5%A3%B0%E7%81%AF%E5%BD%B1%E9%87%8C%E7%9A%84%E7%A7%A6%E6%B7%AE%E6%B2%B3" class="extiw" title="s:桨声灯影里的秦淮河">桨声灯影里的秦淮河</a>》</li></ul></li>""",
            "li",
            "我们的梦醒了，我们知道就要上岸了；我们心里充满了幻灭的情思。",
            "《桨声灯影里的秦淮河》",
        ),
    ]

    crawler = ZhWikiQuoteCrawler()

    for html, tag, content, source in testcases:
        element = BeautifulSoup(html, "html5lib").find(tag)
        cookie = crawler.parse_item(element)
        assert cookie.content == content
        assert cookie.source == source
