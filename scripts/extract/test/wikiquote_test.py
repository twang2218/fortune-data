from bs4 import BeautifulSoup

from extract import (
    DailyEnWikiQuoteCrawler,
    DeWikiQuoteCrawler,
    # EnWikiQuoteCrawler,
    FrWikiQuoteCrawler,
    ZhWikiQuoteCrawler,
)


def test_crawler_wikiquote_de():
    testcases = [
        (
            """
"Abends werden die Faulen fleissig." - Citatboken, Bokförlaget Natur och Kultur, Stockholm, 1967, ISBN 91-27-01681-1
""",
            "Abends werden die Faulen fleissig.",
            "Citatboken, Bokförlaget Natur och Kultur, Stockholm, 1967, ISBN 91-27-01681-1",
        ),
        (
            """
"Abwarten und Tee trinken." - Wander-DSL, Bd. 5, Sp. 702, commons. (Dort zitiert als: "Abwarten und Theetrinken.")
""",
            "Abwarten und Tee trinken.",
            'Wander-DSL, Bd. 5, Sp. 702, commons. (Dort zitiert als: "Abwarten und Theetrinken.")',
        ),
        (
            """
"Adel verpflichtet." (Noblesse oblige) - nach Pierre-Marc-Gaston de Lévis, Maximes et réflections
""",
            "Adel verpflichtet.",
            "nach Pierre-Marc-Gaston de Lévis, Maximes et réflections",
        ),
        (
            """
            "Die Katze Erinnerung: Unabhängig, unbestechlich, ungehorsam. Und doch ein wohltuender Geselle, wenn sie sich zeigt, selbst wenn sie sich unerreichbar hält." - Uwe Johnson (27. August)
""",
            "Die Katze Erinnerung: Unabhängig, unbestechlich, ungehorsam. Und doch ein wohltuender Geselle, wenn sie sich zeigt, selbst wenn sie sich unerreichbar hält.",
            "Uwe Johnson",
        ),
    ]

    crawler = DeWikiQuoteCrawler()

    for text, content, source in testcases:
        content, source = crawler.parse_source_from_content(text)
        assert content == content
        assert source == source


def test_crawler_wikiquote_en_daily():
    testcases = [
        (
            """<dd>11.  I have a dream that my four little children will one day live in a nation where they will not be judged by the color of their skin but by the content of their character. ~ <a href="/wiki/Martin_Luther_King" class="mw-redirect" title="Martin Luther King">Martin Luther King</a> <small> (This was the first "Quote of the Day" at Wikiquote, selected by <a href="/wiki/User:Nanobug" title="User:Nanobug">Nanobug</a> on <a href="/wiki/11_July" class="mw-redirect" title="11 July">11 July</a> <a href="/wiki/2003" class="mw-disambig" title="2003">2003</a>.) </small></dd>""",
            "I have a dream that my four little children will one day live in a nation where they will not be judged by the color of their skin but by the content of their character.",
            "Martin Luther King",
        ),
        (
            """<dd>20. I found one day in school a boy of medium size ill-treating a smaller boy. I expostulated, but he replied: 'The bigs hit me, so I hit the babies; that's fair.' In these words he epitomized the history of the human race. ~ <i>Education and the Social Order</i> by <a href="/wiki/Bertrand_Russell" title="Bertrand Russell">Bertrand Russell</a></dd>""",
            "I found one day in school a boy of medium size ill-treating a smaller boy. I expostulated, but he replied: 'The bigs hit me, so I hit the babies; that's fair.' In these words he epitomized the history of the human race.",
            "Education and the Social Order by Bertrand Russell",
        ),
        (
            """<li><i>Where is the Life we have lost in living? <br> Where is the wisdom we have lost in knowledge? <br> Where is the knowledge we have lost in information?</i> <br> ~ <a href="/wiki/T._S._Eliot" title="T. S. Eliot">T. S. Eliot</a> ~</li>""",
            "Where is the Life we have lost in living? \n Where is the wisdom we have lost in knowledge? \n Where is the knowledge we have lost in information?",
            "T. S. Eliot",
        ),
        (
            """<dd>15. <i>Our chiefs said 'Done,' and I did not deem it; <br> Our seers said 'Peace,' and it was not peace; <br> Earth will grow worse till men redeem it, <br> And wars more evil, ere all wars cease.</i> <br> ~ "A Song of Defeat" by <a href="/wiki/Gilbert_Keith_Chesterton" class="mw-redirect" title="Gilbert Keith Chesterton">Gilbert Keith Chesterton</a> ~</dd>""",
            "Our chiefs said 'Done,' and I did not deem it; \n Our seers said 'Peace,' and it was not peace; \n Earth will grow worse till men redeem it, \n And wars more evil, ere all wars cease.",
            '"A Song of Defeat" by Gilbert Keith Chesterton',
        ),
        (
            """
            <li><i>And, oh! what beautiful years were these<br> When our hearts clung each to each;<br>When life was filled and our senses thrilled<br> In the first faint dawn of speech.</i><p class="mw-empty-elt"></p><p><i>Thus life by life and love by love<br> We passed through the cycles strange,<br>And breath by breath and death by death<br> We followed the chain of change.</i> <br> ~ <a href="/wiki/Langdon_Smith" title="Langdon Smith">Langdon Smith</a> ~</p></li>
""",
            "And, oh! what beautiful years were these\n When our hearts clung each to each;\nWhen life was filled and our senses thrilled\n In the first faint dawn of speech.\nThus life by life and love by love\n We passed through the cycles strange,\nAnd breath by breath and death by death\n We followed the chain of change.",
            "Langdon Smith",
        ),
        (
            """<li>My life seemed to be a series of events and accidents. Yet when I look back I see a pattern.~ <a href="/wiki/Beno%C3%AEt_Mandelbrot" title="Benoît Mandelbrot">Benoît Mandelbrot</a></li>""",
            "My life seemed to be a series of events and accidents. Yet when I look back I see a pattern.",
            "Benoît Mandelbrot",
        ),
    ]

    crawler = DailyEnWikiQuoteCrawler()
    for html, content, source in testcases:
        soup = BeautifulSoup(html, "html5lib")
        element = soup.find("li")
        if not element:
            element = soup.find("dd")
        cookie = crawler.parse_item(element)
        assert cookie.content == content
        assert cookie.source == source


