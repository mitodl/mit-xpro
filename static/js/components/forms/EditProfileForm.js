// @flow
import React from "react"
import { isNil } from "ramda"
import { Formik, Form } from "formik"

import {
  profileValidation,
  legalAddressValidation,
  LegalAddressFields,
  ProfileFields
} from "./ProfileFormFields"

import type { Country, User } from "../../flow/authTypes"

type Props = {
  onSubmit: Function,
  countries: Array<Country>,
  user: User
}

const getInitialValues = (user: User) => ({
  name:          user.name,
  email:         user.email,
  legal_address: user.legal_address,
  profile:       {
    ...user.profile,
    // Should be null but React complains about null values in form fields. So we need to convert to
    // string and then back to null on submit.
    // $FlowFixMe
    job_function: isNil(user.profile.job_function)
      ? ""
      : user.profile.job_function,
    // $FlowFixMe
    company_size: isNil(user.profile.company_size)
      ? ""
      : user.profile.company_size,
    // $FlowFixMe
    leadership_level: isNil(user.profile.leadership_level)
      ? ""
      : user.profile.leadership_level,
    // $FlowFixMe
    years_experience: isNil(user.profile.years_experience)
      ? ""
      : user.profile.years_experience
  }
})

const EditProfileForm = ({ onSubmit, countries, user }: Props) => (
  <Formik
    onSubmit={onSubmit}
    validationSchema={legalAddressValidation.concat(profileValidation)}
    initialValues={getInitialValues(user)}
    render={({ isSubmitting, setFieldValue, setFieldTouched, values }) => (
      <Form>
        <LegalAddressFields
          countries={countries}
          setFieldValue={setFieldValue}
          setFieldTouched={setFieldTouched}
          values={values}
          includePassword={false}
        />
        <ProfileFields />
        <div className="row-inner justify-content-end">
          <div className="row justify-content-end">
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary btn-light-blue"
            >
              Continue
            </button>
          </div>
        </div>
      </Form>
    )}
  />
)

export default EditProfileForm
