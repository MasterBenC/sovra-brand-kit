"""从新内容清单生成 Sovra 课件。所有几何参数使用英寸。"""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
STYLES = json.loads((ROOT/'assets/role-styles.json').read_text())
INK, GRAY, PURPLE, ORANGE = '18181C','85858F','5145FF','FF925C'
def tidy(t):
    return re.sub(r'(?<=AI) +(?=[\u3400-\u9fff])|(?<=[\u3400-\u9fff]) +(?=AI)', '', t.strip())

def rect(s,name,x,y,w,h,color):
    z=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    z.name=name;z.fill.solid();z.fill.fore_color.rgb=RGBColor.from_string(color)
    z.line.fill.background()
    st=z._element.find('p:style',z._element.nsmap)
    if st is not None:z._element.remove(st)
    return z

def text(s,name,t,x,y,w,h,size,color=INK,line=None,ea='PingFang SC',latin='Arial',align='left'):
    t=tidy(t)
    if not t: raise ValueError(f'{name} 缺少文字')
    line=line or size*1.28
    for row in t.split('\n'):
        units=sum(1 if unicodedata.east_asian_width(c) in 'WF' else .57 for c in row)
        if units*size>w*72+.2: raise ValueError(f'{name} 超宽，请在语义处分行或拆页：{row}')
    if line*len(t.split('\n'))>h*72+3:raise ValueError(f'{name} 超高，请拆页：{t}')
    z=s.shapes.add_textbox(*map(Inches,(x,y,w,h)));z.name=name
    f=z.text_frame;f.auto_size=MSO_AUTO_SIZE.NONE;f.word_wrap=False
    f.margin_top=f.margin_bottom=f.margin_left=f.margin_right=0
    for i,row in enumerate(t.split('\n')):
        p=f.paragraphs[0] if i==0 else f.add_paragraph()
        p.space_before=p.space_after=Pt(0);p.line_spacing=Pt(line)
        p.alignment=PP_ALIGN.RIGHT if align=='right' else PP_ALIGN.LEFT
        u=p.add_run();u.text=row;u.font.name=latin;u.font.size=Pt(size)
        u.font.bold=False;u.font.italic=False;u.font.color.rgb=RGBColor.from_string(color)
        rp=u._r.get_or_add_rPr();e=OxmlElement('a:ea');e.set('typeface',ea);rp.append(e);rp.set('spc','0')
    return z

def fixed(s,key,t,**changes):
    style={**STYLES[key],**changes};return text(s,key.split('/')[-1],t,**style)

def add_body(s,page,folder):
    title=page['title'];two='\n' in title
    fixed(s,'正文/统一正文主标题',title,h=.78 if two else .42)
    y=1.34 if two else 1.05
    if page.get('lead'):
        text(s,'正文导语',page['lead'],.42,y,9.16,.36,14);y+=.60
    kind=page['type']
    if kind in ('flow','cards'):
        items=page['items'];assert 2<=len(items)<=4
        gap=.22;w=(9.16-gap*(len(items)-1))/len(items)
        for i,(label,desc) in enumerate(items):
            x=.42+i*(w+gap)
            rect(s,'分组底色',x,y,w,2.42,'F8F8FB')
            rect(s,'结构线',x,y,w,.022,PURPLE)
            if kind=='flow':text(s,'步骤编号',f'{i+1:02}',x+.14,y+.20,w-.28,.35,17,PURPLE)
            text(s,'分组标题',label,x+.14,y+.67,w-.28,.4,15)
            text(s,'分组说明',desc,x+.14,y+1.22,w-.28,1.0,12,line=17)
    elif kind in ('table','case','data'):
        rows=[page['columns'],*page['rows']];cols=len(rows[0]);assert 2<=cols<=4 and 2<=len(rows)<=6
        assert all(len(row)==cols for row in rows)
        rh=min(.69,(4.43-y)/len(rows));cw=9.16/cols
        for i,row in enumerate(rows):
            top=y+i*rh
            if i==0:rect(s,'表头底色',.42,top,9.16,rh,'F5F4FA')
            rect(s,'表格横线',.42,top,9.16,.008,PURPLE if i==0 else 'DADAE0')
            for j,val in enumerate(row):
                text(s,'表头' if i==0 else '表格单元',val,.52+j*cw,top+.06,cw-.20,rh-.09,12,line=15)
    elif kind=='visual':
        path=folder/page['asset']
        if not page.get('provenance'):raise ValueError('素材需登记来源或出图记录')
        with Image.open(path) as img: ratio=img.width/img.height
        h=min(4.52-y,9.16/ratio);w=h*ratio
        s.shapes.add_picture(str(path), Inches(.42+(9.16-w)/2), Inches(y), Inches(w), Inches(h))
    else:raise ValueError('未知正文类型 '+kind)
    if page.get('takeaway'):
        rect(s,'结论强调',.42,4.64,.028,.27,ORANGE)
        text(s,'正文结论',page['takeaway'],.54,4.62,9,.33,13)
    if page.get('source'):fixed(s,'正文/统一来源及补充说明',page['source'])
    if kind in ('data','case') and not page.get('source'):raise ValueError('案例、数据页缺少来源')

