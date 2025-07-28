// Main JavaScript file for Work Order Management System

$(document).ready(function() {
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Form validation enhancement
    $('form').on('submit', function() {
        var $form = $(this);
        var $submitBtn = $form.find('button[type="submit"]');
        
        // Add loading state
        $submitBtn.prop('disabled', true);
        $submitBtn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...');
        
        // Re-enable after 3 seconds (fallback)
        setTimeout(function() {
            $submitBtn.prop('disabled', false);
            $submitBtn.html($submitBtn.data('original-text') || 'Submit');
        }, 3000);
    });

    // Store original button text
    $('button[type="submit"]').each(function() {
        $(this).data('original-text', $(this).html());
    });

    // Table row hover effect
    $('.table-hover tbody tr').hover(
        function() {
            $(this).addClass('table-active');
        },
        function() {
            $(this).removeClass('table-active');
        }
    );

    // Confirm delete actions
    $('.btn-delete').on('click', function(e) {
        if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
            e.preventDefault();
        }
    });

    // Dynamic form field updates
    $('select[name="campus"]').on('change', function() {
        var campusId = $(this).val();
        var officeSelect = $('select[name="office"]');
        
        if (campusId) {
            // Show loading state
            officeSelect.prop('disabled', true);
            officeSelect.html('<option value="">Loading offices...</option>');
            
            // Fetch offices for selected campus
            $.ajax({
                url: '/ajax/get-offices/',
                data: {
                    'campus_id': campusId
                },
                success: function(data) {
                    officeSelect.empty();
                    officeSelect.append('<option value="">Select Office</option>');
                    
                    $.each(data.offices, function(index, office) {
                        officeSelect.append(
                            $('<option></option>').val(office.id).text(office.name)
                        );
                    });
                    
                    officeSelect.prop('disabled', false);
                },
                error: function() {
                    officeSelect.html('<option value="">Error loading offices</option>');
                    officeSelect.prop('disabled', false);
                }
            });
        } else {
            officeSelect.empty();
            officeSelect.append('<option value="">Select Office</option>');
        }
    });

    // Status badge color updates
    function updateStatusBadges() {
        $('.badge').each(function() {
            var $badge = $(this);
            var text = $badge.text().toLowerCase();
            
            if (text.includes('pending')) {
                $badge.removeClass().addClass('badge bg-warning');
            } else if (text.includes('ongoing') || text.includes('on going')) {
                $badge.removeClass().addClass('badge bg-info');
            } else if (text.includes('completed')) {
                $badge.removeClass().addClass('badge bg-success');
            } else if (text.includes('cancelled')) {
                $badge.removeClass().addClass('badge bg-danger');
            }
        });
    }

    // Initialize status badges
    updateStatusBadges();

    // Search functionality for tables
    $('.table-search').on('keyup', function() {
        var value = $(this).val().toLowerCase();
        var table = $(this).data('table');
        
        $('#' + table + ' tbody tr').filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });

    // Export functionality (placeholder)
    $('.btn-export').on('click', function(e) {
        e.preventDefault();
        alert('Export functionality will be implemented here.');
    });

    // Print functionality
    $('.btn-print').on('click', function(e) {
        e.preventDefault();
        window.print();
    });

    // Refresh data periodically (for real-time updates)
    function refreshDashboard() {
        if (window.location.pathname === '/') {
            $.ajax({
                url: '/',
                success: function(data) {
                    // Update statistics if needed
                    // This is a placeholder for real-time updates
                }
            });
        }
    }

    // Refresh every 30 seconds if on dashboard
    if (window.location.pathname === '/') {
        setInterval(refreshDashboard, 30000);
    }

    // Mobile menu improvements
    $('.navbar-toggler').on('click', function() {
        $(this).toggleClass('collapsed');
    });

    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        var target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 70
            }, 1000);
        }
    });

    // Form field focus improvements
    $('.form-control, .form-select').on('focus', function() {
        $(this).parent().addClass('focused');
    }).on('blur', function() {
        $(this).parent().removeClass('focused');
    });

    // Loading state for AJAX requests
    $(document).on('ajaxStart', function() {
        $('body').addClass('loading');
    }).on('ajaxStop', function() {
        $('body').removeClass('loading');
    });

    // Success message auto-dismiss
    $('.alert-success').delay(3000).fadeOut(500);

    // Error message manual dismiss
    $('.alert-danger .btn-close').on('click', function() {
        $(this).closest('.alert').fadeOut(300);
    });

    // Initialize any additional plugins or features
    console.log('Work Order Management System initialized');
}); 

    // Technician Analytics Chart (Chart.js)
    if ($('#technicianChart').length) {
        const chartData = window.chartData || {};
        const statuses = ['pending', 'on_going', 'completed'];
        const colors = {
            pending: 'rgba(255, 193, 7, 0.7)',
            on_going: 'rgba(13, 202, 240, 0.7)',
            completed: 'rgba(25, 135, 84, 0.7)'
        };

        const labelsSet = new Set();
        const datasets = [];

        // Collect all dates across technicians
        Object.entries(chartData).forEach(([technician, dateMap]) => {
            Object.keys(dateMap).forEach(date => labelsSet.add(date));
        });

        const sortedLabels = Array.from(labelsSet).sort();

        statuses.forEach(status => {
            Object.entries(chartData).forEach(([technician, dateMap]) => {
                const data = sortedLabels.map(date => {
                    return dateMap[date]?.[status] || 0;
                });

                datasets.push({
                    label: `${technician} - ${status.replace('_', ' ').toUpperCase()}`,
                    data: data,
                    fill: false,
                    borderColor: colors[status],
                    backgroundColor: colors[status],
                    tension: 0.3
                });
            });
        });

        const ctx = document.getElementById('technicianChart').getContext('2d');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Work Orders'
                        }
                    }
                }
            }
        });
    }