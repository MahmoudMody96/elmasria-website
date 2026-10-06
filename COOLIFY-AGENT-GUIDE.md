# دليل الوكيل للتعامل مع Coolify — الإنتاج الحقيقي

> لمن يفّذ؟ أي وكيل/مساعد AI هيشتغل على سيرفر الإنتاج `169.58.65.43` أو منصة الديمو.
> كل قاعدة في الملف دي مدفوعة الثمن — وقعت فعلًا وعلّمنا ساعات. لا تعيد اكتشافها.

---

## 1) بطاقة تعريف البيئة (احفظها)

| العنصر | القيمة |
|---|---|
| الخادم | `ubuntu@169.58.65.43` (Contabo, Ubuntu 24.04) |
| SSH | `ssh -F /dev/null -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 ubuntu@169.58.65.43` |
| ملاحظة `-F /dev/null` | **إلزامية على Linux** — علامة BOM في `~/.ssh/config` بتكسر OpenSSH بدونها. **على Windows لا يوجد `/dev/null`**: احذف `-F` تمامًا واستخدم `-o UserKnownHostsFile=NUL` |
| Coolify | `https://coolify.aidy.site` (v4.3.23 — متحقق 2026-09-27 عبر وسم الصورة) — API: `https://coolify.aidy.site/api/v1` |
| ⚠️ أسماء الحاويات | **`coolify` و`coolify-db` ليست أسماء ثابتة** — حاوية التطبيق وقاعدة البيانات بأسماء Coolify عشوائية تتغير مع النشر. حدّدها ديناميكيًا بالصورة (انظر فخ 17). الثابت فقط: `coolify-proxy` و`coolify-sentinel` |
| البروكسي | حاوية `coolify-proxy` = **Traefik v3.6** — مالك بورتات 80/443 |
| الـ dynamic config | `/data/coolify/proxy/dynamic/` على الخادم = `/traefik/dynamic/` داخل الحاوية |
| منصة الديمو | تطبيق UUID `dn8njwsop4hbviehs90o6o8t` — registry محلي `127.0.0.1:5000/demoplat` |
| ن8ن | خدمة UUID `cyhw0supg8pncp7yu3nb18d9` — **لا تعبث بشبكتها** (شبكة `cyhw0...` منفصلة عن `coolify` بلا قصد) |

**قاعدة API الذهبية**: استخدم `https://coolify.aidy.site/api/v1` فقط. متغير البيئة `COOLIFY_API_URL` المحلي قد يشير إلى مضيف `sslip.io` قديم راوتر راح — فطلبه يرجع `404 page not found` ولا علاقة لذلك بـ Coolify نفسه.

---

## 2) بنية التوجيه — افهمها قبل أن تلمس شيئًا

```
الإنترنت → Traefik (coolify-proxy)
              ├─ Docker provider: راوترات مولّدة من labels حاويات Coolify
              └─ File provider: ملفات /data/coolify/proxy/dynamic/*.yaml
                    ├─ coolify.yaml      ← لوحة التحكم (لا تعدّله)
                    └─ aidy-wildcard.yaml ← صائد *.aidy.site للديمو (النصف الآخر في الريبو)
```

- الراوترات الحرفية (`demo.aidy.site`, `sender.aidy.site`…) تأتي من **labels التطبيقات** وتفوز دائمًا.
- `aidy-wildcard.yaml` له `priority: 1` — يلتقط ما لم يطالبه أحد: أي `سب-دومين.aidy.site` جديد **بدون أي إعداد** لأنه يقع فيه.
- خلفية الراوتر الويلدكارد = **اسم حاوية الديمو حرفيًا**، واسم الحاوية يتغير مع كل نشر — لهذا توجد الخطوة 6 في `scripts/deploy.mjs`.

---

## 3) الفخاخ التي وقعنا فيها — احذرها حرفيًا

