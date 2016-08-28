from __future__ import print_function, unicode_literals

from redis_collections.sortedsets import SortedSetCounter

from .base import RedisTestCase


class SortedSetCounterTestCase(RedisTestCase):

    def create_sortedset(self, *args, **kwargs):
        kwargs['redis'] = self.redis
        return SortedSetCounter(*args, **kwargs)

    def test_init(self):
        self.assertEqual(self.create_sortedset().items(), [])

        items = [('0', 1.0), ('1', 2.0)]
        self.assertEqual(self.create_sortedset(items).items(), items)

        data = {'0': 1.0, '1': 2.0}
        self.assertEqual(self.create_sortedset(data).items(), items)

    def test_repr(self):
        ssc = self.create_sortedset([('zero', 0.0), ('one', 1.0)])
        repr_ssc = repr(ssc)
        self.assertIn("'zero': 0.0", repr_ssc)
        self.assertIn("'one': 1.0", repr_ssc)

    def test_contains(self):
        ssc = self.create_sortedset()

        ssc.set_score('member_1', 1)
        self.assertIn('member_1', ssc)

        self.assertNotIn('member_2', ssc)

        ssc.discard_member('member_1')
        self.assertNotIn('member_1', ssc)

        # Unlike a Python dict or collections.Counter instance,
        # SortedSetCounter does not refuse to store numeric types like
        # 1, 1.0, complex(1, 0) in the same collection
        ssc.set_score(1, 100)
        self.assertNotIn(1.0, ssc)

        ssc.set_score(1.0, 1000)
        self.assertIn(1.0, ssc)

    def test_iter(self):
        items = [('0', 1.0), ('1', 2.0)]
        ssc = self.create_sortedset(items)

        self.assertEqual(tuple(ssc.__iter__()), tuple(items))

    def test_len(self):
        ssc = self.create_sortedset()

        self.assertEqual(len(ssc), 0)

        ssc.set_score('member_1', 1)
        self.assertEqual(len(ssc), 1)

        ssc.set_score('member_2', 2.0)
        self.assertEqual(len(ssc), 2)

        ssc.discard_member('member_1')
        self.assertEqual(len(ssc), 1)

    def test_clear(self):
        ssc = self.create_sortedset([('0', 1.0), ('1', 2.0)])
        self.assertEqual(ssc.items(), [('0', 1.0), ('1', 2.0)])

        ssc.clear()
        self.assertEqual(ssc.items(), [])

    def test_copy(self):
        items = [('0', 1.0), ('1', 2.0)]
        ssc_1 = self.create_sortedset(items)

        ssc_2 = ssc_1.copy()
        self.assertEqual(ssc_2.items(), items)
        self.assertTrue(ssc_1.redis, ssc_2.redis)

    def test_count_between(self):
        items = [('0', 1.0), ('1', 2.0), ('2', 4.0), ('3', 8.0)]
        ssc = self.create_sortedset(items)

        self.assertEqual(ssc.count_between(), 4)
        self.assertEqual(ssc.count_between(2.0), 3)
        self.assertEqual(ssc.count_between(2.0, 4.0), 2)
        self.assertEqual(ssc.count_between(4.0), 2)
        self.assertEqual(ssc.count_between(8.0), 1)
        self.assertEqual(ssc.count_between(0.0, 0.9), 0)
        self.assertEqual(ssc.count_between(8.1), 0)
        self.assertEqual(ssc.count_between(4.0, 2.0), 0)

    def test_discard_between(self):
        items = [
            ('0', 1), ('1', 2), ('2', 4), ('3', 8), ('4', 16), ('5', 32)
        ]

        ssc_1 = self.create_sortedset(items)
        ssc_1.discard_between(min_rank=1)
        self.assertEqual(ssc_1.items(), items[:1])

        ssc_2 = self.create_sortedset(items)
        ssc_2.discard_between(min_rank=1, max_rank=-2)
        self.assertEqual(ssc_2.items(), [items[0], items[5]])

        ssc_3 = self.create_sortedset(items)
        ssc_3.discard_between(max_rank=-2)
        self.assertEqual(ssc_3.items(), items[5:])

        ssc_4 = self.create_sortedset(items)
        ssc_4.discard_between(min_score=2)
        self.assertEqual(ssc_4.items(), items[:1])

        ssc_4 = self.create_sortedset(items)
        ssc_4.discard_between(min_score=2, max_score=16)
        self.assertEqual(ssc_4.items(), [items[0], items[5]])

        ssc_5 = self.create_sortedset(items)
        ssc_5.discard_between(max_score=16)
        self.assertEqual(ssc_5.items(), items[5:])

        ssc_6 = self.create_sortedset(items)
        ssc_6.discard_between(min_rank=4, min_score=4)
        self.assertEqual(ssc_6.items(), items[:2])

        ssc_7 = self.create_sortedset(items)
        ssc_7.discard_between(0, 1, 16, 32)
        self.assertEqual(ssc_7.items(), items[2:4])

        ssc_8 = self.create_sortedset(items)
        ssc_8.discard_between()
        self.assertEqual(ssc_8.items(), items)

    def test_discard_member(self):
        ssc = self.create_sortedset()

        ssc.set_score('member_1', 1)
        self.assertIn('member_1', ssc)
        ssc.discard_member('member_1')
        self.assertNotIn('member_1', ssc)

        # No error for removing non-existient member
        ssc.discard_member('member_1')

    def test_get(self):
        ssc = self.create_sortedset([('member_1', 1), ('member_2', 2.0)])

        self.assertEqual(ssc.get_score('member_1'), 1)
        self.assertEqual(ssc.get_score('member_2'), 2.0)
        self.assertEqual(ssc.get_score('member_3', 0), 0)
        self.assertEqual(ssc.get_score('member_4'), None)

    def test_increment_score(self):
        ssc = self.create_sortedset()

        ssc.increment_score('member_1')
        self.assertEqual(ssc.get_score('member_1'), 1.0)

        ssc.increment_score('member_1', 1.0)
        self.assertEqual(ssc.get_score('member_1'), 2.0)

        self.assertRaises(ValueError, ssc.increment_score, 'member_1', '!')

    def test_get_rank(self):
        items = [('member_1', 1), ('member_2', 2.0), ('member_3', 30.0)]
        ssc = self.create_sortedset(items)

        self.assertEqual(ssc.get_rank('member_1'), 0)
        self.assertEqual(ssc.get_rank('member_2'), 1)
        self.assertEqual(ssc.get_rank('member_3'), 2)
        self.assertEqual(ssc.get_rank('member_4'), None)

        self.assertEqual(ssc.get_rank('member_4', reverse=True), None)
        self.assertEqual(ssc.get_rank('member_3', reverse=True), 0)
        self.assertEqual(ssc.get_rank('member_2', reverse=True), 1)
        self.assertEqual(ssc.get_rank('member_1', reverse=True), 2)

    def test_items(self):
        items = [
            ('0', 1), ('1', 2), ('2', 4), ('3', 8), ('4', 16), ('5', 32)
        ]
        ssc = self.create_sortedset(items)

        self.assertEqual(ssc.items(), items[:])

        self.assertEqual(ssc.items(min_rank=1), items[1:])
        self.assertEqual(ssc.items(min_rank=1, max_rank=-2), items[1:-1])
        self.assertEqual(ssc.items(max_rank=-2), items[:-1])
        self.assertEqual(
            ssc.items(min_rank=1, max_rank=4, reverse=True), items[4:0:-1]
        )

        self.assertEqual(ssc.items(min_score=4), items[2:])
        self.assertEqual(ssc.items(min_score=4, max_score=16), items[2:-1])
        self.assertEqual(ssc.items(max_score=4), items[:3])
        self.assertEqual(
            ssc.items(min_score=2, max_score=16, reverse=True), items[4:0:-1]
        )

        self.assertEqual(ssc.items(min_rank=1, min_score=4), items[2:])
        self.assertEqual(ssc.items(min_rank=3, min_score=4), items[3:])
        self.assertEqual(ssc.items(max_rank=4, min_score=4), items[2:5])
        self.assertEqual(ssc.items(1, 4, 4, 8), items[2:4])
        self.assertEqual(ssc.items(1, 4, 4, 8, reverse=True), items[3:1:-1])

    def test_update(self):
        ssc = self.create_sortedset([('member_1', 0.0)])

        ssc.update({'member_1': 1, 'member_2': 2.0})
        self.assertEqual(ssc.get_score('member_1'), 1)
        self.assertEqual(ssc.get_score('member_2'), 2.0)

        ssc.update([('member_2', 20.0), ('member_3', 30.0)])
        self.assertEqual(ssc.get_score('member_2'), 20.0)
        self.assertEqual(ssc.get_score('member_3'), 30.0)

        zc_2 = self.create_sortedset()
        zc_2.set_score('member_3', 40.0)
        ssc.update(zc_2)
        self.assertEqual(ssc.get_score('member_3'), 40.0)
