# -*- coding: utf-8 -*-

from django.test import TestCase
from translations import utils


class TextSplitTest(TestCase):
    maxDiff = None

    def test_en_split(self):
        text_to_split = u"""
        Ever since MySQL replication has existed, people have dreamed of a good solution to automatically split read from write operations, sending the writes to the MySQL master and load balancing the reads over a set of MySQL slaves. While if at first it seems easy to solve, the reality is far more complex.

First, the tool needs to make sure it parses and analyses correctly all the forms of SQL MySQL supports in order to sort writes from reads, something that is not as easy as it (seems). Second, it needs to take into account if a session is in a transaction or not.

While in a transaction, the default transaction isolation level in InnoDB, Repeatable-read, and the MVCC framework insure that you’ll get a consistent view for the duration of the transaction. That means all statements executed inside a transaction must run on the master but, when the transaction commits or rollbacks, the following select statements on the session can be again load balanced to the slaves, if the session is in autocommit mode of course.

Then, what do you do with sessions that set variables? Do you restrict those sessions to the master or you replay them to the slave? If you replay the set variable commands, you need to associate the client connection to a set of MySQL backend connections, made of at least a master and a slave. What about temporary objects like with “create temporary table…”? How do you deal when a slave lags behind or what if worse, replication is broken? Those are just a few of the challenges you face when you want to build a tool to perform read/write splitting.

Over the last few years, a few products have tried to tackle the read/write split challenge. The MySQL_proxy was the first attempt I am aware of at solving this problem but it ended up with many limitations. ScaleARC does a much better job and is very usable but it stills has some limitations. The latest contender is MaxScale from MariaDB and this post is a road story..."? Of my first implementation of MaxScale for a customer.

Let me first introduce what is MaxScale exactly. MaxScale is an open source project, developed by MariaDB, that aims to be a modular proxy for MySQL. Most of the functionality in MaxScale is implemented as modules, which includes for example, modules for the MySQL protocol, client side and server side.
        """
        good_result = [u'Ever since MySQL replication has existed, people have dreamed of a good solution to automatically split read from write operations, sending the writes to the MySQL master and load balancing the reads over a set of MySQL slaves.',
                       u'While if at first it seems easy to solve, the reality is far more complex.',
                       u'First, the tool needs to make sure it parses and analyses correctly all the forms of SQL MySQL supports in order to sort writes from reads, something that is not as easy as it (seems).',
                       u'Second, it needs to take into account if a session is in a transaction or not.',
                       u'While in a transaction, the default transaction isolation level in InnoDB, Repeatable-read, and the MVCC framework insure that you\u2019ll get a consistent view for the duration of the transaction.',
                       u'That means all statements executed inside a transaction must run on the master but, when the transaction commits or rollbacks, the following select statements on the session can be again load balanced to the slaves, if the session is in autocommit mode of course.',
                       u'Then, what do you do with sessions that set variables?',
                       u'Do you restrict those sessions to the master or you replay them to the slave?',
                       u'If you replay the set variable commands, you need to associate the client connection to a set of MySQL backend connections, made of at least a master and a slave.',
                       u'What about temporary objects like with \u201ccreate temporary table\u2026\u201d?',
                       u'How do you deal when a slave lags behind or what if worse, replication is broken?',
                       u'Those are just a few of the challenges you face when you want to build a tool to perform read/write splitting.',
                       u'Over the last few years, a few products have tried to tackle the read/write split challenge.',
                       u'The MySQL_proxy was the first attempt I am aware of at solving this problem but it ended up with many limitations.',
                       u'ScaleARC does a much better job and is very usable but it stills has some limitations.',
                       u'The latest contender is MaxScale from MariaDB and this post is a road story..."?',
                       u'Of my first implementation of MaxScale for a customer.',
                       u'Let me first introduce what is MaxScale exactly.',
                       u'MaxScale is an open source project, developed by MariaDB, that aims to be a modular proxy for MySQL.',
                       u'Most of the functionality in MaxScale is implemented as modules, which includes for example, modules for the MySQL protocol, client side and server side.',]
        sentences, marked_text = utils.split_text(text_to_split, 'en')
        self.assertEqual(sentences, good_result)

    def test_fr_split(self):
        text_to_split = u"""
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
        good_result = [u'Ce virus est-il contagieux?',
                       u'Le MERS-CoV est contagieux.',
                       u"Cependant, indique l'OMS, \xable virus ne semble pas passer facilement d'une personne \xe0 une autre \xe0 moins qu'il y ait un contact proche, comme cela se produit lorsqu'on d\xe9livre des soins \xe0 un patient sans porter de protections\xbb.",
                       u"Contrairement au SARS-CoV pour lequel existait une transmission a\xe9roport\xe9e (lors d'\xe9ternuements ou de toux), le MERS-CoV n\xe9cessite une grande proximit\xe9.",
                       u"Le mode de transmission de l'animal \u2013 du chameau \u2013 \xe0 l'homme n'est pas totalement \xe9lucid\xe9.",
                       u"Les soins sans protection efficace ou avec de mauvaises pratiques ont fr\xe9quemment \xe9t\xe9 \xe0 l'origine d'une transmission interhumaine, avec des cas group\xe9s dans des \xe9tablissements de soins.",
                       u"En revanche, il n'y a pas eu une profusion de transmissions entre des individus au sein de la population g\xe9n\xe9rale.",
                       u'Cela explique que le nombre de cas depuis 2012 soit rest\xe9 limit\xe9.',
                       u"Existe-t-il des moyens de pr\xe9vention de l'infection?",
                       u"Les mesures d'hygi\xe8ne classiques (lavage des mains) sont importantes pour les personnes se rendant dans les pays touch\xe9s du Moyen-Orient, en particulier en cas de contact avec des animaux.",
                       u"L'OMS recommande d'y \xe9viter la consommation de viande crue ou peu cuite ou de lait de chamelle non pasteuris\xe9 ou chauff\xe9.",
                       u"Les personnes souffrantes de diab\xe8te, d'insuffisance r\xe9nale, de pathologie pulmonaire chronique ou immunod\xe9prim\xe9es semblent expos\xe9es \xe0 un risque \xe9lev\xe9 d'atteinte s\xe9v\xe8re en cas d'infection par le MERS-CoV.",
                       u'Existe-t-il un traitement?',
                       u"Il n'y a aucun traitement contre ce virus pour l'instant.",
                       u'La prise en charge consiste en des soins de supports et une r\xe9animation en milieu sp\xe9cialis\xe9.',
                       u"En utilisant des singes comme mod\xe8le de l'infection, des chercheurs am\xe9ricains ont pour l'instant d\xe9montr\xe9, sur des cultures de cellules, la capacit\xe9 de deux antiviraux: la ribavirine et l'interf\xe9ron-alpha 2b.",
                       u"Ils pourraient emp\xeacher le virus de se reproduire, mais la d\xe9monstration reste \xe0 faire chez l'homme.",
                       u'Peut-on voyager vers les pays o\xf9 les premiers cas ont \xe9t\xe9 recens\xe9s?',
                       u"L'OMS et les autorit\xe9s nationales n'ont pas \xe9mis de restrictions aux voyages vers l'Arabie saoudite et les autres pays de la p\xe9ninsule Arabique ou vers la Jordanie, ni m\xeame de restrictions commerciales.",]
        sentences, marked_text = utils.split_text(text_to_split, 'fr')
        self.assertEqual(sentences, good_result)

    def test_ru_split(self):
        text_to_split = u"""
        Существует несколько историографических названий государства, преобладавших в литературе в разное время — «Древнерусское государство», «Древняя Русь», «Киевская Русь», «Киевское государство».

