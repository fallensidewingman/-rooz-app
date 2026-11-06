from pathlib import Path
from datetime import datetime
import base64
import re
import shutil
import sys

ROOT = Path.cwd()
MAIN = ROOT / 'lib' / 'main.dart'
PUBSPEC = ROOT / 'pubspec.yaml'


def fail(message: str) -> None:
    print(f'ERROR: {message}', file=sys.stderr)
    raise SystemExit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f'{label}: expected exactly one match, found {count}. No files were changed.')
    return text.replace(old, new, 1)


if not MAIN.exists() or not PUBSPEC.exists():
    fail('Run this script from the Rooz project root (the folder containing pubspec.yaml and lib/main.dart).')

main = MAIN.read_text(encoding='utf-8')
pubspec = PUBSPEC.read_text(encoding='utf-8')

if 'class RoozPlanImport' in main or 'file_picker:' in pubspec:
    fail('The Rooz import/recurrence update seems to be already installed. I stopped to avoid applying it twice.')

# 1) Dependency and imports.
main = replace_once(
    main,
    "import 'dart:math' as math;\n",
    "import 'dart:math' as math;\n\nimport 'package:file_picker/file_picker.dart';\n",
    'file_picker import',
)
pubspec = replace_once(
    pubspec,
    '  flutter_localizations:\n    sdk: flutter\n',
    '  flutter_localizations:\n    sdk: flutter\n  file_picker: ^13.3.2\n',
    'file_picker dependency',
)
pubspec = replace_once(pubspec, 'version: 1.1.1+3', 'version: 1.2.0+4', 'app version bump')

# 2) Backward-compatible task model with independent completion per recurring date.
start = main.find('class TaskItem {')
end = main.find('class TaskStore {', start)
if start < 0 or end < 0:
    fail('Could not locate TaskItem model. No files were changed.')
model = r'''class TaskItem {
  const TaskItem({
    required this.id,
    required this.title,
    required this.date,
    required this.createdAt,
    this.reminderAt,
    this.isDone = false,
    this.category = 'شخصی',
    this.repeatWeekdays = const [],
    this.completedDates = const [],
    this.occurrenceDate,
  });

  final int id;
  final String title;
  /// For a recurring task, this is the first active date of the series.
  final DateTime date;
  final DateTime createdAt;
  final DateTime? reminderAt;
  final bool isDone;
  final String category;
  /// DateTime.weekday values: Monday = 1 ... Sunday = 7.
  final List<int> repeatWeekdays;
  /// Completion dates for recurring tasks, stored as yyyy-MM-dd.
  final List<String> completedDates;
  /// Temporary calendar projection; it is never saved to JSON.
  final DateTime? occurrenceDate;

  bool get isRecurring => repeatWeekdays.isNotEmpty;
  DateTime get displayDate => occurrenceDate ?? date;

  bool occursOn(DateTime value) {
    final day = _dateOnly(value);
    if (day.isBefore(_dateOnly(date))) return false;
    if (!isRecurring) return DateUtils.isSameDay(date, day);
    return repeatWeekdays.contains(day.weekday);
  }

  bool isDoneOn(DateTime value) {
    if (!isRecurring) return isDone;
    return completedDates.contains(_dateKey(value));
  }

  TaskItem forDate(DateTime value) {
    final day = _dateOnly(value);
    final reminder = reminderAt == null
        ? null
        : DateTime(day.year, day.month, day.day, reminderAt!.hour, reminderAt!.minute);
    return copyWith(
      isDone: isDoneOn(day),
      reminderAt: reminder,
      occurrenceDate: day,
    );
  }

  TaskItem withOccurrenceDone(DateTime value, bool done) {
    final dates = completedDates.toSet();
    final key = _dateKey(value);
    if (done) {
      dates.add(key);
    } else {
      dates.remove(key);
    }
    final sorted = dates.toList()..sort();
    return copyWith(completedDates: sorted);
  }

  TaskItem copyWith({
    String? title,
    DateTime? date,
    DateTime? reminderAt,
    bool clearReminder = false,
    bool? isDone,
    String? category,
    List<int>? repeatWeekdays,
    List<String>? completedDates,
    DateTime? occurrenceDate,
  }) {
    return TaskItem(
      id: id,
      title: title ?? this.title,
      date: date ?? this.date,
      createdAt: createdAt,
      reminderAt: clearReminder ? null : (reminderAt ?? this.reminderAt),
      isDone: isDone ?? this.isDone,
      category: category ?? this.category,
      repeatWeekdays: repeatWeekdays ?? this.repeatWeekdays,
      completedDates: completedDates ?? this.completedDates,
      occurrenceDate: occurrenceDate ?? this.occurrenceDate,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'date': date.toIso8601String(),
        'createdAt': createdAt.toIso8601String(),
        'reminderAt': reminderAt?.toIso8601String(),
        'isDone': isDone,
        'category': category,
        'repeatWeekdays': repeatWeekdays,
        'completedDates': completedDates,
      };

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    final now = DateTime.now();
    final weekdays = ((json['repeatWeekdays'] as List<dynamic>?) ?? const [])
        .whereType<num>()
        .map((value) => value.toInt())
        .where((day) => day >= 1 && day <= 7)
        .toSet()
        .toList()
      ..sort();
    final completed = ((json['completedDates'] as List<dynamic>?) ?? const [])
        .whereType<String>()
        .toSet()
        .toList()
      ..sort();

    return TaskItem(
      id: (json['id'] as num).toInt(),
      title: json['title'] as String? ?? 'کار بدون عنوان',
      date: _dateOnly(DateTime.tryParse(json['date'] as String? ?? '') ?? now),
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ?? now,
      reminderAt: DateTime.tryParse(json['reminderAt'] as String? ?? ''),
      isDone: json['isDone'] as bool? ?? false,
      category: json['category'] as String? ?? 'شخصی',
      repeatWeekdays: weekdays,
      completedDates: completed,
    );
  }
}

'''
main = main[:start] + model + main[end:]

