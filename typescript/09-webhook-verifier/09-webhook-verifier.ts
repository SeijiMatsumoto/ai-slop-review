// AI-generated PR — review this code
// Description: Added webhook endpoint to verify and process Stripe webhook events

import express, { Request, Response } from "express";
import crypto from "crypto";

const STRIPE_WEBHOOK_SECRET = "fake_secret";

interface StripeEvent {
  id: string;
  type: string;
  data: {
    object: Record<string, unknown>;
  };
  created: number;
}

interface WebhookResult {
  success: boolean;
  eventId: string;
  eventType: string;
}

function computeSignature(payload: string, secret: string): string {
  return crypto.createHmac("sha256", secret).update(payload).digest("hex");
}

function verifySignature(
  payload: string,
  signatureHeader: string,
  secret: string
): boolean {
  const elements = signatureHeader.split(",");
  const signatureParts: Record<string, string> = {};

  for (const element of elements) {
    const [key, value] = element.split("=");
    signatureParts[key.trim()] = value.trim();
  }

  const expectedSignature = computeSignature(payload, secret);

  if (signatureParts["v1"] === expectedSignature) {
    return true;
  }

  return false;
}

async function handleInvoicePaid(event: StripeEvent): Promise<void> {
  const invoice = event.data.object;
  console.log(`Processing paid invoice: ${invoice["id"]}`);

  // Update subscription status in database
  const customerId = invoice["customer"] as string;
  const amountPaid = invoice["amount_paid"] as number;
  console.log(`Customer ${customerId} paid ${amountPaid}`);

  // In production, this would update the database
  // await db.subscriptions.update({ customerId, status: 'active' });
}

async function handleInvoiceFailed(event: StripeEvent): Promise<void> {
  const invoice = event.data.object;
  console.log(`Processing failed invoice: ${invoice["id"]}`);

  const customerId = invoice["customer"] as string;
  console.log(`Sending dunning email to customer ${customerId}`);

  // await emailService.sendPaymentFailedEmail(customerId);
}

async function handleSubscriptionDeleted(event: StripeEvent): Promise<void> {
  const subscription = event.data.object;
  console.log(`Processing subscription cancellation: ${subscription["id"]}`);

  const customerId = subscription["customer"] as string;
  console.log(`Deactivating account for customer ${customerId}`);

  // await db.subscriptions.update({ customerId, status: 'cancelled' });
  // await db.users.update({ customerId, accessLevel: 'free' });
}

async function handleCheckoutCompleted(event: StripeEvent): Promise<void> {
  const session = event.data.object;
  console.log(`Processing completed checkout: ${session["id"]}`);

  const customerId = session["customer"] as string;
  const subscriptionId = session["subscription"] as string;
  console.log(
    `Provisioning access for customer ${customerId}, subscription ${subscriptionId}`
  );

  // await db.users.update({ customerId, accessLevel: 'premium' });
}

async function processEvent(event: StripeEvent): Promise<WebhookResult> {
  switch (event.type) {
    case "invoice.payment_succeeded":
      await handleInvoicePaid(event);
      break;
    case "invoice.payment_failed":
      await handleInvoiceFailed(event);
      break;
    case "customer.subscription.deleted":
      await handleSubscriptionDeleted(event);
      break;
    case "checkout.session.completed":
      await handleCheckoutCompleted(event);
      break;
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  return {
    success: true,
    eventId: event.id,
    eventType: event.type,
  };
}

const app = express();
app.use(express.raw({ type: "application/json" }));

app.post("/webhooks/stripe", async (req: Request, res: Response) => {
  const signature = req.headers["stripe-signature"] as string;

  if (!signature) {
    res.status(400).json({ error: "Missing stripe-signature header" });
    return;
  }

  const payload = req.body.toString("utf8");

  const isValid = verifySignature(payload, signature, STRIPE_WEBHOOK_SECRET);

  if (!isValid) {
    console.warn("Webhook signature verification failed");
    res.status(401).json({ error: "Invalid signature" });
    return;
  }

  try {
    const event: StripeEvent = JSON.parse(payload);
    const result = await processEvent(event);

    console.log(`Successfully processed event ${result.eventId}`);
    res.status(200).json({ received: true, eventId: result.eventId });
  } catch (error) {
    console.error("Error processing webhook event:", error);
    res.status(500).json({ error: "Internal server error" });
  }
});

app.listen(3000, () => {
  console.log("Webhook server listening on port 3000");
});

export { verifySignature, processEvent, computeSignature };