def test_crawler_wikiquote_fr():
    testcases = [
        (
            """<div class="citation" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">L'art d'écrire est un art très futile s'il n'implique pas avant tout l'art de voir le monde comme un potentiel de fiction.</div><ul data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><li data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><div class="ref" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><i data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">Littératures</i>&nbsp;(1980), <a href="/wiki/Vladimir_Nabokov" title="Vladimir Nabokov" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">Vladimir Nabokov</a>&nbsp;(trad. Hélène Pasquier), éd. Robert Laffont, coll.&nbsp;«&nbsp;Bouquins&nbsp;»,&nbsp;2010, partie Littératures I,&nbsp;Bons lecteurs et bons écrivains,&nbsp;p.&nbsp;36</div></li></ul>""",
            "L'art d'écrire est un art très futile s'il n'implique pas avant tout l'art de voir le monde comme un potentiel de fiction.",
            "Littératures (1980), Vladimir Nabokov (trad. Hélène Pasquier), éd. Robert Laffont, coll. « Bouquins », 2010, partie Littératures I, Bons lecteurs et bons écrivains, p. 36",
        ),
        (
            """<div class="citation" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">Lorsque la vie débarrasse de l'inessentiel par lequel elle se laisse trop souvent encombrer, elle redonne toutes ses chances à la création&nbsp;: si quelqu'un a jamais été persuadé qu'en art «&nbsp;qui perd gagne&nbsp;», c'est bien Chateaubriand.</div><ul data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">
<li data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><span class="precisions" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">Il est ici question de <a href="/wiki/Fran%C3%A7ois-Ren%C3%A9_de_Chateaubriand" title="François-René de Chateaubriand" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">Chateaubriand</a> et de son incarcération.</span></li></ul><ul data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><li data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><div class="ref" data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"> «&nbsp;Les prisons du poète&nbsp;», Philippe Berthier, <i data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">Chateaubriand — Revue Littéraire Europe</i>&nbsp;<small data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">(ISSN&nbsp;0014-2751)</small>, nº&nbsp;775-776,&nbsp;Novembre-décembre 1993, p.&nbsp;70</div></li></ul><p data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9"><br data-immersive-translate-walked="708b90e4-2325-4fa1-829c-84ae25b191a9">
</p>""",
            "Lorsque la vie débarrasse de l'inessentiel par lequel elle se laisse trop souvent encombrer, elle redonne toutes ses chances à la création : si quelqu'un a jamais été persuadé qu'en art « qui perd gagne », c'est bien Chateaubriand.",
            "« Les prisons du poète », Philippe Berthier, Chateaubriand — Revue Littéraire Europe , nº 775-776, Novembre-décembre 1993, p. 70",
        ),
    ]

    crawler = FrWikiQuoteCrawler()
    for html, content, source in testcases:
        soup = BeautifulSoup(html, "html5lib")
        element = soup.find("div")
        cookie = crawler.parse_item(element)
        assert cookie.content == content
        assert cookie.source == source


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
