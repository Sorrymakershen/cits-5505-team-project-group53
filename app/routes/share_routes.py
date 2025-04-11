from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.travel_plan import TravelPlan, PlanShare
from app.models.user import User
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email

share_bp = Blueprint('share', __name__, url_prefix='/share')

class SharePlanForm(FlaskForm):
    email = StringField('用户邮箱', validators=[DataRequired(), Email()])
    permission = SelectField('权限类型', 
                           choices=[('view', '只能查看'), ('edit', '可以编辑')],
                           default='view')
    submit = SubmitField('分享')

@share_bp.route('/plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def share_plan(plan_id):
    """分享旅行计划给其他用户"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # 确认当前用户是计划的所有者
    if plan.user_id != current_user.id:
        flash('您无权分享此旅行计划', 'danger')
        return redirect(url_for('plan.view_plan', plan_id=plan_id))
    
    form = SharePlanForm()
    
    # 处理表单提交
    if form.validate_on_submit():
        # 查找接收用户
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user:
            flash(f'未找到邮箱为 {form.email.data} 的用户', 'danger')
        elif user.id == current_user.id:
            flash('您不能将计划分享给自己', 'warning')
        else:
            # 检查是否已经分享给这个用户
            existing_share = PlanShare.query.filter_by(
                plan_id=plan.id,
                shared_with_id=user.id
            ).first()
            
            if existing_share:
                # 更新现有的分享权限
                existing_share.permission = form.permission.data
                flash(f'已更新与 {user.username} 的分享权限', 'info')
            else:
                # 创建新的分享
                share = PlanShare(
                    plan_id=plan.id,
                    shared_by_id=current_user.id,
                    shared_with_id=user.id,
                    permission=form.permission.data
                )
                db.session.add(share)
                flash(f'已成功分享旅行计划给 {user.username}', 'success')
            
            db.session.commit()
    
    # 获取当前已分享的用户列表
    shared_users = []
    for share in plan.shares:
        user = User.query.get(share.shared_with_id)
        if user:
            shared_users.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'permission': share.permission
            })
    
    return render_template('share/share_plan.html', 
                          title=f'分享计划: {plan.title}',
                          plan=plan,
                          form=form,
                          shared_users=shared_users)

@share_bp.route('/remove/<int:plan_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_share(plan_id, user_id):
    """移除对特定用户的计划分享"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # 确认当前用户是计划的所有者
    if plan.user_id != current_user.id:
        return jsonify({'success': False, 'error': '无权限'}), 403
    
    # 查找并删除分享记录
    share = PlanShare.query.filter_by(
        plan_id=plan.id,
        shared_with_id=user_id
    ).first()
    
    if share:
        user = User.query.get(user_id)
        db.session.delete(share)
        db.session.commit()
        
        username = user.username if user else f'ID: {user_id}'
        return jsonify({
            'success': True,
            'message': f'已取消与 {username} 的分享'
        })
    else:
        return jsonify({'success': False, 'error': '未找到分享记录'}), 404

@share_bp.route('/shared-with-me')
@login_required
def shared_with_me():
    """查看其他用户分享的计划"""
    shared_plans = []
    
    for share in current_user.shared_with_me:
        plan = TravelPlan.query.get(share.plan_id)
        owner = User.query.get(plan.user_id) if plan else None
        
        if plan and owner:
            shared_plans.append({
                'plan': plan,
                'owner': owner,
                'permission': share.permission
            })
    
    return render_template('share/shared_with_me.html',
                          title='分享给我的计划',
                          shared_plans=shared_plans)
