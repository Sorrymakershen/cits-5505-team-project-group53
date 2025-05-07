function updateNavbarStyle() {
    const navbar = document.querySelector('.navbar');
    const scrollPosition = window.scrollY || document.documentElement.scrollTop;

    if (scrollPosition > 20) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
}

window.addEventListener('scroll', updateNavbarStyle);
window.addEventListener('load', updateNavbarStyle);
