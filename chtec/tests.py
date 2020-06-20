# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
import unittest
from chtec_lib import utils


def print_results(sentences):
    for sent in sentences:
        print("u\"" + sent + "\",")


class TextSplitTest(unittest.TestCase):
    maxDiff = None

    def test_en_split(self):
        text_to_split = """
        Ever since MySQL replication has existed, people have dreamed of a good solution to automatically split read from write operations, sending the writes to the MySQL master and load balancing the reads over a set of MySQL slaves. While if at first it seems easy to solve, the reality is far more complex.

First, the tool needs to make sure it parses and analyses correctly all the forms of SQL MySQL supports in order to sort writes from reads, something that is not as easy as it (seems). Second, it needs to take into account if a session is in a transaction or not.

While in a transaction, the default transaction isolation level in InnoDB, Repeatable-read, and the MVCC framework insure that you’ll get a consistent view for the duration of the transaction. That means all statements executed inside a transaction must run on the master but, when the transaction commits or rollbacks, the following select statements on the session can be again load balanced to the slaves, if the session is in autocommit mode of course.

Then, what do you do with sessions that set variables? Do you restrict those sessions to the master or you replay them to the slave? If you replay the set variable commands, you need to associate the client connection to a set of MySQL backend connections, made of at least a master and a slave. What about temporary objects like with “create temporary table…”? How do you deal when a slave lags behind or what if worse, replication is broken? Those are just a few of the challenges you face when you want to build a tool to perform read/write splitting.

Over the last few years, a few products have tried to tackle the read/write split challenge. The MySQL_proxy was the first attempt I am aware of at solving this problem but it ended up with many limitations. ScaleARC does a much better job and is very usable but it stills has some limitations. The latest contender is MaxScale from MariaDB and this post is a road story..."? Of my first implementation of MaxScale for a customer.

Let me first introduce what is MaxScale exactly. MaxScale is an open source project, developed by MariaDB, that aims to be a modular proxy for MySQL. Most of the functionality in MaxScale is implemented as modules, which includes for example, modules for the MySQL protocol, client side and server side.
        """
        good_result = ['Ever since MySQL replication has existed, people have dreamed of a good solution to automatically split read from write operations, sending the writes to the MySQL master and load balancing the reads over a set of MySQL slaves.',
                       'While if at first it seems easy to solve, the reality is far more complex.',
                       'First, the tool needs to make sure it parses and analyses correctly all the forms of SQL MySQL supports in order to sort writes from reads, something that is not as easy as it (seems).',
                       'Second, it needs to take into account if a session is in a transaction or not.',
                       'While in a transaction, the default transaction isolation level in InnoDB, Repeatable-read, and the MVCC framework insure that you\u2019ll get a consistent view for the duration of the transaction.',
                       'That means all statements executed inside a transaction must run on the master but, when the transaction commits or rollbacks, the following select statements on the session can be again load balanced to the slaves, if the session is in autocommit mode of course.',
                       'Then, what do you do with sessions that set variables?',
                       'Do you restrict those sessions to the master or you replay them to the slave?',
                       'If you replay the set variable commands, you need to associate the client connection to a set of MySQL backend connections, made of at least a master and a slave.',
                       'What about temporary objects like with \u201ccreate temporary table\u2026\u201d?',
                       'How do you deal when a slave lags behind or what if worse, replication is broken?',
                       'Those are just a few of the challenges you face when you want to build a tool to perform read/write splitting.',
                       'Over the last few years, a few products have tried to tackle the read/write split challenge.',
                       'The MySQL_proxy was the first attempt I am aware of at solving this problem but it ended up with many limitations.',
                       'ScaleARC does a much better job and is very usable but it stills has some limitations.',
                       'The latest contender is MaxScale from MariaDB and this post is a road story..."?',
                       'Of my first implementation of MaxScale for a customer.',
                       'Let me first introduce what is MaxScale exactly.',
                       'MaxScale is an open source project, developed by MariaDB, that aims to be a modular proxy for MySQL.',
                       'Most of the functionality in MaxScale is implemented as modules, which includes for example, modules for the MySQL protocol, client side and server side.',]
        sentences, marked_text, count_num = utils.split_text(text_to_split, 'en')
        self.assertEqual(sentences, good_result)

    def test_fr_split(self):
        text_to_split = """
        Ce virus est-il contagieux?
Le MERS-CoV est contagieux. Cependant, indique l'OMS, «le virus ne semble pas passer facilement d'une personne à une autre à moins qu'il y ait un contact proche, comme cela se produit lorsqu'on délivre des soins à un patient sans porter de protections». Contrairement au SARS-CoV pour lequel existait une transmission aéroportée (lors d'éternuements ou de toux), le MERS-CoV nécessite une grande proximité.
Le mode de transmission de l'animal – du chameau – à l'homme n'est pas totalement élucidé. Les soins sans protection efficace ou avec de mauvaises pratiques ont fréquemment été à l'origine d'une transmission interhumaine, avec des cas groupés dans des établissements de soins. En revanche, il n'y a pas eu une profusion de transmissions entre des individus au sein de la population générale. Cela explique que le nombre de cas depuis 2012 soit resté limité.
Existe-t-il des moyens de prévention de l'infection?
Les mesures d'hygiène classiques (lavage des mains) sont importantes pour les personnes se rendant dans les pays touchés du Moyen-Orient, en particulier en cas de contact avec des animaux. L'OMS recommande d'y éviter la consommation de viande crue ou peu cuite ou de lait de chamelle non pasteurisé ou chauffé. Les personnes souffrantes de diabète, d'insuffisance rénale, de pathologie pulmonaire chronique ou immunodéprimées semblent exposées à un risque élevé d'atteinte sévère en cas d'infection par le MERS-CoV.
Existe-t-il un traitement?
Il n'y a aucun traitement contre ce virus pour l'instant. La prise en charge consiste en des soins de supports et une réanimation en milieu spécialisé. En utilisant des singes comme modèle de l'infection, des chercheurs américains ont pour l'instant démontré, sur des cultures de cellules, la capacité de deux antiviraux: la ribavirine et l'interféron-alpha 2b. Ils pourraient empêcher le virus de se reproduire, mais la démonstration reste à faire chez l'homme.
Peut-on voyager vers les pays où les premiers cas ont été recensés?
L'OMS et les autorités nationales n'ont pas émis de restrictions aux voyages vers l'Arabie saoudite et les autres pays de la péninsule Arabique ou vers la Jordanie, ni même de restrictions commerciales.
        """
        good_result = ['Ce virus est-il contagieux?',
                       'Le MERS-CoV est contagieux.',
                       "Cependant, indique l'OMS, \xable virus ne semble pas passer facilement d'une personne \xe0 une autre \xe0 moins qu'il y ait un contact proche, comme cela se produit lorsqu'on d\xe9livre des soins \xe0 un patient sans porter de protections\xbb.",
                       "Contrairement au SARS-CoV pour lequel existait une transmission a\xe9roport\xe9e (lors d'\xe9ternuements ou de toux), le MERS-CoV n\xe9cessite une grande proximit\xe9.",
                       "Le mode de transmission de l'animal \u2013 du chameau \u2013 \xe0 l'homme n'est pas totalement \xe9lucid\xe9.",
                       "Les soins sans protection efficace ou avec de mauvaises pratiques ont fr\xe9quemment \xe9t\xe9 \xe0 l'origine d'une transmission interhumaine, avec des cas group\xe9s dans des \xe9tablissements de soins.",
                       "En revanche, il n'y a pas eu une profusion de transmissions entre des individus au sein de la population g\xe9n\xe9rale.",
                       'Cela explique que le nombre de cas depuis 2012 soit rest\xe9 limit\xe9.',
                       "Existe-t-il des moyens de pr\xe9vention de l'infection?",
                       "Les mesures d'hygi\xe8ne classiques (lavage des mains) sont importantes pour les personnes se rendant dans les pays touch\xe9s du Moyen-Orient, en particulier en cas de contact avec des animaux.",
                       "L'OMS recommande d'y \xe9viter la consommation de viande crue ou peu cuite ou de lait de chamelle non pasteuris\xe9 ou chauff\xe9.",
                       "Les personnes souffrantes de diab\xe8te, d'insuffisance r\xe9nale, de pathologie pulmonaire chronique ou immunod\xe9prim\xe9es semblent expos\xe9es \xe0 un risque \xe9lev\xe9 d'atteinte s\xe9v\xe8re en cas d'infection par le MERS-CoV.",
                       'Existe-t-il un traitement?',
                       "Il n'y a aucun traitement contre ce virus pour l'instant.",
                       'La prise en charge consiste en des soins de supports et une r\xe9animation en milieu sp\xe9cialis\xe9.',
                       "En utilisant des singes comme mod\xe8le de l'infection, des chercheurs am\xe9ricains ont pour l'instant d\xe9montr\xe9, sur des cultures de cellules, la capacit\xe9 de deux antiviraux: la ribavirine et l'interf\xe9ron-alpha 2b.",
                       "Ils pourraient emp\xeacher le virus de se reproduire, mais la d\xe9monstration reste \xe0 faire chez l'homme.",
                       'Peut-on voyager vers les pays o\xf9 les premiers cas ont \xe9t\xe9 recens\xe9s?',
                       "L'OMS et les autorit\xe9s nationales n'ont pas \xe9mis de restrictions aux voyages vers l'Arabie saoudite et les autres pays de la p\xe9ninsule Arabique ou vers la Jordanie, ni m\xeame de restrictions commerciales.",]
        sentences, marked_text, count_num = utils.split_text(text_to_split, 'fr')
        self.assertEqual(sentences, good_result)

    def test_ru_split(self):
        text_to_split = """
        Существует несколько историографических названий государства, преобладавших в литературе в разное время — «Древнерусское государство», «Древняя Русь», «Киевская Русь», «Киевское государство».

Определение «древнерусский» не связано с общепринятым в историографии делением древности и Средневековья в западной и центральной Европе, в соответствии с которым древность заканчивается к середине I тыс. н.э. с угасанием традиционной античной культуры. Применительно к Руси под древностью обычно понимается так называемый домонгольский период IX — середины XIII веков, чтобы отличить эту эпоху от последующих этапов русской истории.

Термин «Киевская Русь» возник в первой половине XIX века, пройдя за историю своего употребления существенную эволюцию. Во второй половине XIX века термин приобрёл дополнительное, хронологическое измерение — одной из стадий русской истории и государственности. В этом случае киевский период обычно заканчивали 1169 годом, что было связано с бытовавшим в дореволюционной историографии представлением о переносе столицы Руси из Киева во Владимир. В украинской националистической историографии того же времени уточняющий термин «Киевская Русь» не был особо популярным, поскольку подразумевал существование других форм или проявлений Руси (будь то в географическом или хронологическом смысле).
        """
        good_result = ["Существует несколько историографических названий государства, преобладавших в литературе в разное время — «Древнерусское государство», «Древняя Русь», «Киевская Русь», «Киевское государство».",
                       "Определение «древнерусский» не связано с общепринятым в историографии делением древности и Средневековья в западной и центральной Европе, в соответствии с которым древность заканчивается к середине I тыс. н.э. с угасанием традиционной античной культуры.",
                       "Применительно к Руси под древностью обычно понимается так называемый домонгольский период IX — середины XIII веков, чтобы отличить эту эпоху от последующих этапов русской истории.",
                       "Термин «Киевская Русь» возник в первой половине XIX века, пройдя за историю своего употребления существенную эволюцию.",
                       # "Одним из первых его использовал М. А. Максимович в своей работе «Откуда идёт русская земля» (1837) в узко географическом смысле для обозначения Киевского княжества, в одном ряду с такими словосочетаниями как «Червоная Русь», «Суздальская Русь» и др.",
                       # "В таком же значении термин употребляли С. М. Соловьёв («Русь Киевская», «Русь Черниговская», «Русь Ростовская или Суздальская»), Н. И. Костомаров и Д. И. Иловайский.",
                       "Во второй половине XIX века термин приобрёл дополнительное, хронологическое измерение — одной из стадий русской истории и государственности.",
                       "В этом случае киевский период обычно заканчивали 1169 годом, что было связано с бытовавшим в дореволюционной историографии представлением о переносе столицы Руси из Киева во Владимир.",
                       # "В. О. Ключевский использовал этот термин несистематически, иногда сочетая узкогеографические и хронологические рамки и отличая «старую Киевскую Русь» от «Руси новой, верхневолжской», иногда подразумевая под ним все земли Руси в соответствующий период.",
                       # "У С. Ф. Платонова, А. Е. Преснякова и других авторов начала XX века термин стал использоваться в государственно-политическом смысле как именование государства всех восточных славян в эпоху, когда Киев был общим политическим центром.",
                       "В украинской националистической историографии того же времени уточняющий термин «Киевская Русь» не был особо популярным, поскольку подразумевал существование других форм или проявлений Руси (будь то в географическом или хронологическом смысле).",
                       # "Основоположник украинской исторической школы М. С. Грушевский им почти не пользовался, предпочитая термины «Киевское государство» или «Руська держава» («Русское государство», противопоставленное в его версии государству Московскому).",
                       ]
        sentences, marked_text, count_num = utils.split_text(text_to_split, 'ru')
        self.assertEqual(sentences, good_result)

    def test_zh_split(self):
        text_to_split = """
        “你们来这里拍电影？”赵红旗问。“这里有什么好拍的？”

“这个电影是写生活在煤矿的几个初中生的故事。”我说。

“什么样的故事？”

“土匪老妈还差不多。”老板娘笑着回敬了一句，抓了把瓜子，到外面跟厨师聊天去了。

我们吃完饭出来，天黑得透透的，星星像是从很远的地方射过来的长矛，穿透黑夜的帷幕，露出点点银亮的矛尖。镇子很静，在酒桌上听了那些故事以后，这种静谧变得阴险和杀机重重了。

小莫家的旅馆是一栋两层小楼，一共八个房间，厕所是公用的，没有洗澡间。惟一一间带浴室的房间，是小莫自己用的，他带我们去看他的浴盆，他介绍那两条金龙鱼的样子就好像它们是他的儿子。

第二天一早起来，夏末秋初的季节，洗脸的水居然冰手。洗过脸后，神清气爽，我们散步走过两条街，去昨天吃过饭的饭店？!街上不少骑自行车上班的人，铃声嘀铃铃响，树上还有雾气没有褪尽，像丝丝缕缕的白絮。空气又凉又湿，有重量似的。

赵红旗和张景乾先到了，餐桌上面摆着煮鸡蛋，馒头，葱油饼，小米粥，几个凉菜都是大盘的，老板娘跟我们打了声招呼就进了厨房，接着听到里面一阵声响，她又端出四盘热菜来。

“弄得太隆重了，”我说，“平时我们都不吃早餐的。”

“也没什么好吃的，你们将就将就，”赵红旗说，“晚上我看看能不能弄个野狍子，烤着吃吃。”

“千万别，”我们几个直摆手，连说好几遍，务必让赵红旗相信我们是认真的，不是跟他客气。

“那吃蛤蟆吧，现在的蛤蟆最肥？!”赵红旗问小莫，“哎对了，老吴不是会捉蛇吗？让他捉两条来。”

“千万别千万别。”我们又开始猛摆手。

“我最怕蛇了。”我说。

“切成段炖熟了，你根本看不出是什么玩意儿。”小莫说，“女孩儿吃毒蛇还美容呢，脸上不长疙瘩。”

“我宁可长疙瘩。”我说。

周为和方磊也坚决反对吃蛇，“从现在开始除了绿叶儿的东西其他的我们都不吃了。”

张景乾让我们逗笑了，对赵红旗说，“给他们弄点儿新鲜榛蘑炖老母鸡。”

吃完了饭，张景乾去上班，赵红旗开车，带着小莫跟我们去山上。公路像层层捆缚山的绳索，我们像砣螺似的转了一圈儿又一圈儿，往下面看时，松树镇变成了一个漏斗的底坐。又开了一会儿，一些小煤窑开始出现在我们眼前，规模不大，大部分是斜井，往外运煤的小火车车厢，跟棺材差不多大小，开动的时候晃里晃当地响。工人们每天坐着这些小火车进掌子面工作，下班再坐这小火车出来。

赵红旗和小莫谁都认识，方磊和周为拿着摄像机取景的时候，他们跟煤窑主，或者主管聊天。

他们无一例外地问我们是干什么的。赵红旗说我们是拍电影的，他们的回答全都一样，“这地方有什么好拍的？!”

“是煤矿里一些中学生的故事。”赵红旗说。

他们很快谈起真正关心的事情，贮藏量怎么样？煤质如何？找到买家没有？今年冬天的煤价是涨还是降？他们都为钱焦虑，工人的工资拖欠得太久了，再不赶紧把煤发走弄回钱来，不知道哪天刨煤的大镐头就刨到他们的脑袋上了。
        """
        good_result = ["“你们来这里拍电影？”",
                       "赵红旗问。",
                       "“这里有什么好拍的？”",
                       "“这个电影是写生活在煤矿的几个初中生的故事。”",
                       "我说。",
                       "“什么样的故事？”",
                       "“土匪老妈还差不多。”",
                       "老板娘笑着回敬了一句，抓了把瓜子，到外面跟厨师聊天去了。",
                       "我们吃完饭出来，天黑得透透的，星星像是从很远的地方射过来的长矛，穿透黑夜的帷幕，露出点点银亮的矛尖。",
                       "镇子很静，在酒桌上听了那些故事以后，这种静谧变得阴险和杀机重重了。",
                       "小莫家的旅馆是一栋两层小楼，一共八个房间，厕所是公用的，没有洗澡间。",
                       "惟一一间带浴室的房间，是小莫自己用的，他带我们去看他的浴盆，他介绍那两条金龙鱼的样子就好像它们是他的儿子。",
                       "第二天一早起来，夏末秋初的季节，洗脸的水居然冰手。",
                       "洗过脸后，神清气爽，我们散步走过两条街，去昨天吃过饭的饭店？!",
                       "街上不少骑自行车上班的人，铃声嘀铃铃响，树上还有雾气没有褪尽，像丝丝缕缕的白絮。",
                       "空气又凉又湿，有重量似的。",
                       "赵红旗和张景乾先到了，餐桌上面摆着煮鸡蛋，馒头，葱油饼，小米粥，几个凉菜都是大盘的，老板娘跟我们打了声招呼就进了厨房，接着听到里面一阵声响，她又端出四盘热菜来。",
                       "“弄得太隆重了，”我说，“平时我们都不吃早餐的。”",
                       "“也没什么好吃的，你们将就将就，”赵红旗说，“晚上我看看能不能弄个野狍子，烤着吃吃。”",
                       "“千万别，”我们几个直摆手，连说好几遍，务必让赵红旗相信我们是认真的，不是跟他客气。",
                       "“那吃蛤蟆吧，现在的蛤蟆最肥？!”",
                       "赵红旗问小莫，“哎对了，老吴不是会捉蛇吗？",
                       "让他捉两条来。”",
                       "“千万别千万别。”",
                       "我们又开始猛摆手。",
                       "“我最怕蛇了。”",
                       "我说。",
                       "“切成段炖熟了，你根本看不出是什么玩意儿。”",
                       "小莫说，“女孩儿吃毒蛇还美容呢，脸上不长疙瘩。”",
                       "“我宁可长疙瘩。”",
                       "我说。",
                       "周为和方磊也坚决反对吃蛇，“从现在开始除了绿叶儿的东西其他的我们都不吃了。”",
                       "张景乾让我们逗笑了，对赵红旗说，“给他们弄点儿新鲜榛蘑炖老母鸡。”",
                       "吃完了饭，张景乾去上班，赵红旗开车，带着小莫跟我们去山上。",
                       "公路像层层捆缚山的绳索，我们像砣螺似的转了一圈儿又一圈儿，往下面看时，松树镇变成了一个漏斗的底坐。",
                       "又开了一会儿，一些小煤窑开始出现在我们眼前，规模不大，大部分是斜井，往外运煤的小火车车厢，跟棺材差不多大小，开动的时候晃里晃当地响。",
                       "工人们每天坐着这些小火车进掌子面工作，下班再坐这小火车出来。",
                       "赵红旗和小莫谁都认识，方磊和周为拿着摄像机取景的时候，他们跟煤窑主，或者主管聊天。",
                       "他们无一例外地问我们是干什么的。",
                       "赵红旗说我们是拍电影的，他们的回答全都一样，“这地方有什么好拍的？!”",
                       "“是煤矿里一些中学生的故事。”",
                       "赵红旗说。",
                       "他们很快谈起真正关心的事情，贮藏量怎么样？",
                       "煤质如何？",
                       "找到买家没有？",
                       "今年冬天的煤价是涨还是降？",
                       "他们都为钱焦虑，工人的工资拖欠得太久了，再不赶紧把煤发走弄回钱来，不知道哪天刨煤的大镐头就刨到他们的脑袋上了。",]
        sentences, marked_text, count_num = utils.split_text(text_to_split, 'zh')
        self.assertEqual(sentences, good_result)

    def test_es_split(self):
        text_to_split = """
        Al cabo de un tiempo la princesa, que estaba deseando tener inteligencia, dijo a Riquete el del Copete que se comprometía a casarse con él dentro de un año.

Desde ese mismo instante algo cambió en la princesa. Podía expresarse fácilmente y lo hacía con gran corrección y exquisitos modales. Cuando volvió al palacio todo el mundo quedó maravillado ante el cambio tan extraordinario que había experimentado y no tardaron en llegar príncipes de reinos vecinos que buscaban conquistar su corazón.

Llegó uno rico y apuesto y aunque le gustó desde el primer momento decidió ir a pensar al bosque. Allí se encontró con un grupo numeroso de cocineros que preparaban un gran banquete.

Pero cuando preguntó para quien trabajaban le respondieron que para la boda del príncipe Riquete el del Copete que se celebraba al día siguiente. ¡La princesa lo había olvidado por completo al volverse inteligente y olvidar todas sus tonterías!

En ese momento el príncipe Riquete el del Copete apareció por allí.

- Disculpadme pero creo que no voy a poder corresponderos como vos esperáis.
- ¿Por qué? ¿Qué ha ocurrido? ¿Hay algo en mi que no sea mi fealdad y no os guste?
- No no lo hay. Sois un hombre inteligente, bueno y educado
- Entonces está en vuestra mano convertirme en el hombre más bello de entre todos los hombres.
- ¿En mi mano? - dijo la princesa sorprendida
- La misma hada que me concedió el don de hacer inteligente a quien amase os concedió a vos al nacer el don de hacer hermosa a la persona a quien amáseis.
- Nada me gustaría más. Deseo con todo mi corazón que os convirtáis en el príncipe más hermoso y agradable del mundo.

Y en cuanto la princesa pronunció estas palabras Riquete el del Copete se convirtió en el hombre mejor plantado y más agradable que jamás había conocido.

Hay quien dice que nada tuvo que ver el hada y que todo fue fruto del amor de la princesa, que fue capaz de hacerle ver todas las cualidades buenas de su amante por encima de la fealdad de su rostro y de su cuerpo.
        """
        good_result = ["Al cabo de un tiempo la princesa, que estaba deseando tener inteligencia, dijo a Riquete el del Copete que se comprometía a casarse con él dentro de un año.",
                       "Desde ese mismo instante algo cambió en la princesa.",
                       "Podía expresarse fácilmente y lo hacía con gran corrección y exquisitos modales.",
                       "Cuando volvió al palacio todo el mundo quedó maravillado ante el cambio tan extraordinario que había experimentado y no tardaron en llegar príncipes de reinos vecinos que buscaban conquistar su corazón.",
                       "Llegó uno rico y apuesto y aunque le gustó desde el primer momento decidió ir a pensar al bosque.",
                       "Allí se encontró con un grupo numeroso de cocineros que preparaban un gran banquete.",
                       "Pero cuando preguntó para quien trabajaban le respondieron que para la boda del príncipe Riquete el del Copete que se celebraba al día siguiente.",
                       "¡La princesa lo había olvidado por completo al volverse inteligente y olvidar todas sus tonterías!",
                       "En ese momento el príncipe Riquete el del Copete apareció por allí.",
                       "- Disculpadme pero creo que no voy a poder corresponderos como vos esperáis.",
                       "- ¿Por qué?",
                       "¿Qué ha ocurrido?",
                       "¿Hay algo en mi que no sea mi fealdad y no os guste?",
                       "- No no lo hay.",
                       "Sois un hombre inteligente, bueno y educado",
                       "- Entonces está en vuestra mano convertirme en el hombre más bello de entre todos los hombres.",
                       "- ¿En mi mano?",
                       "- dijo la princesa sorprendida",
                       "- La misma hada que me concedió el don de hacer inteligente a quien amase os concedió a vos al nacer el don de hacer hermosa a la persona a quien amáseis.",
                       "- Nada me gustaría más.",
                       "Deseo con todo mi corazón que os convirtáis en el príncipe más hermoso y agradable del mundo.",
                       "Y en cuanto la princesa pronunció estas palabras Riquete el del Copete se convirtió en el hombre mejor plantado y más agradable que jamás había conocido.",
                       "Hay quien dice que nada tuvo que ver el hada y que todo fue fruto del amor de la princesa, que fue capaz de hacerle ver todas las cualidades buenas de su amante por encima de la fealdad de su rostro y de su cuerpo.",]
        sentences, marked_text, count_num = utils.split_text(text_to_split, 'es')
        # print_results(sentences)
        self.assertEqual(sentences, good_result)

if __name__ == '__main__':
    unittest.main()
