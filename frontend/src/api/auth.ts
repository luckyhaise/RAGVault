import { apiRequest } from "./client"
import {  type CreateAccount, type CreateAccountRequest,type CreateAccountResponse, type CreateRequestResponse } from "../types/auth_types"

const base_URL = new URL("http://localhost:8000/api/v1/user")


export async function requestCreateAccount(data: CreateAccountRequest): Promise<CreateRequestResponse> {
  return await   apiRequest<CreateRequestResponse>(
    data, `${base_URL}/request-create`
    ,"application/json"
  )
}







export async function verifyAndCreateAccount(data: CreateAccount): Promise<CreateAccountResponse>{
  return await apiRequest<CreateAccountResponse>(data,base_URL+"/create","application/json")
}
