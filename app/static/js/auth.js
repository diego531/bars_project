document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const roleSelect = document.getElementById('role');
    const loginButton = document.getElementById('loginButton');

    function checkInputs() {
        if (usernameInput.value.trim() !== '' &&
            passwordInput.value.trim() !== '' &&
            roleSelect.value !== '') {
            loginButton.disabled = false;
        } else {
            loginButton.disabled = true;
        }
    }

    usernameInput.addEventListener('input', checkInputs);
    passwordInput.addEventListener('input', checkInputs);
    roleSelect.addEventListener('change', checkInputs);

    // Llamar una vez al cargar para verificar el estado inicial 
    checkInputs();
});