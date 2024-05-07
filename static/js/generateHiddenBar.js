document.addEventListener("DOMContentLoaded", function() {
    var columnMenu = document.getElementById('column-menu');
    var tableContainer = document.getElementById('my-table');
    
    var table = tableContainer.getElementsByTagName('table')[0];
    var columnNames = Array.from(table.tHead.rows[0].cells).map(function(cell) {
        return cell.textContent.trim();
        });
    var columnIndex = Array.from(table.tBodies[0].rows[0].cells).map(function(_, index) {
        return index;
        });
        
        
    var headerRow = table.tHead.rows[0];

    columnNames.forEach(function(columnName, index) {
        if(index === 0){
            return;
        }
        var checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'column-toggle';
        checkbox.dataset.column = columnIndex[index];
        
        if (columnName.indexOf("(")){
            checkbox.checked = true;                
        }
        else{
            checkbox.checked = false;
            // 根据规则，隐藏
            var column = columnIndex[index];
            Array.from(table.tBodies[0].rows).forEach(function(row) {
                var cell = row.cells[column];
                cell.style.display = this.checked ? '' : 'none';
                }, 
            this);
            var headerCell = headerRow.cells[column];
            headerCell.style.display = this.checked ? '' : 'none';
        }

        
        var label = document.createElement('label');
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(columnName));
        
        var div = document.createElement('div');
        div.appendChild(label);
        
        columnMenu.appendChild(div);
        });
    
    var checkboxes = document.querySelectorAll('.column-toggle');
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            var column = this.dataset.column;
            var columnIndex = Array.from(table.tHead.rows[0].cells).map(function(cell, index) {
                return index;
                });
        
            Array.from(table.tBodies[0].rows).forEach(function(row) {
                var cell = row.cells[column];
                cell.style.display = this.checked ? '' : 'none';
                }, this
                );
        
            var headerCell = headerRow.cells[column];
            headerCell.style.display = this.checked ? '' : 'none';
            });
        });
    
    columnMenu.style.display = 'none';

    var dropdownButton = document.getElementById('dropdown-button');
    dropdownButton.addEventListener('click', function(){
            if(columnMenu.style.display === ''){
                columnMenu.style.display = 'none';
            }else{
                columnMenu.style.display = '';
            }
        })
    });
    