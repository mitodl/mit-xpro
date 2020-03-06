// @flow
import type { Course, BaseCourseRun, Program } from "./courseTypes"
import {PRODUCT_TYPE_COURSERUN, PRODUCT_TYPE_PROGRAM} from "../constants"
import type { ExtendedLegalAddress } from "./authTypes"

export type CheckoutResponse = {
  url: string,
  payload: CheckoutPayload,
  method?: ?string,
  errors?: string|Array<string>
};

export type CheckoutPayload = {
  "access_key": string,
  "amount": string,
  "consumer_id": string,
  "currency": string,
  "locale": string,
  "override_custom_cancel_page": string,
  "override_custom_receipt_page": string,
  "profile_id": string,
  "reference_number": string,
  "signature": string,
  "signed_date_time": string,
  "signed_field_names": string,
  "transaction_type": string,
  "transaction_uuid": string,
  "unsigned_field_names": string,
};

export type ProductVersion = {
  type: PRODUCT_TYPE_COURSERUN | PRODUCT_TYPE_PROGRAM,
  courses: Array<Course>,
  thumbnail_url: string,
  price: string,
  description: string,
  content_title: string,
  object_id: number,
  product_id: number,
  id: number,
  readable_id: string,
  run_tag: ?string,
  created_on: string,
  start_date: ?string,
}

export type BasketItem = ProductVersion & {
  run_ids: Array<number>,
}

export type CouponSelection = {
  code: string,
  amount: string,
  targets: Array<number>
}

export type DataConsentUser = {
  consent_date: string,
  consent_text: string,
  id: number,
  company: Company
}

export type B2BOrderStatus = {
  status: string,
  num_seats: number,
  total_price: string,
  item_price: string,
  discount: ?string,
  email: string,
  contract_number: ?string,
  product_version: ProductVersion,
}

export type B2BCouponStatusPayload = {
  code: string,
  product_id: number,
}

export type B2BCouponStatusResponse = {
  code: string,
  product_id: number,
  discount_percent: string,
}

export type BasketResponse = {
  items: Array<BasketItem>,
  coupons: Array<CouponSelection>,
  data_consents: Array<DataConsentUser>
}

type BasketItemPayload = {
  product_id: number|string,
  run_ids?: Array<number>,
}

export type BasketPayload = {
  items?: Array<BasketItemPayload>,
  coupons?: Array<{ code: string }>,
  data_consents?: Array<number>
}

export type ProductVersionSummary = {
  price: string,
  content_title: string,
  readable_id: string,
  start_date: Date
}

export type OrderLine = {
  price: string,
  quantity: number,
  total_paid: string,
  discount: string,
  content_title: string,
  readable_id: string,
  start_date: string,
  end_date: string
}

export type OrderSummary = {
  id: string,
  created_on: string,
  reference_number: string
}

export type CybersourceReceiptSummary = {
  card_number: string,
  card_type: ?string
}

export type OrderReceiptResponse = {
  coupon: ?string,
  lines: [OrderLine],
  purchaser: ExtendedLegalAddress,
  order: OrderSummary,
  receipt: ?CybersourceReceiptSummary
}

export type Company = {
  id: number,
  name: string,
}

export type CouponPayment = {
  id: number,
  created_on: Date,
  updated_on: Date,
  name: string
}

export type CouponPaymentVersion = {
  id: number,
  payment: CouponPayment,
  created_on: Date,
  updated_on: Date,
  tag: ?string,
  automatic: boolean,
  coupon_type: string,
  num_coupon_codes: number,
  max_redemptions: number,
  max_redemptions_per_user: number,
  amount: number,
  expiration_date: Date,
  activation_date: Date,
  payment_type: ?string,
  payment_transaction: ?string,
  company: ?Company,
  include_future_runs: boolean
}

export type Coupon = {
  name: string,
  coupon_code: string,
  enabled: boolean,
  created_on: Date,
  updated_on: Date
}

export type SimpleProduct = {
  id: number,
  product_type: string,
  visible_in_bulk_form: boolean,
}

export type Product = SimpleProduct & {
  title: string,
}

export type ProductDetail = Product & {
  latest_version: ProductVersion,
}

export type ProductMap = {
  [PRODUCT_TYPE_COURSERUN | PRODUCT_TYPE_PROGRAM]: {
    (string): [BaseCourseRun | Program]
  }
}

export type BulkCouponPayment = {
  id: number,
  name: string,
  version: CouponPaymentVersion,
  products: Array<SimpleProduct>,
  created_on: Date,
  updated_on: Date
}

export type BulkCouponPaymentsResponse = {
  coupon_payments: Array<BulkCouponPayment>,
  product_map: ProductMap
}

export type BulkCouponSendResponse = {
  emails:             Array<string>,
  bulk_assignment_id: number
}

export type B2BCheckoutPayload = {
  num_seats: number,
  product_version_id: number,
  discount_code: ?string,
  email: string,
  contract_number: ?string
}

export type EnrollmentCode = {
  coupon_code: number,
  product_id: number,
  expiration_date: Date,
  product_title: string,
  product_type: string,
  thumbnail_url: string,
  start_date: Date,
}
