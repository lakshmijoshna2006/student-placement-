/**
 * Student Placement & Training Management System
 * Global JavaScript Utilities & Interactions
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } catch (e) {
                // Ignore if already closed
            }
        }, 5000);
    });

    // 2. Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 3. Client-side PDF Resume file validation
    const resumeInputs = document.querySelectorAll('input[type="file"][accept*="pdf"], input#resume');
    resumeInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const fileName = file.name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                const fileSize = file.size / (1024 * 1024); // in MB

                if (fileExt !== 'pdf') {
                    alert('Invalid file format! Please upload a valid PDF document (.pdf) only.');
                    this.value = '';
                    return;
                }

                if (fileSize > 10) {
                    alert('File size exceeds 10 MB limit! Please upload a smaller PDF resume.');
                    this.value = '';
                    return;
                }
            }
        });
    });

    // 4. Quick Table Live Search Filter
    const liveSearchInput = document.getElementById('tableLiveSearch');
    if (liveSearchInput) {
        liveSearchInput.addEventListener('keyup', function () {
            const query = this.value.toLowerCase();
            const targetTable = document.querySelector('.table-filterable tbody');
            if (targetTable) {
                const rows = targetTable.getElementsByTagName('tr');
                Array.from(rows).forEach(function (row) {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(query) ? '' : 'none';
                });
            }
        });
    }

    // 5. Password confirmation check on registration forms
    const regForm = document.querySelector('form.needs-password-match');
    if (regForm) {
        regForm.addEventListener('submit', function (e) {
            const pass = regForm.querySelector('input[name="password"]');
            const confirm = regForm.querySelector('input[name="confirm_password"]');
            if (pass && confirm && pass.value !== confirm.value) {
                e.preventDefault();
                alert('Passwords do not match! Please check and try again.');
                confirm.focus();
            }
        });
    }

    // 6. Delete Action Confirmation Modal Handling
    const deleteButtons = document.querySelectorAll('.btn-confirm-delete');
    deleteButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const itemName = this.getAttribute('data-item-name') || 'this record';
            if (!confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
                e.preventDefault();
            }
        });
    });
});
