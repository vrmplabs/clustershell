#!/usr/bin/env python
# ClusterShell propagation test suite
# Written by H. Doreau
# $Id$


"""Unit test for Propagation"""

import copy
import sys
import time
import unittest
import tempfile

# profiling imports
#import cProfile
#from guppy import hpy
# ---

sys.path.insert(0, '../lib')

from ClusterShell.Propagation import *
from ClusterShell.NodeSet import NodeSet


def chrono(func):
    def timing(*args):
        start = time.time()
        res = func(*args)
        #print "execution time: %f s" % (time.time() - start)
        return res
    return timing


class PropagationTest(unittest.TestCase):
    def _gen_tree(self):
        """generate a sample topology tree"""
        tmpfile = tempfile.NamedTemporaryFile()
        tmpfile.write('[DEFAULT]\n')
        tmpfile.write('admin[0-2]: proxy\n')
        tmpfile.write('proxy: STA[0-400]\n')
        tmpfile.write('STA[0-400]: STB[0-2000]\n')
        tmpfile.write('STB[0-2000]: node[0-11000]\n')
        tmpfile.flush()
        parser = TopologyParser()
        parser.load(tmpfile.name)
        return parser.tree('admin1')

    @chrono
    def testConvertingTree(self):
        """test topology to propagation tree conversion"""
        ptree = PropagationTree()
        ptree.load(self._gen_tree(), 'node[0-10000]', 64)
        # count the number of each instances
        admins = gateways = edgenodes = 0
        for node in ptree.nodes.itervalues():
            if isinstance(node, AdminNode):
                admins += 1
            elif isinstance(node, GatewayNode):
                gateways += 1
            elif isinstance(node, EdgeNode):
                edgenodes += 1
            else:
                self.fail('Unknown instance in the propagation tree: %s' % \
                    type(node))
        # WARNING : these values depends on the content of the tmpfile written
        # by self._gen_tree() (appart for admins)
        self.assertEqual(admins, 1)
        self.assertEqual(gateways, 2403)
        self.assertEqual(edgenodes, 10001) # only involved edge nodes are instancied

    @chrono
    def testMessagesPropagation(self):
        """test message passing between nodes"""
        ptree = PropagationTree()
        ptree.load(self._gen_tree(), 'node[0-10000]', 64)
        msg = PropagationMessage()
        admin = 'admin1'
        admin_inst = ptree.nodes[admin]

        msg['src'] = admin
        msg['dst'] = 'STB1564'
        msg['str'] = 'Hello, world!'

        before = time.time()
        admin_inst.send_message(msg)
        time_msg0 = time.time() - before

        msg['str'] = 'Hello, world, again!'
        before = time.time()
        admin_inst.send_message(msg)
        time_msg1 = time.time() - before
        # test the router's cache mecanism
        self.failUnless(time_msg1 < time_msg0)

    @chrono
    def testRouting(self):
        """
        """
        ptree = PropagationTree()
        ptree.load(self._gen_tree(), 'node[0-10000]', 64)
        msg = PropagationMessage()
        admin = 'admin1'
        admin_inst = ptree.nodes[admin]

        msg['src'] = admin
        msg['dst'] = 'nonexistentnode'
        msg['str'] = 'Hello, world!'
        self.assertRaises(RoutesResolvingError, admin_inst.send_message, msg)


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(PropagationTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    #cProfile.run('main()')
    main()

