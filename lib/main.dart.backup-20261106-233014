import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:shamsi_date/shamsi_date.dart';
import 'package:timezone/data/latest_all.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;

const Color _accent = Color(0xFF5865D9);
const Color _accentSoft = Color(0xFFE9ECFF);
const Color _amber = Color(0xFFE0AD55);
const Color _coral = Color(0xFFC96C60);
const Color _lightBackground = Color(0xFFF6F7FB);
const Color _darkBackground = Color(0xFF111521);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await ReminderService.instance.initialize();
  } catch (_) {
    // The app remains usable when notification initialization is unavailable.
  }
  runApp(const RoozApp());
}

// -----------------------------------------------------------------------------
// App, themes and persistence
// -----------------------------------------------------------------------------

class RoozApp extends StatefulWidget {
  const RoozApp({super.key});

  @override
  State<RoozApp> createState() => _RoozAppState();
}

class _RoozAppState extends State<RoozApp> {
  ThemeMode _themeMode = ThemeMode.system;
  bool _remindersDefault = !kIsWeb;
  final SharedPreferencesAsync _preferences = SharedPreferencesAsync();

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    try {
      final theme = await _preferences.getString('rooz_theme_mode_v2');
      final reminders = await _preferences.getBool('rooz_reminders_default_v2');
      if (!mounted) return;
      setState(() {
        _themeMode = switch (theme) {
          'light' => ThemeMode.light,
          'dark' => ThemeMode.dark,
          _ => ThemeMode.system,
        };
        _remindersDefault = reminders ?? !kIsWeb;
      });
    } catch (_) {}
  }

  Future<void> _setThemeMode(ThemeMode value) async {
    setState(() => _themeMode = value);
    final key = switch (value) {
      ThemeMode.light => 'light',
      ThemeMode.dark => 'dark',
      ThemeMode.system => 'system',
    };
    await _preferences.setString('rooz_theme_mode_v2', key);
  }

  Future<void> _setRemindersDefault(bool value) async {
    setState(() => _remindersDefault = value);
    await _preferences.setBool('rooz_reminders_default_v2', value);
  }

  ThemeData _theme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: _accent,
      brightness: brightness,
      surface: dark ? const Color(0xFF1B2130) : Colors.white,
    ).copyWith(
      primary: _accent,
      secondary: _amber,
      error: _coral,
      outline: dark ? const Color(0xFF343B50) : const Color(0xFFE5E8F0),
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: dark ? _darkBackground : _lightBackground,
      dividerColor: scheme.outline,
      textTheme: const TextTheme(
        headlineSmall: TextStyle(fontSize: 25, fontWeight: FontWeight.w900, height: 1.25),
        titleLarge: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
        titleMedium: TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        bodyLarge: TextStyle(fontSize: 14, height: 1.5),
        bodyMedium: TextStyle(fontSize: 13, height: 1.5),
        bodySmall: TextStyle(fontSize: 11, height: 1.4),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? const Color(0xFF252C3B) : const Color(0xFFF1F3F8),
        contentPadding: const EdgeInsets.symmetric(horizontal: 15, vertical: 15),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: _accent, width: 1.3),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: dark ? const Color(0xFF1B2130) : Colors.white,
        indicatorColor: dark ? const Color(0xFF30395F) : _accentSoft,
        labelTextStyle: WidgetStateProperty.resolveWith<TextStyle?>((states) {
          return TextStyle(
            fontSize: 10,
            fontWeight: states.contains(WidgetState.selected)
                ? FontWeight.w800
                : FontWeight.w500,
          );
        }),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: dark ? const Color(0xFF293149) : const Color(0xFF252B3B),
        contentTextStyle: const TextStyle(color: Colors.white, fontSize: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'روز',
      debugShowCheckedModeBanner: false,
      locale: const Locale('fa', 'IR'),
      supportedLocales: const [Locale('fa', 'IR'), Locale('en', 'US')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      themeMode: _themeMode,
      theme: _theme(Brightness.light),
      darkTheme: _theme(Brightness.dark),
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: HomeShell(
          themeMode: _themeMode,
          remindersDefault: _remindersDefault,
          onThemeChanged: _setThemeMode,
          onRemindersDefaultChanged: _setRemindersDefault,
        ),
      ),
    );
  }
}

class TaskItem {
  const TaskItem({
    required this.id,
    required this.title,
    required this.date,
    required this.createdAt,
    this.reminderAt,
    this.isDone = false,
    this.category = 'شخصی',
  });

  final int id;
  final String title;
  final DateTime date;
  final DateTime createdAt;
  final DateTime? reminderAt;
  final bool isDone;
  final String category;

  TaskItem copyWith({
    String? title,
    DateTime? date,
    DateTime? reminderAt,
    bool clearReminder = false,
    bool? isDone,
    String? category,
  }) {
    return TaskItem(
      id: id,
      title: title ?? this.title,
      date: date ?? this.date,
      createdAt: createdAt,
      reminderAt: clearReminder ? null : (reminderAt ?? this.reminderAt),
      isDone: isDone ?? this.isDone,
      category: category ?? this.category,
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
      };

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    final now = DateTime.now();
    return TaskItem(
      id: (json['id'] as num).toInt(),
      title: json['title'] as String? ?? 'کار بدون عنوان',
      date: _dateOnly(DateTime.tryParse(json['date'] as String? ?? '') ?? now),
      createdAt: DateTime.tryParse(json['createdAt'] as String? ?? '') ?? now,
      reminderAt: DateTime.tryParse(json['reminderAt'] as String? ?? ''),
      isDone: json['isDone'] as bool? ?? false,
      category: json['category'] as String? ?? 'شخصی',
    );
  }
}

class TaskStore {
  static const String _key = 'rooz_tasks_v1';
  final SharedPreferencesAsync _preferences = SharedPreferencesAsync();

