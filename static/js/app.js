/* اسکریپت‌های مشترک رابط کاربری: نمایش/مخفی‌کردن رمز عبور + به‌روزرسانی دوره‌ای اعلان‌ها */
document.addEventListener('DOMContentLoaded', function () {
    // ۱) افزودن آیکن چشم به تمام ورودی‌های رمز عبور
    document.querySelectorAll('input[type="password"]').forEach(function (input) {
        if (input.dataset.eyeAttached) return;
        input.dataset.eyeAttached = '1';

        var wrapper = document.createElement('div');
        wrapper.className = 'position-relative';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        input.style.paddingLeft = '2.5rem';

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-sm position-absolute top-50 start-0 translate-middle-y text-muted';
        btn.style.border = 'none';
        btn.style.background = 'none';
        btn.innerHTML = '👁';
        btn.setAttribute('aria-label', 'نمایش/مخفی‌کردن رمز عبور');
        btn.addEventListener('click', function () {
            if (input.type === 'password') {
                input.type = 'text';
                btn.innerHTML = '🙈';
            } else {
                input.type = 'password';
                btn.innerHTML = '👁';
            }
        });
        wrapper.appendChild(btn);
    });

    // ۲) به‌روزرسانی دوره‌ای شمارنده اعلان‌های نخوانده (هر ۳۰ ثانیه)
    var bellCountEl = document.getElementById('notif-unread-count');
    if (bellCountEl && window.NOTIF_UNREAD_URL) {
        var refreshUnread = function () {
            fetch(window.NOTIF_UNREAD_URL, { credentials: 'same-origin' })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.unread_count > 0) {
                        bellCountEl.textContent = data.unread_count;
                        bellCountEl.classList.remove('d-none');
                    } else {
                        bellCountEl.classList.add('d-none');
                    }
                })
                .catch(function () {});
        };
        refreshUnread();
        setInterval(refreshUnread, 30000);
    }
});
