from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """首页 - 展示应用介绍和引导用户注册/登录"""
    return render_template('main/index.html', title='旅行规划平台 - 首页')

@main_bp.route('/about')
def about():
    """关于页面 - 详细介绍应用功能和使用方法"""
    return render_template('main/about.html', title='关于我们')

@main_bp.route('/dashboard')
def dashboard():
    """用户仪表板 - 提供用户个人数据和功能入口"""
    if not current_user.is_authenticated:
        flash('请先登录以访问仪表板', 'warning')
        return redirect(url_for('auth.login'))
    
    return render_template('main/dashboard.html', title='个人仪表板')
