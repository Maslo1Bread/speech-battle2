import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:speech/main.dart';
import 'package:speech/session/session_controller.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Splash then login screen', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(SpeechBattleApp(session: SessionController()));
    expect(find.text('Speech-Battle'), findsOneWidget);
    await tester.pump(const Duration(milliseconds: 2300));
    expect(find.text('Войти'), findsOneWidget);
  });
}
