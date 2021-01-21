import notifications from "../notifications.js"
import tooltip from "../tooltip.js"
import hero from "../hero.js"
import testimonialsCarousel from "../testimonials_carousel.js"
import coursewareCarousel from "../courseware_carousel.js"
import textVideoSection from "../text_video_section.js"
import imageCarousel from "../image_carousel.js"
import facultyCarousel from "../faculty_carousel.js"

document.addEventListener("DOMContentLoaded", function() {
  notifications()
  tooltip()
  hero()
  testimonialsCarousel()
  coursewareCarousel()
  textVideoSection()
  imageCarousel()
  facultyCarousel()
})
