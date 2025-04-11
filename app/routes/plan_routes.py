from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.travel_plan import TravelPlan
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import datetime
import json

plan_bp = Blueprint('plan', __name__, url_prefix='/plans')

class TravelPlanForm(FlaskForm):
    title = StringField('计划名称', validators=[DataRequired()])
    destination = StringField('目的地', validators=[DataRequired()])
    start_date = DateField('开始日期', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('结束日期', validators=[DataRequired()], format='%Y-%m-%d')
    budget = FloatField('预算 (￥)', validators=[Optional(), NumberRange(min=0)])
    preferences = TextAreaField('偏好与兴趣', validators=[Optional()])
    submit = SubmitField('保存计划')

@plan_bp.route('/')
@login_required
def list_plans():
    """列出用户的所有旅行计划"""
    user_plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(TravelPlan.created_at.desc()).all()
    shared_plans = [share.travel_plan for share in current_user.shared_with_me]
    
    return render_template('plans/list.html', 
                          title='我的旅行计划',
                          user_plans=user_plans,
                          shared_plans=shared_plans)

@plan_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_plan():
    """创建新的旅行计划"""
    form = TravelPlanForm()
    
    if form.validate_on_submit():
        plan = TravelPlan(
            title=form.title.data,
            destination=form.destination.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            budget=form.budget.data,
            user_id=current_user.id
        )
        
        # 处理偏好数据
        if form.preferences.data:
            preferences = {
                'interests': form.preferences.data.split(','),
                'created_at': datetime.utcnow().isoformat()
            }
            plan.set_preferences(preferences)
        
        db.session.add(plan)
        db.session.commit()
        flash('旅行计划创建成功！', 'success')
        return redirect(url_for('plan.view_plan', plan_id=plan.id))
    
    return render_template('plans/create.html', 
                          title='创建旅行计划',
                          form=form)

@plan_bp.route('/<int:plan_id>')
@login_required
def view_plan(plan_id):
    """查看旅行计划详情"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # 检查用户是否有权访问该计划
    is_owner = plan.user_id == current_user.id
    is_shared = any(share.shared_with_id == current_user.id for share in plan.shares)
    
    if not (is_owner or is_shared):
        flash('您无权访问此旅行计划', 'danger')
        return redirect(url_for('plan.list_plans'))
    
    return render_template('plans/view.html', 
                          title=f'旅行计划: {plan.title}',
                          plan=plan,
                          is_owner=is_owner)

@plan_bp.route('/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """编辑旅行计划"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # 验证是否是计划所有者
    if plan.user_id != current_user.id:
        flash('您无权编辑此旅行计划', 'danger')
        return redirect(url_for('plan.view_plan', plan_id=plan_id))
    
    form = TravelPlanForm(obj=plan)
    
    if form.validate_on_submit():
        plan.title = form.title.data
        plan.destination = form.destination.data
        plan.start_date = form.start_date.data
        plan.end_date = form.end_date.data
        plan.budget = form.budget.data
        
        # 更新偏好数据
        if form.preferences.data:
            preferences = plan.get_preferences()
            preferences['interests'] = form.preferences.data.split(',')
            preferences['updated_at'] = datetime.utcnow().isoformat()
            plan.set_preferences(preferences)
        
        db.session.commit()
        flash('旅行计划已更新', 'success')
        return redirect(url_for('plan.view_plan', plan_id=plan.id))
    
    # 预填充偏好字段
    if plan.preferences:
        preferences = plan.get_preferences()
        if 'interests' in preferences:
            form.preferences.data = ', '.join(preferences['interests'])
    
    return render_template('plans/edit.html', 
                          title=f'编辑计划: {plan.title}',
                          form=form,
                          plan=plan)

@plan_bp.route('/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """删除旅行计划"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # 验证是否是计划所有者
    if plan.user_id != current_user.id:
        flash('您无权删除此旅行计划', 'danger')
        return redirect(url_for('plan.view_plan', plan_id=plan_id))
    
    db.session.delete(plan)
    db.session.commit()
    flash('旅行计划已删除', 'success')
    return redirect(url_for('plan.list_plans'))

@plan_bp.route('/<int:plan_id>/generate', methods=['POST'])
@login_required
def generate_plan(plan_id):
    """自动生成行程和预算分配"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # 验证是否有权操作该计划
    if plan.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权限'}), 403
    
    # 在实际项目中，这里会调用某些算法或AI服务来生成行程
    # 这里使用模拟数据作为示例
    
    # 生成行程示例
    itinerary = {
        'days': []
    }
    
    # 计算旅行天数
    delta = (plan.end_date - plan.start_date).days + 1
    
    # 为每一天生成行程
    for i in range(delta):
        day = {
            'day': i + 1,
            'date': (plan.start_date + db.func.interval(f'{i} days')).isoformat(),
            'activities': [
                {
                    'time': '09:00',
                    'name': '参观景点',
                    'location': f'{plan.destination}景点{i+1}',
                    'description': '体验当地文化'
                },
                {
                    'time': '12:00',
                    'name': '午餐',
                    'location': f'{plan.destination}餐厅{i+1}',
                    'description': '品尝当地美食'
                },
                {
                    'time': '14:00',
                    'name': '休闲活动',
                    'location': f'{plan.destination}公园{i+1}',
                    'description': '放松身心'
                },
                {
                    'time': '18:00',
                    'name': '晚餐',
                    'location': f'{plan.destination}餐厅{i+2}',
                    'description': '享用晚餐'
                }
            ]
        }
        itinerary['days'].append(day)
    
    # 生成预算分配
    total_budget = plan.budget or 5000  # 如果没有预算，使用默认值
    budget_allocation = {
        'total': total_budget,
        'categories': {
            '住宿': round(total_budget * 0.4, 2),
            '餐饮': round(total_budget * 0.3, 2),
            '交通': round(total_budget * 0.15, 2),
            '景点门票': round(total_budget * 0.1, 2),
            '购物与其他': round(total_budget * 0.05, 2)
        }
    }
    
    # 保存生成的数据
    plan.set_itinerary(itinerary)
    plan.set_budget_allocation(budget_allocation)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': '已成功生成旅行规划',
        'redirect': url_for('plan.view_plan', plan_id=plan.id)
    })
