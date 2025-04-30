window.addEventListener('scroll', function() {
    var colorChangeElement = document.querySelector('.navbar');
    var scrollPosition = window.scrollY || document.documentElement.scrollTop; // 获取滚动条位置

    if (scrollPosition > 20) {
        colorChangeElement.style.backgroundColor = '#EDF8FE'; // 超过20像素，背景变为红色
    } else {
        colorChangeElement.style.backgroundColor = 'white'; // 否则为白色
    }
});
window.onload = function(){
    var colorChangeElement = document.querySelector('.navbar');
    var scrollPosition = window.scrollY || document.documentElement.scrollTop; // 获取滚动条位置
 
    if (scrollPosition > 20) {
        colorChangeElement.style.backgroundColor = '#EDF8FE'; // 超过20像素，背景变为红色
    } else {
        colorChangeElement.style.backgroundColor = 'white'; // 否则为白色
    }
}