### 🔱 فخاخ Traefik v3.6
1. **`Host(...) || HostRegexp(...)` في راوتر واحد = الشيطان**: v3.6 يطنّش جزء الـ HostRegexp من زوج OR بصمت — الراوتر "يعمل" للجزء الحرفي و404 للباقي. لا تصدّق نجاحًا جزئيًا.
2. **`{placeholder:.+}` داخل ملف YAML يُحلّل نظيفًا ولا يطابق أبدًا**: صيغة الـ placeholder تعمل في docker labels وتفشل في الملفات. في الملفات اكتب **regex خام**: `` HostRegexp(`[a-z0-9-]+[.]aidy[.]site`) `` — والنقطة `[.]` أوضح من `\.`.
3. **راوتر TLS لا يمكن اشتقاق شهادة من قاعدته يُرمى كاملًا مع ميدل-ويره وخدمته**: مرجعية `middleware@docker` أو `service@docker` من ملف الـ file provider حين يكون مصدرها الحاوية المسقطة = "does not exist". اجعل ملفاتك **مكتفية ذاتيًا**: ميدل-وير وخدمة خاصة بها، صفر إشارات لـ `@docker`.
4. **`Router defined multiple times with different configurations`**: حاويتان شغالتان بنفس اسم الراوتر (تداخل نشرات). Traefik يرمي الراوتر كله حتى زوال التداخل — أوقف القديمة أو انتظر اكتمال النشر.
5. **الاختبار الداخلي عبر 127.0.0.1 يضلّلك في TLS**: SNI المرسل يكون `127.0.0.1` فلا يطابق قيود شهادات الراوترات. اختبر من السيرفر بـ `curl --resolve domain:443:127.0.0.1` ليمرّ SNI صحيح.

### 🎭 فخاخ Coolify
6. **`ports_exposes` لا تساوي البورت الفعلي**: تحقق دائمًا من التطبيق نفسه `curl http://<container-IP>:<port>/`. و**`custom_labels` (base64) في إعدادات التطبيق يتغلب على كل شيء** — لو الراوتر يوجّه لبورت غلط، فُكّ التشفير وافحصه قبل أي شيء آخر.
7. **النشر من واجهة Coolify UI يترك خلفية الراوتر الويلدكارد على الحاوية القديمة** → كل `*.aidy.site` يقع 502 رغم أن التطبيق healthy. انشر دائمًا بـ `node scripts/deploy.mjs`، أو شغّل خطوة 6 يدويًا بعد أي نشر UI.
8. **ملف `dynamic/` قد يختفي ويُعاد توليده أثناء نشاط Coolify** — لا تشخّص من لقطة واحدة؛ أعد الفحص بعد ثوان.

### 🔑 فخاخ قواعد البيانات
9. **اختبار كلمة المرور عبر 127.0.0.1 داخل حاوية Postgres = عديم القيمة**: قاعدة `trust` تغطي الـ localhost فأي كلمة مرور تنجح. اختبر المصادقة الفعلية بالاتصال **بعنوان IP الحاوية** (يسقط على `scram-sha-256`).
10. `POSTGRES_PASSWORD` في الـ env يعمل فقط عند أول initdb — **تغييره لا يغيّر كلمة مرور موجودة**؛ استخدم `ALTER ROLE` ثم حدّث الـ env ثم أعد التشغيل.