  Future<List<TaskItem>> load() async {
    final raw = await _preferences.getString(_key);
    if (raw == null || raw.isEmpty) return [];
    try {
      final decoded = jsonDecode(raw) as List<dynamic>;
      return decoded
          .map((item) => TaskItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> save(List<TaskItem> tasks) async {
    await _preferences.setString(
      _key,
      jsonEncode(tasks.map((task) => task.toJson()).toList()),
    );
  }

  Future<void> clear() => _preferences.remove(_key);
}

// -----------------------------------------------------------------------------
// Local notifications
// -----------------------------------------------------------------------------

class ReminderService {
  ReminderService._();
  static final ReminderService instance = ReminderService._();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  bool _ready = false;

  bool get supported => !kIsWeb &&
      (defaultTargetPlatform == TargetPlatform.iOS ||
          defaultTargetPlatform == TargetPlatform.android);

  Future<void> initialize() async {
    if (_ready || !supported) return;
    tz_data.initializeTimeZones();
    try {
      final zone = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(tz.getLocation(zone.identifier));
    } catch (_) {
      tz.setLocalLocation(tz.getLocation('Etc/UTC'));
    }

    const darwin = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );
    await _plugin.initialize(
      settings: const InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: darwin,
        macOS: darwin,
      ),
    );
    _ready = true;
  }

  Future<bool> requestPermission() async {
    if (!supported) return false;
    await initialize();
    final ios = _plugin.resolvePlatformSpecificImplementation<
        IOSFlutterLocalNotificationsPlugin>();
    if (ios != null) {
      return await ios.requestPermissions(
            alert: true,
            badge: true,
            sound: true,
          ) ??
          false;
    }
    final android = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    if (android != null) {
      return await android.requestNotificationsPermission() ?? true;
    }
    return false;
  }

  Future<bool> schedule(TaskItem task) async {
    if (!supported || task.reminderAt == null || task.isDone) return false;
    final when = task.reminderAt!;
    if (!when.isAfter(DateTime.now())) return false;
    try {
      await initialize();
      if (!_ready) return false;
      final permissionGranted = await requestPermission();
      if (!permissionGranted) return false;
      await _plugin.zonedSchedule(
        id: task.id,
        title: 'یادآوری کار',
        body: task.title,
        scheduledDate: tz.TZDateTime.from(when, tz.local),
        notificationDetails: const NotificationDetails(
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
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<void> cancel(int id) async {
    if (!supported) return;
    try {
      await initialize();
      if (_ready) await _plugin.cancel(id: id);
    } catch (_) {}
  }
}

// -----------------------------------------------------------------------------
// Main shell and state
// -----------------------------------------------------------------------------

enum TaskFilter { all, pending, done }

class HomeShell extends StatefulWidget {
  const HomeShell({
    super.key,
    required this.themeMode,
    required this.remindersDefault,
    required this.onThemeChanged,
    required this.onRemindersDefaultChanged,
  });

  final ThemeMode themeMode;
  final bool remindersDefault;
  final ValueChanged<ThemeMode> onThemeChanged;
  final ValueChanged<bool> onRemindersDefaultChanged;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  final TaskStore _store = TaskStore();
  List<TaskItem> _tasks = [];
  bool _loading = true;
  int _tab = 0;
  TaskFilter _filter = TaskFilter.all;
  DateTime _selectedDate = _dateOnly(DateTime.now());
  Jalali _calendarMonth = Jalali.now().copy(day: 1);
  Jalali _statsMonth = Jalali.now().copy(day: 1);

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  Future<void> _loadTasks() async {
    try {
      final loaded = await _store.load();
      if (!mounted) return;
      setState(() {
        _tasks = loaded;
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _persist() async {
    try {
      await _store.save(_tasks);
    } catch (_) {
      if (mounted) _message('ذخیره‌سازی اطلاعات با خطا روبه‌رو شد.');
    }
  }

  void _changeCalendarMonth(Jalali value) {
    setState(() {
      _calendarMonth = value.copy(day: 1);
      final selected = Jalali.fromDateTime(_selectedDate);
      if (selected.year != value.year || selected.month != value.month) {
        _selectedDate = _dateOnly(value.toDateTime());
      }
    });
  }

  void _message(String text) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(text)));
  }

  Future<void> _openEditor({TaskItem? task, DateTime? date}) async {
    final result = await showModalBottomSheet<TaskItem>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (_) => TaskEditorSheet(
        task: task,
        initialDate: date ?? task?.date ?? _selectedDate,
        remindersDefault: widget.remindersDefault,
      ),
    );
    if (result == null) return;

    final index = _tasks.indexWhere((item) => item.id == result.id);
    setState(() {
      if (index >= 0) {
        _tasks[index] = result;
      } else {
        _tasks.add(result);
      }
      _selectedDate = result.date;
    });
    await _persist();
    await ReminderService.instance.cancel(result.id);
    if (result.reminderAt != null && !result.isDone) {
      final scheduled = await ReminderService.instance.schedule(result);
      if (!scheduled && mounted && !kIsWeb) {
        _message('کار ذخیره شد، اما اعلان تنظیم نشد. دسترسی اعلان‌ها را در تنظیمات بررسی کن.');
      }
    }
  }

  Future<void> _toggleTask(TaskItem task) async {
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
  }

  Future<void> _deleteTask(TaskItem task) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('حذف کار؟'),
        content: Text('«${task.title}» از فهرست حذف می‌شود.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('انصراف'),
          ),
          FilledButton.tonal(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('حذف'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    setState(() => _tasks.removeWhere((item) => item.id == task.id));
    await _persist();
    await ReminderService.instance.cancel(task.id);
  }

  Future<void> _clearAllTasks() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('پاک‌کردن همهٔ کارها؟'),
        content: const Text('این کار برگشت‌پذیر نیست و تمام تسک‌های ذخیره‌شده حذف می‌شوند.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('انصراف'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            style: FilledButton.styleFrom(backgroundColor: _coral),
            child: const Text('پاک‌کردن همه'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    for (final task in _tasks) {
      await ReminderService.instance.cancel(task.id);
    }
    setState(() => _tasks.clear());
    await _store.clear();
    _message('همهٔ کارها حذف شدند.');
  }

  Future<void> _askNotificationPermission() async {
    if (kIsWeb) {
      _message('اعلان زمان‌بندی‌شده در نسخهٔ مرورگر در دسترس نیست.');
      return;
    }
    final granted = await ReminderService.instance.requestPermission();
    _message(granted
        ? 'دسترسی اعلان‌ها فعال شد.'
        : 'دسترسی اعلان‌ها داده نشد. تنظیمات اعلان Rooz را در آیفون بررسی کن.');
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: _loading
            ? const Center(child: CircularProgressIndicator(color: _accent))
            : Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 760),
                  child: IndexedStack(
                    index: _tab,
                    children: [
                      TodayPage(
                        tasks: _tasks,
                        selectedDate: _selectedDate,
                        filter: _filter,
                        onDateChanged: (value) => setState(() => _selectedDate = value),
                        onFilterChanged: (value) => setState(() => _filter = value),
                        onToggle: _toggleTask,
                        onEdit: (task) => _openEditor(task: task),
                        onDelete: _deleteTask,
                        onAdd: () => _openEditor(date: _selectedDate),
                        onOpenSettings: () => setState(() => _tab = 3),
                      ),
                      CalendarPage(
                        tasks: _tasks,
                        selectedDate: _selectedDate,
                        visibleMonth: _calendarMonth,
                        onDateChanged: (value) => setState(() => _selectedDate = value),
                        onMonthChanged: _changeCalendarMonth,
                        onToggle: _toggleTask,
                        onEdit: (task) => _openEditor(task: task),
                        onDelete: _deleteTask,
                        onAdd: () => _openEditor(date: _selectedDate),
                      ),
                      InsightsPage(
                        tasks: _tasks,
                        month: _statsMonth,
                        onMonthChanged: (value) => setState(() => _statsMonth = value),
                      ),
                      SettingsPage(
                        themeMode: widget.themeMode,
                        remindersDefault: widget.remindersDefault,
                        onThemeChanged: widget.onThemeChanged,
                        onRemindersDefaultChanged: widget.onRemindersDefaultChanged,
                        onRequestNotifications: _askNotificationPermission,
                        onClearAll: _clearAllTasks,
                        taskCount: _tasks.length,
                      ),
                    ],
                  ),
                ),
              ),
      ),
      floatingActionButton: _tab == 0 || _tab == 1
          ? FloatingActionButton.extended(
              onPressed: () => _openEditor(date: _selectedDate),
              backgroundColor: scheme.primary,
              foregroundColor: Colors.white,
              elevation: 2,
              icon: const Icon(Icons.add_rounded),
              label: const Text('کار جدید', style: TextStyle(fontWeight: FontWeight.w800)),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (value) => setState(() => _tab = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.grid_view_rounded),
            selectedIcon: Icon(Icons.grid_view_rounded),
            label: 'امروز',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month_rounded),
            label: 'تقویم',
          ),
          NavigationDestination(
            icon: Icon(Icons.insights_outlined),
            selectedIcon: Icon(Icons.insights_rounded),
            label: 'گزارش',
          ),
          NavigationDestination(
            icon: Icon(Icons.tune_rounded),
            selectedIcon: Icon(Icons.tune_rounded),
            label: 'تنظیمات',
          ),
        ],
      ),
    );
  }
}

// -----------------------------------------------------------------------------
// Today dashboard
// -----------------------------------------------------------------------------

class TodayPage extends StatelessWidget {
  const TodayPage({
    super.key,
    required this.tasks,
    required this.selectedDate,
    required this.filter,
    required this.onDateChanged,
    required this.onFilterChanged,
    required this.onToggle,
    required this.onEdit,
    required this.onDelete,
    required this.onAdd,
    required this.onOpenSettings,
  });

  final List<TaskItem> tasks;
  final DateTime selectedDate;
  final TaskFilter filter;
  final ValueChanged<DateTime> onDateChanged;
  final ValueChanged<TaskFilter> onFilterChanged;
  final ValueChanged<TaskItem> onToggle;
  final ValueChanged<TaskItem> onEdit;
  final ValueChanged<TaskItem> onDelete;
  final VoidCallback onAdd;
  final VoidCallback onOpenSettings;

