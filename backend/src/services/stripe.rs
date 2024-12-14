use anyhow::Result;
use serde::{Deserialize, Serialize};
use stripe::{
    Client, CreatePaymentIntent, Currency, Customer, PaymentIntent,
    PaymentMethod, PaymentMethodCard, Webhook,
};
use uuid::Uuid;

use crate::{
    config::Config,
    models::{
        payment::{CardDetails, PaymentIntent as DbPaymentIntent},
        subscription::Subscription,
    },
};

pub struct StripeService {
    client: Client,
    webhook_secret: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CreatePaymentIntentRequest {
    pub subscription_id: Uuid,
}

impl StripeService {
    pub fn new(config: &Config) -> Self {
        Self {
            client: Client::new(&config.stripe_secret_key),
            webhook_secret: config.stripe_webhook_secret.clone(),
        }
    }

    pub async fn create_payment_intent(
        &self,
        user_id: Uuid,
        subscription: &Subscription,
    ) -> Result<DbPaymentIntent> {
        // Create or get Stripe customer
        let customer = self.get_or_create_customer(user_id).await?;

        // Create payment intent
        let mut create_intent = CreatePaymentIntent::new(
            stripe::Amount::from_f64_in_currency(Currency::USD, subscription.price_monthly)?,
            Currency::USD,
        );
        create_intent.customer = Some(&customer.id);
        create_intent.setup_future_usage = Some(stripe::PaymentIntentSetupFutureUsage::OffSession);

        let payment_intent = PaymentIntent::create(&self.client, create_intent).await?;

        // Create payment intent in our database
        let db_payment_intent = DbPaymentIntent::create(
            &crate::DB_POOL,
            user_id,
            subscription.id,
            payment_intent.id.to_string(),
            subscription.price_monthly,
            payment_intent.client_secret.unwrap_or_default(),
        )
        .await?;

        Ok(db_payment_intent)
    }

    pub async fn handle_webhook(&self, payload: &[u8], signature: &str) -> Result<()> {
        let event = Webhook::construct_event(payload, signature, &self.webhook_secret)?;

        match event.type_ {
            stripe::EventType::PaymentIntentSucceeded => {
                if let Some(payment_intent) = event.data.object.as_payment_intent() {
                    self.handle_payment_success(payment_intent).await?;
                }
            }
            stripe::EventType::PaymentIntentPaymentFailed => {
                if let Some(payment_intent) = event.data.object.as_payment_intent() {
                    self.handle_payment_failure(payment_intent).await?;
                }
            }
            _ => (),
        }

        Ok(())
    }

    async fn handle_payment_success(&self, payment_intent: &PaymentIntent) -> Result<()> {
        let payment_intent_id = payment_intent.id.to_string();
        
        // Update payment intent status
        DbPaymentIntent::update_status(
            &crate::DB_POOL,
            &payment_intent_id,
            "succeeded",
        ).await?;

        // Get payment intent from our database
        if let Some(db_payment_intent) = DbPaymentIntent::get_by_stripe_id(
            &crate::DB_POOL,
            &payment_intent_id,
        ).await? {
            // Create payment history record
            crate::models::payment::PaymentHistory::create(
                &crate::DB_POOL,
                db_payment_intent.user_id,
                db_payment_intent.subscription_id,
                db_payment_intent.id,
                db_payment_intent.amount,
                "succeeded",
            ).await?;

            // Activate subscription
            crate::models::subscription::UserSubscription::activate(
                &crate::DB_POOL,
                db_payment_intent.user_id,
                db_payment_intent.subscription_id,
            ).await?;
        }

        Ok(())
    }

    async fn handle_payment_failure(&self, payment_intent: &PaymentIntent) -> Result<()> {
        let payment_intent_id = payment_intent.id.to_string();
        
        // Update payment intent status
        DbPaymentIntent::update_status(
            &crate::DB_POOL,
            &payment_intent_id,
            "failed",
        ).await?;

        // Get payment intent from our database
        if let Some(db_payment_intent) = DbPaymentIntent::get_by_stripe_id(
            &crate::DB_POOL,
            &payment_intent_id,
        ).await? {
            // Create payment history record
            crate::models::payment::PaymentHistory::create(
                &crate::DB_POOL,
                db_payment_intent.user_id,
                db_payment_intent.subscription_id,
                db_payment_intent.id,
                db_payment_intent.amount,
                "failed",
            ).await?;
        }

        Ok(())
    }

    async fn get_or_create_customer(&self, user_id: Uuid) -> Result<Customer> {
        // Try to find existing customer by user ID metadata
        let mut customers = Customer::list(
            &self.client,
            &stripe::ListCustomers {
                metadata: Some(vec![("user_id", user_id.to_string())]),
                ..Default::default()
            },
        )
        .await?;

        if let Some(customer) = customers.data.pop() {
            Ok(customer)
        } else {
            // Create new customer
            let mut create_customer = stripe::CreateCustomer::new();
            create_customer.metadata = Some(vec![("user_id", user_id.to_string())].into_iter().collect());
            
            Ok(Customer::create(&self.client, create_customer).await?)
        }
    }

    pub async fn attach_payment_method(
        &self,
        user_id: Uuid,
        payment_method_id: &str,
    ) -> Result<CardDetails> {
        let payment_method = PaymentMethod::retrieve(&self.client, payment_method_id).await?;
        
        if let Some(PaymentMethodCard {
            brand,
            last4,
            exp_month,
            exp_year,
            ..
        }) = payment_method.card
        {
            let card_details = CardDetails {
                brand: brand.to_string(),
                last4,
                exp_month,
                exp_year,
            };

            // Save payment method to our database
            crate::models::payment::PaymentMethod::create(
                &crate::DB_POOL,
                user_id,
                payment_method_id.to_string(),
                Some(card_details.clone()),
            )
            .await?;

            Ok(card_details)
        } else {
            anyhow::bail!("Invalid payment method type")
        }
    }
} 