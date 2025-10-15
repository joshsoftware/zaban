class ApplicationController < ActionController::Base
  include ActionController::RequestForgeryProtection

  protect_from_forgery with: :null_session
  allow_browser versions: :modern
  before_action :authenticate_request

  private

  def authenticate_request
    header = request.headers['Authorization']
    header = header.split(' ').last if header.present?

    decoded = JsonWebToken.decode(header)
    @current_user = User.find(decoded[:user_id]) if decoded
  rescue ActiveRecord::RecordNotFound, JWT::DecodeError
    render json: { error: "Unauthorized" }, status: :unauthorized
  end
end