# 3) Safe .rooz JSON parser. No executable content is ever evaluated.
parser = r'''class RoozPlanImport {
  const RoozPlanImport({required this.title, required this.tasks});

  final String title;
  final List<TaskItem> tasks;

  factory RoozPlanImport.parse(String source) {
    final decoded = jsonDecode(source);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('ساختار فایل باید یک شیء JSON باشد.');
    }
    if (decoded['format'] != 'rooz' || decoded['version'] != 1) {
      throw const FormatException('فرمت یا نسخهٔ فایل Rooz پشتیبانی نمی‌شود.');
    }
    final rawTasks = decoded['tasks'];
    if (rawTasks is! List || rawTasks.isEmpty) {
      throw const FormatException('فایل هیچ کاری برای واردکردن ندارد.');
    }
    if (rawTasks.length > 1000) {
      throw const FormatException('حداکثر ۱۰۰۰ کار را می‌توان در یک فایل وارد کرد.');
    }

    final rootCalendar = (decoded['calendar'] as String? ?? 'gregorian').toLowerCase();
    final tasks = <TaskItem>[];
    for (var index = 0; index < rawTasks.length; index++) {
      final raw = rawTasks[index];
      if (raw is! Map<String, dynamic>) {
        throw FormatException('ساختار کار شمارهٔ ${index + 1} معتبر نیست.');
      }
      final title = (raw['title'] as String? ?? '').trim();
      if (title.isEmpty) {
        throw FormatException('عنوان کار شمارهٔ ${index + 1} خالی است.');
      }

      final dateValue = raw['date'] ?? raw['startDate'];
      if (dateValue is! String || dateValue.trim().isEmpty) {
        throw FormatException('تاریخ کار «$title» مشخص نشده است.');
      }
      final calendar = (raw['calendar'] as String? ?? rootCalendar).toLowerCase();
      final date = _parseRoozDate(dateValue, calendar);
      final weekdays = _parseRoozWeekdays(raw['repeatWeekdays']);
      final timeValue = raw['reminderTime'] ?? raw['time'];
      DateTime? reminder;
      if (timeValue != null) {
        if (timeValue is! String || !RegExp(r'^\d{1,2}:\d{2}$').hasMatch(timeValue)) {
          throw FormatException('ساعت یادآوری کار «$title» معتبر نیست.');
        }
        final parts = timeValue.split(':').map(int.parse).toList();
        if (parts[0] < 0 || parts[0] > 23 || parts[1] < 0 || parts[1] > 59) {
          throw FormatException('ساعت یادآوری کار «$title» خارج از محدوده است.');
        }
        reminder = DateTime(date.year, date.month, date.day, parts[0], parts[1]);
      }

      tasks.add(TaskItem(
        id: index + 1,
        title: title,
        date: date,
        createdAt: DateTime.now(),
        reminderAt: reminder,
        category: (raw['category'] as String? ?? 'شخصی').trim().isEmpty
            ? 'شخصی'
            : (raw['category'] as String).trim(),
        repeatWeekdays: weekdays,
      ));
    }
    return RoozPlanImport(
      title: (decoded['title'] as String? ?? 'برنامهٔ واردشده').trim(),
      tasks: tasks,
    );
  }
}

DateTime _parseRoozDate(String value, String calendar) {
  final normalized = value
      .replaceAll('۰', '0').replaceAll('۱', '1').replaceAll('۲', '2')
      .replaceAll('۳', '3').replaceAll('۴', '4').replaceAll('۵', '5')
      .replaceAll('۶', '6').replaceAll('۷', '7').replaceAll('۸', '8')
      .replaceAll('۹', '9');
  final match = RegExp(r'^(\d{4})-(\d{1,2})-(\d{1,2})$').firstMatch(normalized);
  if (match == null) throw FormatException('تاریخ «$value» باید به شکل YYYY-MM-DD باشد.');
  final year = int.parse(match.group(1)!);
  final month = int.parse(match.group(2)!);
  final day = int.parse(match.group(3)!);
  try {
    if (calendar == 'jalali') {
      return _dateOnly(Jalali(year, month, day).toDateTime());
    }
    if (calendar != 'gregorian') {
      throw FormatException('تقویم «$calendar» پشتیبانی نمی‌شود.');
    }
    final result = DateTime(year, month, day);
    if (result.year != year || result.month != month || result.day != day) {
      throw FormatException('تاریخ «$value» معتبر نیست.');
    }
    return _dateOnly(result);
  } on RangeError {
    throw FormatException('تاریخ «$value» معتبر نیست.');
  }
}

List<int> _parseRoozWeekdays(dynamic value) {
  if (value == null) return const [];
  if (value is! List) throw const FormatException('repeatWeekdays باید یک آرایه باشد.');
  const names = <String, int>{
    'monday': 1, 'mon': 1, 'دوشنبه': 1,
    'tuesday': 2, 'tue': 2, 'سه شنبه': 2, 'سه‌شنبه': 2,
    'wednesday': 3, 'wed': 3, 'چهارشنبه': 3,
    'thursday': 4, 'thu': 4, 'پنجشنبه': 4, 'پنج شنبه': 4,
    'friday': 5, 'fri': 5, 'جمعه': 5,
    'saturday': 6, 'sat': 6, 'شنبه': 6,
    'sunday': 7, 'sun': 7, 'یکشنبه': 7, 'یک شنبه': 7,
  };
  final result = <int>{};
  for (final item in value) {
    final day = item is num ? item.toInt() : names[item.toString().trim().toLowerCase()];
    if (day == null || day < 1 || day > 7) {
      throw FormatException('روز تکرار «$item» معتبر نیست؛ از ۱ تا ۷ یا نام روز استفاده کن.');
    }
    result.add(day);
  }
  return result.toList()..sort();
}

'''
main = replace_once(main, 'class TaskStore {', parser + 'class TaskStore {', 'Rooz plan parser insertion')

