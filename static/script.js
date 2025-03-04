window.addEventListener("scroll", function() {
    var header = document.querySelector(".header");
    if (window.scrollY > 50) {  // When scrolled 50px or more
        header.classList.add("scrolled");
    } else {
        header.classList.remove("scrolled");
    }
});