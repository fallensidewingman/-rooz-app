import 'package:flutter_test/flutter_test.dart';
import 'package:rooz_app/main.dart';

void main() {
  group('Rooz weekly tasks', () {
    final saturday = DateTime(2026, 11, 7);
    final monday = DateTime(2026, 11, 9);
    final wednesday = DateTime(2026, 11, 11);
    final sunday = DateTime(2026, 11, 8);

    test('projects a recurring task onto selected weekdays only', () {
      final task = TaskItem(
        id: 1,
        title: 'مطالعه',
        date: saturday,
        createdAt: saturday,
        repeatWeekdays: const [6, 1, 3],
      );
      expect(task.occursOn(saturday), isTrue);
      expect(task.occursOn(monday), isTrue);
      expect(task.occursOn(wednesday), isTrue);
      expect(task.occursOn(sunday), isFalse);
    });

    test('stores completion separately for each occurrence', () {
      final task = TaskItem(
        id: 2,
        title: 'زبان',
        date: saturday,
        createdAt: saturday,
        repeatWeekdays: const [6, 1],
      );
      final updated = task.withOccurrenceDone(monday, true);
      expect(updated.isDoneOn(monday), isTrue);
      expect(updated.isDoneOn(saturday), isFalse);
    });

    test('loads an old task record without recurrence fields', () {
      final task = TaskItem.fromJson({
        'id': 3,
        'title': 'کار قدیمی',
        'date': '2026-11-07T00:00:00.000',
        'createdAt': '2026-11-06T12:00:00.000',
        'isDone': false,
        'category': 'شخصی',
      });
      expect(task.isRecurring, isFalse);
      expect(task.occursOn(saturday), isTrue);
      expect(task.occursOn(monday), isFalse);
    });

    test('parses Jalali dates and weekdays from a .rooz plan', () {
      final plan = RoozPlanImport.parse('''
        {
          "format": "rooz",
          "version": 1,
          "calendar": "jalali",
          "title": "برنامه تست",
          "tasks": [
            {
              "title": "تمرین",
              "date": "1405-08-16",
              "repeatWeekdays": [6, 1, 3]
            }
          ]
        }
      ''');
      expect(plan.tasks, hasLength(1));
      expect(plan.tasks.single.repeatWeekdays, [1, 3, 6]);
      expect(plan.tasks.single.date.weekday, 6);
    });
  });
}
