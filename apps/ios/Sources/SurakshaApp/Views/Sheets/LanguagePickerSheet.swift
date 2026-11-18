import SwiftUI

public struct RegionalLanguage: Identifiable, Sendable {
    public var id: String { code }
    public let code: String
    public let name: String
    public let nativeName: String
    public let flag: String

    public init(code: String, name: String, nativeName: String, flag: String) {
        self.code = code
        self.name = name
        self.nativeName = nativeName
        self.flag = flag
    }
}

public let SUPPORTED_LANGUAGES: [RegionalLanguage] = [
    RegionalLanguage(code: "en", name: "English", nativeName: "English", flag: "🇬🇧"),
    RegionalLanguage(code: "hi", name: "Hindi", nativeName: "हिंदी", flag: "🇮🇳"),
    RegionalLanguage(code: "ta", name: "Tamil", nativeName: "தமிழ்", flag: "🇮🇳"),
    RegionalLanguage(code: "te", name: "Telugu", nativeName: "తెలుగు", flag: "🇮🇳"),
    RegionalLanguage(code: "bn", name: "Bengali", nativeName: "বাংলা", flag: "🇮🇳")
]

public struct LanguagePickerSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Binding public var currentLanguageCode: String
    public let onSelect: (String) -> Void

    public init(currentLanguageCode: Binding<String>, onSelect: @escaping (String) -> Void) {
        self._currentLanguageCode = currentLanguageCode
        self.onSelect = onSelect
    }

    public var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                Text("Powered by Project Bhashini Vernacular AI Engine")
                    .font(.system(size: 13))
                    .foregroundStyle(Color.secondary)
                    .padding(.horizontal, 20)

                List {
                    ForEach(SUPPORTED_LANGUAGES) { lang in
                        Button(action: {
                            currentLanguageCode = lang.code
                            onSelect(lang.code)
                            dismiss()
                        }) {
                            HStack {
                                Text(lang.flag)
                                    .font(.system(size: 24))

                                VStack(alignment: .leading, spacing: 2) {
                                    Text(lang.nativeName)
                                        .font(.system(size: 16, weight: .bold))
                                        .foregroundStyle(Color.primary)
                                    Text(lang.name)
                                        .font(.system(size: 12))
                                        .foregroundStyle(Color.secondary)
                                }

                                Spacer()

                                if currentLanguageCode == lang.code {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(Color(red: 0.22, green: 0.74, blue: 0.97))
                                        .font(.system(size: 20))
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
                #if os(iOS)
                .listStyle(.insetGrouped)
                #endif
            }
            .navigationTitle("🗣️ Regional Language")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}
