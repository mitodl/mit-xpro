// @flow
import { mount } from "enzyme/build"
import React from "react"
import { assert } from "chai"
import sinon from "sinon"
import { Field } from "formik"

import { CheckoutForm } from "./CheckoutForm"

import { makeBasketResponse } from "../../factories/ecommerce"
import {
  calculateDiscount,
  calculatePrice,
  formatPrice,
  formatRunTitle
} from "../../lib/ecommerce"
import { PRODUCT_TYPE_COURSERUN, PRODUCT_TYPE_PROGRAM } from "../../constants"
import { calcSelectedRunIds } from "../../containers/pages/CheckoutPage"

describe("CheckoutForm", () => {
  let sandbox,
    onSubmitStub,
    basket,
    coupon,
    couponCode,
    basketItem,
    submitCouponStub

  beforeEach(() => {
    basket = makeBasketResponse()
    basketItem = basket.items[0]
    coupon = basket.coupons[0]
    couponCode = "asdf"
    sandbox = sinon.createSandbox()
    onSubmitStub = sandbox.stub()
    submitCouponStub = sandbox.stub()
  })

  afterEach(() => {
    sandbox.restore()
  })

  const renderForm = (props = {}) =>
    mount(
      <CheckoutForm
        onSubmit={onSubmitStub}
        coupon={coupon}
        couponCode={couponCode}
        item={basketItem}
        submitCoupon={submitCouponStub}
        selectedRuns={{}}
        {...props}
      />
    )

  ;[true, false].forEach(hasCoupon => {
    it(`shows your basket ${
      hasCoupon ? "with" : "without"
    } a coupon`, async () => {
      basketItem.type = "program"
      const inner = await renderForm({
        coupon: hasCoupon ? coupon : null
      })
      assert.equal(inner.find(".item-type").text(), "Program")
      assert.equal(
        inner.find(".header .description").text(),
        basketItem.description
      )
      assert.equal(inner.find(".item-row").length, basketItem.courses.length)
      basketItem.courses.forEach((course, i) => {
        const courseRow = inner.find(".item-row").at(i)
        assert.equal(courseRow.find("img").prop("src"), course.thumbnail_url)
        assert.equal(courseRow.find("img").prop("alt"), course.title)
        assert.equal(courseRow.find(".title").text(), course.title)
      })
      assert.equal(
        inner.find(".price-row").text(),
        `Price:${formatPrice(basketItem.price)}`
      )

      if (hasCoupon) {
        assert.equal(
          inner.find(".discount-row").text(),
          `Discount:${formatPrice(calculateDiscount(basketItem, coupon))}`
        )
      } else {
        assert.isFalse(inner.find(".discount-row").exists())
      }

      assert.equal(
        inner.find(".total-row").text(),
        `Total:${formatPrice(
          calculatePrice(basketItem, hasCoupon ? coupon : null)
        )}`
      )
    })
  })

  it("renders a course run basket item", async () => {
    basketItem.type = PRODUCT_TYPE_COURSERUN

    const inner = await renderForm()

    assert.equal(inner.find(".item-type").text(), "Course")
    assert.equal(inner.find(".item-row").length, 1)
    assert.equal(inner.find("img").prop("src"), basketItem.thumbnail_url)
    assert.equal(inner.find("img").prop("alt"), basketItem.description)
    assert.equal(inner.find(".item-row .title").text(), basketItem.description)
  })
  ;[true, false].forEach(hasRuns => {
    it(`validates ${hasRuns ? "existing" : "present"} runs`, async () => {
      basketItem.type = PRODUCT_TYPE_PROGRAM
      const runs = {}
      if (hasRuns) {
        for (const course of basketItem.courses) {
          runs[course.id] = course.courseruns[0].id
        }
      }
      const inner = await renderForm({
        selectedRuns: runs
      })
      const fields = inner.find(".title-column").find(Field)
      basketItem.courses.forEach((course, i) => {
        const field = fields.at(i)
        const result = field.prop("validate")()
        if (hasRuns) {
          assert.isUndefined(result)
        } else {
          assert.equal(result, `No run selected for ${course.title}`)
        }
      })
    })
  })

  //
  ;[true, false].forEach(hasQueryParam => {
    it(`displays the coupon code${
      hasQueryParam ? " from a query parameter" : " from the coupon object"
    }`, async () => {
      const inner = await renderForm({
        couponCode: hasQueryParam ? couponCode : ""
      })
      inner.update()
      assert.equal(
        inner.find(".coupon-code-row input").prop("value"),
        hasQueryParam ? couponCode : coupon.code
      )
    })
  })

  it("loads the coupon code on mount", async () => {
    await renderForm()
    sinon.assert.calledWith(submitCouponStub, couponCode)
  })

  it("does not load the coupon code if there is none", async () => {
    await renderForm({ couponCode: "" })
    sinon.assert.notCalled(submitCouponStub)
  })

  it("does not load the coupon code if the code matches the coupon already in the basket", async () => {
    await renderForm({ couponCode: basket.coupons[0].code })
    sinon.assert.notCalled(submitCouponStub)
  })

  //
  ;[true, false].forEach(hasCouponCode => {
    it(`${
      hasCouponCode ? "submits" : "clears"
    } the coupon code after the apply button is clicked`, async () => {
      const inner = await renderForm({
        couponCode: hasCouponCode ? couponCode : "",
        coupon:     hasCouponCode ? coupon : null
      })
      submitCouponStub.reset()

      inner.find(".apply-button").prop("onClick")()
      sinon.assert.calledWith(submitCouponStub, hasCouponCode ? couponCode : "")
    })

    it(`${
      hasCouponCode ? "submits" : "clears"
    } the coupon code after the enter key is pressed`, async () => {
      const inner = await renderForm({
        couponCode: hasCouponCode ? couponCode : "",
        coupon:     hasCouponCode ? coupon : null
      })
      submitCouponStub.reset()

      inner.find("input.coupon-code-entry").prop("onKeyDown")({
        key:            "Enter",
        preventDefault: sandbox.stub()
      })
      sinon.assert.calledWith(submitCouponStub, hasCouponCode ? couponCode : "")
    })
  })

  it("does not do anything special if a key that's not Enter is pressed in the coupon code box", async () => {
    const inner = await renderForm()
    submitCouponStub.reset()
    inner.find("input.coupon-code-entry").prop("onKeyDown")({
      key: "x"
    })
    sinon.assert.notCalled(submitCouponStub)
  })

  it("does not show a select for course run product", async () => {
    basket.items[0].type = PRODUCT_TYPE_COURSERUN
    const inner = await renderForm()
    assert.equal(inner.find("select").length, 0)
  })

  it("shows a select with options for a program product, and updates a run", async () => {
    basketItem.type = PRODUCT_TYPE_PROGRAM
    const selectedRuns = calcSelectedRunIds(basketItem)
    const inner = await renderForm({
      selectedRuns
    })
    assert.equal(inner.find("select").length, basketItem.courses.length)
    basketItem.courses.forEach((course, i) => {
      const select = inner.find("select").at(i)

      const runId = selectedRuns[course.id]
      assert.equal(select.prop("value"), runId)

      const runs = course.courseruns
      assert.equal(select.find("option").length, runs.length + 1)
      const firstOption = select.find("option").at(0)
      assert.equal(firstOption.prop("value"), "")
      assert.equal(firstOption.text(), "Select a course run")

      runs.forEach((run, j) => {
        const runOption = select.find("option").at(j + 1)
        assert.equal(runOption.prop("value"), run.id)
        assert.equal(runOption.text(), formatRunTitle(run))
      })
    })
  })
})
