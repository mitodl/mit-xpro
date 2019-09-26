// @flow
import React from "react"
import sinon from "sinon"
import { assert } from "chai"
import { mount } from "enzyme"

import { BulkEnrollmentForm } from "./BulkEnrollmentForm"
import { makeBulkCouponPayment, makeProduct } from "../../factories/ecommerce"
import { findFormikFieldByName } from "../../lib/test_utils"
import { PRODUCT_TYPE_PROGRAM, PRODUCT_TYPE_COURSERUN } from "../../constants"

describe("BulkEnrollment", () => {
  let sandbox, submitRequestStub, bulkCouponPayments, productMap

  const defaultSubmitResponse = {
    body: {
      emails: ["a@b.com"]
    },
    status: 200
  }

  const createTestData = () => {
    const firstPayment = makeBulkCouponPayment(),
      secondPayment = makeBulkCouponPayment(),
      firstProduct = makeProduct(),
      secondProduct = makeProduct(),
      thirdProduct = makeProduct()

    firstProduct.product_type = PRODUCT_TYPE_COURSERUN
    secondProduct.product_type = PRODUCT_TYPE_COURSERUN
    thirdProduct.product_type = PRODUCT_TYPE_PROGRAM

    firstPayment.products = [firstProduct, secondProduct]
    secondPayment.products = [firstProduct]

    return {
      bulkCouponPayments: [firstPayment, secondPayment],
      products:           {
        [PRODUCT_TYPE_COURSERUN]: {
          [firstProduct.id.toString()]:  firstProduct,
          [secondProduct.id.toString()]: secondProduct
        },
        [PRODUCT_TYPE_PROGRAM]: {
          [thirdProduct.id.toString()]: thirdProduct
        }
      }
    }
  }

  const renderForm = (props = {}) =>
    mount(
      <BulkEnrollmentForm
        bulkCouponPayments={bulkCouponPayments}
        productMap={productMap}
        submitRequest={submitRequestStub}
        {...props}
      />
    )

  beforeEach(() => {
    sandbox = sinon.createSandbox()
    submitRequestStub = sandbox.stub().returns(defaultSubmitResponse)
    const testData = createTestData()
    bulkCouponPayments = testData.bulkCouponPayments
    productMap = testData.products
  })

  it("submits a request to send bulk enrollment emails", async () => {
    const dummyPayload = { dummy: "payload" }
    const setSubmitting = sandbox.stub(),
      resetForm = sandbox.stub(),
      setErrors = sandbox.stub()

    const wrapper = renderForm()
    const formProps = wrapper.find("Formik").props()
    await formProps.onSubmit(dummyPayload, {
      setSubmitting,
      resetForm,
      setErrors
    })
    sinon.assert.calledWith(submitRequestStub, dummyPayload)
    sinon.assert.calledWith(setSubmitting, false)
    sinon.assert.calledOnce(resetForm)
  })

  it("renders the form", () => {
    const wrapper = renderForm()
    const form = wrapper.find("Formik")
    assert.isTrue(form.find("input[name='users_file']").exists())
    assert.isTrue(findFormikFieldByName(form, "product_id").exists())
    assert.isTrue(findFormikFieldByName(form, "coupon_payment_id").exists())
    assert.isTrue(form.find("button[type='submit']").exists())
  })
})
