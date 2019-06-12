// @flow
import React from "react"
import { Formik, Field, Form } from "formik"

import { formatErrors } from "../../lib/form"
import {
  calculateDiscount,
  calculatePrice,
  formatPrice,
  formatRunTitle
} from "../../lib/ecommerce"

import type { BasketItem, CouponSelection } from "../../flow/ecommerceTypes"

export type SetFieldError = (fieldName: string, fieldValue: any) => void
export type UpdateProduct = (
  productId: number,
  runId: number,
  setFieldError: SetFieldError
) => Promise<void>
export type Values = {
  runs: { [number]: string },
  couponCode: ?string
}
export type Actions = {
  setFieldError: SetFieldError,
  setErrors: (errors: Object) => void,
  setSubmitting: (submitting: boolean) => void,
  setValues: (values: Values) => void
}
type Errors = {
  runs?: string,
  coupons?: string,
  items?: string
}
type CommonProps = {
  item: BasketItem,
  coupon: ?CouponSelection,
  onSubmit: (Values, Actions) => Promise<void>,
  submitCoupon: (
    couponCode: ?string,
    setFieldError: SetFieldError
  ) => Promise<void>,
  updateProduct: UpdateProduct
}
type OuterProps = CommonProps & {
  couponCode: ?string,
  selectedRuns: Object
}
type InnerProps = CommonProps &
  Actions & {
    errors: Errors,
    values: Values,
    onMount: () => void
  }

class InnerCheckoutForm extends React.Component<InnerProps> {
  componentDidMount() {
    this.props.onMount()
  }

  renderBasketItem = () => {
    const { item, values, setFieldError, setValues, updateProduct } = this.props

    if (item.type === "program") {
      return (
        <React.Fragment>
          {item.courses.map(course => (
            <div className="flex-row item-row" key={course.id}>
              <div className="flex-row item-column">
                <img src={course.thumbnail_url} alt={course.title} />
              </div>
              <div className="title-column">
                <div className="title">{course.title}</div>
                <Field
                  component="select"
                  name={`runs.${course.id}`}
                  className="run-selector"
                >
                  <option value={""} key={"null"}>
                    Select a course run
                  </option>
                  {course.courseruns.map(run => (
                    <option value={run.id} key={run.id}>
                      {formatRunTitle(run)}
                    </option>
                  ))}
                </Field>
              </div>
            </div>
          ))}
        </React.Fragment>
      )
    } else {
      const course = item.courses[0]
      return (
        <div className="flex-row item-row">
          <div className="flex-row item-column">
            <img src={item.thumbnail_url} alt={item.description} />
          </div>
          <div className="title-column">
            <div className="title">{item.description}</div>
            <Field
              component="select"
              name={`runs.${course.id}`}
              className="run-selector"
              onChange={e => {
                setValues({
                  ...values,
                  runs: {
                    ...values.runs,
                    [course.id]: e.target.value
                  }
                })

                if (!e.target.value) {
                  return
                }

                const selectedRunId = parseInt(e.target.value)
                const run = course.courseruns.find(
                  run => run.id === selectedRunId
                )
                if (run && run.product_id) {
                  updateProduct(run.product_id, run.id, setFieldError)
                }
              }}
            >
              <option value={""} key={"null"}>
                Select a course run
              </option>
              {course.courseruns.map(run =>
                run.product_id ? (
                  <option value={run.id} key={run.id}>
                    {formatRunTitle(run)}
                  </option>
                ) : null
              )}
            </Field>
          </div>
        </div>
      )
    }
  }

  render() {
    const {
      errors,
      values,
      setFieldError,
      item,
      coupon,
      submitCoupon
    } = this.props
    return (
      <Form className="checkout-page container">
        <div className="row header">
          <div className="col-12">
            <div className="page-title">Checkout</div>
            <div className="purchase-text">
              You are about to purchase the following:
            </div>
            <div className="item-type">
              {item.type === "program" ? "Program" : "Course"}
            </div>
            <hr />
            {item.type === "program" ? (
              <span className="description">{item.description}</span>
            ) : null}
          </div>
        </div>
        <div className="row">
          <div className="col-lg-7">
            {this.renderBasketItem()}
            {formatErrors(errors.runs)}
            <div className="enrollment-input">
              <div className="enrollment-row">
                Enrollment / Promotional Code
              </div>
              <div className="flex-row coupon-code-row">
                <Field
                  type="text"
                  name="couponCode"
                  className="coupon-code-entry"
                  onKeyDown={event => {
                    if (event.key === "Enter") {
                      event.preventDefault()
                      submitCoupon(values.couponCode, setFieldError)
                    }
                  }}
                />
                <button
                  className="apply-button"
                  type="button"
                  onClick={() => submitCoupon(values.couponCode, setFieldError)}
                >
                  Apply
                </button>
              </div>
              {formatErrors(errors.coupons)}
            </div>
          </div>
          <div className="col-lg-5 order-summary-container">
            <div className="order-summary">
              <div className="title">Order Summary</div>
              <div className="flex-row price-row">
                <span>Price:</span>
                <span>{formatPrice(item.price)}</span>
              </div>
              {coupon ? (
                <div className="flex-row discount-row">
                  <span>Discount:</span>
                  <span>{formatPrice(calculateDiscount(item, coupon))}</span>
                </div>
              ) : null}
              <div className="bar" />
              <div className="flex-row total-row">
                <span>Total:</span>
                <span>{formatPrice(calculatePrice(item, coupon))}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="row">
          <div className="col-lg-7" />
          <div className="col-lg-5">
            <button className="checkout-button" type="submit">
              Place your order
            </button>
            {formatErrors(errors.items)}
          </div>
        </div>
      </Form>
    )
  }
}

export class CheckoutForm extends React.Component<OuterProps> {
  validate = (values: Values) => {
    const { item } = this.props
    const selectedRuns = values.runs

    const missingCourses = []
    for (const course of item.courses) {
      if (!selectedRuns[course.id]) {
        missingCourses.push(course.title)
      }
    }

    if (missingCourses.length) {
      return {
        runs: `No run selected for ${missingCourses.join(", ")}`
      }
    }

    return {}
  }

  render() {
    const {
      onSubmit,
      coupon,
      couponCode,
      item,
      selectedRuns,
      submitCoupon,
      updateProduct
    } = this.props

    return (
      <Formik
        onSubmit={onSubmit}
        initialValues={{
          couponCode: couponCode || (coupon ? coupon.code : ""),
          runs:       selectedRuns
        }}
        enableReinitialize={true}
        validate={this.validate}
        render={props => (
          <InnerCheckoutForm
            {...props}
            item={item}
            coupon={coupon}
            onSubmit={onSubmit}
            submitCoupon={submitCoupon}
            updateProduct={updateProduct}
            onMount={() => {
              // only submit if there is a couponCode query parameter,
              // and if it's different than one in the existing coupon
              if (couponCode && (!coupon || coupon.code !== couponCode)) {
                submitCoupon(couponCode, props.setFieldError)
              }
            }}
          />
        )}
        item={item}
        coupon={coupon}
      />
    )
  }
}
