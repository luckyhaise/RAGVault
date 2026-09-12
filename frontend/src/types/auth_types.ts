// Request/response contracts for the /api/v1/user/* routes.

export interface LoginIdentifier {
  user_name?: string;
  email?: string;
}

export interface Login extends LoginIdentifier {
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string | null;
}

export interface CreateAccountRequest {
  user_name: string;
  email: string;

  password: string;
  name: string;
}

export interface CreateAccount extends CreateAccountRequest {
  otp_id: string;
  otp: string;
}

export interface CreateRequestResponse {
  otp_id: string;
  task_id: string;
}

export interface CreateAccountResponse {
  id: string;
  email: string;
  name: string;
}

export type ForgotPasswordRequest = LoginIdentifier;

export interface ForgotPasswordChange extends LoginIdentifier {
  new_password: string;
  otp: string;
  otp_id: string;
}

export interface ResetPassword {
  old_password: string;
  new_password: string;
}

// The authenticated user's account details, returned by GET /user/me.
export interface UserProfile {
  id: string;
  user_name: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

// The subset of the profile kept in memory/localStorage for display. It can be
// temporarily derived from login credentials until the API profile arrives.
export interface SessionUser {
  id?: string;
  user_name?: string;
  name?: string;
  email?: string;
  phone?: string;
}