def build(file,output):
    d=json.loads(file.read_text());p=Presentation();p.slide_width=Inches(10);p.slide_height=Inches(5.625)
    sections=d['sections'];assert sections and all(g['pages'] for g in sections)
    agenda_count=(len(sections)+4)//5
    start=2+agenda_count;starts=[]
    for g in sections:starts.append(start);start+=1+len(g['pages'])
    def slide():
        s=p.slides.add_slide(p.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=RGBColor.from_string('FFFFFF');return s
    def footer(s,chapter=False):
        k='章节' if chapter else '正文'
        fixed(s,k+'/中文品牌页脚','灵能涌现');fixed(s,k+'/统一页码',f'{len(p.slides):02}')
    s=slide();s.shapes.add_picture(str(ROOT/'assets/cover.png'),0,0,p.slide_width,p.slide_height)
    for name,t in [('中文品牌','灵能涌现'),('英文品牌','the emergent company'),('活动信息',d['event']),('封面标题',d['title']),('封面说明',d['subtitle']),('讲师','主讲人：'+d['speaker']),('课程目标',d['goal'])]:
        fixed(s,'封面/'+name,t)
    assert 1<=len(d['credentials'])<=3
    for i,t in enumerate(d['credentials']):fixed(s,'封面/讲师身份',t,y=3.78+.22*i)
    s.notes_slide.notes_text_frame.text=d.get('opening_notes','')
    for batch in range(agenda_count):
        s=slide();fixed(s,'目录/统一正文主标题','目录')
        for j,g in enumerate(sections[batch*5:batch*5+5]):
            idx=batch*5+j;dy=.77*j
            rect(s,'目录横条',.30,1.10+dy,9.4,.67,'F8F8FB');rect(s,'目录竖线',1.43,1.24+dy,.012,.4,ORANGE)
            for key,val in [('章节编号',f'{idx+1:02}'),('章节名称',g['title']),('章节起始页',f'{starts[idx]:02}')]:
                fixed(s,'目录/'+key,val,y=1.27+dy)
        rect(s,'页脚线',.30,5.17,9.4,.006,'DDDEE3');footer(s)
    for idx,g in enumerate(sections,1):
        s=slide()
        for key,val in [('课程名称',d['short_title']),('章节编号',f'{idx:02}'),('PART编号',f'PART {idx:02}'),('章节标题',g['title']),('章节内容说明',g['summary'])]:
            fixed(s,'章节/'+key,val)
        rect(s,'章节竖线',2.76,1.31,.008,2.85,'D0D0D3');rect(s,'页脚线',.42,5.20,9.16,.006,'D7D7DB');footer(s,True)
        s.notes_slide.notes_text_frame.text=g.get('notes','')
        for page in g['pages']:
            s=slide();add_body(s,page,file.parent);footer(s);s.notes_slide.notes_text_frame.text=page['notes']
    output.parent.mkdir(parents=True,exist_ok=True);p.save(output)
if __name__=='__main__':
    raise SystemExit('不要直接运行 build.py。交付必须用 publish_ppt.py，否则 ZIP 时间戳会使 PPTX 字节不稳定。')
