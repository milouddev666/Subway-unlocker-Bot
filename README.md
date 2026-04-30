# بوت تيليجرام Subway Surfers

هذا المشروع عبارة عن بوت تيليجرام مكتوب بلغة Python لتوليد وتعديل ملفات الحفظ الخاصة بلعبة Subway Surfers.
تم تحويل المشروع من نسخة PHP قديمة إلى بوت تيليجرام جاهز للاستخدام والرفع على GitHub والنشر لاحقًا.

## المميزات

- إنشاء ملف `wallet.json`
- إنشاء ملف `characters_inventory.json`
- إنشاء ملف `boards_inventory.json`
- إنشاء ملف `profile_portrait.json`
- إنشاء ملف `profile_frame.json`
- إنشاء ملف `user_stats.json` الخاص بالشارات
- إنشاء ملف `upgrades.json`
- إنشاء ملف `top_run.json` مع ملف `user_stats.json` المرافق
- تعديل الملفات المرفوعة مباشرة من تيليجرام
- دعم فتح كل الشخصيات دفعة واحدة
- دعم فتح كل ألواح التزلج دفعة واحدة
- واجهة عربية داخل البوت مع أزرار مرتبة
- دعم الفهارس بالأرقام عبر `/catalog`

## الأوامر داخل البوت

- `/start`
- `/menu`
- `/help`
- `/catalog <characters|hoverboards|portraits|frames> [page]`
- `/wallet`
- `/characters`
- `/characters_all`
- `/hoverboards`
- `/hoverboards_all`
- `/portraits`
- `/frames`
- `/badges`
- `/upgrades`
- `/toprun`
- `/cancel`

## المتطلبات

قبل التشغيل تأكد من وجود:

- Python 3.11 أو أحدث
- pip
- حساب تيليجرام
- Bot Token من [@BotFather](https://t.me/BotFather)

## إنشاء بوت تيليجرام

1. افتح [@BotFather](https://t.me/BotFather) في تيليجرام.
2. أرسل الأمر `/newbot`.
3. اختر اسمًا للبوت.
4. اختر Username للبوت وينتهي غالبًا بـ `bot`.
5. سيعطيك BotFather توكن مثل:

```text
123456789:AAExampleTokenHere
```

احتفظ بهذا التوكن لأنك ستضعه داخل ملف البيئة `.env`.

## تثبيت المشروع والمكتبات

من داخل مجلد المشروع شغّل:

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

إذا أردت تثبيت نسخة التطوير مع أدوات الفحص والاختبارات:

```bash
pip install -e ".[dev]"
```

## إعداد ملف البيئة

أنشئ ملفًا باسم `.env` في جذر المشروع، أو انسخ من الملف `.env.example`.

مثال:

```env
TELEGRAM_BOT_TOKEN=ضع_توكن_البوت_هنا
BOT_MODE=polling
LOG_LEVEL=INFO
DROP_PENDING_UPDATES=true
ALLOWED_USER_IDS=
CATALOG_CACHE_TTL_SECONDS=3600
REQUEST_TIMEOUT_SECONDS=10
CATALOG_PAGE_SIZE=20
DATA_DIR=data
WEBHOOK_URL=
WEBHOOK_SECRET=
WEBHOOK_LISTEN=0.0.0.0
WEBHOOK_PORT=8080
```

## تشغيل البوت

### تشغيل مباشر

```powershell
python -m subway_bot
```

أو على ويندوز يمكنك استخدام:

```powershell
start.bat
```

### تشغيل عبر Docker

```bash
docker compose up --build -d
```

## كيفية استخدام البوت

بعد تشغيله:

1. افتح البوت في تيليجرام.
2. أرسل `/start`.
3. اختر الخدمة من الأزرار.
4. إذا طلب منك البوت قالبًا، أرسل القيم بنفس أسماء المفاتيح الإنجليزية.
5. سيعيد لك ملف JSON جاهزًا للتحميل.

### مثال للمحفظة

أرسل:

```text
hoverboards=999
gamekeys=999
gamecoins=1000000
scoreboosters=99
headstarts=99
eventcoins=5000
```

### مثال للشخصيات

أرسل:

```text
owned=1-10,15,22
selected=1
```

أو لفتح الجميع:

```text
owned=all
selected=1
```

### مثال للألواح

```text
owned=all
selected=1
```

## الملفات التي يمكن رفعها للتعديل

يمكنك رفع هذه الملفات مباشرة للبوت:

- `wallet.json`
- `characters_inventory.json`
- `boards_inventory.json`

وسيقوم البوت بقراءة الملف وإرجاع قالب جاهز للتعديل.

## مكان وضع الملفات داخل الهاتف

غالبًا المسار يكون:

```text
Android > data > com.kiloo.subwaysurf > files > profile
```

ضع الملفات الناتجة داخل هذا المجلد.

## الرفع على GitHub

إذا كنت ستنشر المشروع على GitHub، نفّذ التالي:

1. لا ترفع ملف `.env` لأنه يحتوي على التوكن.
2. ملف `.gitignore` الحالي يمنع رفع `.env` تلقائيًا.
3. ارفع فقط الكود وملفات الإعداد العامة مثل:
   - `README.md`
   - `requirements.txt`
   - `pyproject.toml`
   - `Dockerfile`
   - `docker-compose.yml`
   - مجلد `subway_bot`
   - مجلد `tests`

### أوامر Git الأساسية

```bash
git init
git add .
git commit -m "Initial Arabic Telegram bot release"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

## تشغيل GitHub Actions

يوجد Workflow داخل:

[`build.yml`](./.github/workflows/build.yml)

يقوم بـ:

- تثبيت Python
- تثبيت التبعيات
- تشغيل `ruff`
- تشغيل `pytest`
- بناء صورة Docker ودفعها عند الـ push

## تثبيت المكتبات يدويًا

إذا كنت تريد معرفة المكتبات الأساسية المستخدمة:

- `python-telegram-bot[webhooks]`

وللتطوير:

- `pytest`
- `ruff`

## ملاحظات مهمة

- لا ترفع التوكن إلى GitHub أبدًا.
- إذا رفعت التوكن بالخطأ، ادخل إلى BotFather وغيّره فورًا.
- واجهة البوت أصبحت عربية، لكن مفاتيح القوالب مثل `owned` و `selected` و `gamecoins` تبقى بالإنجليزية حتى تبقى متوافقة مع منطق الكود.
- أوامر فتح الجميع متوفرة الآن للشخصيات والألواح.
