import unittest
from amazons_desktop.game import Game, encode, decode
from amazons_desktop.clock import Clock

class Rules(unittest.TestCase):
    def test_initial(self):
        g=Game()
        self.assertEqual(sum(row.count(1) for row in g.board),4)
        self.assertEqual(sum(row.count(-1) for row in g.board),4)
        self.assertEqual(g.turn,1)
        self.assertEqual(g.board[9][6],1)

    def test_rays_and_blocking(self):
        g=Game()
        self.assertIn((5,1),g.rays((6,0)))
        self.assertIn((4,0),g.rays((6,0)))
        self.assertNotIn((2,0),g.rays((6,0)))
        g.board[5][0]=2
        self.assertNotIn((4,0),g.rays((6,0)))

    def test_move_arrow_origin_undo(self):
        g=Game(); original=[r[:] for r in g.board]
        move=((6,0),(5,0),(6,0))
        g.apply(move)
        self.assertEqual(g.board[6][0],2)
        self.assertEqual(g.turn,-1)
        g.undo()
        self.assertEqual(g.board,original)
        self.assertEqual(g.turn,1)

    def test_illegal_turn_is_atomic(self):
        for move in [((6,0),(4,1),(6,0)), ((6,0),(5,0),(3,0)), ((6,0),(5,0),(2,0)), ((6,0),(5,0),(5,0)), ((-1,0),(5,0),(6,0))]:
            g=Game(); original=[r[:] for r in g.board]
            with self.assertRaises(ValueError): g.apply(move)
            self.assertEqual(g.board,original)
            self.assertEqual(g.history,[])

    def test_terminal(self):
        g=Game(); g.board=[[2]*10 for _ in range(10)]; g.board[0][0]=1
        self.assertEqual(g.winner(),-1)

    def test_protocol(self):
        move=((6,0),(5,0),(6,0))
        self.assertEqual(encode(move),'AGAFAG')
        self.assertEqual(decode(encode(move)),move)
        with self.assertRaises(ValueError): decode('ZZZZZZ')

class Timers(unittest.TestCase):
    def setUp(self):
        self.t=0.0
        self.c=Clock(100,lambda:self.t)

    def test_loading_pause_switch(self):
        self.t=50; self.c.update(); self.assertEqual(self.c.used[1],0)
        self.c.start(1); self.t=60; self.c.finish_turn(-1)
        self.assertEqual(self.c.used[1],10)
        self.t=65; self.c.pause(); self.t=90; self.c.update()
        self.assertEqual(self.c.used[-1],5)
        self.c.start(-1); self.t=92; self.c.finish_turn(1)
        self.c.undo(-1)
        self.assertEqual(self.c.used,{1:10,-1:0})

    def test_timeout(self):
        self.c.start(1); self.t=100; self.c.update()
        self.assertEqual(self.c.expired(),1)
        self.assertEqual(self.c.remaining(1),0)

    def test_unlimited(self):
        self.c.limit=0; self.c.start(1); self.t=1000; self.c.update()
        self.assertIsNone(self.c.expired())

if __name__=='__main__': unittest.main()
