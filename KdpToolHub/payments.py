import os
import stripe
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import User
from models import db
from utils import log_action
from datetime import datetime, timedelta

# Set Stripe API key (Test mode)
stripe.api_key = os.environ.get('STRIPE_TEST_SECRET_KEY', os.environ.get('STRIPE_SECRET_KEY', 'sk_test_dummy_key'))

YOUR_DOMAIN = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
if not YOUR_DOMAIN.startswith('http'):
    YOUR_DOMAIN = f'https://{YOUR_DOMAIN}'

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        plan_type = request.form.get('plan_type')
        
        # Define price IDs for different plans (Test Mode)
        # Only monthly plan is available
        price_ids = {
            'monthly': 'price_1Rmk6EFqKwGQTECIBFLj0b8h'  # $15.00/month (Test)
        }
        
        if plan_type not in price_ids:
            flash('Invalid plan type', 'error')
            return redirect(url_for('plans'))
        
        # Create or get Stripe customer
        # Always create a new customer in test mode to avoid Live/Test conflicts
        customer = stripe.Customer.create(
            email=current_user.email,
            name=f"{current_user.first_name} {current_user.last_name}",
            metadata={
                'user_id': current_user.id,
                'mode': 'test'
            }
        )
        # Update customer ID for test mode
        current_user.stripe_customer_id = customer.id
        db.session.commit()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            line_items=[
                {
                    'price': price_ids[plan_type],
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'{YOUR_DOMAIN}/payments/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{YOUR_DOMAIN}/payments/cancel',
            metadata={
                'user_id': current_user.id,
                'plan_type': plan_type
            }
        )
        
        log_action(current_user.id, 'payment_initiated', f'Initiated {plan_type} subscription', 
                  request.remote_addr, request.user_agent.string)
        
        return redirect(checkout_session.url, code=303)
        
    except stripe.error.StripeError as e:
        flash(f'Payment error: {str(e)}', 'error')
        return redirect(url_for('plans'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('plans'))

@payments_bp.route('/success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    
    # Prevent direct access - require valid session_id from Stripe
    if not session_id:
        flash('Access denied. Invalid payment session.', 'error')
        return redirect(url_for('plans'))
    
    # Check referrer to ensure coming from Stripe
    referrer = request.headers.get('Referer', '')
    if not referrer.startswith('https://checkout.stripe.com'):
        flash('Access denied. Please complete payment through proper channels.', 'error')
        return redirect(url_for('plans'))
    
    try:
        # Retrieve the checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Verify this session belongs to current user
        customer_id = checkout_session.customer
        if current_user.stripe_customer_id != customer_id:
            flash('Access denied. Payment session does not belong to current user.', 'error')
            return redirect(url_for('plans'))
        
        if checkout_session.payment_status == 'paid':
            # Update user subscription
            plan_type = checkout_session.metadata.get('plan_type')
            subscription_id = checkout_session.subscription
            
            current_user.subscription_type = plan_type
            current_user.stripe_subscription_id = subscription_id
            current_user.subscription_start = datetime.utcnow()
            
            # Set subscription end date (monthly only)
            current_user.subscription_end = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            
            # Send welcome email for new subscription
            from utils import send_subscription_email
            send_subscription_email(current_user, 'subscription_created')
            
            log_action(current_user.id, 'payment_completed', f'Completed {plan_type} subscription', 
                      request.remote_addr, request.user_agent.string)
            
            flash('Payment successful! Your subscription is now active.', 'success')
        else:
            flash('Payment was not completed successfully.', 'error')
            
    except stripe.error.StripeError as e:
        flash(f'Error verifying payment: {str(e)}', 'error')
        return redirect(url_for('plans'))
    
    return render_template('subscription/success.html')

@payments_bp.route('/cancel')
@login_required
def payment_cancel():
    # Check referrer to ensure coming from Stripe checkout
    referrer = request.headers.get('Referer', '')
    if not referrer.startswith('https://checkout.stripe.com'):
        flash('Access denied. This page is only accessible during payment cancellation.', 'error')
        return redirect(url_for('plans'))
    
    log_action(current_user.id, 'payment_cancelled', 'Cancelled payment', 
              request.remote_addr, request.user_agent.string)
    flash('Payment was cancelled.', 'info')
    return render_template('subscription/cancel.html')

@payments_bp.route('/manage-subscription')
@login_required
def manage_subscription():
    if not current_user.stripe_customer_id:
        flash('No subscription found.', 'error')
        return redirect(url_for('plans'))
    
    try:
        # Create a billing portal session
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f'{YOUR_DOMAIN}/tools/settings'
        )
        
        log_action(current_user.id, 'billing_portal_access', 'Accessed billing portal', 
                  request.remote_addr, request.user_agent.string)
        
        return redirect(session.url, code=303)
        
    except stripe.error.StripeError as e:
        flash(f'Error accessing billing portal: {str(e)}', 'error')
        return redirect(url_for('tools.settings'))

@payments_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    from werkzeug.security import check_password_hash
    
    data = request.get_json()
    current_password = data.get('currentPassword')
    confirmation = data.get('confirmation')
    
    # Verify password
    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'success': False, 'message': 'Invalid password'})
    
    # Verify confirmation text (server-side validation)
    if not confirmation or confirmation.strip() != 'CANCEL':
        return jsonify({'success': False, 'message': 'Security verification failed: You must type "CANCEL" exactly in capital letters to confirm'})
    
    if not current_user.stripe_subscription_id:
        return jsonify({'success': False, 'message': 'No active subscription found'})
    
    try:
        # Cancel the subscription immediately in Stripe
        stripe.Subscription.cancel(
            current_user.stripe_subscription_id
        )
        
        # Automatic refund process - no user choice required
        refund_message = ""
        refund_processed = False
        
        # Always attempt to process refund automatically
        try:
            charges = stripe.Charge.list(
                customer=current_user.stripe_customer_id,
                limit=1
            )
            if charges.data:
                latest_charge = charges.data[0]
                # Create refund for the latest charge
                refund = stripe.Refund.create(
                    charge=latest_charge.id,
                    reason='requested_by_customer'
                )
                refund_message = " A full refund has been automatically processed and will appear in your account within 5-10 business days."
                refund_processed = True
                log_action(current_user.id, 'automatic_refund_processed', f'Automatic refund processed: {refund.id}', 
                          request.remote_addr, request.user_agent.string)
            else:
                refund_message = " No recent charges found for refund. Please contact support if you believe this is an error."
                log_action(current_user.id, 'auto_refund_no_charges', 'Automatic refund attempted but no charges found', 
                          request.remote_addr, request.user_agent.string)
        except stripe.error.StripeError as refund_error:
            refund_message = " Automatic refund could not be processed. Please contact support for manual processing."
            log_action(current_user.id, 'auto_refund_failed', f'Automatic refund failed: {str(refund_error)}', 
                      request.remote_addr, request.user_agent.string)
        except Exception as e:
            refund_message = " Refund processing encountered an error. Please contact support for assistance."
            log_action(current_user.id, 'auto_refund_error', f'Automatic refund error: {str(e)}', 
                      request.remote_addr, request.user_agent.string)
        
        # Update user subscription status immediately
        current_user.subscription_type = 'free'
        current_user.stripe_subscription_id = None
        current_user.subscription_end = None
        current_user.daily_usage_count = 0  # Reset daily usage
        db.session.commit()
        
        # Send email notification for subscription cancellation
        from utils import send_subscription_email
        send_subscription_email(current_user, 'subscription_cancelled', refund_processed=refund_processed)
        
        log_action(current_user.id, 'subscription_cancelled_auto_refund', 'Cancelled subscription with automatic refund', 
                  request.remote_addr, request.user_agent.string)
        
        success_message = f'Subscription cancelled successfully.{refund_message}'
        return jsonify({'success': True, 'message': success_message})
        
    except stripe.error.StripeError as e:
        return jsonify({'success': False, 'message': f'Error cancelling subscription: {str(e)}'})

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'invoice.payment_succeeded':
        subscription = event['data']['object']
        handle_successful_payment(subscription)
    
    elif event['type'] == 'invoice.payment_failed':
        subscription = event['data']['object']
        handle_failed_payment(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)
    
    else:
        print(f'Unhandled event type: {event["type"]}')
    
    return 'Success', 200

def handle_successful_payment(invoice):
    """Handle successful payment webhook"""
    customer_id = invoice['customer']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        # Check if this is a new subscription (user was on free plan)
        is_new_subscription = user.subscription_type == 'free'
        
        # Update subscription
        user.subscription_type = 'monthly'
        user.subscription_end = datetime.utcnow() + timedelta(days=30)
        db.session.commit()
        
        # Send welcome email for new subscriptions
        if is_new_subscription:
            from utils import send_subscription_email
            send_subscription_email(user, 'subscription_created')
        
        log_action(user.id, 'payment_webhook_success', 'Payment successful via webhook', None, None)

def handle_failed_payment(invoice):
    """Handle failed payment webhook"""
    customer_id = invoice['customer']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        log_action(user.id, 'payment_webhook_failed', 'Payment failed via webhook', None, None)
        # Optionally send notification email or take other actions

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation webhook"""
    customer_id = subscription['customer']
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    
    if user:
        user.subscription_type = 'free'
        user.subscription_end = None  # Clear subscription end date
        user.stripe_subscription_id = None
        user.daily_usage_count = 0  # Reset daily usage
        db.session.commit()
        
        log_action(user.id, 'subscription_webhook_cancelled', 'Subscription cancelled via webhook', None, None)
