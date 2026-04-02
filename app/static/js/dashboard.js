/**
 * dashboard.js – Chart.js initialisation for the index/dashboard page.
 * Data is passed via data-* attributes on the <canvas> elements so
 * no inline scripts are needed (satisfies strict CSP).
 */
'use strict';

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // --- Status bar chart ---
    var statusCanvas = document.getElementById('statusChart');
    if (statusCanvas) {
      var sd = statusCanvas.dataset;
      new Chart(statusCanvas, {
        type: 'bar',
        data: {
          labels: ['To Do', 'In Progress', 'Done'],
          datasets: [{
            label: 'Tasks',
            data: [
              parseInt(sd.todo, 10),
              parseInt(sd.inprogress, 10),
              parseInt(sd.done, 10)
            ],
            backgroundColor: ['#6c757d', '#0d6efd', '#198754'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
        }
      });
    }

    // --- Priority doughnut chart ---
    var priorityCanvas = document.getElementById('priorityChart');
    if (priorityCanvas) {
      var pd = priorityCanvas.dataset;
      new Chart(priorityCanvas, {
        type: 'doughnut',
        data: {
          labels: ['Low', 'Medium', 'High'],
          datasets: [{
            data: [
              parseInt(pd.low, 10),
              parseInt(pd.medium, 10),
              parseInt(pd.high, 10)
            ],
            backgroundColor: ['#198754', '#ffc107', '#dc3545'],
            hoverOffset: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } }
        }
      });
    }
  });
}());
