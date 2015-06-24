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