  @override
  Widget build(BuildContext context) {
    final dayTasks = tasks.where((task) => DateUtils.isSameDay(task.date, selectedDate)).toList()
      ..sort(_taskSort);
    final done = dayTasks.where((task) => task.isDone).length;
    final progress = dayTasks.isEmpty ? 0.0 : done / dayTasks.length;
    final visible = dayTasks.where((task) {
      return switch (filter) {
        TaskFilter.all => true,
        TaskFilter.pending => !task.isDone,
        TaskFilter.done => task.isDone,
      };
    }).toList();
    final today = DateUtils.isSameDay(selectedDate, DateTime.now());

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 110),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _TopBar(onSettings: onOpenSettings),
              const SizedBox(height: 27),
              Text(
                today ? 'برای امروز چه برنامه‌ای داری؟' : 'برنامهٔ این روز',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 5),
              Text(
                today ? 'یک قدم کوچک هم پیشرفت محسوب می‌شود.' : _fullDate(selectedDate),
                style: TextStyle(color: _muted(context), fontSize: 12),
              ),
              const SizedBox(height: 18),
              _QuickDateStrip(selectedDate: selectedDate, onChanged: onDateChanged),
              const SizedBox(height: 20),
              _DailySummaryCard(
                done: done,
                total: dayTasks.length,
                progress: progress,
                date: selectedDate,
              ),
              const SizedBox(height: 29),
              Row(
                children: [
                  const Expanded(child: _SectionTitle(title: 'کارهای این روز')),
                  Text(
                    '${_fa(visible.length)} مورد',
                    style: TextStyle(color: _muted(context), fontSize: 11),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              _FilterBar(value: filter, onChanged: onFilterChanged),
              const SizedBox(height: 13),
              if (visible.isEmpty)
                _EmptyState(
                  title: filter == TaskFilter.done
                      ? 'هنوز کاری تکمیل نشده'
                      : filter == TaskFilter.pending
                          ? 'همهٔ کارها انجام شده‌اند'
                          : 'برای این روز کاری ثبت نشده',
                  subtitle: 'با افزودن یک کار، برنامه‌ات را مشخص کن.',
                  onAdd: onAdd,
                )
              else
                ...visible.map(
                  (task) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: TaskCard(
                      task: task,
                      onToggle: () => onToggle(task),
                      onEdit: () => onEdit(task),
                      onDelete: () => onDelete(task),
                    ),
                  ),
                ),
              const SizedBox(height: 16),
              if (dayTasks.isNotEmpty)
                TextButton.icon(
                  onPressed: onAdd,
                  icon: const Icon(Icons.add_rounded, size: 18),
                  label: const Text('افزودن کار دیگر'),
                ),
            ]),
          ),
        ),
      ],
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.onSettings});
  final VoidCallback onSettings;

  @override
  Widget build(BuildContext context) {
    final now = Jalali.now();
    return Row(
      children: [
        Container(
          width: 43,
          height: 43,
          decoration: BoxDecoration(
            color: _accent,
            borderRadius: BorderRadius.circular(15),
          ),
          child: const Icon(Icons.done_all_rounded, color: Colors.white, size: 24),
        ),
        const SizedBox(width: 11),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'روز',
                style: TextStyle(
                  color: _text(context),
                  fontWeight: FontWeight.w900,
                  fontSize: 22,
                  height: 1.1,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                '${now.formatter.wN}، ${_jalaliDate(now)}',
                style: TextStyle(color: _muted(context), fontSize: 11),
              ),
            ],
          ),
        ),
        IconButton.filledTonal(
          onPressed: onSettings,
          tooltip: 'تنظیمات',
          icon: const Icon(Icons.tune_rounded, size: 19),
        ),
      ],
    );
  }
}

class _QuickDateStrip extends StatelessWidget {
  const _QuickDateStrip({required this.selectedDate, required this.onChanged});
  final DateTime selectedDate;
  final ValueChanged<DateTime> onChanged;

  @override
  Widget build(BuildContext context) {
    final firstDay = _dateOnly(selectedDate);
    return SizedBox(
      height: 76,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: 7,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final date = firstDay.add(Duration(days: index));
          final selected = DateUtils.isSameDay(date, selectedDate);
          final jalali = Jalali.fromDateTime(date);
          return Material(
            color: selected ? _accent : Theme.of(context).colorScheme.surface,
            borderRadius: BorderRadius.circular(17),
            child: InkWell(
              borderRadius: BorderRadius.circular(17),
              onTap: () => onChanged(date),
              child: SizedBox(
                width: 53,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      _weekdayShort(jalali.weekDay),
                      style: TextStyle(
                        color: selected ? Colors.white.withValues(alpha: .8) : _muted(context),
                        fontSize: 10,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      _fa(jalali.day),
                      style: TextStyle(
                        color: selected ? Colors.white : _text(context),
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _DailySummaryCard extends StatelessWidget {
  const _DailySummaryCard({
    required this.done,
    required this.total,
    required this.progress,
    required this.date,
  });

  final int done;
  final int total;
  final double progress;
  final DateTime date;

  @override
  Widget build(BuildContext context) {
    final remaining = total - done;
    return Container(
      padding: const EdgeInsets.all(19),
      decoration: BoxDecoration(
        color: const Color(0xFF202A46),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'پیشرفت ${_jalaliDate(Jalali.fromDateTime(date))}',
                  style: const TextStyle(color: Color(0xFFC4CEF2), fontSize: 11),
                ),
                const SizedBox(height: 9),
                Text(
                  total == 0 ? 'شروع از یک قدم' : '$done از $total کار انجام شد',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    fontSize: 18,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  total == 0
                      ? 'برنامهٔ امروزت را بساز.'
                      : remaining == 0
                          ? 'همهٔ کارهای این روز تکمیل شده‌اند.'
                          : '${_fa(remaining)} کار باقی مانده است.',
                  style: const TextStyle(color: Color(0xFFD5DCF8), fontSize: 11),
                ),
                const SizedBox(height: 15),
                ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 6,
                    backgroundColor: Colors.white.withValues(alpha: .16),
                    valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF9AA8FF)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 18),
          SizedBox(
            width: 72,
            height: 72,
            child: Stack(
              alignment: Alignment.center,
              children: [
                SizedBox.expand(
                  child: CircularProgressIndicator(
                    value: progress,
                    strokeWidth: 6,
                    strokeCap: StrokeCap.round,
                    backgroundColor: Colors.white.withValues(alpha: .16),
                    valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF9AA8FF)),
                  ),
                ),
                Text(
                  '${(progress * 100).round()}٪',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 17),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.title, this.subtitle});
  final String title;
  final String? subtitle;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: TextStyle(color: _text(context), fontSize: 17, fontWeight: FontWeight.w900)),
          if (subtitle != null) ...[
            const SizedBox(height: 3),
            Text(subtitle!, style: TextStyle(color: _muted(context), fontSize: 11)),
          ],
        ],
      );
}

class _FilterBar extends StatelessWidget {
  const _FilterBar({required this.value, required this.onChanged});
  final TaskFilter value;
  final ValueChanged<TaskFilter> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _FilterChip(label: 'همه', selected: value == TaskFilter.all, onTap: () => onChanged(TaskFilter.all)),
        const SizedBox(width: 7),
        _FilterChip(label: 'در انتظار', selected: value == TaskFilter.pending, onTap: () => onChanged(TaskFilter.pending)),
        const SizedBox(width: 7),
        _FilterChip(label: 'انجام‌شده', selected: value == TaskFilter.done, onTap: () => onChanged(TaskFilter.done)),
      ],
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({required this.label, required this.selected, required this.onTap});
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: selected ? scheme.primary : scheme.surface,
      borderRadius: BorderRadius.circular(30),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(30),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 9),
          child: Text(
            label,
            style: TextStyle(
              color: selected ? Colors.white : _muted(context),
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ),
    );
  }
}

// -----------------------------------------------------------------------------
// Calendar
// -----------------------------------------------------------------------------

class CalendarPage extends StatelessWidget {
  const CalendarPage({
    super.key,
    required this.tasks,
    required this.selectedDate,
    required this.visibleMonth,
    required this.onDateChanged,
    required this.onMonthChanged,
    required this.onToggle,
    required this.onEdit,
    required this.onDelete,
    required this.onAdd,
  });

