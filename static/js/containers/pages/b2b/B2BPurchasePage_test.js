// @flow
import sinon from "sinon"
import { assert } from "chai"

import IntegrationTestHelper from "../../../util/integration_test_helper"
import B2BPurchasePage, {
  B2BPurchasePage as InnerB2BPurchasePage
} from "./B2BPurchasePage"

import * as formFuncs from "../../../lib/form"
import { makeProduct } from "../../../factories/ecommerce"

describe("B2BPurchasePage", () => {
  let helper, renderPage, products

  beforeEach(() => {
    helper = new IntegrationTestHelper()
    products = [makeProduct(), makeProduct(), makeProduct()]
    renderPage = helper.configureHOCRenderer(
      B2BPurchasePage,
      InnerB2BPurchasePage,
      {
        entities: {
          products
        }
      },
      {
        location: {
          search: ""
        }
      }
    )
  })

  afterEach(() => {
    helper.cleanup()
  })

  it("loads products on mount", async () => {
    await renderPage()
    helper.handleRequestStub.withArgs("/api/products/", "POST").returns({
      body:   undefined,
      status: 200
    })
  })

  it("renders a form", async () => {
    const { inner } = await renderPage()
    const props = inner.find("B2BPurchaseForm").props()
    assert.deepEqual(props.products, products)
  })

  it("submits the form to Cybersource", async () => {
    const { inner } = await renderPage()

    const url = "/api/b2b/checkout/"
    const payload = { pay: "load" }
    helper.handleRequestStub.withArgs("/api/b2b/checkout/", "POST").returns({
      body: {
        url,
        payload
      },
      status: 200
    })
    const submitStub = helper.sandbox.stub()
    const form = document.createElement("form")
    // $FlowFixMe: need to overwrite this function to mock it
    form.submit = submitStub
    const createFormStub = helper.sandbox
      .stub(formFuncs, "createCyberSourceForm")
      .returns(form)
    const selectedProduct = products[1]
    const values = {
      product:   selectedProduct.id,
      num_seats: 5,
      email:     "email@example.com"
    }
    const actions = {
      setSubmitting: helper.sandbox.stub(),
      setErrors:     helper.sandbox.stub()
    }
    await inner.find("B2BPurchaseForm").prop("onSubmit")(values, actions)
    sinon.assert.calledWith(createFormStub, url, payload)
    sinon.assert.calledWith(submitStub)
    sinon.assert.calledWith(
      helper.handleRequestStub,
      "/api/b2b/checkout/",
      "POST",
      {
        body: {
          email:              values.email,
          product_version_id: selectedProduct.latest_version.id,
          num_seats:          values.num_seats
        },
        headers: {
          "X-CSRFTOKEN": null
        },
        credentials: undefined
      }
    )
    sinon.assert.calledWith(actions.setSubmitting, false)
    sinon.assert.notCalled(actions.setErrors)
  })

  it("submits the form but redirects to a location instead of submitting a form to CyberSource", async () => {
    const { inner } = await renderPage()

    const url = "/a/b/c/"
    const payload = { pay: "load" }
    helper.handleRequestStub.withArgs("/api/b2b/checkout/", "POST").returns({
      body: {
        url,
        payload,
        method: "GET"
      },
      status: 200
    })
    const submitStub = helper.sandbox.stub()
    const form = document.createElement("form")
    // $FlowFixMe: need to overwrite this function to mock it
    form.submit = submitStub
    const actions = {
      setSubmitting: helper.sandbox.stub(),
      setErrors:     helper.sandbox.stub()
    }
    const selectedProduct = products[1]
    const values = {
      product:   selectedProduct.id,
      num_seats: 5,
      email:     "email@example.com"
    }
    await inner.find("B2BPurchaseForm").prop("onSubmit")(values, actions)

    sinon.assert.notCalled(actions.setErrors)
    sinon.assert.calledWith(actions.setSubmitting, false)
    assert.isTrue(window.location.toString().endsWith(url))
  })

  it("submits the form but receives an error", async () => {
    const { inner } = await renderPage()

    const errors = "some errors 😩"
    helper.handleRequestStub.withArgs("/api/b2b/checkout/", "POST").returns({
      body: {
        errors
      },
      status: 500
    })
    const selectedProduct = products[1]
    const values = {
      product:   selectedProduct.id,
      num_seats: 5,
      email:     "email@example.com"
    }
    const actions = {
      setSubmitting: helper.sandbox.stub(),
      setErrors:     helper.sandbox.stub()
    }
    await inner.find("B2BPurchaseForm").prop("onSubmit")(values, actions)
    sinon.assert.calledWith(actions.setErrors, errors)
    sinon.assert.calledWith(actions.setSubmitting, false)
  })

  it("sets requestPending when a request is in progress", async () => {
    const { inner } = await renderPage({
      queries: {
        b2bCheckoutMutation: {
          isPending: true
        }
      }
    })
    assert.isTrue(inner.find("B2BPurchaseForm").prop("requestPending"))
  })
})
