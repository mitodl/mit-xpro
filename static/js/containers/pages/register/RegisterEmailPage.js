// @flow
import React from "react"
import { compose } from "redux"
import { connect } from "react-redux"
import { mutateAsync } from "redux-query"
import { createStructuredSelector } from "reselect"

import { addUserNotification } from "../../../actions"
import queries from "../../../lib/queries"
import {
  STATE_ERROR,
  STATE_REGISTER_CONFIRM_SENT,
  STATE_LOGIN_PASSWORD,
  handleAuthResponse
} from "../../../lib/auth"
import { qsNextSelector } from "../../../lib/selectors"
import { ALERT_TYPE_TEXT } from "../../../constants"

import RegisterEmailForm from "../../../components/forms/RegisterEmailForm"

import type { RouterHistory, Location } from "react-router"
import type { Response } from "redux-query"
import type { AuthResponse } from "../../../flow/authTypes"
import type { RegisterEmailFormValues } from "../../../components/forms/RegisterEmailForm"

type Props = {
  location: Location,
  history: RouterHistory,
  params: { next: string },
  registerEmail: (
    email: string,
    recaptcha: ?string,
    next: ?string
  ) => Promise<Response<AuthResponse>>,
  addUserNotification: Function
}

const emailNotificationText = (email: string): string =>
  `We sent an email to ${email}. Please verify your address to continue.`

const accountExistsNotificationText = (email: string): string =>
  `You already have an account with ${email}. Enter password to sign in.`
export class RegisterEmailPage extends React.Component<Props> {
  async onSubmit(
    { email, recaptcha }: RegisterEmailFormValues,
    { setSubmitting, setErrors }: any
  ) {
    const {
      addUserNotification,
      registerEmail,
      params: { next },
      history
    } = this.props

    try {
      const { body } = await registerEmail(email, recaptcha, next)

      handleAuthResponse(history, body, {
        [STATE_REGISTER_CONFIRM_SENT]: () => {
          addUserNotification({
            "email-sent": {
              type:  ALERT_TYPE_TEXT,
              props: {
                text: emailNotificationText(email)
              }
            }
          })
        },
        [STATE_LOGIN_PASSWORD]: () => {
          addUserNotification({
            "account-exists": {
              type:  ALERT_TYPE_TEXT,
              color: "danger",
              props: {
                text: accountExistsNotificationText(email)
              }
            }
          })
        },
        // eslint-disable-next-line camelcase
        [STATE_ERROR]: ({ field_errors }: AuthResponse) =>
          setErrors(field_errors)
      })
    } finally {
      setSubmitting(false)
    }
  }

  render() {
    return (
      <div className="container auth-page">
        <div className="row">
          <h1 className="col-12">Create Account</h1>
        </div>
        <div className="auth-form auth-card card-shadow row">
          <div className="col-12">
            <RegisterEmailForm onSubmit={this.onSubmit.bind(this)} />
          </div>
        </div>
      </div>
    )
  }
}

const mapStateToProps = createStructuredSelector({
  params: createStructuredSelector({
    next: qsNextSelector
  })
})

const registerEmail = (email: string, recaptcha: ?string, nextUrl: ?string) =>
  mutateAsync(queries.auth.registerEmailMutation(email, recaptcha, nextUrl))

const mapDispatchToProps = {
  registerEmail,
  addUserNotification
}

export default compose(
  connect(
    mapStateToProps,
    mapDispatchToProps
  )
)(RegisterEmailPage)