  final List<TaskItem> tasks;
  final DateTime selectedDate;
  final Jalali visibleMonth;
  final ValueChanged<DateTime> onDateChanged;
  final ValueChanged<Jalali> onMonthChanged;
  final ValueChanged<TaskItem> onToggle;
  final ValueChanged<TaskItem> onEdit;
  final ValueChanged<TaskItem> onDelete;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final selectedTasks = tasks.where((task) => DateUtils.isSameDay(task.date, selectedDate)).toList()
      ..sort(_taskSort);
    final selectedJalali = Jalali.fromDateTime(selectedDate);
    final theme = Theme.of(context);

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 110),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              const _SectionTitle(title: 'تقویم برنامه‌ها', subtitle: 'روزها و کارهای ثبت‌شده را مرور کن.'),
              const SizedBox(height: 19),
              _SurfaceCard(
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${visibleMonth.formatter.mN} ${_fa(visibleMonth.year)}',
                            style: TextStyle(color: _text(context), fontSize: 18, fontWeight: FontWeight.w900),
                          ),
                        ),
                        TextButton(
                          onPressed: () {
                            final now = _dateOnly(DateTime.now());
                            onDateChanged(now);
                            onMonthChanged(Jalali.now().copy(day: 1));
                          },
                          child: const Text('امروز'),
                        ),
                        IconButton(
                          visualDensity: VisualDensity.compact,
                          onPressed: () => onMonthChanged(visibleMonth.addMonths(-1).copy(day: 1)),
                          icon: const Icon(Icons.chevron_right_rounded),
                        ),
                        IconButton(
                          visualDensity: VisualDensity.compact,
                          onPressed: () => onMonthChanged(visibleMonth.addMonths(1).copy(day: 1)),
                          icon: const Icon(Icons.chevron_left_rounded),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Row(
                      children: [
                        _WeekdayLabel('ش'), _WeekdayLabel('ی'), _WeekdayLabel('د'),
                        _WeekdayLabel('س'), _WeekdayLabel('چ'), _WeekdayLabel('پ'), _WeekdayLabel('ج'),
                      ],
                    ),
                    const SizedBox(height: 9),
                    _CalendarGrid(
                      month: visibleMonth,
                      selectedDate: selectedDate,
                      tasks: tasks,
                      onSelected: onDateChanged,
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        _CalendarLegend(color: _accent, label: 'انتخاب‌شده'),
                        const SizedBox(width: 16),
                        _CalendarLegend(color: _amber, label: 'دارای کار'),
                        const Spacer(),
                        Text('${_fa(visibleMonth.monthLength)} روز', style: TextStyle(color: _muted(context), fontSize: 10)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 25),
              Row(
                children: [
                  Expanded(
                    child: _SectionTitle(
                      title: selectedJalali.formatter.wN,
                      subtitle: _jalaliDate(selectedJalali),
                    ),
                  ),
                  Text('${_fa(selectedTasks.length)} کار', style: TextStyle(color: _muted(context), fontSize: 11)),
                ],
              ),
              const SizedBox(height: 12),
              if (selectedTasks.isEmpty)
                _EmptyState(
                  title: 'برای این روز کاری ثبت نشده',
                  subtitle: 'می‌توانی یک کار تازه به این تاریخ اضافه کنی.',
                  onAdd: onAdd,
                )
              else
                ...selectedTasks.map(
                  (task) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: TaskCard(
                      task: task,
                      onToggle: () => onToggle(task),
                      onEdit: () => onEdit(task),
                      onDelete: () => onDelete(task),
                    ),
                  ),
                ),
            ]),
          ),
        ),
      ],
    );
  }
}

class _CalendarGrid extends StatelessWidget {
  const _CalendarGrid({
    required this.month,
    required this.selectedDate,
    required this.tasks,
    required this.onSelected,
  });

  final Jalali month;
  final DateTime selectedDate;
  final List<TaskItem> tasks;
  final ValueChanged<DateTime> onSelected;

