function disableButton(optbtn,femail,otp,reset)
{
    var email_val = document.getElementById(femail.id).value;
    if (email_val.length > 10){
        optbtn.disabled = true;
        document.getElementById(femail.id).disabled = true;
        document.getElementById(otp.id).disabled = false;
        document.getElementById(reset.id).disabled = false;
    }
}


$(document).ready(function(){
    $(".multi_select").selectpicker();
})

// === Real-time Notification Badge Update ===
function updateNotificationBadge() {
    const notificationIcon = document.getElementById('notification-icon');
    if (!notificationIcon) return;

    // Get the current displayed count
    const badge = document.getElementById('notification-badge');
    const currentCount = badge ? parseInt(badge.textContent, 10) || 0 : 0;

    fetch('/notifications/count')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const newCount = data.count || 0;

            if (badge) {
                if (newCount > 0) {
                    badge.textContent = newCount;
                    badge.classList.remove('hidden');
                    badge.style.display = 'flex';
                } else {
                    badge.classList.add('hidden');
                    badge.style.display = 'none';
                }
            }

            // If new notifications have arrived, shake the bell
            if (newCount > 0 && newCount > currentCount) {
                notificationIcon.classList.add('shake');
                // Remove the class after the animation finishes
                setTimeout(() => {
                    notificationIcon.classList.remove('shake');
                }, 820); // Corresponds to animation duration
            }
        })
        .catch(err => {
            console.error('Error fetching notification count:', err);
        });
}

// Poll every 10 seconds instead of 30 for more responsive updates
setInterval(updateNotificationBadge, 10000);

// Run on page load
document.addEventListener('DOMContentLoaded', function() {
    updateNotificationBadge();
    
    // Also update when the page becomes visible (user switches back to tab)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            updateNotificationBadge();
        }
    });
});
