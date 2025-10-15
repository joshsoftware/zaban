module Api
  module V1
    class AuthController < ApplicationController
      # Skip authentication for signup and signin
      skip_before_action :authenticate_request, only: [:signup, :signin]

      # POST /api/v1/signup
      def signup
        user = User.new(user_params)
        if user.save
          token = JsonWebToken.encode(user_id: user.id)
          render json: { token:, user: user.slice(:id, :email, :first_name, :last_name) }, status: :created
        else
          render json: { errors: user.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # POST /api/v1/signin
      def signin
        user = User.find_by(email: params[:email])
        if user&.authenticate(params[:password])
          token = JsonWebToken.encode(user_id: user.id)
          render json: { token:, user: user.slice(:id, :email, :first_name, :last_name) }, status: :ok
        else
          render json: { error: "Invalid email or password" }, status: :unauthorized
        end
      end

      private

      def user_params
        params.permit(:first_name, :last_name, :email, :password, :password_confirmation)
      end
    end
  end
end
