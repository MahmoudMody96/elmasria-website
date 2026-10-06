# -*- coding: utf-8 -*-
"""SEO v29-H: normalize meta descriptions to 120-160 chars (index + og sync)."""
import glob, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW = {
 'index.html': 'شركة المصرية للسلامة والصحة المهنية منذ 1999: استشارات وتنفيذ في السلامة والصحة المهنية والحماية المدنية والدراسات البيئية والأيزو والمقاولات. اتصل 01096087999.',
 'services/iso.html': 'التأهيل والحصول على شهادات الايزو في الجودة والسلامة والصحة المهنية: تجهيز النظام الداخلي والوثائق والتدريب ثم متابعة التفتيش حتى الحصول على الشهادة.',
 'services/landscape.html': 'تنفيذ أعمال اللاند سكيب وتنسيق الحدائق بالمصانع والشركات مع عقود صيانة شهرية ومهندسين وفنيين متخصصين ومعدات وزي موحد لخروج العمل بأفضل صورة.',
 'services/manpower.html': 'تعيين العمال بالأقسام الإنتاجية لكل التخصصات بعد المقابلات والفحص الشامل، مع التأمين الاجتماعي والصحي وجميع حقوق العامل طبقًا للقانون المصري.',
 'services/cleaning.html': 'خدمات أعمال النظافة: تنظيف وتلميع الأرضيات والزجاج والمكاتب والحمامات على مدار اليوم لجميع الأقسام الإنتاجية والإدارية داخل المنشآت.',
 'services/football-fields.html': 'إنشاء وصيانة ملاعب كرة القدم: تهيئة التربة وطبقة الأساس وطبقة سد المسام وطبقة المطاط وطبقة الإسفنج وتحديد الملعب وفق المواصفات الفنية.',
 'services/construction.html': 'أعمال المقاولات والإنشاءات طبقًا للقانون المصري والكود المصري في البناء — تنفيذ الأعمال الإنشائية والتهيئة والتجهيز داخل المنشآت والشركات.',
 'services/index.html': 'جميع خدمات المصرية للسلامة والصحة المهنية: السلامة المهنية، الحماية المدنية، مكافحة الآفات، الدراسات البيئية، الأيزو، العيادة، العمالة، المقاولات، النظافة، اللاندسكيب والملاعب.',
}
def rd(p):
    with open(p, encoding='utf-8') as f: return f.read()
def wr(p, t):
    with open(p, 'w', encoding='utf-8', newline='\r\n') as f: f.write(t)
n = 0
for sub, nd in NEW.items():
    path = os.path.join(ROOT, sub.replace('/', os.sep))
    t0 = rd(path); t = t0
    mo = re.search(r'<meta name="description" content="([^"]*)"', t)
    old = mo.group(1) if mo else None
    if old != nd:
        t = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + nd + m.group(2), t, count=1)
        # keep og:description in sync only when it mirrored the old description
        if old:
            t = re.sub(r'(<meta property="og:description" content=")[^"]*(")',
                       lambda m: m.group(1) + nd + m.group(2) if m.group(0).find(old) > 0 else m.group(0), t, count=1)
    if t != t0:
        wr(path, t); n += 1; print('H-fixed ' + sub + ' len=' + str(len(nd)))
print('H-DONE ' + str(n))
