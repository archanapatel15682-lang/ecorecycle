// ===============================
// Plastic Waste Recycling Website
// JavaScript
// ===============================


// Page load message
document.addEventListener("DOMContentLoaded", function () {
    console.log("EcoRecycle Website Loaded Successfully");
});


// ===============================
// Registration Form Validation
// ===============================

const registerForm = document.querySelector(
    'form[action="/register"]'
);

if (registerForm) {

    registerForm.addEventListener("submit", function (event) {

        const password = registerForm.querySelector(
            'input[name="password"]'
        ).value;

        if (password.length < 6) {
            alert("Password must be at least 6 characters.");
            event.preventDefault();
        }
    });
}


// ===============================
// Pickup Request Validation
// ===============================

const requestForm = document.querySelector(
    'form[action="/request"]'
);

if (requestForm) {

    requestForm.addEventListener("submit", function (event) {

        const quantity = requestForm.querySelector(
            'input[name="quantity"]'
        ).value;

        if (quantity <= 0) {
            alert("Please enter a valid plastic waste quantity.");
            event.preventDefault();
        }
    });
}


// ===============================
// Login Form
// ===============================

const loginForm = document.querySelector(
    'form[action="/login"]'
);

if (loginForm) {

    loginForm.addEventListener("submit", function () {
        console.log("Login form submitted");
    });
}