### 🔒 فخاخ عامة
11. كل شيء تحت `/data/coolify/` يحتاج `sudo` والمجلدات مملوكة لـ uid 9999 — نسّق الملفات الجديدة `chown 9999:root`.
12. لا تكتب أسرارًا في مستودع الكود **أبدًا** — لا حتى "مؤقتًا". `.env` و`backups/` مستثناة في `.gitignore` عمدًا.
13. `docker system prune -a -f` يمسح الصور بما فيها التي يعتمد عليها الـ registry المحلي — لا تشغّله عشوائيًا.
14. **ملفات CRLF من Windows تكسر bash على السيرفر بصمت** (اتكشف 2026-09-27): أي سكربت `.sh` مكتوب من Windows يحمل `\r` في نهايات الأسطر فيفشل الـ pipe والـ redirect وقوالب Go ويلصق `\r` بأسماء الأوامر (`id\r: command not found`). القاعدة: **نفّذ أوامر SSH كـ arguments مباشرة** (سطر واحد بسيط)، ولو لزم ملف سكربت فحوّله لـ LF أولًا.
15. **ممنوع piping سكربت عبر stdin من PowerShell** (`Get-Content x.sh | ssh ... 'bash -s'`): الـ pipeline يعيد حقن CRLF حتى لو الملف LF. البديل: نفس الأمر كـ argument مباشر.
16. **باكتيك Traefik عبر PowerShell** (اتكشف 2026-09-27): قاعدة `Host(`example.com`)` تحتاج باكتيك حرفيًا عند bash البعيد. من PowerShell ضع الأمر كله بين `"..."` وضاعف الباكتيك (`` `` ``) وغلّف كل `-l` بمفردات `'...'` — PowerShell يأكل علامات التنصيص الخارجية عند استدعاء الأوامر الأصلية، فالمفردات الداخلية هي ما يحمي الباكتيك.
17. **لا تعتمد اسم حاوية — حدّده بالصورة** (اتكشف 2026-09-27): `sudo docker ps --format '{{.Names}}={{.Image}}'` ثم اختر بالصورة (`coollabsio/coolify:*` للتطبيق، `postgres:*` للقاعدة). الأسماء العشوائية تتغير مع كل rolling، والثابت منها فقط `coolify-proxy` و`coolify-sentinel`.
18. **اقتباس PowerShell عند تمرير أوامر SSH (اتكشف 2026-09-28 أثناء نشر elmasria)**: من ويندوز اتبع هذه الأربعة بدقة:
    - ضع الأمر البعيد **كله في سلسلة واحدة**: `ssh host 'remote cmd'` — علامات التنصيص **المفردة** تنجو حتى bash البعيد، أما **المزدوجة `"` فتُبتلع** فيصل الأمر مبتورًا للسيرفر.
    - لذلك لا تمرّر قوالب Go بعلامات مزدوجة: `--format "{{.Names}}"` ⟶ `template parsing error: template: :1: unclosed action`، وبالمفردة `--format '{{.Names}}'` تعمل. (نفس الدرس في §8 بصيغة أخرى.)
    - `$(...)` و`$VAR` **تُفسَّر محليًا** داخل سلسلة PowerShell المزدوجة: جملة `IP=$(sudo docker inspect ...)` نفّذت `sudo` على **ويندوز** نفسها ("Sudo is disabled on this machine") ورجعت فراغًا فصار الفحص `direct=000` — نتيجة مضلِّلة تمامًا. الحل: سلسلة PowerShell مفردة `'...'` (ومعها `''` لمفردة داخلية)، أو استبدل القوالب بـ`curl`/`grep` مباشرة.
    - مسار المفتاح لا يتوسّع داخل سلسلة مفردة: `-i $HOME\.ssh\id_ed25519` يفشل ⟶ اكتب المسار الكامل `-i C:\Users\<user>\.ssh\id_ed25519`.
19. **`reset()` بلا متغيّر يفشل في PHP 8** (اتكشف 2026-10-06 أثناء مراقبة نشر elmasria): `reset($data["deployments"] ?? [])` خطأ قاتل فورًا (`Argument #1 could not be passed by reference`) لأن `reset` تأخذ مرجعًا ولا تقبل تعبيرًا. اسكربتات المراقبة عبر `docker exec coolify php` تُخرج **لا شيء مع exit 255** بلا رسالة — بداية مضمونة لضياع الوقت. الصحيح: خزّن التعبير في متغيّر أولًا (`$deps = $data["deployments"] ?? []; $first = $deps ? $deps[0] : [];`) وشغّل أول اختبار بـ`php -d display_errors=1`.
20. **`curl.exe -o NUL` من Git Bash ينشئ ملفًا فعليًا اسمه `NUL` في الريبو** (اتكشف 2026-10-06): أمر صالح في PowerShell يتحول في Git Bash إلى إنشاء ملف عادي (~94 بايت)، و`git add -A` كاد يدفعه (`short read while indexing NUL`). القاعدة: من Git Bash استخدم `-o /dev/null`، وقبل أي `git add -A` راجع `git status --short` وأي `??` شارد.

---

## 4) التشخيص: من العرَض إلى السبب

### القاعدة الأولى: ميّز 404 عن 502 — هما عالمان مختلفان تمامًا

| العرَض | المعنى | أين الخطأ |
|---|---|---|
| `404` **نص عادي** بطول 19 بايت ("404 page not found") | لا يوجد راوتر طابق الطلب إطلاقًا | مشكلة توجيه: ملف/labels/قاعدة |
| `404` **بمحتوى HTML كبير** (5KB+) | التطبيق وصل ورفض بنفسه (slug غير موجود) | طبيعي للديمو — ليس عطلًا |
| `502` | راوتر طابق لكن الخلفية لا ترد | الحاوية/البورت/الشبكة |

### سيناريو: كل `*.aidy.site` فجأة 404 نصي
```bash
# 1) هل خلفية الويلدكارد على حاوية حية؟
ssh ... 'sudo grep "url:" /data/coolify/proxy/dynamic/aidy-wildcard.yaml
         sudo docker ps --format "{{.Names}}" | grep dn8njwsop4hbviehs90o6o8t'
# الاسم في الملف ≠ الاسم الحي؟ هذا هو السبب. حدّث السطر (sed) — Traefik يلتقطه ساخنًا.
# 2) سجلات البروكسي:
ssh ... 'sudo docker logs coolify-proxy --since 30m 2>&1 | grep -i error'
# 3) تأكد أن الملف ما زال موجودًا في dynamic/ (أحيانًا يُعاد توليد المجلد)
```

