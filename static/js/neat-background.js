/*
   پس‌زمینه گرادیان متحرک نوار بالا با کتابخانه @firecms/neat.
   رنگ‌ها دقیقاً همان پالت برند سامانه (سبز جنگلی + نارنجی راهسازی) هستند
   تا نوار بالا با بقیه سامانه هماهنگ باشد. سرعت و شدت موج عمداً کم نگه
   داشته شده تا برای یک نرم‌افزار کاری/اداری بیش‌ازحد شلوغ به نظر نرسد.

   کتابخانه از CDN (jsDelivr) به‌صورت ماژول ES بارگذاری می‌شود؛ نیازی به
   نصب npm یا build جداگانه در پروژه Django نیست.
*/

import { NeatGradient } from "https://cdn.jsdelivr.net/npm/@firecms/neat/+esm";

document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById("neatBackgroundCanvas");
    if (!canvas) return;

    // اگر مرورگر کاربر خیلی قدیمی باشد و WebGL نداشته باشد، به‌آرامی از
    // خطا صرف‌نظر می‌کنیم و رنگ ساده CSS (تعریف‌شده در neat-background.css)
    // جایگزین می‌شود.
    try {
        new NeatGradient({
            ref: canvas,
            colors: [
                { color: "#0F2418", enabled: true }, // سبز تیره برند
                { color: "#15532D", enabled: true }, // سبز جنگلی اصلی
                { color: "#2F7A4A", enabled: true }, // سبز میانی
                { color: "#EA9A3E", enabled: true }, // نارنجی کهرمانی (تاکیدی)
                { color: "#D5E8D4", enabled: false }, // سبز روشن (خاموش، برای تنوع بیشتر در آینده)
            ],
            speed: 1.1,
            horizontalPressure: 3,
            verticalPressure: 3,
            waveFrequencyX: 1.5,
            waveFrequencyY: 2,
            waveAmplitude: 4,
            shadows: 1,
            highlights: 3,
            colorBrightness: 1,
            colorSaturation: 5,
            wireframe: false,
            colorBlending: 7,
            backgroundColor: "#15532D",
            backgroundAlpha: 1,
            resolution: 1,
            grainScale: 2,
            grainSparsity: 0,
            grainIntensity: 0.03,
            grainSpeed: 1,
            flowEnabled: true,
            flowDistortionA: 0,
            flowDistortionB: 0,
            flowScale: 1,
            flowEase: 0,
            shapeType: "plane",
            cameraLock: true,
        });
    } catch (err) {
        // بی‌سروصدا رد می‌شویم؛ رنگ پس‌زمینه ساده در CSS جایگزین می‌شود
        console.warn("پس‌زمینه گرادیان بارگذاری نشد (مرورگر پشتیبانی نمی‌کند):", err);
    }
});
