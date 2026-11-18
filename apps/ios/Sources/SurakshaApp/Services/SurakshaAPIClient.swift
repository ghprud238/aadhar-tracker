import Foundation

public struct APIEnvelope<T: Codable & Sendable>: Codable, Sendable {
    public let data: T
}

public actor SurakshaAPIClient {
    public static let shared = SurakshaAPIClient()

    private let baseURL: URL
    private var sessionToken: String?
    private var cachedEtag: String?
    private var cachedBootstrap: MobileBootstrapPayload?

    public init(baseURL: URL = URL(string: "http://127.0.0.1:8000/api/v1")!) {
        self.baseURL = baseURL
    }

    public func authenticate(email: String = "resident@example.com") async throws -> String {
        let authURL = baseURL.appendingPathComponent("auth/callback")
        var components = URLComponents(url: authURL, resolvingAgainstBaseURL: true)!
        components.queryItems = [URLQueryItem(name: "email", value: email)]

        let (data, response) = try await URLSession.shared.data(from: components.url!)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let dataObj = json?["data"] as? [String: Any],
              let token = dataObj["session_id"] as? String else {
            throw URLError(.cannotParseResponse)
        }

        self.sessionToken = token
        return token
    }

    public func fetchBootstrap() async throws -> MobileBootstrapPayload {
        if sessionToken == nil {
            _ = try await authenticate()
        }

        let url = baseURL.appendingPathComponent("mobile/bootstrap")
        var request = URLRequest(url: url)
        request.setValue("Bearer \(sessionToken!)", forHTTPHeaderField: "Authorization")
        if let etag = cachedEtag {
            request.setValue(etag, forHTTPHeaderField: "If-None-Match")
        }

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        if httpResponse.statusCode == 304, let cached = cachedBootstrap {
            return cached
        }

        guard httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        if let etag = httpResponse.allHeaderFields["ETag"] as? String {
            self.cachedEtag = etag
        }

        let decoded = try JSONDecoder().decode(APIEnvelope<MobileBootstrapPayload>.self, from: data)
        self.cachedBootstrap = decoded.data
        return decoded.data
    }

    public func fetchActivity() async throws -> MobileActivityPayload {
        if sessionToken == nil {
            _ = try await authenticate()
        }

        let url = baseURL.appendingPathComponent("mobile/activity")
        var request = URLRequest(url: url)
        request.setValue("Bearer \(sessionToken!)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoded = try JSONDecoder().decode(APIEnvelope<MobileActivityPayload>.self, from: data)
        return decoded.data
    }

    public func analyzeScam(message: String, channel: String = "video_call", sender: String? = nil) async throws -> ScamAnalysisData {
        if sessionToken == nil {
            _ = try await authenticate()
        }

        let url = baseURL.appendingPathComponent("mobile/scam-radar/analyze")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(sessionToken!)", forHTTPHeaderField: "Authorization")

        var body: [String: Any] = [
            "message_text": message,
            "channel": channel
        ]
        if let s = sender { body["sender_header"] = s }
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoded = try JSONDecoder().decode(APIEnvelope<ScamAnalysisData>.self, from: data)
        return decoded.data
    }

    public func verifyQR(rawQR: String) async throws -> PassVerificationData {
        if sessionToken == nil {
            _ = try await authenticate()
        }

        let url = baseURL.appendingPathComponent("mobile/qr/verify")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(sessionToken!)", forHTTPHeaderField: "Authorization")

        let body: [String: Any] = [
            "raw_qr_payload": rawQR,
            "verifier_entity": "Suraksha Native iOS App"
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }

        let decoded = try JSONDecoder().decode(APIEnvelope<PassVerificationData>.self, from: data)
        return decoded.data
    }

    public func toggleAutoRelock(action: String, seconds: Int = 600) async throws {
        if sessionToken == nil {
            _ = try await authenticate()
        }

        let url = baseURL.appendingPathComponent("mobile/biometric/auto-relock")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(sessionToken!)", forHTTPHeaderField: "Authorization")

        let body: [String: Any] = [
            "action": action,
            "duration_seconds": seconds
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (_, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
    }
}
