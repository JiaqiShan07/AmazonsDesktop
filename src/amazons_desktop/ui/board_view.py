"""Cached board and antialiased sprites; redraw only after state/layout changes."""
from functools import lru_cache
from PIL import Image, ImageDraw, ImageTk
from .move_trail import trail

@lru_cache(maxsize=4)
def background(size):
    image=Image.new('RGB',(size+1,size+1),'#ffffff')
    draw=ImageDraw.Draw(image)
    for row in range(10):
        for col in range(10):
            bounds=(round(col*size/10),round(row*size/10),round((col+1)*size/10),round((row+1)*size/10))
            draw.rectangle(bounds,fill='#ffffff' if (row+col)%2==0 else '#f0f2f5',outline='#d9dde3')
    return image

@lru_cache(maxsize=4)
def sprites(cell):
    factor=3
    size=cell*factor
    center=size/2
    result={}
    for value in (1,-1,2,'move','arrow'):
        image=Image.new('RGBA',(size,size))
        draw=ImageDraw.Draw(image)
        radius=size*({1:.33,-1:.33,2:.30,'move':.09,'arrow':.153}[value])
        bounds=(center-radius,center-radius,center+radius,center+radius)
        if value in (1,-1):
            draw.ellipse(bounds,fill='#242a33' if value==1 else '#ffffff',outline='#242a33' if value==1 else '#636d7b',width=2*factor)
        elif value=='arrow':
            draw.ellipse(bounds,outline='#3982f7',width=2*factor)
        else:
            draw.ellipse(bounds,fill='#3982f7' if value==2 else '#385fe0')
        result[value]=image.resize((cell,cell),Image.Resampling.LANCZOS)
    return result


def render(board, cell, hints, shooting, selected, last):
    size=round(cell*10)
    image=background(size).copy()
    if last is not None:
        overlay=trail(size, last)
        image.paste(overlay, (0, 0), overlay)
    draw=ImageDraw.Draw(image)
    icons=sprites(round(size/10))
    for row in range(10):
        for col in range(10):
            x,y=round(col*size/10),round(row*size/10)
            right,bottom=round((col+1)*size/10),round((row+1)*size/10)
            if (row,col)==selected:
                draw.rectangle((x+2,y+2,right-2,bottom-2),outline='#385fe0',width=3)
            value=board[row][col]
            key=value if value else ('arrow' if shooting else 'move') if (row,col) in hints else None
            if key is not None:
                sprite=icons[key]
                image.paste(sprite,(x,y),sprite)
    return ImageTk.PhotoImage(image)
