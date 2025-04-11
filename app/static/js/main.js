// main.js - 旅行规划平台的主要JavaScript文件

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化Bootstrap提示工具
    initTooltips();
    
    // 处理日期选择器逻辑
    initDatePickers();
    
    // 平滑滚动
    initSmoothScrolling();
    
    // 初始化表单验证
    initFormValidation();
});

// 初始化Bootstrap提示工具
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 处理日期选择器逻辑
function initDatePickers() {
    // 获取开始日期和结束日期输入框
    const startDateInput = document.querySelector('input[name="start_date"]');
    const endDateInput = document.querySelector('input[name="end_date"]');
    
    if (startDateInput && endDateInput) {
        // 确保结束日期不早于开始日期
        startDateInput.addEventListener('change', function() {
            if (endDateInput.value && new Date(startDateInput.value) > new Date(endDateInput.value)) {
                endDateInput.value = startDateInput.value;
            }
            endDateInput.min = startDateInput.value;
        });
        
        // 设置初始最小日期
        if (startDateInput.value) {
            endDateInput.min = startDateInput.value;
        }
    }
}

// 平滑滚动到锚点
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

// 表单验证
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// 动态添加和删除行程项目
function addItineraryItem(dayId) {
    const dayContainer = document.getElementById(dayId);
    if (!dayContainer) return;
    
    const itemCount = dayContainer.querySelectorAll('.activity-item').length;
    const itemId = `${dayId}-item-${itemCount + 1}`;
    
    const template = `
        <div class="card activity-card mb-3" id="${itemId}">
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="mb-3">
                            <label class="form-label">时间</label>
                            <input type="time" class="form-control form-control-sm" name="${dayId}[${itemCount}][time]">
                        </div>
                    </div>
                    <div class="col-md-9">
                        <div class="mb-3">
                            <label class="form-label">活动名称</label>
                            <input type="text" class="form-control form-control-sm" name="${dayId}[${itemCount}][name]">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <div class="mb-3">
                            <label class="form-label">地点</label>
                            <input type="text" class="form-control form-control-sm" name="${dayId}[${itemCount}][location]">
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <div class="mb-3">
                            <label class="form-label">描述</label>
                            <textarea class="form-control form-control-sm" name="${dayId}[${itemCount}][description]" rows="2"></textarea>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-danger" onclick="removeItineraryItem('${itemId}')">
                    删除此活动
                </button>
            </div>
        </div>
    `;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template.trim();
    dayContainer.querySelector('.activities-container').appendChild(tempDiv.firstChild);
}

// 删除行程项目
function removeItineraryItem(itemId) {
    const item = document.getElementById(itemId);
    if (item) {
        item.remove();
    }
}

// 添加旅行日
function addTravelDay() {
    const daysContainer = document.getElementById('days-container');
    if (!daysContainer) return;
    
    const dayCount = daysContainer.querySelectorAll('.day-container').length;
    const dayId = `day-${dayCount + 1}`;
    
    const template = `
        <div class="card mb-4 day-container" id="${dayId}">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">第 ${dayCount + 1} 天</h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <label class="form-label">日期</label>
                    <input type="date" class="form-control" name="${dayId}[date]">
                </div>
                <h6>活动</h6>
                <div class="activities-container">
                    <!-- 这里将动态添加活动 -->
                </div>
                <button type="button" class="btn btn-sm btn-primary mt-3" onclick="addItineraryItem('${dayId}')">
                    添加活动
                </button>
            </div>
        </div>
    `;
    
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = template.trim();
    daysContainer.appendChild(tempDiv.firstChild);
}

// 生成随机的旅行计划（仅用于演示）
function generateDemoTravelPlan() {
    alert('这是一个示例功能，在实际应用中，将使用真实数据生成旅行计划。');
    // 在这里可以添加生成示例旅行计划的代码
}