  @override
  Widget build(BuildContext context) {
    final firstWeekDay = Jalali(month.year, month.month, 1).weekDay;
    final leading = firstWeekDay - 1;
    final days = month.monthLength;
    final itemCount = ((leading + days + 6) ~/ 7) * 7;
    final now = Jalali.now();
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: itemCount,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 7,
        mainAxisSpacing: 5,
        crossAxisSpacing: 4,
        childAspectRatio: 0.88,
      ),
      itemBuilder: (context, index) {
        final day = index - leading + 1;
        if (day < 1 || day > days) return const SizedBox.shrink();
        final date = Jalali(month.year, month.month, day);
        final dateTime = _dateOnly(date.toDateTime());
        final selected = DateUtils.isSameDay(dateTime, selectedDate);
        final isToday = date.year == now.year && date.month == now.month && date.day == now.day;
        final count = tasks.where((task) => DateUtils.isSameDay(task.date, dateTime)).length;
        return Material(
          color: selected ? _accent : Colors.transparent,
          borderRadius: BorderRadius.circular(13),
          child: InkWell(
            onTap: () => onSelected(dateTime),
            borderRadius: BorderRadius.circular(13),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  _fa(day),
                  style: TextStyle(
                    color: selected ? Colors.white : _text(context),
                    fontSize: 12,
                    fontWeight: selected || isToday ? FontWeight.w900 : FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 5),
                Container(
                  width: 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: count == 0
                        ? (isToday && !selected ? _accent : Colors.transparent)
                        : selected
                            ? Colors.white
                            : _amber,
                    shape: BoxShape.circle,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _WeekdayLabel extends StatelessWidget {
  const _WeekdayLabel(this.label);
  final String label;

  @override
  Widget build(BuildContext context) => Expanded(
        child: Center(
          child: Text(label, style: TextStyle(color: _muted(context), fontSize: 10, fontWeight: FontWeight.w800)),
        ),
      );
}

class _CalendarLegend extends StatelessWidget {
  const _CalendarLegend({required this.color, required this.label});
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 7, height: 7, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
          const SizedBox(width: 5),
          Text(label, style: TextStyle(color: _muted(context), fontSize: 10)),
        ],
      );
}

// -----------------------------------------------------------------------------
// Monthly insights and chart
// -----------------------------------------------------------------------------

class DailyCount {
  const DailyCount({required this.day, required this.total, required this.done});
  final int day;
  final int total;
  final int done;
  int get pending => total - done;
}

class InsightsPage extends StatelessWidget {
  const InsightsPage({
    super.key,
    required this.tasks,
    required this.month,
    required this.onMonthChanged,
  });

  final List<TaskItem> tasks;
  final Jalali month;
  final ValueChanged<Jalali> onMonthChanged;

  @override
  Widget build(BuildContext context) {
    final daily = List<DailyCount>.generate(month.monthLength, (index) {
      final day = index + 1;
      final dayTasks = tasks.where((task) {
        final value = Jalali.fromDateTime(task.date);
        return value.year == month.year && value.month == month.month && value.day == day;
      }).toList();
      return DailyCount(
        day: day,
        total: dayTasks.length,
        done: dayTasks.where((task) => task.isDone).length,
      );
    });
    final total = daily.fold<int>(0, (sum, item) => sum + item.total);
    final done = daily.fold<int>(0, (sum, item) => sum + item.done);
    final pending = total - done;
    final rate = total == 0 ? 0.0 : done / total;
    final activeDays = daily.where((item) => item.total > 0).length;
    final bestDay = daily.fold<DailyCount?>(null, (best, item) {
      if (item.total == 0) return best;
      if (best == null || item.done > best.done) return item;
      return best;
    });

    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [
        SliverPadding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 35),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              const _SectionTitle(title: 'گزارش عملکرد', subtitle: 'تصویر روشن‌تری از روند انجام کارها داشته باش.'),
              const SizedBox(height: 20),
              _SurfaceCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Expanded(child: Text('عملکرد ماهانه', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900))),
                        _MonthSwitcher(
                          month: month,
                          onPrevious: () => onMonthChanged(month.addMonths(-1).copy(day: 1)),
                          onNext: () => onMonthChanged(month.addMonths(1).copy(day: 1)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text('تعداد کارهای تکمیل‌شده و باقی‌مانده در هر روز', style: TextStyle(color: _muted(context), fontSize: 11)),
                    const SizedBox(height: 19),
                    Row(
                      children: [
                        _LegendDot(color: _accent, label: 'انجام‌شده'),
                        const SizedBox(width: 16),
                        _LegendDot(color: Theme.of(context).colorScheme.outline, label: 'انجام‌نشده'),
                        const Spacer(),
                        Text('${_fa(month.monthLength)} روز', style: TextStyle(color: _muted(context), fontSize: 10)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 178,
                      width: double.infinity,
                      child: CustomPaint(
                        painter: MonthlyBarsPainter(
                          values: daily,
                          doneColor: _accent,
                          pendingColor: Theme.of(context).colorScheme.outline,
                          gridColor: Theme.of(context).dividerColor,
                          labelColor: _muted(context),
                        ),
                      ),
                    ),
                    const SizedBox(height: 15),
                    Row(
                      children: [
                        Expanded(child: _MetricCard(label: 'انجام‌شده', value: _fa(done), color: _accent)),
                        const SizedBox(width: 8),
                        Expanded(child: _MetricCard(label: 'باقی‌مانده', value: _fa(pending), color: _coral)),
                        const SizedBox(width: 8),
                        Expanded(child: _MetricCard(label: 'درصد تکمیل', value: '${_fa((rate * 100).round())}٪', color: _text(context))),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 17),
              Row(
                children: [
                  Expanded(child: _MetricCardLarge(icon: Icons.event_available_rounded, label: 'روزهای فعال', value: _fa(activeDays), detail: 'از ${_fa(month.monthLength)} روز', tint: _accentSoft, accent: _accent)),
                  const SizedBox(width: 10),
                  Expanded(child: _MetricCardLarge(icon: Icons.emoji_events_outlined, label: 'بهترین روز', value: bestDay == null ? '—' : _fa(bestDay.day), detail: bestDay == null ? 'هنوز داده‌ای نیست' : '${_fa(bestDay.done)} کار تکمیل‌شده', tint: const Color(0xFFFBF1DF), accent: _amber)),
                ],
              ),
              const SizedBox(height: 17),
              _SurfaceCard(
                child: Row(
                  children: [
                    SizedBox(
                      width: 54,
                      height: 54,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          CircularProgressIndicator(
                            value: rate,
                            strokeWidth: 5,
                            strokeCap: StrokeCap.round,
                            backgroundColor: Theme.of(context).colorScheme.outline.withValues(alpha: .35),
                            valueColor: const AlwaysStoppedAnimation<Color>(_accent),
                          ),
                          Text('${(rate * 100).round()}٪', style: TextStyle(color: _text(context), fontWeight: FontWeight.w900, fontSize: 11)),
                        ],
                      ),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('جمع‌بندی این ماه', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 14)),
                          const SizedBox(height: 4),
                          Text(
                            total == 0
                                ? 'برای این ماه هنوز کاری ثبت نکرده‌ای.'
                                : 'از ${_fa(total)} کار ثبت‌شده، ${_fa(done)} کار تکمیل شده است.',
                            style: TextStyle(color: _muted(context), fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ]),
          ),
        ),
      ],
    );
  }
}

class MonthlyBarsPainter extends CustomPainter {
  MonthlyBarsPainter({
    required this.values,
    required this.doneColor,
    required this.pendingColor,
    required this.gridColor,
    required this.labelColor,
  });

  final List<DailyCount> values;
  final Color doneColor;
  final Color pendingColor;
  final Color gridColor;
  final Color labelColor;

  @override
  void paint(Canvas canvas, Size size) {
    const top = 8.0;
    const labelHeight = 25.0;
    final bottom = size.height - labelHeight;
    final chartHeight = bottom - top;
    final maxValue = values.fold<int>(1, (maxSoFar, value) => value.total > maxSoFar ? value.total : maxSoFar);
    final grid = Paint()..color = gridColor.withValues(alpha: .75)..strokeWidth = 1;
    for (var i = 0; i <= 3; i++) {
      final y = top + chartHeight * i / 3;
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    final slot = size.width / math.max(1, values.length);
    final barWidth = math.min(9.0, slot * .62).toDouble();
    final donePaint = Paint()..color = doneColor;
    final pendingPaint = Paint()..color = pendingColor;
    for (final item in values) {
      if (item.total == 0) continue;
      final x = size.width - (item.day - .5) * slot - barWidth / 2;
      final allHeight = chartHeight * item.total / maxValue;
      final doneHeight = chartHeight * item.done / maxValue;
      final pendingHeight = allHeight - doneHeight;
      if (pendingHeight > 0) {
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromLTWH(x, bottom - allHeight, barWidth, pendingHeight),
            const Radius.circular(3),
          ),
          pendingPaint,
        );
      }
      if (doneHeight > 0) {
        canvas.drawRRect(
          RRect.fromRectAndRadius(
            Rect.fromLTWH(x, bottom - doneHeight, barWidth, doneHeight),
            const Radius.circular(3),
          ),
          donePaint,
        );
      }
    }

    final labels = <int>{1, 5, 10, 15, 20, 25, values.length};
    for (final day in labels) {
      if (day < 1 || day > values.length) continue;
      final painter = TextPainter(
        text: TextSpan(
          text: _fa(day),
          style: TextStyle(color: labelColor, fontSize: 9, fontWeight: FontWeight.w500),
        ),
        textDirection: TextDirection.rtl,
      )..layout();
      final x = size.width - (day - .5) * slot - painter.width / 2;
      painter.paint(canvas, Offset(x, bottom + 6));
    }
  }

  @override
  bool shouldRepaint(covariant MonthlyBarsPainter oldDelegate) =>
      oldDelegate.values != values ||
      oldDelegate.doneColor != doneColor ||
      oldDelegate.pendingColor != pendingColor ||
      oldDelegate.gridColor != gridColor ||
      oldDelegate.labelColor != labelColor;
}

class _MonthSwitcher extends StatelessWidget {
  const _MonthSwitcher({required this.month, required this.onPrevious, required this.onNext});
  final Jalali month;
  final VoidCallback onPrevious;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _MonthArrow(icon: Icons.chevron_right_rounded, onTap: onPrevious),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 7),
          child: Text('${month.formatter.mN} ${_fa(month.year)}', style: TextStyle(color: _text(context), fontSize: 11, fontWeight: FontWeight.w800)),
        ),
        _MonthArrow(icon: Icons.chevron_left_rounded, onTap: onNext),
      ],
    );
  }
}

class _MonthArrow extends StatelessWidget {
  const _MonthArrow({required this.icon, required this.onTap});
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: .55),
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          child: SizedBox(width: 29, height: 29, child: Icon(icon, size: 18, color: _muted(context))),
        ),
      );
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label});
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
          const SizedBox(width: 5),
          Text(label, style: TextStyle(color: _muted(context), fontSize: 10)),
        ],
      );
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.label, required this.value, required this.color});
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 7),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: .5),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.w900)),
            const SizedBox(height: 3),
            Text(label, style: TextStyle(color: _muted(context), fontSize: 9)),
          ],
        ),
      );
}

class _MetricCardLarge extends StatelessWidget {
  const _MetricCardLarge({
    required this.icon,
    required this.label,
    required this.value,
    required this.detail,
    required this.tint,
    required this.accent,
  });
  final IconData icon;
  final String label;
  final String value;
  final String detail;
  final Color tint;
  final Color accent;