Определение «древнерусский» не связано с общепринятым в историографии делением древности и Средневековья в западной и центральной Европе, в соответствии с которым древность заканчивается к середине I тыс. н.э. с угасанием традиционной античной культуры. Применительно к Руси под древностью обычно понимается так называемый домонгольский период IX — середины XIII веков, чтобы отличить эту эпоху от последующих этапов русской истории.

Термин «Киевская Русь» возник в первой половине XIX века, пройдя за историю своего употребления существенную эволюцию. Одним из первых его использовал М. А. Максимович в своей работе «Откуда идёт русская земля» (1837) в узко географическом смысле для обозначения Киевского княжества, в одном ряду с такими словосочетаниями как «Червоная Русь», «Суздальская Русь» и др. В таком же значении термин употребляли С. М. Соловьёв («Русь Киевская», «Русь Черниговская», «Русь Ростовская или Суздальская»), Н. И. Костомаров и Д. И. Иловайский. Во второй половине XIX века термин приобрёл дополнительное, хронологическое измерение — одной из стадий русской истории и государственности. В этом случае киевский период обычно заканчивали 1169 годом, что было связано с бытовавшим в дореволюционной историографии представлением о переносе столицы Руси из Киева во Владимир. В. О. Ключевский использовал этот термин несистематически, иногда сочетая узкогеографические и хронологические рамки и отличая «старую Киевскую Русь» от «Руси новой, верхневолжской», иногда подразумевая под ним все земли Руси в соответствующий период. У С. Ф. Платонова, А. Е. Преснякова и других авторов начала XX века термин стал использоваться в государственно-политическом смысле как именование государства всех восточных славян в эпоху, когда Киев был общим политическим центром. В украинской националистической историографии того же времени уточняющий термин «Киевская Русь» не был особо популярным, поскольку подразумевал существование других форм или проявлений Руси (будь то в географическом или хронологическом смысле). Основоположник украинской исторической школы М. С. Грушевский им почти не пользовался, предпочитая термины «Киевское государство» или «Руська держава» («Русское государство», противопоставленное в его версии государству Московскому).
        """
        good_result = [u"Существует несколько историографических названий государства, преобладавших в литературе в разное время — «Древнерусское государство», «Древняя Русь», «Киевская Русь», «Киевское государство».",
                       u"Определение «древнерусский» не связано с общепринятым в историографии делением древности и Средневековья в западной и центральной Европе, в соответствии с которым древность заканчивается к середине I тыс. н.э. с угасанием традиционной античной культуры.",
                       u"Применительно к Руси под древностью обычно понимается так называемый домонгольский период IX — середины XIII веков, чтобы отличить эту эпоху от последующих этапов русской истории.",
                       u"Термин «Киевская Русь» возник в первой половине XIX века, пройдя за историю своего употребления существенную эволюцию.",
                       u"Одним из первых его использовал М. А. Максимович в своей работе «Откуда идёт русская земля» (1837) в узко географическом смысле для обозначения Киевского княжества, в одном ряду с такими словосочетаниями как «Червоная Русь», «Суздальская Русь» и др.",
                       u"В таком же значении термин употребляли С. М. Соловьёв («Русь Киевская», «Русь Черниговская», «Русь Ростовская или Суздальская»), Н. И. Костомаров и Д. И. Иловайский.",
                       u"Во второй половине XIX века термин приобрёл дополнительное, хронологическое измерение — одной из стадий русской истории и государственности.",
                       u"В этом случае киевский период обычно заканчивали 1169 годом, что было связано с бытовавшим в дореволюционной историографии представлением о переносе столицы Руси из Киева во Владимир.",
                       u"В. О. Ключевский использовал этот термин несистематически, иногда сочетая узкогеографические и хронологические рамки и отличая «старую Киевскую Русь» от «Руси новой, верхневолжской», иногда подразумевая под ним все земли Руси в соответствующий период.",
                       u"У С. Ф. Платонова, А. Е. Преснякова и других авторов начала XX века термин стал использоваться в государственно-политическом смысле как именование государства всех восточных славян в эпоху, когда Киев был общим политическим центром.",
                       u"В украинской националистической историографии того же времени уточняющий термин «Киевская Русь» не был особо популярным, поскольку подразумевал существование других форм или проявлений Руси (будь то в географическом или хронологическом смысле).",
                       u"Основоположник украинской исторической школы М. С. Грушевский им почти не пользовался, предпочитая термины «Киевское государство» или «Руська держава» («Русское государство», противопоставленное в его версии государству Московскому).",]
        sentences, marked_text = utils.split_text(text_to_split, 'ru')
        self.assertEqual(sentences, good_result)
