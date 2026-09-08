


export interface CreateAccountRequest {
  user_name: string;
  email: string;
  phone:string
  password: string;
  name: string;
  
}
export interface CreateAccount extends CreateAccountRequest{
  otp_id: string;
  otp:string
}

export interface CreateRequestResponse {
  otp_id: string;
  celery_id: string;
}
export interface CreateAccountResponse {
    access_token: string;
    refresh_token: string;
  }