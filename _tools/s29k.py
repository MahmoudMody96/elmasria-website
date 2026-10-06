# -*- coding: utf-8 -*-
"""SEO v29-K: shorten services/index description to <=160 chars."""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'services', 'index.html')
with open(p, encoding='utf-8') as f: t = f.read()
nd = 'جميع خدمات المصرية للسلامة والصحة المهنية: السلامة المهنية والحماية المدنية ومكافحة الآفات والدراسات البيئية والأيزو والعيادة والعمالة والمقاولات والنظافة واللاندسكيب.'
t = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + nd + m.group(2), t, count=1)
t = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + nd + m.group(2), t, count=1)
t = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")', lambda m: m.group(1) + nd + m.group(2), t, count=1)
with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t)
print('K-DONE len=' + str(len(nd)))