# 4) Recurring notification scheduling: one weekly OS notification per selected weekday.
schedule_start = main.find('  Future<bool> schedule(TaskItem task) async {')
cancel_start = main.find('  Future<void> cancel(int id) async {', schedule_start)
if schedule_start < 0 or cancel_start < 0:
    fail('Could not locate reminder scheduling methods. No files were changed.')
new_schedule = r'''  int _weeklyNotificationId(int taskId, int weekday) {
    final mixed = (taskId ^ (weekday * 0x45d9f3b)) & 0x7fffffff;
    return mixed == taskId ? (mixed + 1) & 0x7fffffff : mixed;
  }

  DateTime? _nextWeeklyDate(TaskItem task, int weekday) {
    final reminder = task.reminderAt;
    if (reminder == null) return null;
    final now = DateTime.now();
    for (var offset = 0; offset <= 14; offset++) {
      final day = _dateOnly(task.date).add(Duration(days: offset));
      if (day.weekday != weekday) continue;
      final candidate = DateTime(day.year, day.month, day.day, reminder.hour, reminder.minute);
      if (candidate.isAfter(now)) return candidate;
    }
    return null;
  }

  Future<bool> schedule(TaskItem task) async {
    if (!supported || task.reminderAt == null) return false;
    if (!task.isRecurring && task.isDone) return false;
    try {
      await initialize();
      if (!_ready) return false;
      final permissionGranted = await requestPermission();
      if (!permissionGranted) return false;

      const details = NotificationDetails(
        android: AndroidNotificationDetails(
          'rooz_task_reminders',
          'یادآوری کارها',
          channelDescription: 'اعلان زمان‌بندی‌شده برای کارهای روزانه',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(
          presentAlert: true,
          presentBadge: true,
          presentSound: true,
        ),
      );

      if (task.isRecurring) {
        var scheduledAny = false;
        for (final weekday in task.repeatWeekdays) {
          final when = _nextWeeklyDate(task, weekday);
          if (when == null) continue;
          await _plugin.zonedSchedule(
            id: _weeklyNotificationId(task.id, weekday),
            title: 'یادآوری کار',
            body: task.title,
            scheduledDate: tz.TZDateTime.from(when, tz.local),
            notificationDetails: details,
            androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
            matchDateTimeComponents: DateTimeComponents.dayOfWeekAndTime,
          );
          scheduledAny = true;
        }
        return scheduledAny;
      }

      final when = task.reminderAt!;
      if (!when.isAfter(DateTime.now())) return false;
      await _plugin.zonedSchedule(
        id: task.id,
        title: 'یادآوری کار',
        body: task.title,
        scheduledDate: tz.TZDateTime.from(when, tz.local),
        notificationDetails: details,
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

'''
main = main[:schedule_start] + new_schedule + main[cancel_start:]
old_cancel = r'''  Future<void> cancel(int id) async {
    if (!supported) return;
    try {
      await initialize();
      if (_ready) await _plugin.cancel(id: id);
    } catch (_) {}
  }'''
new_cancel = old_cancel + r'''

  Future<void> cancelTask(TaskItem task) async {
    await cancel(task.id);
    for (final weekday in task.repeatWeekdays) {
      await cancel(_weeklyNotificationId(task.id, weekday));
    }
  }'''
main = replace_once(main, old_cancel, new_cancel, 'recurring notification cancel')

