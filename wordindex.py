try:
    import Tkinter as tk
except:
    from tkinter import font as tkFont

import math

def print_dir(o):
    for attr in [a for a in dir(o) if a[0:2] != ('__')]:
        print attr, '=', getattr(o, attr),
    print '\n\n'

class WordIndexWindow(tk.Frame):

    def __init__(self, master, items=[], height=10, callback=lambda i:None):
        tk.Frame.__init__(self, master)

        self.lbox     = tk.Listbox(self, height=height, exportselection=0)
        self.items    = items
        self.itemcnt  = len(items)
        self.winsize  = height
        self.midwin   = int(math.ceil(height/2.0))
        self.top      = 0
        self.bot      = min(self.winsize-1, self.itemcnt)
        self.active   = 0
        self.select   = -1
        self.style    = self.lbox['activestyle']
        self.callback = callback

        self.lbox.insert(tk.END, *items[self.top : self.bot+1])
        self.lbox.activate(0)
        self.lbox.select_anchor(0)
        self.lbox.pack()
        
        self.lbox.bind('<KeyRelease-Return>' , self._on_enter)
        self.lbox.bind('<KeyRelease-space>'  , self._on_enter)
        self.lbox.bind('<ButtonRelease-1>'   , self._on_click)
        self.lbox.bind('<MouseWheel>'        , self._on_scroll)
        self.lbox.bind('<Button-4>'          , self._on_scroll)
        self.lbox.bind('<Button-5>'          , self._on_scroll)
        self.lbox.bind('<Up>'                , self._on_updown)
        self.lbox.bind('<Down>'              , self._on_updown)
        self.lbox.bind('<Prior>'             , self._on_page_updown)
        self.lbox.bind('<Next>'              , self._on_page_updown)
        self.lbox.bind('<Control-Home>'      , self._on_ctrl_endhome)
        self.lbox.bind('<Control-End>'       , self._on_ctrl_endhome)

    class _scroll_down_event:
        num = 5
        delta = -1
    class _scroll_up_event:
        num = 4
        delta = 1
    class _down_event:
        keysym = 'Down'
    class _up_event:
        keysym = 'Up'

    def _redraw(self, relist=True):
        if relist:
            self.lbox.delete(0, tk.END)
            self.lbox.insert(0, *self.items[self.top : self.bot+1])
        
        if (self.top <= self.select <= self.bot):
            self.lbox.select_set(self.select - self.top)

        if (self.top <= self.active <= self.bot):
            self.lbox.activate(self.active - self.top)
            if self.lbox['activestyle'] == 'none':
                self.lbox['activestyle'] = self.style 
        else:
            # the only solution I could think of at the moment
            # to avoid activating (underlining) items by Listbox
            # when it's not wanted, that is when scrolling outside
            # area with active item
            self.lbox['activestyle'] = 'none'

    def _on_scroll(self, event):
        if event.num == 5 or event.delta < 0:
            # DOWN
            if self.bot < self.itemcnt-1:
                self.top += 1
                self.bot += 1
        elif event.num == 4 or event.delta > 0:
            # UP
            if self.top > 0:
                self.top -= 1
                self.bot -= 1

        self._redraw()
        return 'break'

    def _on_click(self, event):
        # this is after mouse is released and newly active item has been
        # already chosen by the Listbox itself and is marked under ANCHOR
        #self.select = self.top+self.lbox.index(tk.ANCHOR)
        self.select = self.top + int(self.lbox.curselection()[0])
        self.active = self.select
        self._redraw(False)
        self.callback(self.select)
        return 'break'

    def _on_enter(self, event):
        # space or enter is released, old selection must be manually removed
        # and new selection will be where now active item is
        self.lbox.select_clear(self.select - self.top)
        self.select = self.top + self.lbox.index(tk.ACTIVE)
        self.active = self.select
        self._redraw(False)
        self.callback(self.select)
        return 'break'

    def _on_updown(self, event):
        # the majority of code here is to cover the behaviour of Listbox
        # when it's scrolled outside the active item visibility and upon
        # eventual arrow movement it reappears centered
        if self.active < self.top or self.active > self.bot:
            was_visible = False
        else:
            was_visible = True

        # moving active item on releasing Up, Down keys
        if event.keysym == 'Down':
            if self.active < self.itemcnt-1:
                self.active += 1
        elif event.keysym == 'Up':
            if self.active > 0:
                self.active -= 1

        if not was_visible:
            # active item wasn't visible
            # jump to the block where it is and center it
            mid = self.midwin
            top = self.active - mid+1
            bot = self.active + mid
            if top < 0:
                top = 0
                bot = self.winsize-1
            elif bot >= self.itemcnt:
                top = self.itemcnt - self.winsize
                bot = self.itemcnt - 1
            self.top = top
            self.bot = bot
            self._redraw()
        else:
            # scroll if the active item is now out of visible area
            if self.active < self.top:
                self._on_scroll(self._scroll_up_event)
            elif self.active > self.bot:
                self._on_scroll(self._scroll_down_event)
            else:
                self._redraw(False)

        return 'break'

    def _on_page_updown(self, event):
        if event.keysym == 'Next':
            if self.bot + self.winsize-1 < self.itemcnt:
                # last item in the window becomes the first one
                self.top = self.bot
                self.bot = self.top + self.winsize-1;
            else:
                self.top = self.itemcnt - min(self.winsize, self.itemcnt)
                self.bot = self.itemcnt - 1
        elif event.keysym == 'Prior':
            if self.top - self.winsize >= 0: 
                # first one become the last one
                self.bot = self.top
                self.top = self.top - self.winsize+1
            else:
                self.bot = 0 + self.winsize-1
                self.top = 0
        self.active = self.top
        self._redraw()
        return 'break'

    def _on_ctrl_endhome(self, event):
        print event.keysym
        return 'break'

    def focus(self):
        self.lbox.focus()

    def rebind(self, items):
        self.items = items
        self.itemcnt = len(items)
        self.active = 0
        self.select = -1
        self.top     = 0
        self.bot     = min(self.winsize-1, self.itemcnt)
        self._redraw()

    def see(self, index, centered=False):
        if index >= self.itemcnt:
            index = self.itemcnt-1
        elif index < 0:
            index = 0
        self.active = index
        self.select = index
        if centered:
            if index - self.midwin < 0:
                self.top = 0
            else:
                self.top = index - self.midwin+1
        else:
            self.top = index
        self.bot = self.top + self.winsize-1
        self._redraw()

    def up(self):
        self._on_updown(self._up_event)
        self._on_enter(None)

    def down(self):
        self._on_updown(self._down_event)
        self._on_enter(None)

    def reset(self):
        self.active = 0
        self.select = -1
        self.top = 0
        self.bot = self.winsize-1
        self._redraw()


                         
if __name__ == '__main__':
    idx = range(4)
    root = tk.Tk()
    lbframe = WordIndexWindow(root, idx)
    lbframe.pack()
    lbframe.see(2)
    root.mainloop()

