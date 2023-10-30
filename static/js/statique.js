var X={{names|safe}}
var Y={{ donne|safe }}
let ctx = document.getElementById('myChart').getContext('2d');
let labels = X;
let colorHex = ['#FB3640', '#EFCA08', '#43AA8B'];

let myChart = new Chart(ctx, {
type: 'pie',
data: {
    datasets: [{
    data: Y,
    backgroundColor: colorHex
    }],
    labels: labels
},
options: {
    responsive: true,
    legend: {
    position: 'bottom'
    },
    plugins: {
    datalabels: {
        color: '#fff',
        anchor: 'end',
        align: 'start',
        offset: -10,
        borderWidth: 2,
        borderColor: '#fff',
        borderRadius: 25,
        backgroundColor: (context) => {
        return context.dataset.backgroundColor;
        },
        font: {
        weight: 'bold',
        size: '10'
        },
        formatter: (value) => {
        return value + ' %';
        }
    }
    }
}
})





var studentsNames = {{studentsNames|safe}}
var absenceHours = {{absenceHours|safe}}
var barBgColor = {{barBgColor|safe}}
var barBorderColor = {{barBorderColor|safe}}

var ctxBar = document.getElementById('myChartBar').getContext('2d');
var myChartBar = new Chart(ctxBar, {
    type: 'bar',

    data: {
        labels: studentsNames,
        datasets: [{
            label: 'Statistiques of Students',
            data: absenceHours,
            backgroundColor: barBgColor,
            borderColor: barBorderColor,
            borderWidth: 2
        }]
    },
    options: {
        scales: {
          xAxes: [{
            ticks: {
              autoSkip: false
            }
          }]
        }
    }
});
