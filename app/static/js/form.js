/**
 * form.js – Character counters and Bootstrap HTML5 validation
 * Used by: create.html, edit.html
 * No inline scripts needed; satisfies strict CSP (no unsafe-inline).
 */
'use strict';

(function () {
  document.addEventListener('DOMContentLoaded', function () {
    // --- Character counters ---
    var titleInput = document.getElementById('title');
    var titleCount = document.getElementById('titleCount');
    if (titleInput && titleCount) {
      titleInput.addEventListener('input', function () {
        titleCount.textContent = titleInput.value.length;
      });
    }

    var descInput = document.getElementById('description');
    var descCount = document.getElementById('descCount');
    if (descInput && descCount) {
      descInput.addEventListener('input', function () {
        descCount.textContent = descInput.value.length;
      });
    }

    // --- Bootstrap HTML5 validation ---
    var form = document.getElementById('taskForm') || document.getElementById('editForm');
    if (form) {
      form.addEventListener('submit', function (e) {
        if (!form.checkValidity()) {
          e.preventDefault();
          e.stopPropagation();
        }
        form.classList.add('was-validated');
      });
    }
  });
}());
