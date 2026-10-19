"""Uses real Tk widgets; set PYTHONPATH=src when running from the checkout."""
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import tempfile
from amazons_desktop.ui.app import App

class Desktop(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk(); self.app=App(self.root); self.app.start(); self.root.update()
    def tearDown(self): self.app.close()
    def click(self,r,c):
        a=self.app
        a.click(SimpleNamespace(x=a.ox+(c+.5)*a.cell,y=a.oy+(r+.5)*a.cell))
        self.root.update()
    def test_complete_turn_cancel_and_undo(self):
        a=self.app
        self.click(6,0); self.assertEqual(a.source,(6,0))
        self.click(5,0); self.assertEqual(a.target,(5,0))
        self.click(3,0); self.assertEqual(len(a.game.history),0)
        a.cancel(); self.assertEqual(a.game.board[6][0],1)
        self.click(6,0);self.click(5,0);self.click(6,0)
        self.assertEqual(a.game.board[6][0],2)
        self.assertEqual(a.game.turn,-1)
        a.undo();self.assertEqual(a.game.turn,1);self.assertEqual(a.game.board[6][0],1)
    def test_pause_timeout_new(self):
        a=self.app;a.toggle_pause();self.click(6,0)
        self.assertIsNone(a.source);self.assertIsNone(a.clock.active)
        a.toggle_pause();a.clock.used[1]=a.clock.limit+1;a.tick_clock()
        self.assertEqual(a.timeout_winner,-1)
        self.click(6,0);self.assertIsNone(a.source)
        a.new();self.assertIsNone(a.timeout_winner)
    def test_engine_move_dispatch(self):
        a=self.app
        a.pending.add(1)
        a.events.put((a.token,1,'output','move AGAFAG'))
        a.poll()
        self.assertEqual(len(a.game.history),1)
        self.assertEqual(a.game.board[6][0],2)
        self.assertEqual(a.game.turn,-1)
        self.assertEqual(a.clock.active,-1)
        self.assertFalse(a.error)
        self.assertNotIn(1,a.pending)

    def test_engine_invalid_move_is_reported(self):
        a=self.app
        a.pending.add(1)
        a.events.put((a.token,1,'output','move ZZZZZZ'))
        a.poll()
        self.assertTrue(a.error)
        self.assertIsNone(a.clock.active)
        self.assertEqual(a.game.history,[])

    def test_old_engine_session_is_ignored(self):
        a=self.app
        previous=a.token
        a.new()
        a.events.put((previous,1,'output','move AGAFAG'))
        a.poll()
        self.assertFalse(a.error)
        self.assertEqual(a.game.history,[])

    def test_save_import_and_resize(self):
        a=self.app;a.commit(((6,0),(5,0),(6,0)))
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/'game.json')
            with patch('amazons_desktop.ui.app.filedialog.asksaveasfilename',return_value=path):a.save()
            a.new()
            with patch('amazons_desktop.ui.app.filedialog.askopenfilename',return_value=path):a.open()
        self.assertEqual(a.replay_index,0)
        a.seek(1)
        self.assertEqual(len(a.game.history),1)
        self.root.geometry('940x760');self.root.update()
        self.assertGreater(a.cell,0)
        self.assertLessEqual(a.oy+10*a.cell,a.canvas.winfo_height())

if __name__=='__main__':unittest.main()
