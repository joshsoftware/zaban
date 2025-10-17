require "net/http"
require "uri"
require "json"
require "securerandom"

module Ai4Bharat
  class BaseService
    DEFAULT_TIMEOUT = 60

    def initialize(api_key: ENV["AI4B_API_KEY"])
      @api_key = api_key
    end

    private

    def build_uri(url)
      URI.parse(url)
    end

    def default_headers
      headers = { "Accept" => "application/json" }
      headers["Authorization"] = "Bearer #{@api_key}" if @api_key && !@api_key.empty?
      headers
    end

    def http_client_for(uri)
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = uri.scheme == "https"
      http.read_timeout = DEFAULT_TIMEOUT
      http.open_timeout = DEFAULT_TIMEOUT
      http
    end

    def post_json(url, payload, extra_headers: {})
      uri = build_uri(url)
      http = http_client_for(uri)
      request = Net::HTTP::Post.new(uri.request_uri, default_headers.merge({ "Content-Type" => "application/json" }).merge(extra_headers))
      request.body = payload.to_json
      response = http.request(request)
      parse_response(response)
    end

    def post_multipart(url, form_data_hash, extra_headers: {})
      uri = build_uri(url)
      http = http_client_for(uri)

      boundary = "----RubyFormBoundary#{SecureRandom.hex(16)}"
      body = multipart_body(form_data_hash, boundary)

      headers = default_headers.merge({
        "Content-Type" => "multipart/form-data; boundary=#{boundary}",
        "Content-Length" => body.bytesize.to_s
      }).merge(extra_headers)

      request = Net::HTTP::Post.new(uri.request_uri, headers)
      request.body = body
      response = http.request(request)
      parse_response(response)
    end

    def multipart_body(form_hash, boundary)
      lines = []
      form_hash.each do |key, value|
        lines << "--#{boundary}"
        if value.is_a?(Hash) && value[:filename]
          filename = value[:filename]
          content = value[:content]
          content_type = value[:content_type] || "application/octet-stream"
          lines << "Content-Disposition: form-data; name=\"#{key}\"; filename=\"#{filename}\""
          lines << "Content-Type: #{content_type}"
          lines << ""
          lines << content
        else
          lines << "Content-Disposition: form-data; name=\"#{key}\""
          lines << ""
          lines << value.to_s
        end
      end
      lines << "--#{boundary}--"
      lines << ""
      lines.join("\r\n")
    end

    def parse_response(response)
      code = response.code.to_i
      if code >= 200 && code < 300
        begin
          JSON.parse(response.body && !response.body.empty? ? response.body : "{}")
        rescue JSON::ParserError
          { "raw" => response.body }
        end
      else
        raise StandardError, "AI4Bharat API error: #{code} #{response.body}"
      end
    end
  end
end



