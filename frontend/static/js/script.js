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
    // Calendar navigation handlers
    const prevBtn = document.getElementById('calendarPrevBtn');
    const nextBtn = document.getElementById('calendarNextBtn');
    const monthLabel = document.getElementById('calendarMonthLabel');

    function parseLabel(labelEl){
        if(!labelEl) return null;
        // Expected format: "Month YYYY"
        const parts = labelEl.textContent.trim().split(/\s+/);
        if(parts.length < 2) return null;
        const monthName = parts[0];
        const year = parseInt(parts[1], 10);
        const monthIndex = [
            'January','February','March','April','May','June','July','August','September','October','November','December'
        ].indexOf(monthName);
        if(monthIndex === -1 || isNaN(year)) return null;
        return {year, month: monthIndex+1};
    }

    function navigate(delta){
        const parsed = parseLabel(monthLabel);
        if(!parsed) return;
        let {year, month} = parsed;
        month += delta;
        if(month === 0){ month = 12; year -= 1; }
        if(month === 13){ month = 1; year += 1; }
        const params = new URLSearchParams(window.location.search);
        params.set('year', year);
        params.set('month', month);
        window.location.search = params.toString();
    }

    if(prevBtn){ prevBtn.addEventListener('click', () => navigate(-1)); }
    if(nextBtn){ nextBtn.addEventListener('click', () => navigate(1)); }

    // Unread total on dashboard
    const unreadEl = document.getElementById('unread-total');
    const sidebarUnread = document.getElementById('sidebar-unread');
    if (unreadEl) {
      fetch('/api/chats/unread')
        .then(r => r.ok ? r.json() : {})
        .then(map => {
          const total = Object.values(map || {}).reduce((a, b) => a + (parseInt(b, 10) || 0), 0);
          unreadEl.textContent = total;
          if (sidebarUnread) {
            sidebarUnread.textContent = total;
            sidebarUnread.style.display = total > 0 ? 'inline-flex' : 'none';
          }
        })
        .catch(() => {});
    }
    
    // Also update when the page becomes visible (user switches back to tab)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            updateNotificationBadge();
        }
    });
});