  @override
  Widget build(BuildContext context) => _SurfaceCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(color: tint, borderRadius: BorderRadius.circular(11)),
              child: Icon(icon, color: accent, size: 18),
            ),
            const SizedBox(height: 13),
            Text(label, style: TextStyle(color: _muted(context), fontSize: 10)),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(color: _text(context), fontSize: 22, fontWeight: FontWeight.w900)),
            const SizedBox(height: 2),
            Text(detail, style: TextStyle(color: _muted(context), fontSize: 9)),
          ],
        ),
      );
}

// -----------------------------------------------------------------------------
// Settings
// -----------------------------------------------------------------------------

class SettingsPage extends StatelessWidget {
  const SettingsPage({
    super.key,
    required this.themeMode,
    required this.remindersDefault,
    required this.onThemeChanged,
    required this.onRemindersDefaultChanged,
    required this.onRequestNotifications,
    required this.onClearAll,
    required this.taskCount,
  });

  final ThemeMode themeMode;
  final bool remindersDefault;
  final ValueChanged<ThemeMode> onThemeChanged;
  final ValueChanged<bool> onRemindersDefaultChanged;
  final VoidCallback onRequestNotifications;
  final VoidCallback onClearAll;
  final int taskCount;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(20, 21, 20, 35),
      children: [
        const _SectionTitle(title: 'تنظیمات', subtitle: 'رفتار و ظاهر روز را مطابق نیازت تنظیم کن.'),
        const SizedBox(height: 22),
        _SettingsGroup(
          title: 'ظاهر برنامه',
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(15, 15, 15, 13),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('پوستهٔ برنامه', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
                  const SizedBox(height: 11),
                  Row(
                    children: [
                      Expanded(child: _ThemeChoice(label: 'روشن', icon: Icons.light_mode_outlined, selected: themeMode == ThemeMode.light, onTap: () => onThemeChanged(ThemeMode.light))),
                      const SizedBox(width: 7),
                      Expanded(child: _ThemeChoice(label: 'تیره', icon: Icons.dark_mode_outlined, selected: themeMode == ThemeMode.dark, onTap: () => onThemeChanged(ThemeMode.dark))),
                      const SizedBox(width: 7),
                      Expanded(child: _ThemeChoice(label: 'سیستم', icon: Icons.brightness_auto_rounded, selected: themeMode == ThemeMode.system, onTap: () => onThemeChanged(ThemeMode.system))),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 15),
        _SettingsGroup(
          title: 'یادآوری‌ها',
          children: [
            SwitchListTile.adaptive(
              value: remindersDefault,
              onChanged: kIsWeb ? null : onRemindersDefaultChanged,
              activeTrackColor: _accent,
              title: const Text('فعال بودن پیش‌فرض یادآوری', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
              subtitle: Text(
                kIsWeb ? 'در نسخهٔ مرورگر یادآوری زمان‌بندی‌شده پشتیبانی نمی‌شود.' : 'برای کارهای جدید، یادآوری به‌صورت پیش‌فرض روشن باشد.',
                style: TextStyle(color: _muted(context), fontSize: 10),
              ),
            ),
            Divider(height: 1, indent: 15, endIndent: 15, color: scheme.outline),
            ListTile(
              onTap: onRequestNotifications,
              leading: const Icon(Icons.notifications_active_outlined),
              title: const Text('دسترسی اعلان‌ها', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
              subtitle: Text('درخواست مجوز نمایش اعلان از سیستم‌عامل', style: TextStyle(color: _muted(context), fontSize: 10)),
              trailing: const Icon(Icons.chevron_left_rounded),
            ),
          ],
        ),
        const SizedBox(height: 15),
        _SettingsGroup(
          title: 'داده‌ها',
          children: [
            ListTile(
              leading: const Icon(Icons.storage_outlined),
              title: const Text('ذخیره‌سازی روی دستگاه', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
              subtitle: Text('${_fa(taskCount)} کار در حافظهٔ محلی برنامه ثبت شده است.', style: TextStyle(color: _muted(context), fontSize: 10)),
            ),
            Divider(height: 1, indent: 15, endIndent: 15, color: scheme.outline),
            ListTile(
              onTap: taskCount == 0 ? null : onClearAll,
              leading: const Icon(Icons.delete_outline_rounded, color: _coral),
              title: const Text('پاک‌کردن همهٔ کارها', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: _coral)),
              subtitle: Text('این عملیات قابل بازگشت نیست.', style: TextStyle(color: _muted(context), fontSize: 10)),
            ),
          ],
        ),
        const SizedBox(height: 22),
        Center(
          child: Column(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(color: _accentSoft, borderRadius: BorderRadius.circular(14)),
                child: const Icon(Icons.done_all_rounded, color: _accent),
              ),
              const SizedBox(height: 8),
              Text('روز', style: TextStyle(color: _text(context), fontSize: 15, fontWeight: FontWeight.w900)),
              Text('نسخهٔ ۱.۱.۰  •  برنامه‌ریزی ساده و متمرکز', style: TextStyle(color: _muted(context), fontSize: 10)),
            ],
          ),
        ),
      ],
    );
  }
}

class _SettingsGroup extends StatelessWidget {
  const _SettingsGroup({required this.title, required this.children});
  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(right: 4, bottom: 8),
            child: Text(title, style: TextStyle(color: _muted(context), fontSize: 11, fontWeight: FontWeight.w800)),
          ),
          _SurfaceCard(padding: EdgeInsets.zero, child: Column(children: children)),
        ],
      );
}

class _ThemeChoice extends StatelessWidget {
  const _ThemeChoice({required this.label, required this.icon, required this.selected, required this.onTap});
  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: selected ? scheme.primaryContainer : scheme.surfaceContainerHighest.withValues(alpha: .55),
      borderRadius: BorderRadius.circular(13),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(13),
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 10),
          child: Column(
            children: [
              Icon(icon, size: 18, color: selected ? scheme.primary : _muted(context)),
              const SizedBox(height: 4),
              Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: selected ? scheme.primary : _muted(context))),
            ],
          ),
        ),
      ),
    );
  }
}

// -----------------------------------------------------------------------------
// Task card, empty state and common surfaces
// -----------------------------------------------------------------------------

class TaskCard extends StatelessWidget {
  const TaskCard({
    super.key,
    required this.task,
    required this.onToggle,
    required this.onEdit,
    required this.onDelete,
  });

