from pathlib import Path

path = Path('lib/main.dart')
if not path.exists():
    raise SystemExit('lib/main.dart پیدا نشد. این اسکریپت را در پوشه اصلی rooz_app اجرا کن.')

source = path.read_text(encoding='utf-8')
changes = []

old = """      tasks.add(TaskItem(
        id: index + 1,
        title: title,
        date: date,
        createdAt: DateTime.now(),
        reminderAt: reminder,
        category: (raw['category'] as String? ?? 'شخصی').trim().isEmpty
            ? 'شخصی'
            : (raw['category'] as String).trim(),
        repeatWeekdays: weekdays,
      ));"""
new = """      final categoryValue = raw['category'];
      final category = categoryValue is String && categoryValue.trim().isNotEmpty
          ? categoryValue.trim()
          : 'شخصی';

      tasks.add(TaskItem(
        id: index + 1,
        title: title,
        date: date,
        createdAt: DateTime.now(),
        reminderAt: reminder,
        category: category,
        repeatWeekdays: weekdays,
      ));"""
if old in source:
    source = source.replace(old, new, 1)
    changes.append('رفع خطای category تهی در RoozPlanImport')
elif "category: category," in source and "final categoryValue = raw['category'];" in source:
    pass
else:
    raise SystemExit('بخش مورد انتظار RoozPlanImport پیدا نشد؛ فایل تغییری نکرد.')

# Guard the State's context after asynchronous file selection and decoding.
anchor = "      final accepted = await showDialog<bool>(\n        context: context,"
nguard = "      if (!mounted) return;\n\n" + anchor
if anchor in source and "if (!mounted) return;\n\n" + anchor not in source:
    source = source.replace(anchor, nguard, 1)
    changes.append('افزودن mounted check پیش از بازکردن پیش‌نمایش واردکردن فایل')

# Dart's unnecessary_underscores lint recommends reusing `_`.
if '(_, __)' in source:
    source = source.replace('(_, __)', '(_, _)')
    changes.append('اصلاح پارامترهای بی‌استفاده برای lint')

# Remove the specific unused ThemeData local reported by flutter analyze.
if "    final theme = Theme.of(context);\n" in source:
    source = source.replace("    final theme = Theme.of(context);\n", '', 1)
    changes.append('حذف متغیر theme بلااستفاده')

path.write_text(source, encoding='utf-8', newline='\n')
print('اصلاحات اعمال شد:')
for item in changes:
    print(f'- {item}')
if not changes:
    print('- فایل از قبل اصلاح شده بود؛ تغییری لازم نبود.')