# 5) Home state: import with preview, duplicate skipping and safe append.
import_method = r'''  int _newTaskId(Set<int> reserved) {
    var candidate = DateTime.now().microsecondsSinceEpoch.remainder(0x7fffffff);
    while (candidate == 0 || reserved.contains(candidate)) {
      candidate = (candidate + 1) & 0x7fffffff;
    }
    reserved.add(candidate);
    return candidate;
  }

  String _importKey(TaskItem task) =>
      '${task.title.trim().toLowerCase()}|${_dateKey(task.date)}|${task.repeatWeekdays.join(',')}';

  Future<void> _importRoozPlan() async {
    try {
      final file = await FilePicker.pickFile(
        type: FileType.custom,
        allowedExtensions: ['rooz'],
      );
      if (file == null) return;
      final bytes = await file.readAsBytes();
      if (bytes.length > 2 * 1024 * 1024) {
        _message('حجم فایل بیشتر از ۲ مگابایت است.');
        return;
      }

      final plan = RoozPlanImport.parse(utf8.decode(bytes));
      final existingKeys = _tasks.map(_importKey).toSet();
      final seenKeys = <String>{};
      final unique = <TaskItem>[];
      var duplicateCount = 0;
      for (final task in plan.tasks) {
        final key = _importKey(task);
        if (existingKeys.contains(key) || !seenKeys.add(key)) {
          duplicateCount++;
        } else {
          unique.add(task);
        }
      }

      final dateList = unique.map((task) => task.date).toList()..sort();
      final dateSummary = dateList.isEmpty
          ? 'همهٔ موارد فایل قبلاً وجود دارند.'
          : 'از ${_shortDate(dateList.first)} تا ${_shortDate(dateList.last)}';
      final accepted = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(plan.title, maxLines: 2, overflow: TextOverflow.ellipsis),
          content: SizedBox(
            width: double.maxFinite,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${_fa(unique.length)} کار جدید آمادهٔ ورود است.'),
                const SizedBox(height: 5),
                Text(dateSummary, style: TextStyle(color: _muted(context), fontSize: 11)),
                if (duplicateCount > 0) ...[
                  const SizedBox(height: 5),
                  Text('${_fa(duplicateCount)} مورد تکراری نادیده گرفته می‌شود.',
                      style: const TextStyle(color: _amber, fontSize: 11)),
                ],
                const SizedBox(height: 12),
                Flexible(
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: unique.length.clamp(0, 8).toInt(),
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (_, index) {
                      final task = unique[index];
                      final repeat = task.isRecurring ? ' • هفتگی' : '';
                      return ListTile(
                        dense: true,
                        contentPadding: EdgeInsets.zero,
                        title: Text(task.title, maxLines: 1, overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                        subtitle: Text('${_shortDate(task.date)}$repeat', style: const TextStyle(fontSize: 10)),
                      );
                    },
                  ),
                ),
                if (unique.length > 8)
                  Text('و ${_fa(unique.length - 8)} کار دیگر...',
                      style: TextStyle(color: _muted(context), fontSize: 10)),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('انصراف'),
            ),
            FilledButton(
              onPressed: unique.isEmpty ? null : () => Navigator.pop(dialogContext, true),
              child: const Text('واردکردن'),
            ),
          ],
        ),
      );
      if (accepted != true || unique.isEmpty) return;

      final reserved = _tasks.map((task) => task.id).toSet();
      final imported = unique.map((task) => TaskItem(
        id: _newTaskId(reserved),
        title: task.title,
        date: task.date,
        createdAt: DateTime.now(),
        reminderAt: task.reminderAt,
        category: task.category,
        repeatWeekdays: task.repeatWeekdays,
      )).toList();

      setState(() => _tasks = [..._tasks, ...imported]);
      await _persist();
      for (final task in imported) {
        if (task.reminderAt != null) {
          await ReminderService.instance.schedule(task);
        }
      }
      _message('${_fa(imported.length)} کار به برنامه اضافه شد.');
    } on FormatException catch (error) {
      _message('فایل Rooz معتبر نیست: ${error.message}');
    } catch (error) {
      _message('خواندن فایل با خطا روبه‌رو شد. دوباره امتحان کن.');
    }
  }

'''
main = replace_once(main, '  Future<void> _deleteTask(TaskItem task) async {', import_method + '  Future<void> _deleteTask(TaskItem task) async {', 'import method insertion')

# Save editor result should preserve recurring settings and completion history.
main = replace_once(
    main,
    "    final index = _tasks.indexWhere((item) => item.id == result.id);\n    setState(() {",
    "    final index = _tasks.indexWhere((item) => item.id == result.id);\n    setState(() {",
    'editor result anchor check',
)
main = replace_once(
    main,
    '    await ReminderService.instance.cancel(result.id);\n    if (result.reminderAt != null && !result.isDone) {',
    '    if (task != null) {\n      await ReminderService.instance.cancelTask(task);\n    } else {\n      await ReminderService.instance.cancel(result.id);\n    }\n    if (result.reminderAt != null && (result.isRecurring || !result.isDone)) {',
    'edit notification replacement',
)

old_toggle = r'''  Future<void> _toggleTask(TaskItem task) async {
    final index = _tasks.indexWhere((item) => item.id == task.id);
    if (index < 0) return;
    final updated = task.copyWith(isDone: !task.isDone);
    setState(() => _tasks[index] = updated);
    await _persist();
    if (updated.isDone) {
      await ReminderService.instance.cancel(updated.id);
    } else if (updated.reminderAt != null) {
      final scheduled = await ReminderService.instance.schedule(updated);
      if (!scheduled && mounted && !kIsWeb) {
        _message('وضعیت کار ذخیره شد، اما اعلان دوباره تنظیم نشد.');
      }
    }
  }'''
