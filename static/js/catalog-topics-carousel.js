/*eslint-env jquery*/
/*eslint semi: ["error", "always"]*/

export default function topicsCarousel() {
  $(".topics-slider").slick({
    rows: 2,
    slidesToShow: 3,
    slidesToScroll: 1,
    dots: false,
    infinite: false,
    autoplay: false,
    responsive: [
      {
        breakpoint: 1024,
        settings: {
          slidesToShow: 3,
          slidesToScroll: 3,
        },
      },
      {
        breakpoint: 992,
        settings: {
          slidesToShow: 2,
          slidesToScroll: 1,
        },
      },
      {
        breakpoint: 767,
        settings: {
          slidesToShow: 1,
          slidesToScroll: 1,
        },
      },
    ],
  });

  $(".topics-slider .slide").on("click", function () {
    const targetUrl = $(this).data("url");
    window.location.href = targetUrl;
  });
}
