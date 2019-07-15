// @flow
import { nthArg } from "ramda"

import { FLOW_LOGIN, FLOW_REGISTER } from "../auth"

import type {
  AuthResponse,
  LegalAddress,
  ProfileForm
} from "../../flow/authTypes"

export const authSelector = (state: any) => state.entities.auth

// uses the next piece of state which is the second argument
const nextState = nthArg(1)

const DEFAULT_OPTIONS = {
  transform: (auth: AuthResponse) => ({ auth }),
  update:    {
    auth: nextState
  },
  options: {
    method: "POST"
  }
}

export default {
  loginEmailMutation: (email: string, next: ?string) => ({
    ...DEFAULT_OPTIONS,
    url:  "/api/login/email/",
    body: { email, next, flow: FLOW_LOGIN }
  }),

  loginPasswordMutation: (password: string, partialToken: string) => ({
    ...DEFAULT_OPTIONS,
    url:  "/api/login/password/",
    body: { password, partial_token: partialToken, flow: FLOW_LOGIN }
  }),

  registerEmailMutation: (
    email: string,
    recaptcha: ?string,
    next: ?string
  ) => ({
    ...DEFAULT_OPTIONS,
    url:  "/api/register/email/",
    body: { email, recaptcha, next, flow: FLOW_REGISTER }
  }),

  registerConfirmEmailMutation: (code: string, partialToken: string) => ({
    ...DEFAULT_OPTIONS,
    url:  "/api/register/confirm/",
    body: {
      verification_code: code,
      partial_token:     partialToken,
      flow:              FLOW_REGISTER
    }
  }),

  registerDetailsMutation: (
    name: string,
    password: string,
    legalAddress: LegalAddress,
    partialToken: string
  ) => ({
    ...DEFAULT_OPTIONS,
    url:  "/api/register/details/",
    body: {
      name,
      password,
      legal_address: legalAddress,
      flow:          FLOW_REGISTER,
      partial_token: partialToken
    }
  }),

  registerExtraDetailsMutation: (
    profileData: ProfileForm,
    partialToken: string
  ) => ({
    ...DEFAULT_OPTIONS,
    url:  "/api/register/extra/",
    body: {
      flow:          FLOW_REGISTER,
      partial_token: partialToken,
      ...profileData.profile
    }
  }),

  forgotPasswordMutation: (email: string) => ({
    url:  "/api/password_reset/",
    body: { email }
  }),

  forgotPasswordConfirmMutation: (
    newPassword: string,
    reNewPassword: string,
    token: string,
    uid: string
  ) => ({
    url:  "/api/password_reset/confirm/",
    body: {
      new_password:    newPassword,
      re_new_password: reNewPassword,
      token,
      uid
    }
  })
}