  final TaskItem task;
  final VoidCallback onToggle;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final categoryColor = _categoryColor(task.category);
    return Material(
      color: scheme.surface,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        onTap: onEdit,
        borderRadius: BorderRadius.circular(18),
        child: Container(
          padding: const EdgeInsets.fromLTRB(12, 11, 13, 11),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: scheme.outline.withValues(alpha: .7)),
          ),
          child: Row(
            children: [
              InkWell(
                onTap: onToggle,
                customBorder: const CircleBorder(),
                child: Container(
                  width: 25,
                  height: 25,
                  decoration: BoxDecoration(
                    color: task.isDone ? _accent : Colors.transparent,
                    shape: BoxShape.circle,
                    border: Border.all(color: task.isDone ? _accent : scheme.outline, width: 1.6),
                  ),
                  child: task.isDone ? const Icon(Icons.check_rounded, color: Colors.white, size: 16) : null,
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: task.isDone ? _muted(context) : _text(context),
                        fontSize: 13,
                        fontWeight: FontWeight.w800,
                        decoration: task.isDone ? TextDecoration.lineThrough : null,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 10,
                      runSpacing: 5,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        _TaskMeta(icon: Icons.label_outline_rounded, label: task.category, color: categoryColor),
                        if (task.reminderAt != null)
                          _TaskMeta(icon: Icons.notifications_none_rounded, label: _time(task.reminderAt!), color: _muted(context)),
                      ],
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                tooltip: 'گزینه‌های کار',
                onSelected: (value) {
                  if (value == 'edit') onEdit();
                  if (value == 'delete') onDelete();
                },
                itemBuilder: (_) => const [
                  PopupMenuItem(value: 'edit', child: ListTile(leading: Icon(Icons.edit_outlined), title: Text('ویرایش'), dense: true)),
                  PopupMenuItem(value: 'delete', child: ListTile(leading: Icon(Icons.delete_outline_rounded, color: _coral), title: Text('حذف'), dense: true)),
                ],
                child: Padding(
                  padding: const EdgeInsets.all(6),
                  child: Icon(Icons.more_horiz_rounded, color: _muted(context), size: 21),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TaskMeta extends StatelessWidget {
  const _TaskMeta({required this.icon, required this.label, required this.color});
  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w600)),
        ],
      );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.title, required this.subtitle, required this.onAdd});
  final String title;
  final String subtitle;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) => _SurfaceCard(
        child: Column(
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: const BoxDecoration(color: _accentSoft, shape: BoxShape.circle),
              child: const Icon(Icons.event_note_rounded, color: _accent, size: 24),
            ),
            const SizedBox(height: 12),
            Text(title, style: TextStyle(color: _text(context), fontSize: 14, fontWeight: FontWeight.w900)),
            const SizedBox(height: 5),
            Text(subtitle, textAlign: TextAlign.center, style: TextStyle(color: _muted(context), fontSize: 11)),
            const SizedBox(height: 11),
            TextButton.icon(onPressed: onAdd, icon: const Icon(Icons.add_rounded, size: 17), label: const Text('افزودن کار')),
          ],
        ),
      );
}

class _SurfaceCard extends StatelessWidget {
  const _SurfaceCard({required this.child, this.padding = const EdgeInsets.all(16)});
  final Widget child;
  final EdgeInsetsGeometry padding;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: padding,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surface,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: Theme.of(context).colorScheme.outline.withValues(alpha: .65)),
        ),
        child: child,
      );
}

// -----------------------------------------------------------------------------
// Create / edit task sheet
// -----------------------------------------------------------------------------

class TaskEditorSheet extends StatefulWidget {
  const TaskEditorSheet({
    super.key,
    required this.initialDate,
    required this.remindersDefault,
    this.task,
  });

  final DateTime initialDate;
  final bool remindersDefault;
  final TaskItem? task;

  @override
  State<TaskEditorSheet> createState() => _TaskEditorSheetState();
}

class _TaskEditorSheetState extends State<TaskEditorSheet> {
  late final TextEditingController _titleController;
  late DateTime _date;
  late TimeOfDay _time;
  late bool _reminderEnabled;
  late String _category;
  String? _validationError;

  static const List<String> _categories = ['شخصی', 'مطالعه', 'کار', 'سلامت'];

  @override
  void initState() {
    super.initState();
    final task = widget.task;
    _titleController = TextEditingController(text: task?.title ?? '');
    _date = _dateOnly(task?.date ?? widget.initialDate);
    final initialReminder = task?.reminderAt ?? DateTime.now().add(const Duration(hours: 1));
    _time = TimeOfDay(hour: initialReminder.hour, minute: initialReminder.minute);
    _reminderEnabled = !kIsWeb && (task?.reminderAt != null || (task == null && widget.remindersDefault));
    _category = task != null && _categories.contains(task.category) ? task.category : 'شخصی';
  }

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  Future<void> _chooseDate() async {
    final now = _dateOnly(DateTime.now());
    final picked = await showDialog<Jalali>(
      context: context,
      builder: (_) => JalaliDatePickerDialog(
        initialDate: Jalali.fromDateTime(_date),
        firstDate: Jalali.fromDateTime(now.subtract(const Duration(days: 3650))),
        lastDate: Jalali.fromDateTime(now.add(const Duration(days: 365 * 5))),
      ),
    );
    if (picked != null) setState(() => _date = _dateOnly(picked.toDateTime()));
  }

  Future<void> _chooseTime() async {
    final picked = await showTimePicker(
      context: context,
      initialTime: _time,
      builder: (context, child) => Directionality(textDirection: TextDirection.rtl, child: child!),
    );
    if (picked != null) setState(() => _time = picked);
  }

  void _save() {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      setState(() => _validationError = 'عنوان کار را وارد کن.');
      return;
    }
    DateTime? reminder;
    if (_reminderEnabled) {
      reminder = DateTime(_date.year, _date.month, _date.day, _time.hour, _time.minute);
      if (!reminder.isAfter(DateTime.now())) {
        setState(() => _validationError = 'زمان یادآوری باید در آینده باشد.');
        return;
      }
    }
    final old = widget.task;
    final now = DateTime.now();
    final result = TaskItem(
      id: old?.id ?? now.millisecondsSinceEpoch.remainder(0x7fffffff),
      title: title,
      date: _date,
      createdAt: old?.createdAt ?? now,
      reminderAt: reminder,
      isDone: old?.isDone ?? false,
      category: _category,
    );
    Navigator.pop(context, result);
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.task != null;
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;
    return Container(
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(27)),
      ),
      padding: EdgeInsets.fromLTRB(20, 12, 20, 20 + bottomInset),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(child: Container(width: 40, height: 4, decoration: BoxDecoration(color: Theme.of(context).colorScheme.outline, borderRadius: BorderRadius.circular(5)))),
              const SizedBox(height: 20),
              Text(isEditing ? 'ویرایش کار' : 'کار تازه', style: TextStyle(color: _text(context), fontSize: 21, fontWeight: FontWeight.w900)),
              const SizedBox(height: 15),
              TextField(
                controller: _titleController,
                autofocus: true,
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _save(),
                onChanged: (_) {
                  if (_validationError != null) setState(() => _validationError = null);
                },
                decoration: const InputDecoration(
                  hintText: 'مثلاً مطالعهٔ معادلات دیفرانسیل',
                  prefixIcon: Icon(Icons.edit_note_rounded),
                ),
              ),
              if (_validationError != null) ...[
                const SizedBox(height: 7),
                Text(_validationError!, style: const TextStyle(color: _coral, fontSize: 11)),
              ],
              const SizedBox(height: 17),
              Text('دسته‌بندی', style: TextStyle(color: _muted(context), fontSize: 11, fontWeight: FontWeight.w800)),
              const SizedBox(height: 9),
              Wrap(
                spacing: 7,
                runSpacing: 7,
                children: _categories.map((category) {
                  final selected = _category == category;
                  return ChoiceChip(
                    label: Text(category),
                    selected: selected,
                    onSelected: (_) => setState(() => _category = category),
                    selectedColor: _accentSoft,
                    labelStyle: TextStyle(color: selected ? _accent : _muted(context), fontSize: 11, fontWeight: FontWeight.w700),
                    side: BorderSide(color: selected ? _accent.withValues(alpha: .35) : Theme.of(context).colorScheme.outline),
                    showCheckmark: false,
                  );
                }).toList(),
              ),
              const SizedBox(height: 15),
              _EditorOption(
                icon: Icons.calendar_today_outlined,
                title: 'تاریخ انجام',
                value: _shortDate(_date),
                onTap: _chooseDate,
              ),
              SwitchListTile.adaptive(
                contentPadding: EdgeInsets.zero,
                value: _reminderEnabled,
                onChanged: kIsWeb ? null : (value) => setState(() => _reminderEnabled = value),
                activeTrackColor: _accent,
                title: const Text('یادآوری با اعلان', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                subtitle: Text(
                  kIsWeb ? 'در نسخهٔ مرورگر اعلان زمان‌بندی‌شده فعال نیست.' : 'در زمان تعیین‌شده روی گوشی اعلان می‌بینی.',
                  style: TextStyle(color: _muted(context), fontSize: 10),
                ),
              ),
              if (_reminderEnabled)
                _EditorOption(
                  icon: Icons.notifications_none_rounded,
                  title: 'ساعت یادآوری',
                  value: _timeText(_time),
                  onTap: _chooseTime,
                ),
              const SizedBox(height: 17),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _save,
                  style: FilledButton.styleFrom(
                    backgroundColor: _accent,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 15),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
                  ),
                  child: Text(isEditing ? 'ذخیرهٔ تغییرات' : 'ذخیرهٔ کار', style: const TextStyle(fontWeight: FontWeight.w900)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EditorOption extends StatelessWidget {
  const _EditorOption({required this.icon, required this.title, required this.value, required this.onTap});
  final IconData icon;
  final String title;
  final String value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
        onTap: onTap,
        dense: true,
        contentPadding: EdgeInsets.zero,
        leading: Icon(icon, color: _muted(context), size: 19),
        title: Text(title, style: TextStyle(color: _text(context), fontSize: 12, fontWeight: FontWeight.w800)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(value, style: TextStyle(color: _muted(context), fontSize: 11)),
            const SizedBox(width: 4),
            Icon(Icons.chevron_left_rounded, color: _muted(context), size: 17),
          ],
        ),
      );
}

