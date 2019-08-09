Release Notes
=============

Version 0.16.4 (Released August 09, 2019)
--------------

- Make checkbox CSS rule more specific to catalog page (#969)

Version 0.16.3 (Released August 08, 2019)
--------------

- Include specific libraries which need transpiling (#959)
- Certificate page customization (CMS)
- Send enrollment/unenrollment emails
- Add support for IE11 (#956)

Version 0.16.1 (Released August 07, 2019)
--------------

- Fix incorrect password redirecting a user to the create account error page
- fix spaces around copoun code

Version 0.16.0 (Released August 06, 2019)
--------------

- Removed un existent field 'description'
- show archive enrollments on dashboard

Version 0.15.2 (Released August 05, 2019)
--------------

- Make voucher search more fuzzy and robust

Version 0.15.1 (Released August 02, 2019)
--------------

- Added explicit buffer size to uWSGI for cookie size issues
- remove redudant code
- js dependencies updated
- #929 Test fixes for program more dates
- Add more information to OrderAudit (#896)
- #679 Set an HTML title on React pages
- #914 Inactive products should not show on catalog
- #783 React should scroll to top on page load

Version 0.15.0 (Released August 01, 2019)
--------------

- Fixed auth flow to support incomplete registrations
- Update JS to fix caniuse-lite warning (#922)
- #882 display more dates on program page
- Added tagging for sentry errors to review apps
- #908 Wagtail admin generated URLs for child pages
- Add staff payment_type to CouponPaymentVersion (#898)

Version 0.14.1 (Released July 26, 2019)
--------------

- Update audit table serialization for program and course run enrollments (#861)
- fix styling on account exists message

Version 0.14.0 (Released July 25, 2019)
--------------

- Django admin for version tables (#830)
- Changed refund command to properly create order audit record
- Move hubspot contact sync task out of atomic transactions (#891)
- Add protection rules for ProductVersion, CouponVersion, CouponPaymentVersion (#795)
- Remove pep8 (#852)
- Use next_run_id for a default for the checkout page course run selection (#856)
- #885 Use catalog_details for featured product card
- disply message when account already exists

Version 0.13.6 (Released July 22, 2019)
--------------

- add heading feidl in who should enroll section

Version 0.13.5 (Released July 19, 2019)
--------------

- Upgrade Python dependencies (#845)
- dont load hero banner video on mobile devices
- - Wrong price for program

Version 0.13.4 (Released July 17, 2019)
--------------

- Update some JS dependencies (#829)

Version 0.13.3 (Released July 17, 2019)
--------------

- change "For Teams" in product subnav to "Enterprise" (#849)

Version 0.13.2 (Released July 16, 2019)
--------------

- Update voucher/templates/enroll.html
- Adjust style and fix typos
- Change voucher page style

Version 0.13.1 (Released July 15, 2019)
--------------

- Change URLs for vouchers to /boeing (#822)

Version 0.13.0 (Released July 15, 2019)
--------------

- Fixed enrollment commands - set order status, changed output (#794)
- fix comparison error when there is not start_data for course run (#836)
- Upgrade Django to 2.2, wagtail to 2.5.1 (#785)
- Used ImageChooserPanel

Version 0.12.3 (Released July 15, 2019)
--------------

- Fix typo with command arg
- Find old vouchers, ensure unique pdf names, add more error logging (#814)
- #792 Featured Product Card Thumbnail Fix
- #776 Allow Mixed Case Section Heads and Subheads

Version 0.12.2 (Released July 12, 2019)
--------------

- Fixed seed data bugs, added products, added deletion command
- Vouchers for django admin (#813)
- Added command to decrypt exports inquiry
- Automate environment variables
- set the background color of menu
- fix color of navigational arrows
- minor scss fixes

Version 0.12.1 (Released July 11, 2019)
--------------

- Update styling of enrolled button and add a check mark (#757)
- Change validation error message to Enrollment / Promotional Code (#797)
- Coerce fields to and from empty strings to fix React uncontrolled warnings (#781)
- new background for faculty section (#779)
- Added config to avoid OSERRORs from uwsgi
- Fix django admin search for CoursewareUser (#773)
- fix styling of header link in mobile view (#799)
- #743 Product page catalog details
- #800 Update Readme regarding index page setup management command
- #742 Learning Outcomes subhead convert to richtext
- fix regex for false positive, add test for invalid codes (#798)

Version 0.12.0 (Released July 09, 2019)
--------------

- Tasawer/fix account creation for Canadian users (#787)
- Upgrade sentry for Python and JS (#771)
- Add notification when user verifies their email (#760)
- update edX devstack installation steps. (#762)
- Coupon form improvements (#737)

Version 0.11.4 (Released July 05, 2019)
--------------

- fix hardcoded product page url (#768)
- Do not include unused_coupons field when syncing contacts to hubspot (#766)
- restyling catalog page to allow featured course (#706)

Version 0.11.3 (Released July 05, 2019)
--------------

- Create 'Coupons' group and additional properties for Hubspot deals (#628)
- Fixed and refactored enrollment commands
- redirect cms login to site signin
- Add text_id to ProductVersion (#692)
- Disable submit button while processing (#725)
- Fixed catalog login/signup urls
- Updating wording on the verification email
- Added catalog link to empty dashboard
- Update tests
- Switch hardcoded url to reverse url

Version 0.11.2 (Released July 03, 2019)
--------------

- Save order on enrollment objects (#676)
- #740 Product Page: Add commas to prices tile
- #739 Remove contractions from subnav
- #738 Remove course position label from product page
- autoComplete attributes for form fields (Chrome) (#730)
- Use site wide notifications for DashboardPage (#701)
- Revert "Remove the old PR template that is hiding the new one"
- Remove the old PR template that is hiding the new one
- Use program.title and run.title instead of product.description (#724)
- #715 Make cms subheads optional
- Added enrollment audit admin classes

Version 0.11.1 (Released July 02, 2019)
--------------

- #726 Remove blog link from footer
- removed phone number from footer

Version 0.11.0 (Released July 01, 2019)
--------------

- Reordered CMS model definitions
- Added 'create account' link to sign in page

Version 0.10.5 (Released June 28, 2019)
--------------

- #704 Watch Now button support for Youtube videos

Version 0.10.4 (Released June 28, 2019)
--------------

- just update the URL
- Fixed margin issue with site-wide notifications

Version 0.10.3 (Released June 27, 2019)
--------------

- Poll dashboard page for course run/program (#678)
- links to web.mit.edu should open in a new tab (#689)
- fix redirect url after signin (#658)
- Tweak notification CSS to prevent video from displaying over notifications (#688)
- Added robots.txt via django-robots

Version 0.10.2 (Released June 27, 2019)
--------------

- Fix header CSS for video on home page (#603)
- Removed links for course runs that have not yet started in edX
- Added course run enrollment email
- Upgraded deps
- Get unused coupons in the UserSerializer instead of CurrentUserRetrieveUpdateViewSet (#667)
- Send email to support when enrollments fail (#634)

Version 0.10.1 (Released June 26, 2019)
--------------

- #659 Catalog: prices are not displayed for some courses/programs
- Add redirect for cancellation and certain merchant fields to CyberSource payload (#604)
- Initial commit
- Remove texts in footer.
- Replace "login" with "Sign in"
- #464 Subnav font style should conform to designs
- Replace "validate" with "verify"

Version 0.10.0 (Released June 25, 2019)
--------------

- catalog page sorting based on start_date
- #610 TemplateDoesNotExist should raise a 404
- #615 Add `live` filter to unexpired course runs
- Remove enableReinitialize, resetForm manually (#637)

Version 0.9.4 (Released June 24, 2019)
-------------

- Proper fix for edx user creation race condition
- Fixed race conditions around user creation and repair scripts
- fix styling of youtube video
- Fixed race condition with AccessToken
- User hubspot-formatted purchaser id in OrderToDealSerializer (#625)
- Convert signout MixedLink to regular <a> tag (#621)
- Fix broken tests for DataConsentUser (#624)
- Clear runs from basket when selected item changes (#569)

Version 0.9.2 (Released June 21, 2019)
-------------

- Renumber migration (#613)
- Make enrollment company blankable in admin (#585)
- User menu (#560)
- Validate data consent agreements have been signed (#580)
- Added enrollment change management commands
- add CatalogPage as subpage to homepage
- add support for youtube videos
- Add hubspot sync all management command and handle line sync errors
- Move sync_hubspot_deal call out of atomic transaction (#571)
- Changed wagtail URLs to use course/program readable id

Version 0.9.1 (Released June 20, 2019)
-------------

- Fix login redirect regression
- Added enrollment change status fields
- Change basket PATCH to use product_id instead of id (#576)
- Add popup for anonymous users to login when they want to enroll (#575)
- Bump django from 2.1.7 to 2.1.9
- Add links to terms of service, privacy policy, refund policy (#525)
- Exclude expired and enrolled runs from courserun dropdowns (#524)
- Layout and wording fixes for register form
- Ensure order of runs is always the same to avoid test flakiness (#557)

Version 0.9.0 (Released June 18, 2019)
-------------

- fix course image thumbnail (#549)
- - link MIT logo in header to web.mit.edu
- Save voucher pdf uploads to S3 (#552)
- Added audit tables for enrollment tables
- - Align dashboard text
- #203 Product Page: fix right margin at 768px
- replace aqua color to more darker color (#529)
- add reply-to email address in emails (#528)
- Data consent checkbox (#519)
- Set checkout page to be accessible only to logged-in users
- fix
- #442 Product Page: Propel your career section
- #448 Courseware: space between text/"view detail"
- add live filter to subpages of home and product pages (#532)
- #466 Catalog: display popover on tab hover
- #468 Footer links should not spawn new tab
- Feedback from Abdul
- #450 Change yellow color because of accessibility
- Fixed site-wide notification styling
- Standardize button text
- updated the style.
- #173 Product page: support HLS video URL in header

Version 0.8.2 (Released June 13, 2019)
-------------

- Added unused coupon reminder alert
- Add enroll/view dashboard button on program page (#495)
- Refactor checkout page to use formik (#435)
- #407 Slick dot should not appear when no scroll
- Fix site  MIT xPRO name everywhere (#488)
- Prevent end users from patching other data consents (#480)
- Disable autoplay/infinite on logos carousel
- replace cost with price.
- #469 Testimonial Carousel Read More Link
- #510 Courseware carousel links not working
- #470 Product page: Subnav scroll fix
- #472 Program Page: don't show "view full program"
- #504 Enroll Now Button Overlapped
- #477 Disable infinite scroll on carousels
- #499 Clicking on Continue Reading Leads to 404
- Store information on voucher redemption and enrollment

Version 0.8.1 (Released June 12, 2019)
-------------

- Expand hubspot settings to sync deal, line, product
- update email template (#487)
- update styling of metadata tiles (#476)
- #428 #447 #448

Version 0.8.0 (Released June 11, 2019)
-------------

- Always show course run selections (#420)
- Fix missing price on product page (#409)

Version 0.7.2 (Released June 10, 2019)
-------------

- Accept product id, not product version id, on checkout page (#429)
- Added register error and denied pages
- Added validation for legal address fields that need it
- Add company to django admin (#445)
- max_redemptions should be 1 for single-use coupons (#417)

Version 0.7.1 (Released June 07, 2019)
-------------

- Add voucher app for course voucher upload and processing
- #157 Serve Catalog Page from Wagtail
- Added forgot password UI
- Check for Hubspot API errors (#396)

Version 0.7.0 (Released June 06, 2019)
-------------

- Implemented bulk enrollment checkout
- Bump djangorestframework from 3.9.1 to 3.9.4 (#414)
- Added template for config change request and PR checkbox
- Bumped drf version
- Integrate HubSpot in HomePage
- add seed resource pages in cms
- Feedback
- Rebase + Migration Conflict Fixes
- Feedback
- Removed unused import
- #155 Integrate Wagtail Routing
- View/edit profile pages (#346)
- Added support for redirect on register existing email
- Add hubspot form in footer
- #383 Add Home Page Instructions to Readme
- Enroll user in edX course runs on order success

Version 0.6.0 (Released May 30, 2019)
-------------

- Fix footer placement
- fix
- initial changes for companies slider
- Added sanctionsLists to the exports request if it is set
- #257: Home Page: Watch Video Button
- #257 Homepage: About MIT xPRO
- fix if only one date available (#382)
- SEO metadata for product pages (#334)
- Additional serializers for hubspot (#347)
- #352 Fix: Set HomePage as Parent of ResourcePage

Version 0.5.2 (Released May 29, 2019)
-------------

- #252 Home Page: Upcoming Courses
- Added workers to pgbouncer
- #250 #251: Home Page Header
- #258 Home Page: Inquire Now
- Trigger hubspot celery tasks where appropriate (#317)
- updated the footer and added links
- #323 Home Page Base
- allow marketing user to add/edit slug for resource pages (#350)
- fix error in console when no notificaiton available (#351)
- Updated login/registration styling
- Enroll/View Dashboard button (#336)
- add support of hub spot subscription.

Version 0.5.1 (Released May 24, 2019)
-------------

- Fixed encrypted response getting ascii-escaped
- add feature site nofication through cms (#309)
- Added hubspot ecommerce bridge (#276)
- Move Header Bundle back to Original Location
- Use query parameters when loading checkout page (#283)
- Fix coupon apply button bug (#296)
- Added SDN compliance api and data model
- Convert Sections to Generic

Version 0.5.0 (Released May 22, 2019)
-------------

- Added recaptcha to register page
- add resource page background image (#304)
- Track enrollment company (#287)
- Fixed dashboard styling again
- #193 Product Page: Subnav
- Updated notebook Dockerfile to be based off correct image

Version 0.4.1 (Released May 17, 2019)
-------------

- Issue #294 Fix Header Navbar Structure
- Additional kwargs, better efficiency for get_valid_coupon_versions query (#243)
- #161 Product Page: More Dates
- Styling for checkout page (#265)
- Renamed BulkEnrollmentDelivery to ProductCouponAssignment
- Misc improvements - fixed dashboard style regressions, handled empty dashboard, added rule to serve course catalog at root route, added enrollment admin classes
- Registration form - Step 2 (#236)
- Don't check CSRF token for index pages (#280)
- #146 Product Page: Faculty Carousel
- #145 Product Page: Learners Carousel
- add google analytics (#261)
- fix static path of banner image (#260)

Version 0.4.0 (Released May 14, 2019)
-------------

- Catalog page design update
- Tasawer/fix build (#262)
- Added user dashboard

Version 0.3.2 (Released May 10, 2019)
-------------

- Redirect users to /dashboard after CyberSource checkout (#234)
- make generic resource page in wagtail (#238)

Version 0.3.1 (Released May 09, 2019)
-------------

- Course run selection UI, various backend changes (#186)
- Registration detail form - Step 1 (#211)
- fix migration dependency after merge (#230)
- #223 add TOS page in CMS (#224)
- #147 Product Page: Courses Carousel
- #143 Product Page: Who Should Enroll
- For Teams Section (#148) (#189)
- Add faqs section (#220)
- CMS page design - What You will learn

Version 0.3.0 (Released May 07, 2019)
-------------

- Move deps into apt.txt so heroku installs them too
- Create new django app and utils for voucher pdf parsing
- update docker compose for local debugging
- Updated travis script section ANSI colors

Version 0.2.2 (Released May 02, 2019)
-------------

- CMS page design - What You will learn

Version 0.2.1 (Released May 02, 2019)
-------------

- Add unique constraints to some models which link other models together (#204)
- Added test script detail to Travis output

Version 0.2.0 (Released April 30, 2019)
-------------

- Added admin-only bulk enrollment form
- Data consent agreement models and API functions (#163)
- -
- changes after suggestion
- changes after suggestion
- Add the tiles on course detail page.

Version 0.1.2 (Released April 26, 2019)
-------------

- Added model for LegalAddress
- Added X-Access-Token header to protect registration API

Version 0.1.1 (Released April 25, 2019)
-------------

- Added a test to verify app.json
- Update basket API to handle courses (#154)
- Update redis (#172)
- Add Course Page Header
- Upgrade some dependencies (#167)

Version 0.1.0 (Released April 23, 2019)
-------------

- Front-end coupon creation (#129)
- Updated OpenEdxApiAuth refresh to account for expiration
- Fix running pytest for a subset of tests that don't create TEST_MEDIA_ROOT
- Checkout page (#108)
- Updated course catalog to match designs and use CMS data
- Update edx configuration docs to match latest setup
- Feedback
- Added settings and documentation to configure logout/login redirects
- seed data updates (#125)
- Switched routes back to "details"
- Added top nav to static pages
- API view for creating coupons (#114)
- Added validation for password length on register
- Added proper login handling of app context
- Rename CouponInvoice and CouponInvoiceVersion models (#115)
- Add thumbnail to basket API, use get_or_create for Basket (#110)
- Bumped djoser to avoid yanked version
- Basket REST API (#97)
- Checkout and order fulfillment ecommerce REST APIs  (#95)
- Added course enrollment button to course detail page
- Added APIs for creating edx api tokens
- Updated README with seed data instructions
- Fixed binding error
- Coupon functions and model changes (#77)
- Move template tag tests out of templatetags module
- Added model for edX tokens
- Fix app.json validity
- Combined auth steps for creating user and setting pw, name
- Bump docker to stretch debian
- Added MAILGUN_SENDER_DOMAIN and removed MAILGUN_URL from required settings
- Add RFC for coupons (#52)
- RFC for ecommerce REST APIs (#86)
- Added API call to create edX user when xpro user is created
- Fixed hijack release redirect url
- Added registration flow
- Ecommerce factories and utility functions (#69)
- Fixed settings tests locally
- Added courseware Django app
- Added login ui
- Add models for ecommerce (#41)
- Added basic course catalog
- RFC: Bot-friendly front-end
- Adding wagtail (#51)
- Added seed data command
- Added redux-query
- Add RFC for ecommerce models (#36)
- Added authentication app
- Added mail app
- Added simple REST API for interacting with course data
- Added course model admin classes
- Added user model, serializer, and read-only api
- Remove tox, move python test and linting to ./travis/python_tests.sh (#44)
- Add rule to serve static files on dev environments (#50)
- Added RFC for Open edX auth integration
- Adding github templates (#43)
- Fixed courses django app
- Updated readme, un-required mailgun vars, added notebook container
- Added initial course models
- RFC for ecommerce infrastructure (#25)
- Added RFC for storing course data
- Fix JS travis builds

