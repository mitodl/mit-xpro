// @flow
import { include } from "named-urls"
import qs from "query-string"

export const getNextParam = (search: string) => qs.parse(search).next || "/"

export const routes = {
  root:      "/",
  catalog:   "/catalog/",
  dashboard: "/dashboard/",
  logout:    "/logout/",

  // authentication related routes
  login: include("/login/", {
    begin:    "",
    password: "password/"
  }),

  register: include("/signup/", {
    begin:   "",
    confirm: "confirm/",
    details: "details/",
    extra:   "extra/"
  }),

  checkout: "/checkout/",

  ecommerceAdmin: include("/ecommerce/admin/", {
    index:      "",
    bulkEnroll: "enroll/",
    coupons:    "coupons/"
  })
}
