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


var trace1 = {
  type: 'bar',
  x: [1, 2, 3, 4],
  y: [5, 10, 2, 8],
  marker: {
      color: '#C8A2C8',
      line: {
          width: 2.5
      }
  }
};

var data = [ trace1 ];

var layout = {
  title: 'Responsive to window\'s size!',
  font: {size: 18}
};

var config = {responsive: true}

Plotly.newPlot('myDiv', data, layout, config );



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
        .then(response => response.json())
        .then(data => {
            const newCount = data.count;

            if (badge) {
                if (newCount > 0) {
                    badge.textContent = newCount;
                    badge.style.display = 'flex';
                } else {
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

// Poll every 30 seconds
setInterval(updateNotificationBadge, 30000);

// Run on page load
document.addEventListener('DOMContentLoaded', updateNotificationBadge);
