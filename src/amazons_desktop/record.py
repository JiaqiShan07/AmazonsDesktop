"""Record model and independent UTF-8 JSON / GB2312 competition serializers."""
from dataclasses import dataclass, field, replace
from datetime import datetime
import re
import json
from .game import Game, encode, decode

POSITION = r'([a-j])(10|[1-9])'
MOVE = re.compile(POSITION + POSITION + r'\(' + POSITION + r'\)')
HEADER = re.compile(r'#\[AM\]\[([^\[\]\r\n]*)\]\[([^\[\]\r\n]*)\]\[([^\[\]\r\n]*)\]\[([^\[\]\r\n]*)\]\[([^\[\]\r\n]*)\];')

def notation(move):
    positions = [chr(97+c)+str(10-r) for r,c in move]
    return positions[0]+positions[1]+'('+positions[2]+')'

def parse_move(text):
    match=MOVE.fullmatch(text)
    if not match:
        raise ValueError('无效棋谱走法：'+text)
    parts=match.groups()
    return tuple((10-int(parts[i+1]),ord(parts[i])-97) for i in (0,2,4))

@dataclass
class Record:
    black: str = '黑方'
    white: str = '白方'
    result: str = '先(后)手胜'
    location: str = field(default_factory=lambda:datetime.now().strftime('%Y-%m-%d Local'))
    event: str = 'Match'
    moves: list = field(default_factory=list)

    def game_at(self,index):
        game=Game()
        for move in self.moves[:index]:
            game.apply(move)
        return game

    def to_bytes(self):
        fields=(self.black,self.white,self.result,self.location,self.event)
        if any(any(c in value for c in '[]\r\n') for value in fields):
            raise ValueError('棋谱头部字段不能包含方括号或换行')
        text='#[AM]'+''.join('['+value+']' for value in fields)+';\n'
        for i,move in enumerate(self.moves):
            text+=(str(i//2+1)+' ' if i%2==0 else ' ')+notation(move)
            if i%2:
                text+='\n'
        return text.encode('gb2312')

    @classmethod
    def from_bytes(cls,raw):
        lines=raw.decode('gbk').splitlines()
        if not lines or not (header:=HEADER.fullmatch(lines[0])):
            raise ValueError('棋谱头部须为 #[AM][黑方][白方][结果][时间地点][赛事];（GBK 编码）')
        record=cls(*header.groups())
        game=Game()
        for number,line in enumerate(lines[1:],1):
            tokens=line.split()
            if len(tokens) not in (2,3) or tokens[0]!=str(number):
                raise ValueError(f'第 {number} 回合编号或走法数量无效')
            if len(tokens)==2 and number!=len(lines)-1:
                raise ValueError('只有最后一回合可以缺少白方走法')
            for text in tokens[1:]:
                if game.winner():
                    raise ValueError('棋谱在棋局结束后仍包含走法')
                move=parse_move(text)
                game.apply(move)
                record.moves.append(move)
        return record

    def with_moves(self, moves, *, result=None):
        return replace(self, moves=list(moves), result=self.result if result is None else result)

    def to_json_bytes(self):
        metadata = {key:getattr(self,key) for key in ('black','white','result','location','event')}
        data = {'format':'amazons-sau-1', 'metadata':metadata, 'moves':[encode(move) for move in self.moves]}
        return (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8')

    @classmethod
    def from_json_bytes(cls, raw):
        data = json.loads(raw.decode('utf-8'))
        if not isinstance(data,dict) or data.get('format')!='amazons-sau-1' or not isinstance(data.get('moves'),list):
            raise ValueError('不支持的 JSON 棋谱格式')
        metadata = data.get('metadata',{})
        keys = ('black','white','result','location','event')
        if not isinstance(metadata,dict) or any(not isinstance(value,str) for key,value in metadata.items() if key in keys):
            raise ValueError('棋谱对局信息必须为文本字段')
        record = cls(**{key:metadata[key] for key in keys if key in metadata})
        game = Game()
        for text in data['moves']:
            if not isinstance(text,str) or game.winner():
                raise ValueError('棋谱包含非法回合')
            move = decode(text)
            game.apply(move)
            record.moves.append(move)
        return record
