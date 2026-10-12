import os
from flask import Flask, render_template, request, redirect, url_for, flash
from extensions import db
import models
from auth import register_user, authenticate_user
from inventory import create_inventory_item, list_inventory_items
from requests_module import create_relief_request, list_relief_requests
from assignments import allocate_request, list_assignments, update_assignment_status
from volunteers import list_volunteers, get_volunteer_assignments
from notifications import list_notifications, mark_notification_read, broadcast_emergency_alert
from incidents import create_incident, list_incidents
from dashboard import get_dashboard_summary
from reports import generate_relief_report

def create_app(test_config=None):
    app=Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY","dev-only-change-me"),SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL","sqlite:///disaster_relief.db"),SQLALCHEMY_TRACK_MODIFICATIONS=False)
    if test_config: app.config.update(test_config)
    db.init_app(app)
    with app.app_context(): db.create_all()

    @app.get('/')
    def index(): return render_template('dashboard.html',summary=get_dashboard_summary())

    @app.route('/register',methods=['GET','POST'])
    def register():
        if request.method=='POST':
            try:
                register_user(request.form.get('name',''),request.form.get('phone'),request.form.get('email',''),request.form.get('password',''),request.form.get('role','Victim'))
                flash('Account created. You can now log in.','success'); return redirect(url_for('login'))
            except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return render_template('register.html')

    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            user=authenticate_user(request.form.get('email'),request.form.get('password'))
            if user: flash(f'Login successful for {user.name} ({user.role}). Demo only: session login is not persisted.','success'); return redirect(url_for('index'))
            flash('Invalid email or password.','danger')
        return render_template('login.html')

    @app.route('/inventory',methods=['GET','POST'])
    def inventory_page():
        if request.method=='POST':
            try: create_inventory_item(request.form['category'],request.form['quantity'],request.form['storage_location'],request.form.get('expiry_date') or None,request.form.get('threshold',0)); flash('Inventory item registered.','success'); return redirect(url_for('inventory_page'))
            except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return render_template('inventory.html',items=list_inventory_items())

    @app.route('/requests',methods=['GET','POST'])
    def requests_page():
        if request.method=='POST':
            try: create_relief_request(int(request.form['user_id']),request.form['category'],int(request.form['quantity']),request.form['urgency'],float(request.form['latitude']),float(request.form['longitude'])); flash('Relief request submitted.','success'); return redirect(url_for('requests_page'))
            except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return render_template('requests.html',requests=list_relief_requests(),users=models.User.query.order_by(models.User.user_id).all())

    @app.route('/assignments',methods=['GET','POST'])
    def assignments_page():
        if request.method=='POST':
            try: allocate_request(int(request.form['request_id']),int(request.form['volunteer_id']),int(request.form['item_id'])); flash('Resource allocated and volunteer notified.','success'); return redirect(url_for('assignments_page'))
            except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return render_template('assignments.html',assignments=list_assignments(),requests=list_relief_requests(status='Pending'),volunteers=list_volunteers(),items=list_inventory_items(available_only=True))

    @app.post('/assignments/<int:task_id>/status')
    def assignment_status(task_id):
        try: update_assignment_status(task_id,request.form['status']); flash('Assignment status updated.','success')
        except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return redirect(url_for('assignments_page'))

    @app.get('/volunteers')
    def volunteers_page(): return render_template('volunteers.html',volunteers=list_volunteers())

    @app.get('/notifications')
    def notifications_page(): return render_template('notifications.html', notifications=models.Notification.query.order_by(models.Notification.created_at.desc()).all(), users=models.User.query.order_by(models.User.name).all())

    @app.post('/notifications/<int:notification_id>/read')
    def notification_read(notification_id):
        try: mark_notification_read(notification_id,int(request.form['user_id'])); flash('Notification marked as read.','success')
        except Exception as e: flash(str(e),'danger')
        return redirect(url_for('notifications_page'))

    @app.route('/alerts',methods=['GET','POST'])
    def alerts_page():
        if request.method=='POST':
            try:
                raw_ids = request.form.getlist('recipient_user_ids')
                recipient_ids = [int(value) for value in raw_ids] if raw_ids else None
                created = broadcast_emergency_alert(request.form.get('message', ''), request.form.get('type','Emergency'), recipient_ids)
                flash(f'Emergency alert sent to {len(created)} recipient(s).','success'); return redirect(url_for('alerts_page'))
            except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return render_template('alerts.html', users=models.User.query.order_by(models.User.name).all())

    @app.route('/incidents',methods=['GET','POST'])
    def incidents_page():
        if request.method=='POST':
            try: create_incident(request.form['title'],request.form.get('description',''),float(request.form['latitude']),float(request.form['longitude']),request.form['severity'],int(request.form['reported_by'])); flash('Incident registered.','success'); return redirect(url_for('incidents_page'))
            except Exception as e: db.session.rollback(); flash(str(e),'danger')
        return render_template('incidents.html',incidents=list_incidents(),users=models.User.query.all())

    @app.get('/reports')
    def reports_page(): return render_template('reports.html',rows=generate_relief_report())
    return app

app=create_app()
if __name__=='__main__': app.run(debug=True)