new_toggle = r'''  Future<void> _toggleTask(TaskItem task) async {
    final index = _tasks.indexWhere((item) => item.id == task.id);
    if (index < 0) return;
    final master = _tasks[index];

    if (master.isRecurring) {
      final occurrenceDate = task.occurrenceDate ?? task.date;
      final updated = master.withOccurrenceDone(
        occurrenceDate,
        !master.isDoneOn(occurrenceDate),
      );
      setState(() => _tasks[index] = updated);
      await _persist();
      return;
    }

    final updated = master.copyWith(isDone: !master.isDone);
    setState(() => _tasks[index] = updated);
    await _persist();
    if (updated.isDone) {
      await ReminderService.instance.cancel(updated.id);
    } else if (updated.reminderAt != null) {
      final scheduled = await ReminderService.instance.schedule(updated);
      if (!scheduled && mounted && !kIsWeb) {
        _message('وضعیت کار ذخیره شد، اما اعلان دوباره تنظیم نشد.');
      }
    }
  }'''
main = replace_once(main, old_toggle, new_toggle, 'per-occurrence completion')
main = replace_once(
    main,
    '    await ReminderService.instance.cancel(task.id);\n  }\n\n  Future<void> _clearAllTasks()',
    '    await ReminderService.instance.cancelTask(task);\n  }\n\n  Future<void> _clearAllTasks()',
    'delete recurring notifications',
)
main = replace_once(
    main,
    '    for (final task in _tasks) {\n      await ReminderService.instance.cancel(task.id);\n    }',
    '    for (final task in _tasks) {\n      await ReminderService.instance.cancelTask(task);\n    }',
    'clear recurring notifications',
)

# 6) Project recurring master tasks into individual dates in Today, Calendar and Insights.
main = replace_once(
    main,
    '    final dayTasks = tasks.where((task) => DateUtils.isSameDay(task.date, selectedDate)).toList()\n      ..sort(_taskSort);',
    '    final dayTasks = tasks\n        .where((task) => task.occursOn(selectedDate))\n        .map((task) => task.forDate(selectedDate))\n        .toList()\n      ..sort(_taskSort);',
    'today recurring projection',
)
main = replace_once(
    main,
    '    final selectedTasks = tasks.where((task) => DateUtils.isSameDay(task.date, selectedDate)).toList()\n      ..sort(_taskSort);',
    '    final selectedTasks = tasks\n        .where((task) => task.occursOn(selectedDate))\n        .map((task) => task.forDate(selectedDate))\n        .toList()\n      ..sort(_taskSort);',
    'calendar recurring projection',
)
main = replace_once(
    main,
    '        final count = tasks.where((task) => DateUtils.isSameDay(task.date, dateTime)).length;',
    '        final count = tasks.where((task) => task.occursOn(dateTime)).length;',
    'calendar task markers',
)
main = replace_once(
    main,
    r'''      final dayTasks = tasks.where((task) {
        final value = Jalali.fromDateTime(task.date);
        return value.year == month.year && value.month == month.month && value.day == day;
      }).toList();''',
    r'''      final dateTime = _dateOnly(Jalali(month.year, month.month, day).toDateTime());
      final dayTasks = tasks
          .where((task) => task.occursOn(dateTime))
          .map((task) => task.forDate(dateTime))
          .toList();''',
    'monthly recurring insights',
)
main = replace_once(main, '  final byDate = a.date.compareTo(b.date);', '  final byDate = a.displayDate.compareTo(b.displayDate);', 'sort projected task dates')
main = replace_once(
    main,
    '                        _TaskMeta(icon: Icons.label_outline_rounded, label: task.category, color: categoryColor),\n                        if (task.reminderAt != null)',
    '                        _TaskMeta(icon: Icons.label_outline_rounded, label: task.category, color: categoryColor),\n                        if (task.isRecurring)\n                          _TaskMeta(icon: Icons.repeat_rounded, label: \'هفتگی\', color: _muted(context)),\n                        if (task.reminderAt != null)',
    'weekly task marker',
)