### سيناريو: تطبيق واحد 502
```bash
# 1) الحاوية شغالة؟ على شبكة coolify؟
ssh ... 'sudo docker inspect <c> --format "{{.State.Status}} {{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}"'
# 2) البورت المعلن = البورت الحي؟
ssh ... 'IP=$(sudo docker inspect <c> --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}")
         curl -s -o /dev/null -w "%{http_code}" http://$IP:3000/   # جرّب البورتات المرشحة'
# لا يوجد شيء يسمع على البورت المعلن؟ الحل من إعدادات التطبيق في Coolify
# (ports_exposes أو custom_labels المشفرة base64) ثم إعادة نشر.
```

### سيناريو: راوتر بعينه مكسور
```bash
ssh ... 'sudo docker logs coolify-proxy --since 1h 2>&1 | grep -iE "error" | grep <app-name>'
# خطأ parse في الـ rule = الراوتر ميت والباقي سليم — أصلح صيغة القاعدة في مصدرها.
```

### قاعدة التنفيذ: غيّر شيئًا واحدًا → تحقق → سجّل
```bash
# مصفوفة التحقق بعد أي تغيير توجيه (من السيرفر، SNI صحيح):
for u in https://noor-dental.aidy.site/ https://coolify.aidy.site/api/health; do
  curl -sk -o /dev/null -w "%{http_code} $u\n" --max-time 15 "$u"
done
# ثم من جهازك عبر DNS الحقيقي — النتيجة الداخلية وحدها ليست دليلًا.
```

---

## 5) إجراءات التشغيل الراسخة

### نشر منصة الديمو (الطريقة الوحيدة الصحيحة)
```bash
cd "D:\MAHMOUD\projects\منصة الديمو"
node scripts/deploy.mjs --dry-run   # جافًا أولًا — دائمًا
node scripts/deploy.mjs             # يختار الوسم، يبني، ينشر، ويصلح الراوتر (خطوة 6)
```
السكربت نفسه يصرخ لو الشهادة على وشك الانتهاء (تنبيه لا حاجز) ويختار وسمًا جديدًا تلقائيًا — إعادة استخدام وسم = فشل صامت كامل (Coolify "يرى الصورة موجودة" ولا يسحبها).

### تدوير سر في خدمة Coolify (النمط المجرب على ن8ن)
1. حدّث القيمة عبر `PATCH /api/v1/services/{uuid}/envs` بقاعدة `{key, value}` — المتغيرات المركبة (`$SERVICE_...`) تتحدث تلقائيًا.
2. `ALTER ROLE` جوه حاوية القاعدة **مباشرةً** — الـ env وحده لا يغيّر كلمة موجودة.
3. أعد تشغيل الخدمة (`POST /api/v1/services/{uuid}/restart`) وتحقق: الحاويات healthy + `healthz` + صفر أخطاء مصادقة + اختبار القديمة يجب أن **يفشل** عبر IP الحاوية (لا عبر 127.0.0.1!).

### إضافة/تعديل توجيه في ملف الـ file provider
1. عدّل `/data/coolify/proxy/dynamic/<file>.yaml` مع `chown 9999:root`.
2. Traefik يراقب المجلد ويطبق ساخنًا — لا restart للبروكسي إلا كخطوة أخيرة.
3. راجع السجلات فورًا: أي خطأ في الملف يُطبع خلال ثوان.
4. حدّث نسخة الريبو (`traefik-aidy-wildcard.yaml`) في نفس الـ commit — السيرفر والريبو توأمان.

---

## 6) الخطوط الحمراء (ممنوع نهائيًا)

- ❌ تعديل `coolify.yaml` أو ملفات n8n أو حذف أي volume — إلا بطلب صريح من المالك في هذه الجلسة.
- ❌ تشغيل `prune`/`rm -rf` على شيء لم تفحصه بنفسك قبل ثوان.
- ❌ تخمين: لا تنفذ على الإنتاج شيئًا لم تقرأ توثيقه — جرّب `--dry-run` أو على حاوية اختبار مؤقتة (واحذفها فورًا).
- ❌ ترك حاوية اختبار أو ملف مؤقت بعد انتهاء مهمتك.
- ❌ الكتابة في المستودع بدون تشغيل `npm test` أولًا.
- ❌ نشر أسرار في الكود أو الشات — كلمات المرور تبقى في Coolify/الخادم وحدهما.

