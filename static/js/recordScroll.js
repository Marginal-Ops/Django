var tableHead = document.querySelectorAll('thead tr th');
tableHead.forEach(function(th){
    th.addEventListener('mouseenter', function(){
        th.setAttribute('title', 'sorted by' + th.innerHTML);
        th.style.cursor = 'pointer';
    })
    th.addEventListener('mouseleave', function(){
        th.removeAttribute('title');
        th.style.cursor = 'auto';
    })
})

function recordScrollPosition(event){
    var scrollPositionX = event.target.scrollLeft
    var scrollPositionY = event.target.scrollTop;
    localStorage.setItem('scrollPositionX', scrollPositionX);
    localStorage.setItem('scrollPositionY', scrollPositionY);
}
window.addEventListener('scroll', function(event){
    var windowX = window.scrollX;
    var windowY = window.scrollY;
    localStorage.setItem('windowX', windowX);
    localStorage.setItem('windowY', windowY);
})
window.addEventListener('load', function(){
    var content = document.getElementById('content');
    content.style.opacity = '1';
    var scrollPositionX = localStorage.getItem('scrollPositionX');
    var scrollPositionY = localStorage.getItem('scrollPositionY');
    console.log(scrollPositionX, scrollPositionY);
    if(scrollPositionX){
        document.querySelector('.my-table').scrollLeft = scrollPositionX;
    }
    if(scrollPositionY){
        document.querySelector('.my-table').scrollTop = scrollPositionY;
    }
    var windowX = localStorage.getItem('windowX');
    var windowY = localStorage.getItem('windowY');
    if(!windowX){
        windowX = 0;
    }
    if(!windowY){
        windowY = 0;
    }
    window.scrollTo( windowX, windowY);
})