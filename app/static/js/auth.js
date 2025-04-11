// 认证页面的交互脚本
document.addEventListener('DOMContentLoaded', function() {
    // 密码显示/隐藏切换功能
    const togglePassword = document.querySelectorAll('.password-toggle');
    togglePassword.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const password = document.querySelector(this.dataset.target);
            if (password.type === 'password') {
                password.type = 'text';
                this.innerHTML = '<i class="bi bi-eye-slash-fill"></i>';
            } else {
                password.type = 'password';
                this.innerHTML = '<i class="bi bi-eye-fill"></i>';
            }
        });
    });

    // 表单输入动画效果
    const formInputs = document.querySelectorAll('.auth-form .form-control');
    formInputs.forEach(function(input) {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focused');
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.parentElement.classList.remove('input-focused');
            }
        });
        
        // 初始检查，如果已有值则添加focused类
        if (input.value !== '') {
            input.parentElement.classList.add('input-focused');
        }
    });

    // 密码强度检测
    const passwordInput = document.querySelector('input[name="password"]');
    if (passwordInput) {
        const strengthIndicator = document.querySelector('.password-strength');
        const strengthMeter = document.querySelector('.strength-meter');
        const strengthText = document.querySelector('.strength-text');
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            
            if (password.length >= 8) strength += 1;
            if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 1;
            if (password.match(/\d/)) strength += 1;
            if (password.match(/[^a-zA-Z0-9]/)) strength += 1;
            
            strengthIndicator.className = 'password-strength';
            
            switch (strength) {
                case 0:
                    strengthIndicator.classList.add('');
                    strengthText.textContent = '请输入密码';
                    break;
                case 1:
                    strengthIndicator.classList.add('weak');
                    strengthText.textContent = '弱';
                    break;
                case 2:
                    strengthIndicator.classList.add('medium');
                    strengthText.textContent = '中等';
                    break;
                case 3:
                    strengthIndicator.classList.add('strong');
                    strengthText.textContent = '强';
                    break;
                case 4:
                    strengthIndicator.classList.add('very-strong');
                    strengthText.textContent = '非常强';
                    break;
            }
        });
    }

    // 表单验证反馈
    const emailInput = document.querySelector('input[name="email"]');
    if (emailInput) {
        const emailValidation = document.querySelector('.email-validation');
        emailInput.addEventListener('input', function() {
            const email = this.value;
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            
            if (email === '') {
                emailValidation.textContent = '';
                emailValidation.className = 'validation-message';
            } else if (emailRegex.test(email)) {
                emailValidation.textContent = '✓ 邮箱格式正确';
                emailValidation.className = 'validation-message valid';
            } else {
                emailValidation.textContent = '✗ 请输入有效的邮箱地址';
                emailValidation.className = 'validation-message invalid';
            }
        });
    }

    // 用户名验证反馈
    const usernameInput = document.querySelector('input[name="username"]');
    if (usernameInput) {
        const usernameValidation = document.querySelector('.username-validation');
        usernameInput.addEventListener('input', function() {
            const username = this.value;
            
            if (username === '') {
                usernameValidation.textContent = '';
                usernameValidation.className = 'validation-message';
            } else if (username.length < 3) {
                usernameValidation.textContent = '✗ 用户名需要至少3个字符';
                usernameValidation.className = 'validation-message invalid';
            } else {
                usernameValidation.textContent = '✓ 用户名格式正确';
                usernameValidation.className = 'validation-message valid';
            }
        });
    }

    // 密码确认匹配验证
    const password2Input = document.querySelector('input[name="password2"]');
    if (password2Input && passwordInput) {
        const password2Validation = document.querySelector('.password2-validation');
        
        function checkPasswordMatch() {
            if (password2Input.value === '') {
                password2Validation.textContent = '';
                password2Validation.className = 'validation-message';
            } else if (password2Input.value === passwordInput.value) {
                password2Validation.textContent = '✓ 密码匹配';
                password2Validation.className = 'validation-message valid';
            } else {
                password2Validation.textContent = '✗ 密码不匹配';
                password2Validation.className = 'validation-message invalid';
            }
        }
        
        password2Input.addEventListener('input', checkPasswordMatch);
        passwordInput.addEventListener('input', checkPasswordMatch);
    }

    // 表单提交动画
    const authForms = document.querySelectorAll('.auth-form');
    authForms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 处理中...';
            submitBtn.disabled = true;
        });
    });
});
