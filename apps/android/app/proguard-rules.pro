# Suraksha Native Android Proguard Rules
-keepattributes *Annotation*
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class in.suraksha.app.data.model.** { *; }
