import { request } from "./client";
import { tokenStore } from "./tokenStore";
import type {
  CreateAccount,
  CreateAccountRequest,
  CreateAccountResponse,
  CreateRequestResponse,
  ForgotPasswordChange,
  ForgotPasswordRequest,
  Login,
  LoginResponse,
  RefreshTokenResponse,
  ResetPassword,
  SessionUser,
  UserProfile,
} from "../types/auth_types";

export interface MessageResponse {
  message?: string;
  detail?: string;
}

export function requestCreateAccount(
  payload: CreateAccountRequest,
): Promise<CreateRequestResponse> {
  return request({ path: "/user/request-create", body: payload, auth: "none" });
}

export function verifyAndCreateAccount(
  payload: CreateAccount,
): Promise<CreateAccountResponse> {
  return request({ path: "/user/create", body: payload, auth: "none" });
}

export function sendLoginRequest(payload: Login): Promise<LoginResponse> {
  return request({ path: "/user/login", body: payload, auth: "none" });
}

export function requestForgotPassword(
  payload: ForgotPasswordRequest,
): Promise<CreateRequestResponse> {
  return request({
    path: "/user/request-forgot-password",
    body: payload,
    auth: "none",
  });
}

export function resetForgottenPassword(
  payload: ForgotPasswordChange,
): Promise<MessageResponse> {
  return request({ path: "/user/forgot-password", body: payload, auth: "none" });
}

export function changePassword(payload: ResetPassword): Promise<MessageResponse> {
  return request({ path: "/user/change-password", body: payload });
}

/** Exchange the refresh token for a new access token and persist the pair. */
export async function refreshSession(): Promise<RefreshTokenResponse> {
  const result = await request<RefreshTokenResponse>({
    path: "/user/refresh-token",
    auth: "refresh",
  });
  tokenStore.setTokens(result.access_token, result.refresh_token);
  return result;
}

export function logoutSession(): Promise<MessageResponse> {
  return request({ path: "/user/logout", auth: "refresh" });
}

/** Fetch the authenticated user's own account details. */
export function fetchUserProfile(): Promise<UserProfile> {
  return request({ path: "/user/me", method: "GET" });
}

export function deriveSessionUser(payload: Login, fallbackName?: string): SessionUser {
  return {
    user_name: payload.user_name,
    email: payload.email,
    name: fallbackName,
  };
}