# 7) Task editor: multi-select weekdays + useful presets.
main = replace_once(
    main,
    "  late bool _reminderEnabled;\n  late String _category;\n  String? _validationError;\n\n  static const List<String> _categories = ['شخصی', 'مطالعه', 'کار', 'سلامت'];",
    "  late bool _reminderEnabled;\n  late String _category;\n  late bool _repeatEnabled;\n  late Set<int> _repeatWeekdays;\n  String? _validationError;\n\n  static const List<String> _categories = ['شخصی', 'مطالعه', 'کار', 'سلامت'];\n  static const List<int> _weekdayOrder = [6, 7, 1, 2, 3, 4, 5];\n  static const Map<int, String> _weekdayLabels = {\n    6: 'شنبه', 7: 'یکشنبه', 1: 'دوشنبه', 2: 'سه‌شنبه',\n    3: 'چهارشنبه', 4: 'پنجشنبه', 5: 'جمعه',\n  };",
    'editor repeat state',
)
main = replace_once(
    main,
    "    _reminderEnabled = !kIsWeb && (task?.reminderAt != null || (task == null && widget.remindersDefault));\n    _category = task != null && _categories.contains(task.category) ? task.category : 'شخصی';",
    "    _reminderEnabled = !kIsWeb && (task?.reminderAt != null || (task == null && widget.remindersDefault));\n    _category = task != null && _categories.contains(task.category) ? task.category : 'شخصی';\n    _repeatEnabled = task?.isRecurring ?? false;\n    _repeatWeekdays = {...?task?.repeatWeekdays};",
    'editor repeat initialization',
)
main = replace_once(
    main,
    '  Future<void> _chooseTime() async {',
    "  void _applyRepeatPreset(Set<int> days) {\n    setState(() {\n      _repeatEnabled = true;\n      _repeatWeekdays = {...days};\n    });\n  }\n\n  Future<void> _chooseTime() async {",
    'weekday preset helper',
)
main = replace_once(
    main,
    '    DateTime? reminder;\n    if (_reminderEnabled) {',
    "    if (_repeatEnabled && _repeatWeekdays.isEmpty) {\n      setState(() => _validationError = 'حداقل یک روز برای تکرار انتخاب کن.');\n      return;\n    }\n    DateTime? reminder;\n    if (_reminderEnabled) {",
    'repeat validation',
)
main = replace_once(
    main,
    "      if (!reminder.isAfter(DateTime.now())) {\n        setState(() => _validationError = 'زمان یادآوری باید در آینده باشد.');\n        return;\n      }",
    "      if (!_repeatEnabled && !reminder.isAfter(DateTime.now())) {\n        setState(() => _validationError = 'زمان یادآوری باید در آینده باشد.');\n        return;\n      }",
    'weekly reminder time validation',
)
main = replace_once(
    main,
    '      isDone: old?.isDone ?? false,\n      category: _category,\n    );',
    '      isDone: old?.isDone ?? false,\n      category: _category,\n      repeatWeekdays: _repeatEnabled ? (_repeatWeekdays.toList()..sort()) : const [],\n      completedDates: _repeatEnabled ? (old?.completedDates ?? const []) : const [],\n    );',
    'save weekly settings',
)
old_date_widget = r'''              _EditorOption(
                icon: Icons.calendar_today_outlined,
                title: 'تاریخ انجام',
                value: _shortDate(_date),
                onTap: _chooseDate,
              ),
              SwitchListTile.adaptive('''
new_date_widget = r'''              _EditorOption(
                icon: Icons.calendar_today_outlined,
                title: 'تاریخ شروع',
                value: _shortDate(_date),
                onTap: _chooseDate,
              ),
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                value: _repeatEnabled,
                onChanged: (value) => setState(() {
                  _repeatEnabled = value;
                  if (value && _repeatWeekdays.isEmpty) {
                    _repeatWeekdays = {_date.weekday};
                  }
                }),
                activeTrackColor: _accent,
                title: const Text('تکرار هفتگی', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                subtitle: Text('این کار در روزهای انتخابی هر هفته تکرار می‌شود.',
                    style: TextStyle(color: _muted(context), fontSize: 10)),
              ),
              if (_repeatEnabled) ...[
                Padding(
                  padding: const EdgeInsets.only(top: 3, bottom: 9),
                  child: Text('روزهای تکرار', style: TextStyle(color: _muted(context), fontSize: 11, fontWeight: FontWeight.w800)),
                ),
                Wrap(
                  spacing: 7,
                  runSpacing: 7,
                  children: _weekdayOrder.map((weekday) {
                    final selected = _repeatWeekdays.contains(weekday);
                    return FilterChip(
                      label: Text(_weekdayLabels[weekday]!),
                      selected: selected,
                      showCheckmark: false,
                      selectedColor: _accentSoft,
                      onSelected: (value) => setState(() {
                        if (value) {
                          _repeatWeekdays.add(weekday);
                        } else {
                          _repeatWeekdays.remove(weekday);
                        }
                      }),
                      labelStyle: TextStyle(color: selected ? _accent : _muted(context), fontSize: 10, fontWeight: FontWeight.w700),
                      side: BorderSide(color: selected ? _accent.withValues(alpha: .35) : Theme.of(context).colorScheme.outline),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 5),
                Wrap(
                  spacing: 4,
                  children: [
                    TextButton(onPressed: () => _applyRepeatPreset({6, 7, 1, 2, 3}), child: const Text('روزهای کاری', style: TextStyle(fontSize: 10))),
                    TextButton(onPressed: () => _applyRepeatPreset({4, 5}), child: const Text('پنجشنبه و جمعه', style: TextStyle(fontSize: 10))),
                    TextButton(onPressed: () => _applyRepeatPreset({6, 7, 1, 2, 3, 4, 5}), child: const Text('هر روز', style: TextStyle(fontSize: 10))),
                  ],
                ),
              ],
              SwitchListTile.adaptive('''
main = replace_once(main, old_date_widget, new_date_widget, 'recurrence picker UI')