## 7) عند الشك

**اقرأ سجلات البروكسي أولًا** (`docker logs coolify-proxy`) — هي تحكي الحقيقة كلها: من طابق، من فشل ولماذا. ثم اختبر من الداخل ثم من الخارج. **غيّر شيئًا واحدًا في كل مرة**، ولو انتهت الجلسة ومهمة ناقصة — وثّقها في آخر رسالة للمالك بما فيها "ما الذي سيكسر لو نُشر الآن".

---

## 8) النشر عبر API — المسارات الصحيحة (درّس 2026-09-09، نشر sender-premium)

> المرجع: `routes/api.php` على فرع `main` في `coollabsio/coolify` — لا تخمّن المسارات، ارجع للمصدر.

| العملية | المسار الصحيح | ملاحظة |
|---|---|---|
| نشر تطبيق (build + start) | `POST /api/v1/deploy` بجسم `{"uuid":"<app-uuid>"}` | يحتاج صلاحية `deploy` على التوكن — بدونه 403 |
| حالة نشر واحد | `GET /api/v1/deployments/{deployment_uuid}` | حقل `status`: `in_progress`/`finished`/`failed` + `commit` |
| نشرات تطبيق | `GET /api/v1/deployments/applications/{app-uuid}` | الأحدث أولًا |
| إيقاف/تشغيل/إعادة | `POST /api/v1/applications/{uuid}/stop|start|restart` | الـ restart يشغّل **الصورة الموجودة** — لا يبني جديدًا |
| إلغاء نشر عالق | `POST /api/v1/deployments/{uuid}/cancel` | |

**فخاخ مدفوعة الثمن:**
- ❌ `POST /api/v1/applications/{uuid}/deploy` **غير موجود أصلًا** (404 مؤكد) — الصح `POST /api/v1/deploy` بالـ uuid في الجسم.
- ❌ توكن بلا صلاحية `deploy` يقرأ كل شيء ويفشل صامتًا/403 عند النشر — تحقق من الصلاحيات قبل ما تلوم الشبكة.
- ⚠️ بعد rolling فاشل قد **لا توجد حاوية أصلًا** (`docker ps -a | grep sender` فاضي) — الإنتاج واقع تمامًا، والنشر الجديد يبني من الصفر (~11 دقيقة) بلا سباق قفل.
- ⚠️ من PowerShell: قوالب Go (`--format "{{.Names}}"`) تنكسر في الـ quoting — استخدم `docker ps -a | grep <name>` plain بلا templates.

**تسلسل النشر الآمن عبر API (sender-premium، مجرّب 2026-09-09):**
1. `GET /api/v1/applications/{uuid}` → سجّل `status` (لو `exited` ولا حاوية = انشر مباشرة، لا Stop لازم).
2. `POST /api/v1/deploy` → خزّن `deployment_uuid`.
3. راقب `GET /api/v1/deployments/{uuid}` كل ~5 دقائق حتى `finished` (البناء الكامل ~11 دقيقة: حزم الويب ~7 صامتة).
4. تحقق: `curl -s https://sender.aidy.site/health` → `version` الجديدة + `db:true`.

---

## ٨.١ الحصول على توكن API (لو مش موجود — بيتولَّد من السيرفر)

التوكن **مش مخزَّن** على السيرفر ولا في بيئة الجلسة. لو `curl` بيرجّع **401** يبقى لازم تولّد واحد — والسكربت `~/create-token.php` الموجود على السيرفر **مش بيشتغل زي ما هو** (وقد يكون اتمسح أصلًا ضمن النظافة — توليده من الصفر أدناه يغني عنه). فخّان مدفوعان الثمن (اتكشفوا 2026-09-21):

1. **`createToken` محتاج session.** في Coolify 4.3.23 (`app/Models/User.php:237`) الدالة بتقرا `session('currentTeam')->id`. في CLI مفيش session → `Attempt to read property "id" on null`. لازم تسبقها بـ `session(['currentTeam' => $team])`.
2. **لازم يتشغّل جوّه حاوية تطبيق Coolify** مش على المضيف — واسمها **عشوائي ومتغير** (ليست `coolify` الثابتة). عندها PHP 8.4 + التطبيق كامل في `/var/www/html` (`artisan` · `vendor/` · `bootstrap/`). حدّد الحاوية الحية بالصورة أولًا:
```bash
sudo docker ps --format '{{.Names}}={{.Image}}'   # دوّر على سطر coollabsio/coolify:*
# مثال: APP=49oolwkj7ramow4c6xn2yscs — استخدم الاسم الحي في كل أوامر cp/exec أدناه
```
3. **وكلاء Windows**: لا تكتب سكربت الـ heredoc في ملف `.sh` (CRLF — انظر فخ 14). الصق الأوامر كـ arguments مباشرة، أو أنشئ ملف PHP عبر `echo <base64>` (الـ base64 سطر واحد بلا مسافات فيمرّ نظيفًا).

