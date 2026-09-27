# Flutter wrapper
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# shared_preferences
-keep class androidx.datastore.** { *; }
-keep class com.google.android.** { *; }

# speech_to_text
-keep class com.csdcorp.speech_to_text.** { *; }

# Keep Kotlin metadata
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes SourceFile,LineNumberTable
