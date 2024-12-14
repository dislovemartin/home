import type { Stripe, StripeElements, StripeCardElement as StripeCardElementType } from '@stripe/stripe-js';

declare global {
  interface Window {
    Stripe?: (key: string) => Stripe;
  }
}

export type { Stripe, StripeElements };

export interface StripeCardElementChangeEvent {
  elementType: 'card';
  error?: {
    type: string;
    code: string;
    message: string;
  };
  complete: boolean;
  empty: boolean;
  value?: {
    postalCode?: string;
  };
}

export type StripeCardElement = StripeCardElementType;

export interface StripePaymentMethod {
  id: string;
  type: string;
  card?: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
  };
}

export interface PaymentIntent {
  id: string;
  client_secret: string;
  status: 'requires_payment_method' | 'requires_confirmation' | 'requires_action' | 'processing' | 'requires_capture' | 'canceled' | 'succeeded';
  amount: number;
  currency: string;
  payment_method?: string;
  payment_method_types: string[];
  created: number;
} 