```bash
# الإيميل الصحيح يُجلب من القاعدة مباشرة (قراءة فقط، لا يطبع في الشات إلا للضرورة):
# sudo docker exec <postgres-الحية-بالاسم-الديناميكي> psql -U coolify -d coolify -tAc "select email from users;"
# عرّف APP باسم حاوية coollabsio/coolify:* الحية قبل المتابعة:
# APP=$(sudo docker ps --format '{{.Names}}={{.Image}}' | grep 'coollabsio/coolify:' | cut -d= -f1)
cat > /tmp/create-token2.php <<'PHP'
<?php
require __DIR__ . '/vendor/autoload.php';
$app = require __DIR__ . '/bootstrap/app.php';
$app->make('Illuminate\Contracts\Console\Kernel')->bootstrap();
$user = \App\Models\User::where('email','<owner-email>')->first();
if (!$user) { fwrite(STDERR, "User not found\n"); exit(1); }
$team = $user->teams()->first() ?: \App\Models\Team::find($user->current_team_id) ?: \App\Models\Team::first();
session(['currentTeam' => $team]);          // ← الفخ الأول
echo $user->createToken('cli-api')->plainTextToken . "\n";
PHP
sudo docker cp /tmp/create-token2.php $APP:/var/www/html/create-token2.php   # $APP = الاسم الحي، ليست "coolify"
sudo docker exec $APP php /var/www/html/create-token2.php > /tmp/tok.out   # للملف، مش للشات
sudo docker exec $APP rm -f /var/www/html/create-token2.php
chmod 600 /tmp/tok.out && rm -f /tmp/create-token2.php
# اختبار سريع (HTTP 200 = التوكن شغال)
T=$(cat /tmp/tok.out)
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $T" \
  https://coolify.aidy.site/api/v1/applications
```

**نظافة إلزامية بعد ما تخلص** — §6 بتقول مفيش أسرار في الكود/الشات، وده يمتد إنك **متسيبش ملف توكن مركون على السيرفر**:

```bash
rm -f /tmp/tok.out
# إلغاء التوكن من القاعدة — باسم التوكن المستخدم (مثال cli-api)، عبر حاوية postgres الحية:
# sudo docker exec <postgres-الحية> psql -U coolify -d coolify -tAc \
#   "delete from personal_access_tokens where name='cli-api';"
```

> 🧠 **درس 2026-09-21 (من sender-premium)**: تنظيف الأسرار **في الريبو لوحده مش كفاية**. لقينا توكن MCP حيّ نصًّا في **نسخة يدوية قديمة** من الريبو مركونة في `/home/ubuntu/` على سيرفر الإنتاج — فلتت لأن كل المراجعات فحصت الريبو المحلي بس، ومحدش فحص **أهداف النشر**. القاعدة: **الفحص لازم يغطي السيرفرات والمخازن والأحجام**، ويكون **بالحمولة (`aud`/`iss`) مش برأس التوكن** — رأس `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9` مشترك بين كل توكنات HS256 ومبيعملش إلا ضجيج (7 ملفات بريئة في فحص واحد).

---

## 9) النشر اليدوي لموقع ثابت — النمط المجرّب (elmasria، 2026-09-27)

> متى؟ موقع ثابت (HTML/CSS/JS) تحتاج له رابط staging سريعًا **دون** إنشاء تطبيق Coolify ودون توكن API ودون المساس بأي راوتر قائم. النمط: صورة nginx في الريجستري المحلي + حاوية مستقلة + راوترات حرفية من labels (تفوز على الويلدكارد تلقائيًا).