# 8) Settings page import action.
main = replace_once(
    main,
    '                        onRequestNotifications: _askNotificationPermission,\n                        onClearAll: _clearAllTasks,',
    '                        onRequestNotifications: _askNotificationPermission,\n                        onImportPlan: _importRoozPlan,\n                        onClearAll: _clearAllTasks,',
    'pass import callback to settings',
)
main = replace_once(
    main,
    '    required this.onRequestNotifications,\n    required this.onClearAll,',
    '    required this.onRequestNotifications,\n    required this.onImportPlan,\n    required this.onClearAll,',
    'settings import constructor',
)
main = replace_once(
    main,
    '  final VoidCallback onRequestNotifications;\n  final VoidCallback onClearAll;',
    '  final VoidCallback onRequestNotifications;\n  final VoidCallback onImportPlan;\n  final VoidCallback onClearAll;',
    'settings import field',
)
main = replace_once(
    main,
    "          children: [\n            ListTile(\n              leading: const Icon(Icons.storage_outlined),",
    "          children: [\n            ListTile(\n              onTap: onImportPlan,\n              leading: const Icon(Icons.file_open_outlined, color: _accent),\n              title: const Text('واردکردن برنامه از فایل', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),\n              subtitle: Text('فایل .rooz ساخته‌شده با ChatGPT را انتخاب کن.', style: TextStyle(color: _muted(context), fontSize: 10)),\n              trailing: const Icon(Icons.chevron_left_rounded),\n            ),\n            Divider(height: 1, indent: 15, endIndent: 15, color: scheme.outline),\n            ListTile(\n              leading: const Icon(Icons.storage_outlined),",
    'settings import tile',
)
main = replace_once(main, 'نسخهٔ ۱.۱.۰  •  برنامه‌ریزی ساده و متمرکز', 'نسخهٔ ۱.۲.۰  •  برنامه‌ریزی ساده و متمرکز', 'displayed app version')

# 9) Add date-key helper used by recurrence completion records.
main = replace_once(
    main,
    'DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);',
    "DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);\n\nString _dateKey(DateTime value) =>\n    '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';",
    'date key helper',
)

# Structural checks before writing anything.
checks = [
    'class RoozPlanImport',
    'bool get isRecurring => repeatWeekdays.isNotEmpty;',
    'DateTimeComponents.dayOfWeekAndTime',
    'task.occursOn(selectedDate)',
    'task.occursOn(dateTime)',
    "allowedExtensions: ['rooz']",
    "onImportPlan: _importRoozPlan",
    "repeatWeekdays: _repeatEnabled",
]
for marker in checks:
    if marker not in main:
        fail(f'Internal verification failed for: {marker}. No files were changed.')

# Confirm balanced basic delimiters is not a Dart parser; this is a sanity check only.
if main.count('class TaskItem {') != 1 or main.count('class RoozPlanImport {') != 1:
    fail('Internal class structure check failed. No files were changed.')