// -----------------------------------------------------------------------------
// Jalali date picker
// -----------------------------------------------------------------------------

class JalaliDatePickerDialog extends StatefulWidget {
  const JalaliDatePickerDialog({
    super.key,
    required this.initialDate,
    required this.firstDate,
    required this.lastDate,
  });

  final Jalali initialDate;
  final Jalali firstDate;
  final Jalali lastDate;

  @override
  State<JalaliDatePickerDialog> createState() => _JalaliDatePickerDialogState();
}

class _JalaliDatePickerDialogState extends State<JalaliDatePickerDialog> {
  late Jalali _selected;
  late Jalali _visibleMonth;

  @override
  void initState() {
    super.initState();
    _selected = widget.initialDate;
    _visibleMonth = widget.initialDate.copy(day: 1);
  }

  bool _allowed(Jalali date) {
    final value = _dateOnly(date.toDateTime());
    return !value.isBefore(_dateOnly(widget.firstDate.toDateTime())) &&
        !value.isAfter(_dateOnly(widget.lastDate.toDateTime()));
  }

  bool get _canPrevious {
    final candidate = _visibleMonth.addMonths(-1);
    return candidate.year > widget.firstDate.year ||
        (candidate.year == widget.firstDate.year && candidate.month >= widget.firstDate.month);
  }

  bool get _canNext {
    final candidate = _visibleMonth.addMonths(1);
    return candidate.year < widget.lastDate.year ||
        (candidate.year == widget.lastDate.year && candidate.month <= widget.lastDate.month);
  }

  @override
  Widget build(BuildContext context) {
    final firstWeekDay = Jalali(_visibleMonth.year, _visibleMonth.month, 1).weekDay;
    final leading = firstWeekDay - 1;
    final days = _visibleMonth.monthLength;
    final cells = ((leading + days + 6) ~/ 7) * 7;
    return AlertDialog(
      backgroundColor: Theme.of(context).colorScheme.surface,
      surfaceTintColor: Colors.transparent,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(23)),
      titlePadding: const EdgeInsets.fromLTRB(18, 18, 18, 8),
      contentPadding: const EdgeInsets.fromLTRB(15, 5, 15, 16),
      title: Row(
        children: [
          const Expanded(child: Text('انتخاب تاریخ شمسی', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900))),
          IconButton(
            visualDensity: VisualDensity.compact,
            onPressed: _canPrevious ? () => setState(() => _visibleMonth = _visibleMonth.addMonths(-1).copy(day: 1)) : null,
            icon: const Icon(Icons.chevron_right_rounded),
          ),
          Text('${_visibleMonth.formatter.mN} ${_fa(_visibleMonth.year)}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800)),
          IconButton(
            visualDensity: VisualDensity.compact,
            onPressed: _canNext ? () => setState(() => _visibleMonth = _visibleMonth.addMonths(1).copy(day: 1)) : null,
            icon: const Icon(Icons.chevron_left_rounded),
          ),
        ],
      ),
      content: SizedBox(
        width: 320,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Row(
              children: [
                _WeekdayLabel('ش'), _WeekdayLabel('ی'), _WeekdayLabel('د'), _WeekdayLabel('س'),
                _WeekdayLabel('چ'), _WeekdayLabel('پ'), _WeekdayLabel('ج'),
              ],
            ),
            const SizedBox(height: 8),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: cells,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 7,
                mainAxisSpacing: 4,
                crossAxisSpacing: 3,
                childAspectRatio: 1,
              ),
              itemBuilder: (context, index) {
                final day = index - leading + 1;
                if (day < 1 || day > days) return const SizedBox.shrink();
                final date = Jalali(_visibleMonth.year, _visibleMonth.month, day);
                final selected = date.year == _selected.year && date.month == _selected.month && date.day == _selected.day;
                final today = date.year == Jalali.now().year && date.month == Jalali.now().month && date.day == Jalali.now().day;
                final allowed = _allowed(date);
                return Material(
                  color: selected ? _accent : (today ? _accentSoft : Colors.transparent),
                  shape: const CircleBorder(),
                  child: InkWell(
                    customBorder: const CircleBorder(),
                    onTap: allowed ? () => setState(() => _selected = date) : null,
                    child: Center(
                      child: Text(
                        _fa(day),
                        style: TextStyle(
                          color: !allowed ? _muted(context).withValues(alpha: .4) : selected ? Colors.white : _text(context),
                          fontSize: 12,
                          fontWeight: selected || today ? FontWeight.w900 : FontWeight.w500,
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 13),
            Row(
              children: [
                TextButton(onPressed: () => Navigator.pop(context), child: const Text('انصراف')),
                const Spacer(),
                FilledButton(
                  onPressed: () => Navigator.pop(context, _selected),
                  style: FilledButton.styleFrom(backgroundColor: _accent, foregroundColor: Colors.white),
                  child: const Text('انتخاب تاریخ'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// -----------------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------------

int _taskSort(TaskItem a, TaskItem b) {
  if (a.isDone != b.isDone) return a.isDone ? 1 : -1;
  final byDate = a.date.compareTo(b.date);
  if (byDate != 0) return byDate;
  if (a.reminderAt == null && b.reminderAt != null) return 1;
  if (a.reminderAt != null && b.reminderAt == null) return -1;
  if (a.reminderAt == null || b.reminderAt == null) return 0;
  return a.reminderAt!.compareTo(b.reminderAt!);
}

DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);

String _fa(Object value) {
  const english = '0123456789';
  const persian = '۰۱۲۳۴۵۶۷۸۹';
  var text = value.toString();
  for (var i = 0; i < english.length; i++) {
    text = text.replaceAll(english[i], persian[i]);
  }
  return text;
}

String _jalaliDate(Jalali value) => '${_fa(value.day)} ${value.formatter.mN} ${_fa(value.year)}';
String _shortDate(DateTime value) => _jalaliDate(Jalali.fromDateTime(value));
String _fullDate(DateTime value) {
  final jalali = Jalali.fromDateTime(value);
  return '${jalali.formatter.wN}، ${_jalaliDate(jalali)}';
}

String _time(DateTime value) => '${_fa(value.hour.toString().padLeft(2, '0'))}:${_fa(value.minute.toString().padLeft(2, '0'))}';
String _timeText(TimeOfDay value) => '${_fa(value.hour.toString().padLeft(2, '0'))}:${_fa(value.minute.toString().padLeft(2, '0'))}';

String _weekdayShort(int weekday) {
  const names = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج'];
  final index = (weekday - 1).clamp(0, 6).toInt();
  return names[index];
}

Color _text(BuildContext context) => Theme.of(context).colorScheme.onSurface;
Color _muted(BuildContext context) => Theme.of(context).colorScheme.onSurface.withValues(alpha: .58);

Color _categoryColor(String category) => switch (category) {
      'مطالعه' => const Color(0xFF527BAA),
      'کار' => const Color(0xFFB07B35),
      'سلامت' => const Color(0xFFB66A7D),
      _ => _accent,
    };