### المتطلبات المسبقة (كلها متحققة على هذا السيرفر)
- الريبو public على GitHub + فيه `Dockerfile` (nginx:alpine) و`nginx.conf` (مع `error_page 404 /404.html`)
- الريجستري المحلي `127.0.0.1:5000` شغال (`nullbox-registry`)
- شبكة `coolify` موجودة (شبكة كل التطبيقات)
- DNS: أي `*.aidy.site` يحلّ لـ `169.58.65.43` — تحقق بـ `nslookup <name>.aidy.site` من جهازك
- `certresolver` المستخدم على الصندوق: `letsencrypt` — تحقق من labels أي تطبيق حي قبل النسخ

### التسلسل (أوامر SSH مباشرة — لا ملفات `.sh` من Windows، فخ 14)
```bash
# 1) بناء ودفع (وسم جديد كل نشر — لا تعيد استخدام وسم، نفس درس deploy.mjs)
rm -rf /tmp/<app>-build
git clone --depth 1 https://github.com/<org>/<repo>.git /tmp/<app>-build
sudo docker build -t 127.0.0.1:5000/<app>:1 /tmp/<app>-build
sudo docker push 127.0.0.1:5000/<app>:1
rm -rf /tmp/<app>-build          # نظافة: لا تترك نسخة الكود على السيرفر
# 2) تشغيل (أسماء الراوترات/الخدمات فريدة — فخ 4)
sudo docker rm -f <app>-web      # تجاهل خطأ "No such container" أول مرة
sudo docker run -d --name <app>-web --restart unless-stopped --network coolify \
  -l 'traefik.enable=true' \
  -l 'traefik.http.routers.http-<app>.entryPoints=http' \
  -l 'traefik.http.routers.http-<app>.middlewares=redirect-to-https' \
  -l 'traefik.http.routers.http-<app>.rule=Host(`<app>.aidy.site`)' \
  -l 'traefik.http.routers.http-<app>.service=http-<app>' \
  -l 'traefik.http.routers.https-<app>.entryPoints=https' \
  -l 'traefik.http.routers.https-<app>.middlewares=gzip' \
  -l 'traefik.http.routers.https-<app>.rule=Host(`<app>.aidy.site`)' \
  -l 'traefik.http.routers.https-<app>.service=https-<app>' \
  -l 'traefik.http.routers.https-<app>.tls=true' \
  -l 'traefik.http.routers.https-<app>.tls.certresolver=letsencrypt' \
  -l 'traefik.http.services.http-<app>.loadbalancer.server.port=80' \
  -l 'traefik.http.services.https-<app>.loadbalancer.server.port=80' \
  127.0.0.1:5000/<app>:1
```
> ⚠️ سطر الـ rule فيه باكتيك — من PowerShell ضع الأمر كله بين `"..."` وضاعف الباكتيك (`` `` ``) وغلّف كل `-l` بمفردات (فخ 16).

### مصفوفة التحقق (بالترتيب — توقف عند أول فشل)
1. `sudo docker inspect <app>-web | grep -i -m2 IPAddress` → خذ IP الحاوية
2. `curl -s -o /dev/null -w "%{http_code}" http://<IP>/` → لازم `200` (يثبت الحاوية والمنفذ)
3. `sudo docker logs coolify-proxy --since 3m | grep -i <app>` → لازم **صفر أخطاء** (يثبت سلامة الراوتر والميدل-وير)
4. `curl -sk -o /dev/null -w "%{http_code}" --resolve <app>.aidy.site:443:127.0.0.1 https://<app>.aidy.site/` → لازم `200` (يثبت SNI+TLS+الخلفية — فخ 5)
5. من جهازك عبر DNS الحقيقي: افتح الصفحة واقرأ المحتوى — النتيجة الداخلية وحدها ليست دليلًا

### حدود النمط (مقصودة)
- الحاوية **خارج إدارة Coolify**: لا تظهر في اللوحة ولا تتحدث تلقائيًا — للتحديث ابنِ وسمًا جديدًا وأعد إنشاءها بنفس الأمر.
- للدومين النهائي (مثال `example.com`): يلزم سجل DNS من نوع A إلى `169.58.65.43` أولًا، ثم كرر نفس الـ labels بالدومين الجديد (راوتران إضافيان أو استبدال).

---

## ٩.١ الثوابت الفعلية لموقع elmasria (هذا المستودع) — لا تخمّنها

