var table = document.getElementById("my-table");
var rows = Array.from(table.querySelectorAll("tbody tr"));
var asc = Array(rows.length).fill(true);

function sortTableByColumn(columnIndex) {

    rows.sort(function (a, b) {
        var tempDiva = document.createElement('div');
        var tempDivb = document.createElement('div');
        tempDiva.innerHTML = a.getElementsByTagName("td")[columnIndex-1].innerHTML;
        tempDivb.innerHTML = b.getElementsByTagName("td")[columnIndex-1].innerHTML;
        var aValue = tempDiva.querySelector('input').value;
        var bValue = tempDivb.querySelector('input').value;
        var a = parseFloat(aValue);
        var b = parseFloat(bValue);
        if (isNaN(a)){
            return 1;
        }else if(isNaN(b)){
            return -1;
        }else{
            return a - b;
        }
    });

    if(asc[columnIndex] === true){
        console.log('des sorting');
        asc[columnIndex] = false;
    }else{
        console.log('asc sorting');
        rows = [...rows].reverse();
        asc[columnIndex] = true;
    }
    

    var tbody = table.querySelector('tbody');
    table.classList.add('transition');
    while(tbody.firstChild){
        tbody.removeChild(tbody.firstChild);
    }

    rows.forEach(function (row) {
        tbody.appendChild(row);
    });

    table.classList.remove('transition');
    table.classList.add('animation');
    setTimeout(() => {
        table.classList.remove('animation');
    }, 500);
}

var headers = table.getElementsByTagName("th");
for (var i = 0; i < headers.length; i++) {
        headers[i].onclick = function () {
        var columnIndex = Array.from(headers).indexOf(this);
        sortTableByColumn(columnIndex);
    };
}