try:
    import Tkinter as tk
    import tkFont
except:
    import tkinter as tk
    from tkinter import font as tkFont

from wordindex import WordIndexWindow

def show_dicts():
    textwin['state'] = tk.NORMAL
    textwin['wrap'] = tk.NONE
    textwin.delete('1.0', tk.END)
    i = 1
    for d in dicts:
        textwin.insert(tk.END, str(i)+'. '+d.ifo['bookname'], '<a>')
        textwin.insert(tk.END, '\n  '+d.ifo['wordcount']+' words, '
                                     +d.ifo['date']+'\n', '<small>')
        i += 1
    if i == 1:
        textwin.insert(tk.END, 'No dictionaries found in ./dic subdirectory.')
    textwin['wrap'] = tk.WORD
    textwin['state'] = tk.DISABLED

def on_dict_select(event):
    line = textwin.index('@%d,%d'%(event.x, event.y))
    line = int(float(line)) + 1
    change_dict(line//2-1)

def change_dict(num):
    global dict_active
    if not (0 <= num < len(dicts)):
        raise IndexError('dictionary index out of range')
    dict_active.unload()
    dict_active = dicts[num]
    dict_active.load()
    root.wm_title(dict_active.ifo['bookname'])
    windex.rebind(dict_active) 
    wentry.delete(0, tk.END)
   

def show_translation(index):
    text = dict_active.dict_data(index)
    #print text
    textwin['state'] = tk.NORMAL
    textwin.delete('1.0', tk.END)
    textwin.insert('1.0', ' '+windex.items[index], 'head')
    insert_formatted('\n'+text)
    textwin['state'] = tk.DISABLED


def insert_formatted(text):
    chunks = text.split('<')
    for ch in chunks:
        tag = 'normal'
        i_close = ch.find('>')
        if ch[0] == '/' and i_close > 0:
            ch = ch[i_close+1:]
        elif i_close > 0:
            tag = '<'+ch[:i_close+1]
            ch = ch[i_close+1:]
        textwin.insert(tk.END, ch, tag)


def on_entry_change(*args):
    word = wentry_sv.get()
    if not word:
        return
    if wentry.red:
        wentry['fg'] = 'black'
        wentry.red = False
    if word[0] == ':':
        # ':' opens command sequence, ignore it
        return
    i = dict_active.search(word, True)
    if i >= 0:
        windex.see(i)
        show_translation(i)
    else:
        wentry['fg'] = 'red'
        wentry.red = True

def command_eval(word):
    if word == ':d':
        show_dicts()
    elif word.startswith(':d'):
        try:
            num = int(word[2:])
            change_dict(num-1)
        except (ValueError, IndexError) as e:
            print e
            wentry.red = True        
    # elif
    # other commands...
    else:
        wentry.red = True
    if wentry.red:
        wentry['fg'] = 'red'


def on_enter(event):
    word = wentry_sv.get()
    if word and word[0] == ':':
        command_eval(word)
    else:
        on_entry_change()

def on_tab(event):
    if event.widget.focus_get() is wentry:
        windex.focus()
    else:
        wentry.focus()
    return 'break'

def on_ctrl_a(event):
    event.widget.select_clear()
    event.widget.select_range(0, tk.END)
    return 'break'

def on_ctrl_bs(event):
    wentry.event_generate('<Control-Shift-Left>')
    wentry.delete(tk.INSERT, tk.ANCHOR)
    return 'break' 

def on_ctrl_del(event):
    wentry.event_generate('<Control-Shift-Right>')
    wentry.delete(tk.ANCHOR, tk.INSERT)
    return 'break'

def on_select(index):
    show_translation(index)

def on_updown(event):
    if windex.select < 0:
        return
    if event.keysym == 'Down':
        windex.down()
    else:
        windex.up()
    show_translation(windex.select)


root = tk.Tk()
root.wm_title('pyStarDictViewer')
root.resizable(height=False, width=False)
root.bind('<Tab>', on_tab)

# set font for text
text_font = tkFont.nametofont("TkTextFont")
text_font.configure(size=12)

# word entry
wentry_sv = tk.StringVar()
wentry_sv.trace('w', on_entry_change)
wentry = tk.Entry(root, textvariable=wentry_sv)
wentry.bind('<Control-a>', on_ctrl_a)
wentry.bind('<Up>', on_updown)
wentry.bind('<Down>', on_updown)
wentry.bind('<Return>', on_enter)
wentry.bind('<Control-BackSpace>', on_ctrl_bs)
wentry.bind('<Control-Delete>', on_ctrl_del)
wentry.red = False

# word index
windex = WordIndexWindow(root, height=15, callback=on_select)
windex.lbox['font'] = text_font

# translation text window
# minimal height is set here and then it's spread
# with a sticky grid property
textwin = tk.Text(root, width=45, height=1, padx=4, pady=2)
textwin['font'] = text_font
textwin['wrap'] = tk.WORD

# status bar & tool bar
bottom_frame = tk.Frame(root)

# status bar
statbar = tk.Label(bottom_frame, text="")
statbar['text'] = 'some info'
statbar.pack(side=tk.LEFT)

# tool bar
tbar_frame = tk.Frame(bottom_frame)
tbar_frame.pack_propagate(0)
tbar_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
tbar_help = tk.Button(tbar_frame, text='help', underline=0)
tbar_help.pack(side=tk.RIGHT)
tbar_dict = tk.Button(tbar_frame, text='dict', underline=0)
tbar_dict.bind('<Button-1>', lambda e:show_dicts())
root     .bind('<Alt-d>',    lambda e:show_dicts())
tbar_dict.pack(side=tk.RIGHT)

# fonts for formating translation text
font_head   = tkFont.Font(family="Arial", size=15, weight=tkFont.BOLD)
font_normal = tkFont.Font(family="Arial", size=13)
font_bold   = tkFont.Font(family="Arial", size=13, weight=tkFont.BOLD)
font_italic = tkFont.Font(family="Arial", size=13, slant=tkFont.ITALIC)
font_small  = tkFont.Font(family="Arial", size=9)

# formatting tags
textwin.tag_config("head"    , foreground="black"  , font=font_head)
textwin.tag_config("normal"  , foreground="black"  , font=font_normal)
textwin.tag_config("<b>"     , foreground="black"  , font=font_bold)
textwin.tag_config("<i>"     , foreground="black"  , font=font_italic)
textwin.tag_config("<small>" , foreground="black"  , font=font_small)

textwin.tag_config("<a>", foreground="blue", underline=1)
textwin.tag_bind("<a>", "<Button-1>", on_dict_select)
textwin.tag_bind("<a>", "<Enter>", lambda e:e.widget.config(cursor="hand2"))
textwin.tag_bind("<a>", "<Leave>", lambda e:e.widget.config(cursor="arrow"))

# grid configuration
wentry .grid(row=0, column=0, sticky='NEWS')
windex .grid(row=1, column=0)
textwin.grid(row=0, column=1, rowspan=2, sticky='NEWS')
bottom_frame.grid(row=2, column=0, columnspan=2, sticky='WE')


if __name__ == '__main__':

    import stardict as sdict

    ifos = sdict.look_for_dicts('./dic')
    dicts = []
    for ifo in ifos:
        try:
            dicts.append(sdict.StarDict(ifo, False));
        except ValueError as e:
            print e, ifo
     
    if dicts:
        dicts = sorted(dicts, key=lambda d:d.ifo['bookname']+d.ifo['wordcount'])
        dict_active = dicts[0]
        dict_active.load()
        windex.rebind(dict_active) 
        root.wm_title(dict_active.ifo['bookname'])
        wentry.focus_set()
    else:
        wentry['state'] = 'disabled'
    
    show_dicts()
    root.mainloop()
    