| العنصر | القيمة |
|---|---|
| الدومين المؤقت (staging) | `https://elmasria.aidy.site` |
| الحاوية | `elmasria-web` — شبكة `coolify` — `--restart unless-stopped` |
| الصورة | `127.0.0.1:5000/elmasria:<N>` — الأوسمة المستخدمة: `1` ثم `2` ثم `3`… **وسم جديد كل نشر** |
| أسماء الراوترات | `http-elmasria` و`https-elmasria` (الخدمتان بنفس الاسم، بورت الخلفية `80`) |
| الـ labels الكاملة | هي حرفيًا الموجودة في §9 مع `<app>` = `elmasria` — تحقق منها بـ `sudo docker inspect elmasria-web | grep -i traefik` قبل أي إعادة إنشاء |
| مصدر الكود على السيرفر | `git clone --depth 1 https://github.com/MahmoudMody96/elmasria-website.git` (public — لا توكن مطلوب) |
| `healthcheck`؟ | لا يوجد — nginx بسيط؛ التحقق بكود الـ HTTP |

**تسلسل النشر الكامل (Windows/PowerShell — لا تعيد استخدام وسم قديم):**
```powershell
# 1) ارفع الكود أولًا — السيرفر يبني من GitHub لا من جهازك
cd "D:\MAHMOUD\projects\موقع شركة المصرية للسلامة والصحة المهنية"; git push origin main

# 2) ابنِ على السيرفر: clone → build → push → نظافة (استبدل 3 بالوسم التالي)
ssh -o UserKnownHostsFile=NUL -i $HOME\.ssh\id_ed25519 ubuntu@169.58.65.43 "rm -rf /tmp/elmasria-build && git clone --depth 1 https://github.com/MahmoudMody96/elmasria-website.git /tmp/elmasria-build && sudo docker build -t 127.0.0.1:5000/elmasria:3 /tmp/elmasria-build && sudo docker push 127.0.0.1:5000/elmasria:3 && rm -rf /tmp/elmasria-build"

# 3) أعد إنشاء الحاوية بنفس الـ labels وبالوسم الجديد (الباكتيك مضاعف — فخ 16)
ssh -o UserKnownHostsFile=NUL -i $HOME\.ssh\id_ed25519 ubuntu@169.58.65.43 "sudo docker rm -f elmasria-web; sudo docker run -d --name elmasria-web --restart unless-stopped --network coolify -l 'traefik.enable=true' -l 'traefik.http.routers.http-elmasria.entryPoints=http' -l 'traefik.http.routers.http-elmasria.middlewares=redirect-to-https' -l 'traefik.http.routers.http-elmasria.rule=Host(``elmasria.aidy.site``)' -l 'traefik.http.routers.http-elmasria.service=http-elmasria' -l 'traefik.http.routers.https-elmasria.entryPoints=https' -l 'traefik.http.routers.https-elmasria.middlewares=gzip' -l 'traefik.http.routers.https-elmasria.rule=Host(``elmasria.aidy.site``)' -l 'traefik.http.routers.https-elmasria.service=https-elmasria' -l 'traefik.http.routers.https-elmasria.tls=true' -l 'traefik.http.routers.https-elmasria.tls.certresolver=letsencrypt' -l 'traefik.http.services.http-elmasria.loadbalancer.server.port=80' -l 'traefik.http.services.https-elmasria.loadbalancer.server.port=80' 127.0.0.1:5000/elmasria:3"
```

**تحقق سريع بعد كل نشر (بعد ثوانٍ من إعادة الإنشاء):**
```powershell
# ⚠️ من PowerShell: كل أمر ssh في سلسلة واحدة، وممنوع التنصيص المزدوج داخلها (فخ 18)
# من السيرفر (SNI صحيح — فخ 5):
ssh ... 'curl -sk -o /dev/null -w "%{http_code}\n" --resolve elmasria.aidy.site:443:127.0.0.1 https://elmasria.aidy.site/'
# من جهازك عبر DNS الحقيقي + تأكيد أن الأصول الجديدة وصلت (?v= في CSS + الأيقونات):
curl.exe -s -o NUL -w "%{http_code}\n" https://elmasria.aidy.site/
curl.exe -s https://elmasria.aidy.site/ | Select-String 'style.css?v='
curl.exe -s -o NUL -w "%{http_code}\n" https://elmasria.aidy.site/assets/img/icons.svg
```

> ملاحظتان خاصتان بهذا الموقع:
> 1. أي تعديل على `assets/css/style.css` **أو** `assets/js/main.js` يلزمه `python _tools/bump_css_version.py` قبل الكوميت (السكربت يرفع إصدار الملفين تلقائيًا)، وإلا يبقى الملف القديم في كاش المتصفح (`expires 7d` في `nginx.conf`).
> 2. `_tools/` وملفات التوثيق `.md` و`.git` **مستثناة في `.dockerignore`** فلا تُنشر على الدومين.