test_content_b64 = 'aW1wb3J0ICdwYWNrYWdlOmZsdXR0ZXJfdGVzdC9mbHV0dGVyX3Rlc3QuZGFydCc7CmltcG9ydCAncGFja2FnZTpyb296X2FwcC9tYWluLmRhcnQnOwoKdm9pZCBtYWluKCkgewogIGdyb3VwKCdSb296IHdlZWtseSB0YXNrcycsICgpIHsKICAgIGZpbmFsIHNhdHVyZGF5ID0gRGF0ZVRpbWUoMjAyNiwgMTEsIDcpOwogICAgZmluYWwgbW9uZGF5ID0gRGF0ZVRpbWUoMjAyNiwgMTEsIDkpOwogICAgZmluYWwgd2VkbmVzZGF5ID0gRGF0ZVRpbWUoMjAyNiwgMTEsIDExKTsKICAgIGZpbmFsIHN1bmRheSA9IERhdGVUaW1lKDIwMjYsIDExLCA4KTsKCiAgICB0ZXN0KCdwcm9qZWN0cyBhIHJlY3VycmluZyB0YXNrIG9udG8gc2VsZWN0ZWQgd2Vla2RheXMgb25seScsICgpIHsKICAgICAgZmluYWwgdGFzayA9IFRhc2tJdGVtKAogICAgICAgIGlkOiAxLAogICAgICAgIHRpdGxlOiAn2YXYt9in2YTYudmHJywKICAgICAgICBkYXRlOiBzYXR1cmRheSwKICAgICAgICBjcmVhdGVkQXQ6IHNhdHVyZGF5LAogICAgICAgIHJlcGVhdFdlZWtkYXlzOiBjb25zdCBbNiwgMSwgM10sCiAgICAgICk7CiAgICAgIGV4cGVjdCh0YXNrLm9jY3Vyc09uKHNhdHVyZGF5KSwgaXNUcnVlKTsKICAgICAgZXhwZWN0KHRhc2sub2NjdXJzT24obW9uZGF5KSwgaXNUcnVlKTsKICAgICAgZXhwZWN0KHRhc2sub2NjdXJzT24od2VkbmVzZGF5KSwgaXNUcnVlKTsKICAgICAgZXhwZWN0KHRhc2sub2NjdXJzT24oc3VuZGF5KSwgaXNGYWxzZSk7CiAgICB9KTsKCiAgICB0ZXN0KCdzdG9yZXMgY29tcGxldGlvbiBzZXBhcmF0ZWx5IGZvciBlYWNoIG9jY3VycmVuY2UnLCAoKSB7CiAgICAgIGZpbmFsIHRhc2sgPSBUYXNrSXRlbSgKICAgICAgICBpZDogMiwKICAgICAgICB0aXRsZTogJ9iy2KjYp9mGJywKICAgICAgICBkYXRlOiBzYXR1cmRheSwKICAgICAgICBjcmVhdGVkQXQ6IHNhdHVyZGF5LAogICAgICAgIHJlcGVhdFdlZWtkYXlzOiBjb25zdCBbNiwgMV0sCiAgICAgICk7CiAgICAgIGZpbmFsIHVwZGF0ZWQgPSB0YXNrLndpdGhPY2N1cnJlbmNlRG9uZShtb25kYXksIHRydWUpOwogICAgICBleHBlY3QodXBkYXRlZC5pc0RvbmVPbihtb25kYXkpLCBpc1RydWUpOwogICAgICBleHBlY3QodXBkYXRlZC5pc0RvbmVPbihzYXR1cmRheSksIGlzRmFsc2UpOwogICAgfSk7CgogICAgdGVzdCgnbG9hZHMgYW4gb2xkIHRhc2sgcmVjb3JkIHdpdGhvdXQgcmVjdXJyZW5jZSBmaWVsZHMnLCAoKSB7CiAgICAgIGZpbmFsIHRhc2sgPSBUYXNrSXRlbS5mcm9tSnNvbih7CiAgICAgICAgJ2lkJzogMywKICAgICAgICAndGl0bGUnOiAn2qnYp9ixINmC2K/bjNmF24wnLAogICAgICAgICdkYXRlJzogJzIwMjYtMTEtMDdUMDA6MDA6MDAuMDAwJywKICAgICAgICAnY3JlYXRlZEF0JzogJzIwMjYtMTEtMDZUMTI6MDA6MDAuMDAwJywKICAgICAgICAnaXNEb25lJzogZmFsc2UsCiAgICAgICAgJ2NhdGVnb3J5JzogJ9i02K7YtduMJywKICAgICAgfSk7CiAgICAgIGV4cGVjdCh0YXNrLmlzUmVjdXJyaW5nLCBpc0ZhbHNlKTsKICAgICAgZXhwZWN0KHRhc2sub2NjdXJzT24oc2F0dXJkYXkpLCBpc1RydWUpOwogICAgICBleHBlY3QodGFzay5vY2N1cnNPbihtb25kYXkpLCBpc0ZhbHNlKTsKICAgIH0pOwoKICAgIHRlc3QoJ3BhcnNlcyBKYWxhbGkgZGF0ZXMgYW5kIHdlZWtkYXlzIGZyb20gYSAucm9veiBwbGFuJywgKCkgewogICAgICBmaW5hbCBwbGFuID0gUm9velBsYW5JbXBvcnQucGFyc2UoJycnCiAgICAgICAgewogICAgICAgICAgImZvcm1hdCI6ICJyb296IiwKICAgICAgICAgICJ2ZXJzaW9uIjogMSwKICAgICAgICAgICJjYWxlbmRhciI6ICJqYWxhbGkiLAogICAgICAgICAgInRpdGxlIjogItio2LHZhtin2YXZhyDYqtiz2KoiLAogICAgICAgICAgInRhc2tzIjogWwogICAgICAgICAgICB7CiAgICAgICAgICAgICAgInRpdGxlIjogItiq2YXYsduM2YYiLAogICAgICAgICAgICAgICJkYXRlIjogIjE0MDUtMDgtMTYiLAogICAgICAgICAgICAgICJyZXBlYXRXZWVrZGF5cyI6IFs2LCAxLCAzXQogICAgICAgICAgICB9CiAgICAgICAgICBdCiAgICAgICAgfQogICAgICAnJycpOwogICAgICBleHBlY3QocGxhbi50YXNrcywgaGFzTGVuZ3RoKDEpKTsKICAgICAgZXhwZWN0KHBsYW4udGFza3Muc2luZ2xlLnJlcGVhdFdlZWtkYXlzLCBbMSwgMywgNl0pOwogICAgICBleHBlY3QocGxhbi50YXNrcy5zaW5nbGUuZGF0ZS53ZWVrZGF5LCA2KTsKICAgIH0pOwogIH0pOwp9Cg=='
TEST = ROOT / 'test' / 'widget_test.dart'
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
shutil.copy2(MAIN, MAIN.with_suffix(f'.dart.backup-{stamp}'))
shutil.copy2(PUBSPEC, PUBSPEC.with_suffix(f'.yaml.backup-{stamp}'))
MAIN.write_text(main, encoding='utf-8', newline='\n')
PUBSPEC.write_text(pubspec, encoding='utf-8', newline='\n')
TEST.parent.mkdir(parents=True, exist_ok=True)
if TEST.exists():
    TEST.with_suffix(f'.dart.backup-{stamp}').write_text(TEST.read_text(encoding='utf-8'), encoding='utf-8')
TEST.write_bytes(base64.b64decode(test_content_b64))

print('Rooz features installed in lib/main.dart and pubspec.yaml.')
print('Backups were created next to the original files.')
print('Next run: flutter pub get')
print('Then run: flutter analyze')
print('Note: weekly notifications recur every selected week day until the task is edited/deleted.')
